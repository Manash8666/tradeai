//! Automated 0DTE Gamma-Squeeze Detection Scanner
//! A gamma squeeze occurs when dealer positions shift deeply negative in aggregate gamma (GEX < 0).
//! Dealers are forced to buy into rising markets and sell into declining ones, creating short squeezes.

use std::collections::HashMap;

#[derive(Default, Clone, Debug)]
pub struct StrikeMetrics {
    pub call_oi: u64,
    pub put_oi: u64,
    pub call_vol: u64,
    pub put_vol: u64,
    pub gamma: f64,
    pub oi_velocity: f64, // d(OI)/dt
}

pub struct GammaSqueezeScanner {
    pub strike_map: HashMap<u64, StrikeMetrics>,
    pub spot_price: f64,
    pub lot_size: f64,
}

impl GammaSqueezeScanner {
    pub fn new(spot: f64, lot_size: f64) -> Self {
        Self {
            strike_map: HashMap::new(),
            spot_price: spot,
            lot_size,
        }
    }

    pub fn compute_aggregate_gex(&self) -> (f64, Option<u64>, bool) {
        let mut net_gex = 0.0;
        let mut max_squeeze_strike = None;
        let mut max_acceleration = 0.0;

        for (&strike, m) in &self.strike_map {
            // Dealers are assumed short retail buying (Negative GEX = destabilizing dealer hedging)
            let call_gex = (m.call_oi as f64) * m.gamma * (self.spot_price * self.spot_price) * self.lot_size;
            let put_gex = (m.put_oi as f64) * m.gamma * (self.spot_price * self.spot_price) * self.lot_size;

            let strike_net_gex = call_gex - put_gex;
            net_gex += strike_net_gex;

            // Detect gamma acceleration near ATM (Within 2% range)
            let dist_pct = ((strike as f64 - self.spot_price) / self.spot_price).abs();
            if dist_pct <= 0.02 && m.oi_velocity > max_acceleration && m.call_vol > (m.put_vol * 3) {
                max_acceleration = m.oi_velocity;
                max_squeeze_strike = Some(strike);
            }
        }

        let is_squeeze_imminent = net_gex < -1_000_000.0 && max_squeeze_strike.is_some();
        (net_gex, max_squeeze_strike, is_squeeze_imminent)
    }
}
