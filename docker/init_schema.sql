-- SEBI Daily Allocation & Peak Margin Reporting Table
CREATE TABLE IF NOT EXISTS sebi_margin_reports (
    report_date DATE NOT NULL,
    client_code VARCHAR(16) NOT NULL,
    exchange VARCHAR(8) NOT NULL,          -- NSE / BSE
    segment VARCHAR(8) NOT NULL,           -- CM (Cash) / FO (Derivatives)
    total_margin_available NUMERIC(15, 2) NOT NULL,
    peak_margin_required NUMERIC(15, 2) NOT NULL,
    eod_margin_required NUMERIC(15, 2) NOT NULL,
    margin_shortfall NUMERIC(15, 2) NOT NULL,
    penalty_applicable NUMERIC(12, 2) DEFAULT 0.00,
    PRIMARY KEY (report_date, client_code, segment)
);

-- SEBI Order Trail Log (Every state change from receipt to fill)
CREATE TABLE IF NOT EXISTS sebi_order_audit_trail (
    event_timestamp TIMESTAMPTZ NOT NULL,
    order_id UUID NOT NULL,
    client_code VARCHAR(16) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    side VARCHAR(4) NOT NULL,
    order_type VARCHAR(8) NOT NULL,
    qty INT NOT NULL,
    limit_price NUMERIC(12, 2),
    trigger_price NUMERIC(12, 2),
    order_status VARCHAR(16) NOT NULL,      -- NEW / MODIFIED / CANCELLED / FILLED
    rejection_code VARCHAR(16),
    order_entry_source VARCHAR(8) DEFAULT 'API'
);

SELECT create_hypertable('sebi_order_audit_trail', 'event_timestamp', if_not_exists => TRUE);
