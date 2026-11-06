import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Check } from 'lucide-react';
import type { ReadyMadeStrategy } from './types';

interface ReadyMadeStrategiesGridProps {
  onSelectStrategy: (strat: ReadyMadeStrategy) => void;
  selectedStrategyId?: string;
}

export const READY_MADE_STRATEGIES: ReadyMadeStrategy[] = [
  // ── BULLISH (9 Strategies) ────────────────────────────────────────────────
  {
    id: 'buy_call',
    name: 'Buy Call',
    category: 'Bullish',
    description: 'Outright bullish call. Limited downside risk (premium paid), unlimited upside potential.',
    legs: [{ action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 }],
  },
  {
    id: 'sell_put',
    name: 'Sell Put',
    category: 'Bullish',
    description: 'Moderately bullish. Collects premium with capped profit, significant downside risk.',
    legs: [{ action: 'SELL', type: 'PE', strike_offset: 0, lots: 1 }],
  },
  {
    id: 'long_synthetic_future',
    name: 'Long Synthetic Future',
    category: 'Bullish',
    description: 'Simulates long futures: Buy ATM Call + Sell ATM Put.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: 0, lots: 1 },
    ],
  },
  {
    id: 'bull_call_spread',
    name: 'Bull Call Spread',
    category: 'Bullish',
    description: 'Defined-risk bullish strategy: Buy lower strike Call + Sell higher strike Call.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
    ],
  },
  {
    id: 'bull_put_spread',
    name: 'Bull Put Spread',
    category: 'Bullish',
    description: 'Credit spread: Sell higher strike Put + Buy lower strike Put for downside protection.',
    legs: [
      { action: 'SELL', type: 'PE', strike_offset: 0, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -2, lots: 1 },
    ],
  },
  {
    id: 'long_calendar_with_calls',
    name: 'Long Calendar with Calls',
    category: 'Bullish',
    description: 'Sell near-term Call + Buy next-expiry Call at the same strike.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 1, lots: 1, expiry_idx: 0 },
      { action: 'BUY', type: 'CE', strike_offset: 1, lots: 1, expiry_idx: 1 },
    ],
  },
  {
    id: 'bull_condor',
    name: 'Bull Condor',
    category: 'Bullish',
    description: '4-legged bullish call condor targeting an upper plateau zone.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: -1, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 1, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 4, lots: 1 },
    ],
  },
  {
    id: 'bull_butterfly',
    name: 'Bull Butterfly',
    category: 'Bullish',
    description: 'Bullish butterfly targeting peak profit at an upper strike.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 2 },
      { action: 'BUY', type: 'CE', strike_offset: 4, lots: 1 },
    ],
  },
  {
    id: 'range_forward',
    name: 'Range Forward',
    category: 'Bullish',
    description: 'Long OTM Call financed by Short OTM Put for low-cost bullish tunnel.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
    ],
  },

  // ── BEARISH (9 Strategies) ────────────────────────────────────────────────
  {
    id: 'buy_put',
    name: 'Buy Put',
    category: 'Bearish',
    description: 'Outright bearish put. Limited downside risk, substantial profit as asset drops.',
    legs: [{ action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 }],
  },
  {
    id: 'sell_call',
    name: 'Sell Call',
    category: 'Bearish',
    description: 'Moderately bearish. Earns premium, faces unlimited upside risk on sudden rally.',
    legs: [{ action: 'SELL', type: 'CE', strike_offset: 0, lots: 1 }],
  },
  {
    id: 'short_synthetic_future',
    name: 'Short Synthetic Future',
    category: 'Bearish',
    description: 'Simulates short future: Sell ATM Call + Buy ATM Put.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 },
    ],
  },
  {
    id: 'bear_call_spread',
    name: 'Bear Call Spread',
    category: 'Bearish',
    description: 'Credit spread: Sell lower strike Call + Buy higher strike Call.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 2, lots: 1 },
    ],
  },
  {
    id: 'bear_put_spread',
    name: 'Bear Put Spread',
    category: 'Bearish',
    description: 'Defined-risk bearish play: Buy higher strike Put + Sell lower strike Put.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
    ],
  },
  {
    id: 'long_calendar_with_puts',
    name: 'Long Calendar with Puts',
    category: 'Bearish',
    description: 'Sell near-term Put + Buy next-expiry Put at the same strike.',
    legs: [
      { action: 'SELL', type: 'PE', strike_offset: -1, lots: 1, expiry_idx: 0 },
      { action: 'BUY', type: 'PE', strike_offset: -1, lots: 1, expiry_idx: 1 },
    ],
  },
  {
    id: 'bear_condor',
    name: 'Bear Condor',
    category: 'Bearish',
    description: '4-legged put condor designed to maximize returns in a downward price zone.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: 1, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -1, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -4, lots: 1 },
    ],
  },
  {
    id: 'bear_butterfly',
    name: 'Bear Butterfly',
    category: 'Bearish',
    description: 'Bearish put butterfly targeting lower strike with high reward-to-risk ratio.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 2 },
      { action: 'BUY', type: 'PE', strike_offset: -4, lots: 1 },
    ],
  },
  {
    id: 'risk_reversal',
    name: 'Risk Reversal',
    category: 'Bearish',
    description: 'Short OTM Call + Long OTM Put creating a pure bearish risk envelope.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -2, lots: 1 },
    ],
  },

  // ── NEUTRAL (8 Strategies) ────────────────────────────────────────────────
  {
    id: 'short_straddle',
    name: 'Short Straddle',
    category: 'Neutral',
    description: 'Sell ATM Call + Sell ATM Put. Maximum profit at ATM strike; high theta decay benefit.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: 0, lots: 1 },
    ],
  },
  {
    id: 'short_strangle',
    name: 'Short Strangle',
    category: 'Neutral',
    description: 'Sell OTM Call + Sell OTM Put. Wide breakeven band to capture premium.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
    ],
  },
  {
    id: 'short_iron_condor',
    name: 'Short Iron Condor',
    category: 'Neutral',
    description: 'Sell OTM Strangle with Long wings for 100% defined risk and margin relief.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: -4, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 4, lots: 1 },
    ],
  },
  {
    id: 'short_iron_butterfly',
    name: 'Short Iron Butterfly',
    category: 'Neutral',
    description: 'Sell ATM Straddle + Buy OTM wings. Tighter profit zone but higher return.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: -3, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 3, lots: 1 },
    ],
  },
  {
    id: 'batman',
    name: 'Batman',
    category: 'Neutral',
    description: 'Broken wing double structure creating dual ear peaks with high probability of profit.',
    legs: [
      { action: 'SELL', type: 'PE', strike_offset: -3, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -1, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 1, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 3, lots: 1 },
    ],
  },
  {
    id: 'jade_lizard',
    name: 'Jade Lizard',
    category: 'Neutral',
    description: 'Short OTM Put + Bear Call Spread. No upside risk if credit exceeds spread width.',
    legs: [
      { action: 'SELL', type: 'PE', strike_offset: -3, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 4, lots: 1 },
    ],
  },
  {
    id: 'reverse_jade_lizard',
    name: 'Reverse Jade Lizard',
    category: 'Neutral',
    description: 'Short OTM Call + Bull Put Spread. No downside risk if credit exceeds spread width.',
    legs: [
      { action: 'SELL', type: 'CE', strike_offset: 3, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -4, lots: 1 },
    ],
  },
  {
    id: 'double_plateau',
    name: 'Double Plateau',
    category: 'Neutral',
    description: 'Constructs two distinct flat profit regions across dual market regimes.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: -4, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -1, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 1, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 4, lots: 1 },
    ],
  },

  // ── OTHER (6 Strategies) ──────────────────────────────────────────────────
  {
    id: 'long_straddle',
    name: 'Long Straddle',
    category: 'Other',
    description: 'Buy ATM Call + Buy ATM Put. Profits on explosive volatility or sharp breakout.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 },
    ],
  },
  {
    id: 'long_strangle',
    name: 'Long Strangle',
    category: 'Other',
    description: 'Buy OTM Call + Buy OTM Put. Cheaper volatility breakout play.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -2, lots: 1 },
    ],
  },
  {
    id: 'long_iron_condor',
    name: 'Long Iron Condor',
    category: 'Other',
    description: 'Long volatility condor with defined maximum loss in center and capped wing gains.',
    legs: [
      { action: 'SELL', type: 'PE', strike_offset: -4, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: -2, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 2, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 4, lots: 1 },
    ],
  },
  {
    id: 'long_iron_butterfly',
    name: 'Long Iron Butterfly',
    category: 'Other',
    description: 'Debit butterfly capitalizing on explosive movement away from the ATM pin strike.',
    legs: [
      { action: 'SELL', type: 'PE', strike_offset: -3, lots: 1 },
      { action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 },
      { action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 3, lots: 1 },
    ],
  },
  {
    id: 'call_ratio_spread',
    name: 'Call Ratio Spread',
    category: 'Other',
    description: 'Buy 1 lower Call + Sell 2 higher Calls. High profit near sold strike.',
    legs: [
      { action: 'BUY', type: 'CE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'CE', strike_offset: 2, lots: 2 },
    ],
  },
  {
    id: 'put_ratio_spread',
    name: 'Put Ratio Spread',
    category: 'Other',
    description: 'Buy 1 higher Put + Sell 2 lower Puts. High profit near sold strike.',
    legs: [
      { action: 'BUY', type: 'PE', strike_offset: 0, lots: 1 },
      { action: 'SELL', type: 'PE', strike_offset: -2, lots: 2 },
    ],
  },
];

