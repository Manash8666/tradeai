//! Continuous SEBI/NSE 200 Orders/Sec Lock-Free Token Bucket
//! SEBI and NSE enforce structural order rate limits: exceeding 200 orders/sec
//! results in temporary port blocking and penalty fines. This lock-free implementation
//! uses atomic CAS (Compare-And-Swap) with sub-nanosecond timestamp precision.

use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

pub struct SebiRateLimiter {
    pub capacity: f64,            // Max burst capacity (e.g., 200.0)
    pub refill_rate_per_ns: f64,  // 200 orders / 1_000_000_000 ns = 0.0000002
    pub state: AtomicU64,         // Bit-packed: [32-bit tokens * 1000] | [32-bit timestamp delta ms]
    pub start_time: Instant,
}

impl SebiRateLimiter {
    pub fn new(max_orders_per_sec: u32) -> Self {
        let capacity = max_orders_per_sec as f64;
        let refill_rate_per_ns = capacity / 1_000_000_000.0;
        let initial_tokens = (capacity * 1000.0) as u64;

        Self {
            capacity,
            refill_rate_per_ns,
            state: AtomicU64::new(initial_tokens << 32),
            start_time: Instant::now(),
        }
    }

    #[inline(always)]
    pub fn try_acquire(&self, tokens: u32) -> bool {
        let requested = (tokens as f64) * 1000.0;

        loop {
            let current_state = self.state.load(Ordering::Relaxed);
            let current_tokens = (current_state >> 32) as f64;
            let last_update_ns = (current_state & 0xFFFF_FFFF) as u64;
            let now_ns = self.start_time.elapsed().as_nanos() as u64;

            let elapsed_ns = now_ns.saturating_sub(last_update_ns);
            let refilled_tokens = (current_tokens + (elapsed_ns as f64 * self.refill_rate_per_ns * 1000.0))
                .min(self.capacity * 1000.0);

            if refilled_tokens < requested {
                return false; // Rate limit breached: Drop or queue
            }

            let new_tokens = (refilled_tokens - requested) as u64;
            let new_state = (new_tokens << 32) | (now_ns & 0xFFFF_FFFF);

            if self.state.compare_exchange_weak(
                current_state,
                new_state,
                Ordering::Release,
                Ordering::Relaxed,
            ).is_ok() {
                return true;
            }
        }
    }
}
