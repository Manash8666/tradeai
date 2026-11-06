//! Real-Time 0DTE Gamma-Scalping Simulation Engine in Rust
//! Holds a long gamma position (e.g. long straddle) and dynamically buys low and sells high
//! in underlying futures/spot to harvest realized volatility and offset theta burn:
//! ΔΠ ≈ 1/2 Γ (ΔS)² - Θ Δt - Σ(Slippage + Tax)

use std::f64::consts::{FRAC_1_SQRT_2, PI};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum OptionType {
    Call,
    Put,
}

#[derive(Debug, Clone)]
pub struct MarketTick {
    pub timestamp_ms: u64,
    pub spot_price: f64,
    pub implied_vol: f64,
}

pub struct BlackScholes;

impl BlackScholes {
    #[inline(always)]
    fn cnd(x: f64) -> f64 {
        // High-precision erf approximation
        let t = 1.0 / (1.0 + 0.2316419 * x.abs());
        let d = 0.3989423 * (-x * x * 0.5).exp();
        let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
        if x > 0.0 { 1.0 - p } else { p }
    }

    #[inline(always)]
    fn pdf(x: f64) -> f64 {
        (-0.5 * x * x).exp() / (2.0 * PI).sqrt()
    }

    pub fn greeks(
        spot: f64,
        strike: f64,
        tau_years: f64,
        iv: f64,
        r: f64,
        opt_type: OptionType,
    ) -> (f64, f64, f64, f64) {
        if tau_years <= 1e-6 {
            let intrinsic = match opt_type {
                OptionType::Call => (spot - strike).max(0.0),
                OptionType::Put => (strike - spot).max(0.0),
            };
            let delta = match opt_type {
                OptionType::Call => if spot > strike { 1.0 } else { 0.0 },
                OptionType::Put => if spot < strike { -1.0 } else { 0.0 },
            };
            return (intrinsic, delta, 0.0, 0.0);
        }

        let sqrt_tau = tau_years.sqrt();
        let d1 = ((spot / strike).ln() + (r + 0.5 * iv * iv) * tau_years) / (iv * sqrt_tau);
        let d2 = d1 - iv * sqrt_tau;

        let ert = (-r * tau_years).exp();
        let pdf_d1 = Self::pdf(d1);

        let price = match opt_type {
            OptionType::Call => spot * Self::cnd(d1) - strike * ert * Self::cnd(d2),
            OptionType::Put => strike * ert * Self::cnd(-d2) - spot * Self::cnd(-d1),
        };

        let delta = match opt_type {
            OptionType::Call => Self::cnd(d1),
            OptionType::Put => Self::cnd(d1) - 1.0,
        };

        let gamma = pdf_d1 / (spot * iv * sqrt_tau);
        let theta_day = (-(spot * pdf_d1 * iv) / (2.0 * sqrt_tau)
            - r * strike * ert * (if opt_type == OptionType::Call { Self::cnd(d2) } else { Self::cnd(-d2) }))
            / 365.0;

        (price.max(0.05), delta, gamma, theta_day)
    }
}

pub struct GammaScalpSimulator {
    pub strike: f64,
    pub expiry_timestamp_ms: u64,
    pub contract_quantity: i32,   // Lots (e.g. 2 for 150 shares on NIFTY)
    pub lot_size: i32,
    pub delta_threshold: f64,     // Rebalance band (e.g. 0.15)
    pub underlying_position: f64, // Current futures/equity hedge
    pub cash_balance: f64,
    pub realized_scalp_pnl: f64,
    pub trade_count: u32,
    pub total_friction_costs: f64,
}

impl GammaScalpSimulator {
    pub fn new(strike: f64, expiry_ms: u64, lots: i32, lot_size: i32, delta_band: f64) -> Self {
        Self {
            strike,
            expiry_timestamp_ms: expiry_ms,
            contract_quantity: lots,
            lot_size,
            delta_threshold: delta_band,
            underlying_position: 0.0,
            cash_balance: 0.0,
            realized_scalp_pnl: 0.0,
            trade_count: 0,
            total_friction_costs: 0.0,
        }
    }

    pub fn process_tick(&mut self, tick: &MarketTick) -> Option<String> {
        let remaining_ms = self.expiry_timestamp_ms.saturating_sub(tick.timestamp_ms);
        let tau_years = (remaining_ms as f64) / (1000.0 * 86400.0 * 365.0);

        // 1. Calculate Option Greeks for Long Straddle (Call + Put)
        let (_, c_delta, c_gamma, _) = BlackScholes::greeks(
            tick.spot_price, self.strike, tau_years, tick.implied_vol, 0.065, OptionType::Call,
        );
        let (_, p_delta, p_gamma, _) = BlackScholes::greeks(
            tick.spot_price, self.strike, tau_years, tick.implied_vol, 0.065, OptionType::Put,
        );

        let total_contracts = (self.contract_quantity * self.lot_size) as f64;
        let straddle_delta = (c_delta + p_delta) * total_contracts;
        let _straddle_gamma = (c_gamma + p_gamma) * total_contracts;

        // 2. Net Portfolio Delta = Options Delta + Spot/Futures Position
        let net_portfolio_delta = straddle_delta + self.underlying_position;

        // 3. Trigger Dynamic Delta Hedge Rebalance
        if net_portfolio_delta.abs() >= (self.delta_threshold * total_contracts) {
            let rebalance_qty = -net_portfolio_delta; // Offset delta back to zero
            let exec_price = tick.spot_price;

            // Indian Market Friction Model (NSE Futures Turnover: 0.00173% + STT 0.02% on sell + GST)
            let turnover = exec_price * rebalance_qty.abs();
            let brokerage = 20.0;
            let stt = if rebalance_qty < 0.0 { turnover * 0.0002 } else { 0.0 };
            let exchange_fee = turnover * 0.0000173;
            let sebi_fee = turnover * 0.000001;
            let gst = (brokerage + exchange_fee + sebi_fee) * 0.18;
            let friction = brokerage + stt + exchange_fee + sebi_fee + gst;

            // Execute synthetic underlying hedge
            self.cash_balance -= (rebalance_qty * exec_price) + friction;
            self.underlying_position += rebalance_qty;
            self.total_friction_costs += friction;
            self.trade_count += 1;

            return Some(format!(
                "Hedge Triggered | Spot: ₹{:.2} | Shuffled: {:.1} shares | Net Delta: {:.2} -> 0.0 | Friction: ₹{:.2}",
                tick.spot_price, rebalance_qty, net_portfolio_delta, friction
            ));
        }

        None
    }
}