/**
 * Procedural SVG Payoff Curve renderer for each strategy card
 * matching the visual aesthetics of StockMojo screenshots 2, 3, 4, 5
 */
function StrategyPayoffIcon({ strategyId }: { strategyId: string }) {
  const zeroY = 42;
  const strokeColor = '#22c55e'; // Green line
  const redFill = 'rgba(239, 68, 68, 0.18)'; // Light red fill
  const greenFill = 'rgba(34, 197, 94, 0.18)'; // Light green fill

  switch (strategyId) {
    // ── BULLISH ──
    case 'buy_call':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 75,55 90,${zeroY}`} fill={redFill} />
          <polygon points={`90,${zeroY} 145,18 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,55 75,55 145,18" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'sell_put':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 50,${zeroY}`} fill={redFill} />
          <polygon points={`50,${zeroY} 75,25 145,25 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,68 75,25 145,25" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'long_synthetic_future':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 80,${zeroY}`} fill={redFill} />
          <polygon points={`80,${zeroY} 145,18 145,${zeroY}`} fill={greenFill} />
          <line x1="15" y1="68" x2="145" y2="18" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      );
    case 'bull_call_spread':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 60,55 75,${zeroY}`} fill={redFill} />
          <polygon points={`75,${zeroY} 95,24 145,24 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,55 60,55 95,24 145,24" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'bull_put_spread':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,58 45,58 60,${zeroY}`} fill={redFill} />
          <polygon points={`60,${zeroY} 80,24 145,24 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,58 45,58 80,24 145,24" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'long_calendar_with_calls':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <path d={`M 15,${zeroY} Q 35,55 55,${zeroY} Q 80,12 105,${zeroY} Q 125,55 145,${zeroY}`} fill={redFill} />
          <path d={`M 55,${zeroY} Q 80,12 105,${zeroY} Z`} fill={greenFill} />
          <path d="M 15,58 Q 50,50 80,16 Q 110,50 145,58" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      );
    case 'bull_condor':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 55,55 70,${zeroY}`} fill={redFill} />
          <polygon points={`70,${zeroY} 85,22 105,22 120,${zeroY}`} fill={greenFill} />
          <polygon points={`120,${zeroY} 135,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,55 55,55 85,22 105,22 135,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'bull_butterfly':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 75,55 88,${zeroY}`} fill={redFill} />
          <polygon points={`88,${zeroY} 105,18 122,${zeroY}`} fill={greenFill} />
          <polygon points={`122,${zeroY} 135,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,55 75,55 105,18 135,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'range_forward':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 50,${zeroY}`} fill={redFill} />
          <polygon points={`110,${zeroY} 145,20 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,68 50,42 110,42 145,20" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );

    // ── BEARISH ──
    case 'buy_put':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,18 70,${zeroY}`} fill={greenFill} />
          <polygon points={`70,${zeroY} 85,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,18 85,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'sell_call':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,25 85,25 110,${zeroY}`} fill={greenFill} />
          <polygon points={`110,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,25 85,25 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'short_synthetic_future':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,18 80,${zeroY}`} fill={greenFill} />
          <polygon points={`80,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <line x1="15" y1="18" x2="145" y2="68" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      );
    case 'bear_call_spread':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,24 65,24 85,${zeroY}`} fill={greenFill} />
          <polygon points={`85,${zeroY} 100,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,24 65,24 100,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'bear_put_spread':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,24 80,24 95,${zeroY}`} fill={greenFill} />
          <polygon points={`95,${zeroY} 115,58 145,58 145,${zeroY}`} fill={redFill} />
          <polyline points="15,24 80,24 115,58 145,58" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'long_calendar_with_puts':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <path d="M 15,58 Q 50,50 80,16 Q 110,50 145,58" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" />
          <path d={`M 55,${zeroY} Q 80,16 105,${zeroY} Z`} fill={greenFill} />
        </svg>
      );
    case 'bear_condor':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 35,55 50,${zeroY}`} fill={redFill} />
          <polygon points={`50,${zeroY} 65,22 85,22 100,${zeroY}`} fill={greenFill} />
          <polygon points={`100,${zeroY} 115,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,55 35,55 65,22 85,22 115,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'bear_butterfly':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 45,55 58,${zeroY}`} fill={redFill} />
          <polygon points={`58,${zeroY} 75,18 92,${zeroY}`} fill={greenFill} />
          <polygon points={`92,${zeroY} 105,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,55 45,55 75,18 105,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'risk_reversal':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,20 50,${zeroY}`} fill={greenFill} />
          <polygon points={`110,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,20 50,42 110,42 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );

    // ── NEUTRAL ──
    case 'short_straddle':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 45,${zeroY}`} fill={redFill} />
          <polygon points={`45,${zeroY} 80,18 115,${zeroY}`} fill={greenFill} />
          <polygon points={`115,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,68 80,18 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'short_strangle':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 40,${zeroY}`} fill={redFill} />
          <polygon points={`40,${zeroY} 65,22 95,22 120,${zeroY}`} fill={greenFill} />
          <polygon points={`120,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,68 65,22 95,22 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'short_iron_condor':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 35,55 50,${zeroY}`} fill={redFill} />
          <polygon points={`50,${zeroY} 65,24 95,24 110,${zeroY}`} fill={greenFill} />
          <polygon points={`110,${zeroY} 125,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,55 35,55 65,24 95,24 125,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'short_iron_butterfly':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,55 50,55 62,${zeroY}`} fill={redFill} />
          <polygon points={`62,${zeroY} 80,18 98,${zeroY}`} fill={greenFill} />
          <polygon points={`98,${zeroY} 110,55 145,55 145,${zeroY}`} fill={redFill} />
          <polyline points="15,55 50,55 80,18 110,55 145,55" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'batman':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 35,${zeroY}`} fill={redFill} />
          <polygon points={`35,${zeroY} 55,22 80,32 105,22 125,${zeroY}`} fill={greenFill} />
          <polygon points={`125,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,68 55,22 80,32 105,22 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'jade_lizard':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 45,${zeroY}`} fill={redFill} />
          <polygon points={`45,${zeroY} 70,22 110,22 145,30 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,68 70,22 110,22 125,30 145,30" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'reverse_jade_lizard':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,30 35,30 50,22 90,22 115,${zeroY}`} fill={greenFill} />
          <polygon points={`115,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,30 35,30 50,22 90,22 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'double_plateau':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,60 30,60 40,${zeroY}`} fill={redFill} />
          <polygon points={`40,${zeroY} 50,24 70,24 80,${zeroY}`} fill={greenFill} />
          <polygon points={`80,${zeroY} 90,24 110,24 120,${zeroY}`} fill={greenFill} />
          <polygon points={`120,${zeroY} 130,60 145,60 145,${zeroY}`} fill={redFill} />
          <polyline points="15,60 30,60 50,24 70,24 80,38 90,24 110,24 130,60 145,60" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );

    // ── OTHER ──
    case 'long_straddle':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,18 45,${zeroY}`} fill={greenFill} />
          <polygon points={`45,${zeroY} 80,68 115,${zeroY}`} fill={redFill} />
          <polygon points={`115,${zeroY} 145,18 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,18 80,68 145,18" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'long_strangle':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,18 40,${zeroY}`} fill={greenFill} />
          <polygon points={`40,${zeroY} 65,65 95,65 120,${zeroY}`} fill={redFill} />
          <polygon points={`120,${zeroY} 145,18 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,18 65,65 95,65 145,18" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'long_iron_condor':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,25 35,25 50,${zeroY}`} fill={greenFill} />
          <polygon points={`50,${zeroY} 65,60 95,60 110,${zeroY}`} fill={redFill} />
          <polygon points={`110,${zeroY} 125,25 145,25 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,25 35,25 65,60 95,60 125,25 145,25" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'long_iron_butterfly':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,25 50,25 62,${zeroY}`} fill={greenFill} />
          <polygon points={`62,${zeroY} 80,68 98,${zeroY}`} fill={redFill} />
          <polygon points={`98,${zeroY} 110,25 145,25 145,${zeroY}`} fill={greenFill} />
          <polyline points="15,25 50,25 80,68 110,25 145,25" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'call_ratio_spread':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,48 55,48 70,${zeroY}`} fill={redFill} />
          <polygon points={`70,${zeroY} 95,18 115,${zeroY}`} fill={greenFill} />
          <polygon points={`115,${zeroY} 145,68 145,${zeroY}`} fill={redFill} />
          <polyline points="15,48 55,48 95,18 145,68" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'put_ratio_spread':
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polygon points={`15,${zeroY} 15,68 45,${zeroY}`} fill={redFill} />
          <polygon points={`45,${zeroY} 65,18 90,${zeroY}`} fill={greenFill} />
          <polygon points={`90,${zeroY} 105,48 145,48 145,${zeroY}`} fill={redFill} />
          <polyline points="15,68 65,18 105,48 145,48" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 160 80" className="w-full h-full">
          <line x1="10" y1={zeroY} x2="150" y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="2,2" />
          <polyline points="15,60 80,20 145,60" fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      );
  }
}

export function ReadyMadeStrategiesGrid({ onSelectStrategy, selectedStrategyId }: ReadyMadeStrategiesGridProps) {
  const [activeCategory, setActiveCategory] = useState<'Bullish' | 'Bearish' | 'Neutral' | 'Other'>('Bullish');

  const categories: ('Bullish' | 'Bearish' | 'Neutral' | 'Other')[] = ['Bullish', 'Bearish', 'Neutral', 'Other'];
  const filteredStrategies = READY_MADE_STRATEGIES.filter((s) => s.category === activeCategory);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Category Filter Pills (Matching StockMojo screenshots) */}
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
        {categories.map((cat) => {
          const isActive = activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className="btn btn-sm"
              style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                padding: 'var(--space-1) var(--space-4)',
                borderRadius: 'var(--radius-full)',
                background: isActive ? 'var(--color-primary-15)' : 'var(--color-bg-secondary)',
                color: isActive ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                border: isActive ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Grid of Strategy Cards with Payoff Curves */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
          gap: 'var(--space-3)',
          maxHeight: '520px',
          overflowY: 'auto',
          paddingRight: 'var(--space-1)',
        }}
      >
        {filteredStrategies.map((strat) => {
          const isSelected = selectedStrategyId === strat.id;

          return (
            <motion.div
              key={strat.id}
              whileHover={{ y: -3, borderColor: 'var(--color-primary)' }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelectStrategy(strat)}
              style={{
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-md)',
                background: isSelected ? 'var(--color-primary-10)' : 'var(--color-bg-secondary)',
                border: isSelected ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
                position: 'relative',
                boxShadow: isSelected ? '0 0 15px var(--color-primary-20)' : 'none',
                transition: 'border 0.2s ease, background 0.2s ease',
              }}
            >
              {/* Payoff SVG preview container */}
              <div
                style={{
                  width: '100%',
                  height: '75px',
                  background: 'var(--color-bg-primary)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border-subtle)',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <StrategyPayoffIcon strategyId={strat.id} />
              </div>

              {/* Title & Selected indicator */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span
                  style={{
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    color: isSelected ? 'var(--color-primary)' : 'var(--color-text-primary)',
                    letterSpacing: '-0.01em',
                  }}
                >
                  {strat.name}
                </span>
                {isSelected ? (
                  <Check size={14} color="var(--color-primary)" />
                ) : (
                  <Sparkles size={11} color="var(--color-text-muted)" />
                )}
              </div>

              <p
                style={{
                  fontSize: '0.62rem',
                  color: 'var(--color-text-muted)',
                  lineHeight: 1.3,
                  margin: 0,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {strat.description}
              </p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
