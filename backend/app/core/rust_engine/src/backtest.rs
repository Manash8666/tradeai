//! End-to-End Tick-Level L2 Backtesting Engine
//! Replays historical Level-2 records, deterministically tracks queue ahead positions,
//! and applies realistic exchange wire latency (50 µs).

use std::collections::{BTreeMap, VecDeque};

#[derive(Clone, Debug)]
pub struct HistoricalL2Record {
    pub timestamp_ns: u64,
    pub token: u32,
    pub ltp: f64,
    pub volume: u64,
    pub bid_prices: [f64; 5],
    pub bid_quantities: [u32; 5],
    pub ask_prices: [f64; 5],
    pub ask_quantities: [u32; 5],
}

pub struct BacktestEngine {
    pub resting_orders: BTreeMap<u64, (f64, u32, u32)>, // OrderId -> (Price, Qty, QueueAhead)
    pub current_cash: f64,
    pub inventory: i32,
    pub total_trades: usize,
    pub latency_ns: u64, // e.g. 50,000 ns (50 µs exchange roundtrip)
    pub pending_orders: VecDeque<(u64, f64, u32)>, // Orders in flight over the wire
}

impl BacktestEngine {
    pub fn new(initial_capital: f64, simulated_latency_us: u64) -> Self {
        Self {
            resting_orders: BTreeMap::new(),
            current_cash: initial_capital,
            inventory: 0,
            total_trades: 0,
            latency_ns: simulated_latency_us * 1000,
            pending_orders: VecDeque::new(),
        }
    }

    pub fn submit_order(&mut self, current_time_ns: u64, price: f64, qty: u32) {
        // Enforce exchange wire latency: Order cannot reach the book immediately
        let arrive_time = current_time_ns + self.latency_ns;
        self.pending_orders.push_back((arrive_time, price, qty));
    }

    pub fn replay_tick(&mut self, tick: &HistoricalL2Record, prev_volume: u64) {
        let volume_delta = tick.volume.saturating_sub(prev_volume);

        // 1. Process wire-latency pending orders arriving at this tick timestamp
        while let Some(&(arrive_time, price, qty)) = self.pending_orders.front() {
            if arrive_time <= tick.timestamp_ns {
                // Determine starting queue ahead at best bid
                let queue_ahead = if (price - tick.bid_prices[0]).abs() < 1e-4 {
                    tick.bid_quantities[0]
                } else {
                    0
                };
                let order_id = self.resting_orders.len() as u64 + 1;
                self.resting_orders.insert(order_id, (price, qty, queue_ahead));
                self.pending_orders.pop_front();
            } else {
                break;
            }
        }

        // 2. Queue Depletion Engine: Burn resting orders against printed volume
        let mut executed_ids = Vec::new();

        for (&order_id, (price, qty, queue_ahead)) in self.resting_orders.iter_mut() {
            if tick.ltp <= *price && volume_delta > 0 {
                if *queue_ahead > 0 {
                    let burn = (*queue_ahead).min(volume_delta as u32);
                    *queue_ahead -= burn;
                } else {
                    // Queue burned out: Execution achieved
                    let fill_qty = (*qty).min(volume_delta as u32);
                    self.current_cash -= (*price) * (fill_qty as f64);
                    self.inventory += fill_qty as i32;
                    self.total_trades += 1;
                    executed_ids.push(order_id);
                }
            }
        }

        for id in executed_ids {
            self.resting_orders.remove(&id);
        }
    }
}
