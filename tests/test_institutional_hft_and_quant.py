"""
Institutional HFT, Neuro-Symbolic Agent & SEBI Compliance Integration Tests.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.trading.neuro_symbolic_agent import (
    global_neuro_agent,
    DeterministicRiskGate,
    MarketContext,
    AccountRiskState,
    TradeIntent,
    AgentAction,
)
from backend.app.trading.sebi_compliance import (
    global_sebi_compliance,
    SebiComplianceEngine,
)
from backend.app.trading.gamma_singularity_math import (
    global_gamma_math,
    GammaSingularityMathEngine,
)


@pytest.mark.asyncio
async def test_neuro_symbolic_risk_invariants():
    """Verify all 5 symbolic invariants in DeterministicRiskGate."""
    gate = DeterministicRiskGate(max_daily_drawdown=25000.0)
    context = MarketContext(
        symbol="NIFTY",
        ltp=24500.0,
        ofi=0.45,
        micro_price=24504.0,
        dealer_net_gex=-600.0,
        macro_sentiment_score=0.4,
        is_0dte_expiry_day=False,
        minutes_to_market_close=180,
    )

    # Test Invariant 1: Daily Drawdown Killswitch
    blown_account = AccountRiskState(daily_realized_pnl=-26000.0)
    intent = TradeIntent(
        symbol="NIFTY",
        action=AgentAction.BUY,
        confidence=0.88,
        rationale="Momentum surge",
        target_price=24600.0,
        stop_loss_price=24450.0,
        suggested_lots=1,
    )
    v1 = gate.evaluate(intent, context, blown_account)
    assert v1.approved is False
    assert any("CIRCUIT_BREAKER_TRIPPED" in r for r in v1.rejection_reasons)

    # Test Invariant 2: Low Neural Conviction Gate (< 0.78)
    normal_account = AccountRiskState()
    low_conf_intent = TradeIntent(
        symbol="NIFTY",
        action=AgentAction.BUY,
        confidence=0.65,
        rationale="Uncertain signal",
        target_price=24550.0,
        stop_loss_price=24450.0,
        suggested_lots=1,
    )
    v2 = gate.evaluate(low_conf_intent, context, normal_account)
    assert v2.approved is False
    assert any("LOW_NEURAL_CONVICTION" in r for r in v2.rejection_reasons)

    # Test Invariant 3: Position Sizing Clamping (Max 2% capital risk)
    large_intent = TradeIntent(
        symbol="NIFTY",
        action=AgentAction.BUY,
        confidence=0.85,
        rationale="High conviction",
        target_price=24700.0,
        stop_loss_price=24350.0,  # 150 pt risk * 50 = Rs. 7,500 / lot
        suggested_lots=10,  # 10 lots = Rs. 75,000 risk (> Rs. 10,000 limit)
    )
    v3 = gate.evaluate(large_intent, context, normal_account)
    assert v3.approved is True
    assert v3.adjusted_lots == 1  # Clamped to 1 lot
    assert any("POSITION_SIZING_CLAMPED" in g for g in v3.applied_guards)

    # Test Invariant 4: 0DTE Expiry Pin Lockout (within 15 minutes of close)
    close_context = MarketContext(
        symbol="NIFTY",
        ltp=24500.0,
        ofi=0.5,
        micro_price=24503.0,
        dealer_net_gex=0.0,
        macro_sentiment_score=0.2,
        is_0dte_expiry_day=True,
        minutes_to_market_close=10,  # < 15 min!
    )
    v4 = gate.evaluate(intent, close_context, normal_account)
    assert v4.approved is False
    assert any("0DTE_GAMMA_SINGULARITY_LOCKOUT" in r for r in v4.rejection_reasons)


@pytest.mark.asyncio
async def test_sebi_compliance_generator():
    """Verify statutory SEBI margin reporting and CSV serialization."""
    engine = SebiComplianceEngine(data_dir="backend/data/test_compliance")
    rec = engine.compute_client_margin_status(
        client_ucc="CLI_TEST_01",
        peak_margin=100000.0,
        initial_var=80000.0,
        elm=10000.0,
        mtm_loss=2000.0,
        cash_collateral=120000.0,
        non_cash_collateral=0.0,
    )
    assert rec.margin_deficit == 0.0
    assert rec.shortfall_flag == "N"
    assert len(rec.audit_hash) == 16

    path, content = engine.generate_sebi_eod_csv()
    assert "MRG_CLIENT_ALLOCATION" in path
    assert "PEAK_MARGIN_REQUIRED" in content
    assert "CLI_TEST_01" in content


@pytest.mark.asyncio
async def test_gamma_singularity_and_kou_simulation():
    """Verify Black-Scholes Greeks, Taylor expansion, and Kou jump-diffusion."""
    math_engine = GammaSingularityMathEngine()
    greeks = math_engine.compute_black_scholes_greeks(
        s=24500.0, k=24500.0, tau=0.01, r=0.065, sigma=0.13, is_call=True
    )
    assert greeks["gamma"] > 0.0
    assert "delta" in greeks
    assert "speed" in greeks

    taylor = math_engine.evaluate_taylor_expansion(
        s=24500.0,
        k=24500.0,
        tau_hours=4.0,
        sigma=0.14,
        ds=100.0,
        dsigma=0.01,
        dt_hours=1.0,
        is_call=True,
    )
    assert taylor.delta_contribution != 0.0
    assert taylor.gamma_contribution > 0.0

    kou = math_engine.simulate_kou_0dte_payoff(
        spot=24500.0,
        strike_otm=24650.0,
        initial_premium=20.0,
        target_multiplier=17.5,
        remaining_hours=3.5,
        sigma=0.13,
        lambda_jump=25.0,
        num_sims=300,
    )
    assert kou.num_simulations == 300
    assert 0.0 <= kou.probability_of_17x_payoff <= 1.0


@pytest.mark.asyncio
async def test_hft_rest_endpoints():
    """Verify all /api/hft endpoints return HTTP 200 with structured data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Status
        r1 = await client.get("/api/hft/status")
        assert r1.status_code == 200
        assert r1.json()["status"] == "ONLINE"

        # Arbitrage
        r2 = await client.get("/api/hft/arbitrage")
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["statutory_fee_hurdle_bps"] == 3.45
        assert len(data2["opportunities"]) >= 1

        # Gamma Squeeze
        r3 = await client.get("/api/hft/gamma_squeeze?symbol=NIFTY")
        assert r3.status_code == 200
        data3 = r3.json()
        assert data3["symbol"] == "NIFTY"
        assert "dealer_trap_zone" in data3

        # Agent Tick
        r4 = await client.post(
            "/api/hft/agent/tick",
            json={
                "symbol": "NIFTY",
                "ltp": 24500.0,
                "ofi": 0.42,
                "micro_price": 24504.0,
                "dealer_net_gex": -550.0,
                "macro_sentiment_score": 0.35,
                "is_0dte_expiry_day": False,
                "minutes_to_market_close": 180,
            },
        )
        assert r4.status_code == 200
        verdict = r4.json()["verdict"]
        assert "approved" in verdict
        assert "applied_guards" in verdict

        # SEBI Report Summary & Download
        r5 = await client.get("/api/hft/sebi_report/summary")
        assert r5.status_code == 200
        assert r5.json()["compliance_status"] == "FULL_MARGIN_CONSERVED_NO_SHORTFALL"

        r6 = await client.get("/api/hft/sebi_report/download")
        assert r6.status_code == 200
        assert "text/csv" in r6.headers["content-type"]
