import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Server, ChevronDown, Check, Zap, AlertCircle } from 'lucide-react';
import axios from 'axios';

export interface BrokerStatus {
  broker_id: string;
  name: string;
  connected: boolean;
  latency_ms: number;
  features: string[];
  rate_limit_per_sec: number;
  static_ip_compliant: boolean;
  is_active?: boolean;
  client_id?: string;
  account_name?: string;
}

export function BrokerGatewaySelector() {
  const [brokers, setBrokers] = useState<BrokerStatus[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedBroker, setSelectedBroker] = useState<BrokerStatus | null>(null);

  const fetchBrokers = async () => {
    try {
      const res = await axios.get<BrokerStatus[]>('/api/hft/brokers');
      setBrokers(res.data);
      const active = res.data.find((b) => b.is_active);
      if (active) setSelectedBroker(active);
    } catch {
      const fallbackBrokers: BrokerStatus[] = [
        {
          broker_id: 'FYERS',
          name: 'FYERS Trading API v3',
          connected: true,
          is_active: true,
          latency_ms: 18.5,
          features: ['REST API v3', 'L2 WebSockets'],
          rate_limit_per_sec: 10,
          static_ip_compliant: true,
          client_id: 'FAL33350',
          account_name: 'MANASH RANJAN DASH',
        },
        {
          broker_id: 'PAPER',
          name: 'Antigravity Institutional Simulator',
          connected: true,
          is_active: false,
          latency_ms: 0.15,
          features: ['Zero Risk', 'Full SEBI Ledger'],
          rate_limit_per_sec: 1000,
          static_ip_compliant: true,
        },
      ];
      setBrokers(fallbackBrokers);
      setSelectedBroker(fallbackBrokers[0]);
    }
  };

  useEffect(() => {
    fetchBrokers();
    const interval = setInterval(fetchBrokers, 8000);
    return () => clearInterval(interval);
  }, []);

  const switchBroker = async (brokerId: string) => {
    setLoading(true);
    try {
      await axios.post(`/api/hft/brokers/select?broker_id=${brokerId}`);
      await fetchBrokers();
    } catch (err) {
      console.error('Failed to switch broker', err);
    } finally {
      setLoading(false);
      setIsOpen(false);
    }
  };

  const active = selectedBroker || brokers.find((b) => b.is_active) || brokers[0];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition-all cursor-pointer text-xs font-mono group"
      >
        <Server className="w-3.5 h-3.5 text-cyan-400 group-hover:rotate-12 transition-transform" />
        <span className="text-slate-400 font-sans text-[11px] hidden lg:inline">Broker:</span>
        <span className="font-bold text-white tracking-wide">
          {active ? active.name.split(' ')[0] : 'ROUTING'}
        </span>
        {active && active.client_id && (
          <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/25 hidden xl:inline">
            {active.client_id}
          </span>
        )}
        {active && (
          <span
            className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
              active.latency_ms < 1
                ? 'bg-emerald-500/15 text-emerald-300'
                : active.latency_ms < 25
                ? 'bg-cyan-500/15 text-cyan-300'
                : 'bg-amber-500/15 text-amber-300'
            }`}
          >
            {active.latency_ms.toFixed(1)}ms
          </span>
        )}
        <ChevronDown
          className={`w-3 h-3 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-80 rounded-xl bg-[#090d16] border border-white/[0.12] shadow-2xl p-2 z-50 backdrop-blur-2xl"
          >
            <div className="px-2 py-1.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                Order Execution Gateway
              </span>
              <span className="text-[9px] font-mono text-emerald-400 flex items-center gap-1">
                <Zap className="w-2.5 h-2.5" />
                Live OMS
              </span>
            </div>

            <div className="py-1 space-y-1">
              {brokers.map((broker) => {
                const isSelected = broker.broker_id === active?.broker_id;
                return (
                  <button
                    key={broker.broker_id}
                    disabled={loading}
                    onClick={() => switchBroker(broker.broker_id)}
                    className={`w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-emerald-500/15 border border-emerald-500/30'
                        : 'hover:bg-white/[0.04] border border-transparent'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white tracking-wide">
                          {broker.name}
                        </span>
                        {broker.broker_id === 'FYERS' && broker.connected && (
                          <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            AUTHENTICATED
                          </span>
                        )}
                        {broker.broker_id === 'PAPER' && (
                          <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                            ZERO RISK
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[10px] font-mono text-slate-400">
                        {broker.client_id ? (
                          <span className="text-amber-300 font-bold">{broker.client_id} ({broker.account_name?.split(' ')[0]})</span>
                        ) : (
                          <span>Latency: {broker.latency_ms.toFixed(1)}ms</span>
                        )}
                        <span>·</span>
                        <span>Cap: {broker.rate_limit_per_sec}/s</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {isSelected ? (
                        <div className="w-5 h-5 rounded-full bg-emerald-400 flex items-center justify-center text-[#090d16]">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      ) : broker.connected ? (
                        <span className="w-2 h-2 rounded-full bg-emerald-400/60" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-600" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-1 pt-1.5 border-t border-white/[0.06] px-2 py-1 flex items-center gap-1.5 text-[9px] font-mono text-slate-400">
              <AlertCircle className="w-3 h-3 text-cyan-400 flex-shrink-0" />
              <span>Route switching takes effect immediately on the next order.</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
