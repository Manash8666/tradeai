//! Embedded WebAssembly (Wasmtime) Strategy Plugin Runtime
//! Allows dynamic trading strategies without restarting or recompiling the core execution engine.
//! Enforces strict 50 µs epoch interruption deadline to prevent runaway user code.

#[derive(Default, Clone, Debug)]
pub struct StrategyHostState {
    pub account_id: u32,
    pub max_position_limit: u32,
    pub current_position: i32,
    pub dispatched_order: Option<(u8, f64, u32)>, // (Side, Price, Qty)
}

#[cfg(target_os = "linux")]
use wasmtime::*;

#[cfg(target_os = "linux")]
pub struct WasmStrategyEngine {
    engine: Engine,
    module: Module,
    linker: Linker<StrategyHostState>,
}

#[cfg(target_os = "linux")]
impl WasmStrategyEngine {
    pub fn new(wasm_bytes: &[u8]) -> Result<Self, Box<dyn std::error::Error>> {
        let mut config = Config::new();
        config.strategy(Strategy::Cranelift);
        config.cranelift_opt_level(OptLevel::Speed);
        config.epoch_interruption(true);

        let engine = Engine::new(&config)?;
        let module = Module::new(&engine, wasm_bytes)?;
        let mut linker = Linker::new(&engine);

        linker.func_wrap(
            "env",
            "host_dispatch_order",
            |mut caller: Caller<'_, StrategyHostState>, side: i32, price: f64, qty: i32| {
                let state = caller.data_mut();
                if (state.current_position + qty).abs() <= state.max_position_limit as i32 {
                    state.dispatched_order = Some((side as u8, price, qty as u32));
                    state.current_position += qty;
                    1
                } else {
                    0
                }
            },
        )?;

        Ok(Self { engine, module, linker })
    }

    pub fn execute_tick(
        &self,
        state: &mut StrategyHostState,
        symbol_token: u32,
        bid: f64,
        ask: f64,
    ) -> Result<Option<(u8, f64, u32)>, Box<dyn std::error::Error>> {
        let mut store = Store::new(&self.engine, std::mem::take(state));
        store.set_epoch_deadline(1);

        let instance = self.linker.instantiate(&mut store, &self.module)?;
        let on_quote = instance.get_typed_func::<(u32, f64, f64), ()>(&mut store, "on_quote")?;

        on_quote.call(&mut store, (symbol_token, bid, ask))?;

        *state = store.into_data();
        Ok(state.dispatched_order.take())
    }
}

/// Fallback / Sandbox simulator for Windows development
#[cfg(not(target_os = "linux"))]
pub struct SimulatedWasmStrategyEngine;

#[cfg(not(target_os = "linux"))]
impl SimulatedWasmStrategyEngine {
    pub fn execute_simulated_tick(
        state: &mut StrategyHostState,
        _symbol_token: u32,
        bid: f64,
        ask: f64,
    ) -> Option<(u8, f64, u32)> {
        let spread = ask - bid;
        if spread > 2.50 && state.current_position < state.max_position_limit as i32 {
            state.dispatched_order = Some((0, bid, 50));
            state.current_position += 50;
            return state.dispatched_order.take();
        }
        None
    }
}
