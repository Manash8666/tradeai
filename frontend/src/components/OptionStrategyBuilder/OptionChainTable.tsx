import { ArrowUpDown, Plus, Settings, ChevronDown } from 'lucide-react';
import type { OptionChainData, StrategyLeg } from './types';

interface OptionChainTableProps {
  data: OptionChainData;
  activeLegs: StrategyLeg[];
  onAddLeg: (action: 'BUY' | 'SELL', type: 'CE' | 'PE', strike: number, price: number, iv: number, delta?: number) => void;
  onSelectExpiry: (idx: number) => void;
  selectedExpiryIdx: number;
}

export function OptionChainTable({
  data,
  activeLegs,
  onAddLeg,
  onSelectExpiry,
  selectedExpiryIdx,
}: OptionChainTableProps) {
  const getLegForStrike = (strike: number, type: 'CE' | 'PE') => {
    return activeLegs.find((l) => l.strike === strike && l.type === type);
  };

  const atmStrike = data.atm_strike;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#090d16',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}
    >
      {/* ── EXPIRY TABS (Matches StockMojo Layout) ──────────────────────── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 10px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
          background: '#070b12',
          gap: 6,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, overflowX: 'auto' }}>
          {data.expiries.map((exp, idx) => {
            const isSelected = selectedExpiryIdx === idx;
            return (
              <button
                key={exp.date}
                onClick={() => onSelectExpiry(idx)}
                style={{
                  fontSize: '0.68rem',
                  fontWeight: isSelected ? 800 : 600,
                  padding: '3px 9px',
                  borderRadius: '6px',
                  background: isSelected ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  color: isSelected ? '#38bdf8' : '#94a3b8',
                  border: isSelected ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid rgba(255, 255, 255, 0.05)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                {exp.label}
              </button>
            );
          })}
          <button
            style={{
              padding: '3px 6px',
              borderRadius: '6px',
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              color: '#94a3b8',
              cursor: 'pointer',
            }}
            title="More Expiries"
          >
            <ChevronDown size={11} />
          </button>
        </div>

        <button
          style={{
            padding: '4px',
            borderRadius: '6px',
            background: 'transparent',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
          }}
          title="Option Chain Columns Configuration"
        >
          <Settings size={13} />
        </button>
      </div>

      {/* ── OPTION CHAIN TABLE ─────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: 'auto', maxHeight: '580px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.70rem', fontFamily: 'JetBrains Mono, monospace' }}>
          {/* Sticky Header */}
          <thead style={{ position: 'sticky', top: 0, zIndex: 10, background: '#0c111c', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <tr style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.62rem' }}>
              <th style={{ padding: '7px 4px', textAlign: 'left', width: '11%' }}>CallΔ</th>
              <th style={{ padding: '7px 4px', textAlign: 'right', width: '15%' }}>LTP</th>
              <th style={{ padding: '7px 4px', textAlign: 'right', width: '19%' }}>OI</th>
              <th style={{ padding: '7px 4px', textAlign: 'center', width: '16%', background: '#111827', color: '#f8fafc' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
                  <span>Strike</span>
                  <ArrowUpDown size={10} />
                </div>
              </th>
              <th style={{ padding: '7px 4px', textAlign: 'left', width: '19%' }}>OI</th>
              <th style={{ padding: '7px 4px', textAlign: 'left', width: '15%' }}>LTP</th>
              <th style={{ padding: '7px 4px', textAlign: 'right', width: '11%' }}>PutΔ</th>
            </tr>
          </thead>

          <tbody>
            {data.strikes.map((s) => {
              const callLeg = getLegForStrike(s.strike, 'CE');
              const putLeg = getLegForStrike(s.strike, 'PE');
              const isAtm = s.is_atm;
              const isCallITM = s.strike < atmStrike;
              const isPutITM = s.strike > atmStrike;

              return (
                <tr
                  key={s.strike}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    background: isAtm ? 'rgba(56, 189, 248, 0.14)' : 'transparent',
                    transition: 'background 0.15s ease',
                  }}
                  className="hover:bg-white/[0.04]"
                >
                  {/* CALL DELTA */}
                  <td
                    style={{
                      padding: '5px 4px',
                      color: '#94a3b8',
                      textAlign: 'left',
                      background: isCallITM && !isAtm ? 'rgba(245, 158, 11, 0.05)' : 'transparent',
                    }}
                  >
                    {s.call.delta.toFixed(2)}
                  </td>

                  {/* CALL LTP (Interactive) */}
                  <td
                    style={{
                      padding: '5px 4px',
                      textAlign: 'right',
                      cursor: 'pointer',
                      fontWeight: 700,
                      color: callLeg ? (callLeg.action === 'BUY' ? '#22c55e' : '#ef4444') : '#f8fafc',
                      background: isCallITM && !isAtm ? 'rgba(245, 158, 11, 0.06)' : 'transparent',
                    }}
                    title="Click to add/toggle Call leg"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 3 }}>
                      {callLeg ? (
                        <span
                          style={{
                            fontSize: '0.52rem',
                            padding: '1px 3px',
                            borderRadius: '3px',
                            background: callLeg.action === 'BUY' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            color: callLeg.action === 'BUY' ? '#22c55e' : '#ef4444',
                            fontWeight: 800,
                          }}
                        >
                          {callLeg.lots}x {callLeg.action}
                        </span>
                      ) : null}
                      <span>{s.call.ltp.toFixed(2)}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAddLeg('BUY', 'CE', s.strike, s.call.ltp, s.call.iv, s.call.delta);
                        }}
                        style={{
                          background: 'rgba(34, 197, 94, 0.15)',
                          color: '#22c55e',
                          border: 'none',
                          borderRadius: 3,
                          padding: '1px 3px',
                          fontSize: '0.55rem',
                          cursor: 'pointer',
                        }}
                        title="Buy Call"
                      >
                        <Plus size={8} />
                      </button>
                    </div>
                  </td>

                  {/* CALL OI BAR (Green bar filling right to left) */}
                  <td
                    style={{
                      padding: '5px 4px',
                      textAlign: 'right',
                      background: isCallITM && !isAtm ? 'rgba(245, 158, 11, 0.05)' : 'transparent',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
                      <span style={{ fontSize: '0.62rem', color: '#64748b' }}>
                        {(s.call.oi / 1000).toFixed(0)}k
                      </span>
                      <div style={{ width: '42px', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${s.call.oi_pct}%`,
                            height: '100%',
                            background: 'rgba(34, 197, 94, 0.75)',
                            marginLeft: 'auto',
                          }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* STRIKE PRICE (Center column) */}
                  <td
                    style={{
                      padding: '5px 4px',
                      textAlign: 'center',
                      fontWeight: isAtm ? 900 : 700,
                      background: isAtm ? 'rgba(56, 189, 248, 0.25)' : '#0d131f',
                      color: isAtm ? '#38bdf8' : '#f8fafc',
                      borderLeft: '1px solid rgba(255, 255, 255, 0.06)',
                      borderRight: '1px solid rgba(255, 255, 255, 0.06)',
                    }}
                  >
                    <span>{s.strike}</span>
                    {isAtm && (
                      <span
                        style={{
                          fontSize: '0.50rem',
                          marginLeft: 3,
                          padding: '1px 3px',
                          background: '#38bdf8',
                          color: '#000',
                          borderRadius: 2,
                          fontWeight: 900,
                        }}
                      >
                        ATM
                      </span>
                    )}
                  </td>

                  {/* PUT OI BAR (Pink/Red bar filling left to right) */}
                  <td
                    style={{
                      padding: '5px 4px',
                      textAlign: 'left',
                      background: isPutITM && !isAtm ? 'rgba(245, 158, 11, 0.05)' : 'transparent',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: 4 }}>
                      <div style={{ width: '42px', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${s.put.oi_pct}%`,
                            height: '100%',
                            background: 'rgba(239, 68, 68, 0.75)',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '0.62rem', color: '#64748b' }}>
                        {(s.put.oi / 1000).toFixed(0)}k
                      </span>
                    </div>
                  </td>

                  {/* PUT LTP (Interactive) */}
                  <td
                    style={{
                      padding: '5px 4px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      fontWeight: 700,
                      color: putLeg ? (putLeg.action === 'BUY' ? '#22c55e' : '#ef4444') : '#f8fafc',
                      background: isPutITM && !isAtm ? 'rgba(245, 158, 11, 0.06)' : 'transparent',
                    }}
                    title="Click to add/toggle Put leg"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: 3 }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAddLeg('BUY', 'PE', s.strike, s.put.ltp, s.put.iv, s.put.delta);
                        }}
                        style={{
                          background: 'rgba(239, 68, 68, 0.15)',
                          color: '#ef4444',
                          border: 'none',
                          borderRadius: 3,
                          padding: '1px 3px',
                          fontSize: '0.55rem',
                          cursor: 'pointer',
                        }}
                        title="Buy Put"
                      >
                        <Plus size={8} />
                      </button>
                      <span>{s.put.ltp.toFixed(2)}</span>
                      {putLeg ? (
                        <span
                          style={{
                            fontSize: '0.52rem',
                            padding: '1px 3px',
                            borderRadius: '3px',
                            background: putLeg.action === 'BUY' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            color: putLeg.action === 'BUY' ? '#22c55e' : '#ef4444',
                            fontWeight: 800,
                          }}
                        >
                          {putLeg.lots}x {putLeg.action}
                        </span>
                      ) : null}
                    </div>
                  </td>

                  {/* PUT DELTA */}
                  <td
                    style={{
                      padding: '5px 4px',
                      color: '#94a3b8',
                      textAlign: 'right',
                      background: isPutITM && !isAtm ? 'rgba(245, 158, 11, 0.05)' : 'transparent',
                    }}
                  >
                    {s.put.delta.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
