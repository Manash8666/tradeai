//! Real-Time Order Flow Imbalance (OFI) & Depth-Weighted Micro-Price Engine
//! Implements Cont-Kukanov-Stoikov (2014) microstructure formulations for high-frequency signal generation.

pub struct MicrostructureSignals {
    prev_bid_price: f64,
    prev_bid_qty: u64,
    prev_ask_price: f64,
    prev_ask_qty: u64,
}

impl MicrostructureSignals {
    pub fn new() -> Self {
        Self {
            prev_bid_price: 0.0,
            prev_bid_qty: 0,
            prev_ask_price: 0.0,
            prev_ask_qty: 0,
        }
    }

    #[inline(always)]
    pub fn update(&mut self, bid_p: f64, bid_q: u64, ask_p: f64, ask_q: u64) -> (f64, f64) {
        // 1. Calculate Micro-Price
        let total_depth = (bid_q + ask_q) as f64;
        let micro_price = if total_depth > 0.0 {
            ((bid_q as f64 * ask_p) + (ask_q as f64 * bid_p)) / total_depth
        } else {
            (bid_p + ask_p) / 2.0
        };

        // 2. Cont-Kukanov-Stoikov Level-1 Order Flow Imbalance (OFI)
        let delta_bid = if bid_p > self.prev_bid_price {
            bid_q as f64
        } else if (bid_p - self.prev_bid_price).abs() < 1e-4 {
            bid_q as f64 - self.prev_bid_qty as f64
        } else {
            -(self.prev_bid_qty as f64)
        };

        let delta_ask = if ask_p < self.prev_ask_price {
            ask_q as f64
        } else if (ask_p - self.prev_ask_price).abs() < 1e-4 {
            ask_q as f64 - self.prev_ask_qty as f64
        } else {
            -(self.prev_ask_qty as f64)
        };

        let ofi = delta_bid - delta_ask;

        // Commit current state for next tick iteration
        self.prev_bid_price = bid_p;
        self.prev_bid_qty = bid_q;
        self.prev_ask_price = ask_p;
        self.prev_ask_qty = ask_q;

        (micro_price, ofi)
    }
}
