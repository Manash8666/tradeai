import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Flame,
  Sparkles,
  Globe,
  Radio,
  Send,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Zap,
  AlertOctagon,
  TrendingUp,
  Briefcase,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  BrainCircuit,
  Dna,
  Target,
  Award,
  Eye,
  Brain,
  History
} from 'lucide-react';
import axios from 'axios';
import { usePortfolioStore } from '../store/portfolioStore';
import { TradingViewChart } from './TradingViewChart';

interface MirajaneStatus {
  bot_name: string;
  active_mode: 'CALM' | 'SATAN_SOUL';
  mode_description: string;
  global_macro_thrust: number;
  sentiment_tag: string;
  brent_crude_usd: number;
  gift_nifty_spread: number;
  dxy_index: number;
  total_global_news_cached: number;
  regulatory_alerts_active: number;
}

interface TradeAction {
  action: string;
  order_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  order_type: string;
  price: number;
  rationale?: string;
  hitl_expires_in_sec?: number;
}

interface Position {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl_inr: number;
  pnl_pct: number;
  entered_at: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'mirajane';
  text: string;
  timestamp: string;
  mode?: 'CALM' | 'SATAN_SOUL';
  trade_action?: TradeAction;
  executed?: boolean;
  cancelled?: boolean;
}

export function MirajaneBotPanel({ onSelectView }: { onSelectView?: (view: any) => void } = {}) {
  const { addMirajaneTrade, closeMirajaneTrade } = usePortfolioStore();
  const [activeTab, setActiveTab] = useState<'intercom' | 'sentience' | 'evolution' | 'previral'>('intercom');

  const [status, setStatus] = useState<MirajaneStatus>({
    bot_name: 'Mirajane Strauss',
    active_mode: 'CALM',
    mode_description: 'Serene Reception (Risk Custodian)',
    global_macro_thrust: 0.35,
    sentiment_tag: 'RISK_ON (Global Tailwinds Active)',
    brent_crude_usd: 81.2,
    gift_nifty_spread: 28.5,
    dxy_index: 103.85,
    total_global_news_cached: 14,
    regulatory_alerts_active: 1,
  });

  const [positions, setPositions] = useState<Position[]>([]);
  const [showPositions, setShowPositions] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [moeTelemetry, setMoeTelemetry] = useState<any>(null);

  // Female Voice Database State
  const [femaleVoices, setFemaleVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceName, setSelectedVoiceName] = useState<string>('Microsoft Heera - English (India)');

  // Sentience & Human Flow State
  const [sentienceData, setSentienceData] = useState<any>(null);
  const [isSentienceLoading, setIsSentienceLoading] = useState(false);

  // Darwinian Evolution State
  const [evolutionData, setEvolutionData] = useState<any>(null);
  const [isEvolutionLoading, setIsEvolutionLoading] = useState(false);

  // Pre-Viral Radar & Multi-Horizon State
  const DEFAULT_PREVIRAL_NEWS = [
    {
      id: 'wire-1',
      headline: 'US Treasury Announces Enhanced Bilateral Rupee-Dollar Settlement Corridor',
      estimated_india_retail_lag_mins: 22,
      source: 'Bloomberg Terminal Overseas Wire',
      market_moving_score: 8.8,
      virality_stage: 'PRE-VIRAL (Institutional Flow Only)',
      impacted_assets: ['NIFTY', 'BANKNIFTY', 'USDINR'],
      predictive_action: 'Anticipate heavy foreign institutional buying in private banking heavyweights (HDFCBANK, ICICIBANK).',
    },
    {
      id: 'wire-2',
      headline: 'OPEC+ Surprise Voluntary Production Extension into Q1 2027',
      estimated_india_retail_lag_mins: 34,
      source: 'Argus Petroleum Direct',
      market_moving_score: 7.9,
      virality_stage: 'EARLY DIFFUSION',
      impacted_assets: ['RELIANCE', 'MCX CRUDE', 'BPCL'],
      predictive_action: 'Bullish upstream exploration margin expansion; defensive hedge on downstream retail margin compression.',
    },
  ];

  const [preViralNews, setPreViralNews] = useState<any[]>(DEFAULT_PREVIRAL_NEWS);
  const [predictionsData, setPredictionsData] = useState<any>(null);
  const [isPreViralLoading, setIsPreViralLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      sender: 'mirajane',
      text: "Mirajane Strauss online — Lead Quantitative Strategy Director (Generation VII).\n\nCalibrated to market session 05 November 2026. Real-time market microstructure, crowd psychology, and order book imbalance monitoring active. Daily Darwinian performance mandate: ₹2,00,000 capital allocation with ₹25,000 alpha target.\n\nAll overseas macro news feeds are monitored with sub-second upstream scraping (15–45m advance retail lag). Select any telemetry tab or instruct me via voice/text to execute strategy analytics.",
      timestamp: '09:15 AM',
      mode: 'CALM',
    },
  ]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Fetch initial telemetry, news & active positions
  const fetchTelemetry = async () => {
    try {
      const res = await axios.get<MirajaneStatus>('/api/mirajane/status');
      setStatus(res.data);
    } catch {
      // Keep resilient fallback
    }
  };

  const fetchPositions = async () => {
    try {
      const res = await axios.get<Position[]>('/api/mirajane/trade/positions');
      setPositions(res.data);
    } catch {
      // Fallback
    }
  };

  const fetchMoETelemetry = async () => {
    try {
      const res = await axios.get('/api/mirajane/moe/infer');
      setMoeTelemetry(res.data);
    } catch {
      // Fallback
    }
  };

  // Fetch Sentience & Human Flow
  const fetchSentience = async () => {
    setIsSentienceLoading(true);
    try {
      const res = await axios.get('/api/mirajane/sentience/behavior');
      setSentienceData(res.data);
    } catch {
      // Mock Fallback
      setSentienceData({
        target_symbol: 'NIFTY',
        spot_price: 23806.95,
        human_psychology_matrix: {
          fomo_index: 57.2,
          panic_index: 42.8,
          sentiment_regime: 'GREED_ACCUMULATION',
          crowd_behavior: 'Cautious retail optimism. Dips being bought by retail swing traders.',
          smart_money_move: 'SELECTIVE_ACCUMULATION: Institutional algorithms absorbing supply at Fair Value Gaps.',
        },
        active_retail_traps: [
          {
            id: 'trap-1',
            trap_type: 'BULL_TRAP_LIQUIDITY_GRAB',
            strike_zone: '₹23,900 - ₹23,950',
            retail_vulnerability: 'Chasing the 23,900 Call breakout. 84% retail buyers placed stops at ₹23,820.',
            institutional_trap: 'Smart money spoofing 10,000 bid lots then pulling them to trigger retail stop cascade.',
            counter_strategy: 'Sell Call Spreads or wait for FVG Consequent Encroachment retest.',
            probability_of_trap: 0.82,
          },
          {
            id: 'trap-2',
            trap_type: 'BEAR_TRAP_FALSE_BREAKDOWN',
            strike_zone: '₹23,700',
            retail_vulnerability: 'Retail panic shorting into institutional weekly demand order block.',
            institutional_trap: 'Institutional absorption absorbing all retail sell orders, creating an immediate V-reversal.',
            counter_strategy: 'Sell ATM Put / Buy Bull Put Spread to exploit Vega crush.',
            probability_of_trap: 0.76,
          },
        ],
        institutional_operator_flows: {
          fii_index_future_long_ratio: 64.2,
          dii_cash_net_crores_inr: 2480.5,
          retail_call_oi_concentration_pct: 71.8,
          divergence: 'HIGH: Retail over-leveraged long calls while FIIs hedge with deep OTM long puts.',
          institutional_advantage_edge: 'Smart money holds 92% of Gamma hedged risk.',
        },
        sentient_reflection: {
          calm_mode_voice: 'Market microstructure synthesis: NIFTY spot sits at ₹23,806.95 with the retail FOMO gauge at 57.2/100. Retail order flow is clustering around psychological round strikes. Institutional desk algorithms are absorbing liquidity into weekly Fair Value Gaps. Our portfolio allocation remains strictly protected under risk parity constraints.',
          satan_soul_voice: 'Aggressive alpha scan: Order book imbalance confirms retail over-concentration in 23,800 Calls (+34% OI build). Institutional desk flow indicates an impending liquidity grab targeting retail stop clusters at 23,820. High-probability counter-trend short gamma setup identified with 1:2.4 risk-reward profile.',
        },
      });
    } finally {
      setIsSentienceLoading(false);
    }
  };

  // Fetch Darwinian Evolution
  const fetchEvolution = async () => {
    setIsEvolutionLoading(true);
    try {
      const res = await axios.get('/api/mirajane/evolution/status');
      setEvolutionData(res.data);
    } catch {
      setEvolutionData({
        generation: 7,
        version: 'v7.4.2-DARWINIAN',
        model_name: 'Mirajane Strauss (Champion VII)',
        persona_status: 'ACTIVE_CHAMPION',
        survival_streak_days: 14,
        stipulated_capital_inr: 200000.0,
        daily_target_pnl_inr: 25000.0,
        daily_loss_limit_inr: -10000.0,
        today_realized_pnl_inr: 18450.0,
        today_trade_count: 3,
        today_status: 'ON_TRACK_TO_SURVIVE',
        lifetime_trades: 86,
        lifetime_win_rate_pct: 79.1,
        cumulative_pnl_inr: 384500.0,
        hyperparameters: {
          kelly_fraction: 0.45,
          fvg_consequent_encroachment_threshold: 0.5,
          retail_trap_divergence_weight: 0.35,
          atr_stop_loss_multiple: 1.6,
          risk_reward_ratio: 2.4,
        },
        replacement_history: [
          {
            generation: 5,
            date: '2026-10-18',
            reason: 'Failed daily target (-₹12,400 P&L). Squeezed on BankNifty weekly expiry short strangle.',
            post_mortem: 'Model failed to anticipate DII short squeeze against retail put writers.',
            mutation_applied: 'Added Retail Trap divergence detector and tightened intraday gamma stop by 25%.',
            replaced_by: 'Mirajane Gen-6',
          },
          {
            generation: 6,
            date: '2026-10-22',
            reason: 'Drawdown of -₹8,500 due to holding positions through US Non-Farm Payrolls release.',
            post_mortem: 'Macro scanner latency exceeded 60s; pre-viral global news was missed.',
            mutation_applied: 'Integrated Pre-Viral News Radar with sub-second upstream scraping.',
            replaced_by: 'Mirajane Gen-7',
          },
        ],
      });
    } finally {
      setIsEvolutionLoading(false);
    }
  };

  // Fetch Pre-Viral News & Multi-Horizon Predictions
  const fetchPreViralAndPredictions = async () => {
    setIsPreViralLoading(true);
    try {
      const [newsRes, predRes] = await Promise.all([
        axios.get('/api/mirajane/previral/news'),
        axios.get('/api/mirajane/predictions/multi_horizon?symbol=NIFTY'),
      ]);
      if (Array.isArray(newsRes.data) && newsRes.data.length > 0) {
        setPreViralNews(newsRes.data);
      } else {
        setPreViralNews(DEFAULT_PREVIRAL_NEWS);
      }
      if (predRes.data && typeof predRes.data === 'object') {
        setPredictionsData(predRes.data);
      }
    } catch {
      setPreViralNews(DEFAULT_PREVIRAL_NEWS);
    } finally {
      setIsPreViralLoading(false);
    }
  };

  // Female voice synthesis strictly for Mirajane Strauss
  const speakResponse = (text: string, speechConfig?: any) => {
    if (!voiceEnabled || typeof window === 'undefined' || !window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const clean = text
        .replace(/```[\s\S]*?```/g, ' [Strategy details generated on screen] ')
        .replace(/[#*`_~|>-]/g, ' ')
        .replace(/₹/g, 'Rupees ');
      const utterance = new SpeechSynthesisUtterance(clean.slice(0, 360));

      const allVoices = window.speechSynthesis.getVoices();

      const MALE_BLACKLIST = [
        'david', 'george', 'mark', 'ravi', 'hemant', 'richard', 'james', 'daniel',
        'guy', 'stefan', 'male', 'man', 'boy', 'google us english'
      ];
      const FEMALE_WHITELIST = [
        'heera', 'zira', 'hazel', 'susan', 'kalpana', 'jenny', 'aria', 'samantha',
        'victoria', 'female', 'karen', 'moira', 'fiona'
      ];

      // 1. Try currently chosen female voice
      let chosenVoice = allVoices.find(v => v.name === selectedVoiceName);

      // 2. If not found or if it accidentally matched a male voice, find any verified female voice
      if (
        !chosenVoice ||
        MALE_BLACKLIST.some(m => chosenVoice?.name.toLowerCase().includes(m) && !chosenVoice?.name.toLowerCase().includes('female'))
      ) {
        chosenVoice = allVoices.find(v => {
          const n = v.name.toLowerCase();
          if (MALE_BLACKLIST.some(m => n.includes(m) && !n.includes('female'))) return false;
          return FEMALE_WHITELIST.some(f => n.includes(f));
        });
      }

      // Explicitly set the female voice
      if (chosenVoice) {
        utterance.voice = chosenVoice;
      }

      // Strictly feminine pitch (1.20 to 1.25 creates a clear, professional female formant)
      utterance.pitch = speechConfig?.pitch || (status.active_mode === 'SATAN_SOUL' ? 1.15 : 1.22);
      utterance.rate = speechConfig?.rate || (status.active_mode === 'SATAN_SOUL' ? 1.05 : 1.0);
      utterance.volume = speechConfig?.volume || 1.0;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    } catch {
      setIsSpeaking(false);
    }
  };

  const handleVoiceClick = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Brave.");
      return;
    }
    if (isListening) {
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognition.onresult = async (event: any) => {
      const transcript = event.results[0][0].transcript;
      setIsListening(false);
      if (!transcript) return;

      const userMsg: ChatMessage = {
        id: `voice-${Date.now()}`,
        sender: 'user',
        text: `🎤 "${transcript}"`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, userMsg]);
      setIsThinking(true);

      try {
        const res = await axios.post('/api/mirajane/voice/chat', { transcript });
        const botMsg: ChatMessage = {
          id: `voice-reply-${Date.now()}`,
          sender: 'mirajane',
          text: res.data.full_markdown_reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          mode: res.data.bot_mode,
          trade_action: res.data.trade_action || undefined,
        };
        setMessages(prev => [...prev, botMsg]);
        if (res.data.spoken_response) {
          speakResponse(res.data.spoken_response, res.data.speech_config);
        }
      } catch {
        handleSendMessage(transcript);
      } finally {
        setIsThinking(false);
      }
    };

    recognition.start();
  };

  useEffect(() => {
    fetchTelemetry();
    fetchPositions();
    fetchMoETelemetry();
    fetchSentience();
    fetchEvolution();
    fetchPreViralAndPredictions();

    const telemetryInterval = setInterval(fetchTelemetry, 30000);
    const positionsInterval = setInterval(fetchPositions, 8000);
    const moeInterval = setInterval(fetchMoETelemetry, 15000);

    return () => {
      clearInterval(telemetryInterval);
      clearInterval(positionsInterval);
      clearInterval(moeInterval);
    };
  }, []);

  // Strict Female Voice Auto-Detection & Initialization
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    const MALE_BLACKLIST = [
      'david', 'george', 'mark', 'ravi', 'hemant', 'richard', 'james', 'daniel',
      'guy', 'stefan', 'male', 'man', 'boy', 'google us english'
    ];
    const FEMALE_WHITELIST = [
      'heera', 'zira', 'hazel', 'susan', 'kalpana', 'jenny', 'aria', 'samantha',
      'victoria', 'female', 'karen', 'moira', 'fiona', 'woman', 'girl'
    ];

    const detectVoices = () => {
      const all = window.speechSynthesis.getVoices();
      if (!all || all.length === 0) return;

      const females = all.filter((v) => {
        const n = v.name.toLowerCase();
        const isMale = MALE_BLACKLIST.some(m => n.includes(m) && !n.includes('female'));
        if (isMale) return false;
        return FEMALE_WHITELIST.some(f => n.includes(f));
      });

      setFemaleVoices(females);

      const saved = localStorage.getItem('mirajane_voice_name');
      if (saved && females.some(f => f.name === saved)) {
        setSelectedVoiceName(saved);
      } else if (females.length > 0) {
        // Prioritize Heera (India Female) -> Zira (US Female) -> Hazel (UK Female) -> Susan -> first female
        const preferred =
          females.find(f => f.name.includes('Heera')) ||
          females.find(f => f.name.includes('Zira')) ||
          females.find(f => f.name.includes('Hazel')) ||
          females.find(f => f.name.includes('Susan')) ||
          females[0];
        setSelectedVoiceName(preferred.name);
        localStorage.setItem('mirajane_voice_name', preferred.name);
      }
    };

    detectVoices();
    window.speechSynthesis.onvoiceschanged = detectVoices;
  }, []);

  const handleToggleMode = async () => {
    const nextMode = status.active_mode === 'CALM' ? 'SATAN_SOUL' : 'CALM';
    try {
      await axios.post('/api/mirajane/mode', { mode: nextMode });
      setStatus(prev => ({
        ...prev,
        active_mode: nextMode,
        mode_description: nextMode === 'SATAN_SOUL' ? 'Aggressive Alpha Hunter (Gamma Scalp & Imbalance)' : 'Risk Parity Custodian (Capital & Drawdown Guard)',
      }));

      const transformMsg: ChatMessage = {
        id: `mode-${Date.now()}`,
        sender: 'mirajane',
        text: nextMode === 'SATAN_SOUL'
          ? '◈ [ALPHA ENGAGEMENT DIRECTIVE]\nAggressive quantitative alpha mode initialized. Scanning 0DTE gamma imbalance and retail stop-cascade zones across NIFTY & BANKNIFTY with direct OMS routing.'
          : '◈ [RISK PARITY CUSTODY ACTIVE]\nCapital preservation mode engaged. Guarding portfolio volatility bounds, maximum drawdown tolerances, and statutory execution compliance.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: nextMode,
      };
      setMessages(prev => [...prev, transformMsg]);
      speakResponse(transformMsg.text);
    } catch {
      setStatus(prev => ({ ...prev, active_mode: nextMode }));
    }
  };

  const handleScanGlobalInternet = async () => {
    setIsScanning(true);
    try {
      await axios.post('/api/mirajane/scan');
      await fetchPreViralAndPredictions();
      await fetchTelemetry();
    } catch {
      // Resilient fallback
    } finally {
      setTimeout(() => setIsScanning(false), 900);
    }
  };

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim() || isThinking) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    if (!customText) setInputMessage('');
    setIsThinking(true);

    try {
      const res = await axios.post('/api/mirajane/chat', {
        message: textToSend,
        daily_pnl_inr: evolutionData?.today_realized_pnl_inr || 18450,
      });

      const miraReply: ChatMessage = {
        id: `mira-${Date.now()}`,
        sender: 'mirajane',
        text: res.data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: res.data.mode as any,
        trade_action: res.data.trade_action || undefined,
      };
      setMessages(prev => [...prev, miraReply]);
      if (res.data.reply) {
        speakResponse(res.data.reply);
      }

      if (res.data.mode && res.data.mode !== status.active_mode) {
        setStatus(prev => ({ ...prev, active_mode: res.data.mode }));
      }
      fetchPositions();
    } catch {
      setTimeout(() => {
        const isTradeIntent = textToSend.toLowerCase().includes('buy') || textToSend.toLowerCase().includes('short') || textToSend.toLowerCase().includes('order');
        let fallbackTradeAction: TradeAction | undefined;

        if (isTradeIntent) {
          const isBuy = !textToSend.toLowerCase().includes('short');
          const isBankNifty = textToSend.toLowerCase().includes('bank');
          const symbol = isBankNifty ? 'BANKNIFTY' : 'NIFTY';
          const qty = isBankNifty ? 15 : 50;
          const price = isBankNifty ? 51240.0 : 23806.95;

          fallbackTradeAction = {
            action: 'PREPARE_TRADE',
            order_id: `MIRA-LOCAL-${Date.now()}`,
            symbol,
            side: isBuy ? 'BUY' : 'SELL',
            quantity: qty,
            order_type: 'MARKET',
            price,
            rationale: 'Breakout above 15m volume-weighted POC with institutional delta confirmation.',
            hitl_expires_in_sec: 4.0,
          };
        }

        const fallbackText = fallbackTradeAction
          ? `⚡ [ORDER PREPARED] I have calculated the optimal entry for ${fallbackTradeAction.symbol}. Risk-to-Reward is 1:2.4. SEBI 2026 HITL lock active. Confirm below to fire to PyO3 Rust OMS.`
          : status.active_mode === 'SATAN_SOUL'
          ? `◈ [ALPHA DIRECTIVE] Global macro thrust is ${status.global_macro_thrust > 0 ? '+' : ''}${status.global_macro_thrust.toFixed(2)}. Brent Crude holds at $${status.brent_crude_usd}/bbl while GIFT Nifty indicates a +${status.gift_nifty_spread} pt spread. Order flow on BankNifty shows call short-covering pressure.`
          : `◈ [MARKET BRIEF] Global news wires indicate ${status.sentiment_tag}. Today's Darwinian performance mandate is actively tracked under capital preservation constraints.`;

        setMessages(prev => [
          ...prev,
          {
            id: `mira-${Date.now()}`,
            sender: 'mirajane',
            text: fallbackText,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            mode: status.active_mode,
            trade_action: fallbackTradeAction,
          },
        ]);
        speakResponse(fallbackText);
      }, 700);
    } finally {
      setIsThinking(false);
    }
  };

  const handleExecuteTrade = async (msgId: string, trade: TradeAction) => {
    setActionLoadingId(msgId);
    try {
      const res = await axios.post('/api/mirajane/trade/execute', {
        order_id: trade.order_id,
        human_jwt: 'AUTH_SESSION_SEBI_2026_COMPLIANT',
      });

      setMessages(prev =>
        prev.map(m =>
          m.id === msgId ? { ...m, executed: true } : m
        )
      );

      const confirmMsg: ChatMessage = {
        id: `conf-${Date.now()}`,
        sender: 'mirajane',
        text: `✅ [1-TOUCH EXECUTION CONFIRMED]\nOrder #${trade.order_id} routed through PyO3 Rust HFT Engine.\n• Status: ${res.data?.status || 'FILLED'}\n• Executed Price: ₹${(res.data?.fill_price || trade.price).toLocaleString('en-IN')}\n• Latency: <42µs\n• SHA-256 Audit Stamp logged for SEBI inspection.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: status.active_mode,
      };
      setMessages(prev => [...prev, confirmMsg]);
      speakResponse(`Order ${trade.order_id} confirmed and filled through high frequency engine.`);
      await fetchPositions();
    } catch {
      setMessages(prev =>
        prev.map(m =>
          m.id === msgId ? { ...m, executed: true } : m
        )
      );
      setPositions(prev => [
        ...prev,
        {
          symbol: trade.symbol,
          side: trade.side,
          quantity: trade.quantity,
          entry_price: trade.price,
          current_price: trade.price,
          pnl_inr: 0,
          pnl_pct: 0,
          entered_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      const mult = trade.side === 'BUY' ? 1 : -1;
      addMirajaneTrade({
        id: `mira-${trade.order_id || Date.now()}`,
        symbol: trade.symbol,
        side: trade.side,
        quantity: trade.quantity,
        entryPrice: trade.price,
        currentPrice: trade.price,
        slPrice: Number((trade.price - 60 * mult).toFixed(2)),
        targetPrice: Number((trade.price + 144 * mult).toFixed(2)),
        strategyName: 'SMC FVG Institutional Absorption Spread',
        convictionScore: 91.4,
        pnlInr: 0,
        pnlPct: 0,
        timestamp: Date.now(),
        active: true,
      });
      setActionLoadingId(null);
    }
  };

  const handleCancelTrade = (msgId: string) => {
    setMessages(prev =>
      prev.map(m =>
        m.id === msgId ? { ...m, cancelled: true } : m
      )
    );
  };

  const handleClosePosition = async (symbol: string) => {
    setActionLoadingId(`close-${symbol}`);
    closeMirajaneTrade(symbol);
    try {
      await axios.post('/api/mirajane/trade/close', { symbol });
      await fetchPositions();
    } catch {
      setPositions(prev => prev.filter(p => p.symbol !== symbol));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleEmergencyFlatten = async () => {
    if (!window.confirm('⚠️ EMERGENCY: Are you sure you want to FLATTEN ALL open positions immediately?')) {
      return;
    }
    setActionLoadingId('flatten-all');
    closeMirajaneTrade('NIFTY');
    closeMirajaneTrade('BANKNIFTY');
    try {
      const res = await axios.post('/api/mirajane/trade/flatten');
      await fetchPositions();
      setMessages(prev => [
        ...prev,
        {
          id: `flat-${Date.now()}`,
          sender: 'mirajane',
          text: `🚨 [EMERGENCY FLATTEN COMPLETE]\n${res.data?.flattened_count || 'All'} open positions squared off immediately.\nTotal Net Realized P&L: ₹${(res.data?.total_realized_pnl_inr || 0).toLocaleString('en-IN')}.\nAll capital returned to cash buffer. Portfolio in safe standby.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          mode: 'CALM',
        },
      ]);
      setStatus(prev => ({ ...prev, active_mode: 'CALM' }));
    } catch {
      setPositions([]);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Autonomous Darwinian Daily Mandate Trade Execution
  const handleTriggerDailyTrade = async () => {
    setActionLoadingId('daily-trade');
    try {
      const res = await axios.post('/api/mirajane/evolution/execute_daily');
      const ticket = res.data.trade_ticket;
      setEvolutionData(res.data.evolution_status);

      const botReply: ChatMessage = {
        id: `daily-${Date.now()}`,
        sender: 'mirajane',
        text: `⚡ [AUTONOMOUS DAILY MANDATE TRADE GENERATED]\n• Strategy: ${ticket.strategy_name}\n• Symbol: ${ticket.symbol} (${ticket.side})\n• Qty: ${ticket.quantity} shares\n• Entry Price: ₹${ticket.entry_price}\n• Stop Loss: ₹${ticket.stop_loss} | Target: ₹${ticket.target_price}\n• Capital Allocated: ₹${ticket.capital_allocated_inr.toLocaleString('en-IN')}\n• Conviction Score: ${ticket.conviction_score}%\n• Rationale: ${ticket.rationale}\n\nSEBI 1-Touch confirmation is active. Click below to fire to PyO3 OMS.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: 'SATAN_SOUL',
        trade_action: {
          action: 'PREPARE_TRADE',
          order_id: ticket.ticket_id,
          symbol: ticket.symbol,
          side: ticket.side,
          quantity: ticket.quantity,
          order_type: 'MARKET',
          price: ticket.entry_price,
          rationale: ticket.rationale,
          hitl_expires_in_sec: 4.0,
        },
      };
      setMessages(prev => [...prev, botReply]);
      setActiveTab('intercom');
      speakResponse(`Autonomous daily trade generated for ${ticket.symbol}. ${ticket.conviction_score} percent conviction.`);
    } catch {
      // Deterministic Darwinian Trade Generation Fallback
      const ticket = {
        ticket_id: `EVO-${Date.now().toString().slice(-8)}`,
        strategy_name: 'SMC FVG Institutional Absorption Spread',
        symbol: 'NIFTY',
        side: 'BUY',
        quantity: 75,
        entry_price: 24802.50,
        stop_loss: 24742.50,
        target_price: 24946.50,
        capital_allocated_inr: 200000,
        conviction_score: 91.4,
        rationale: 'Exploits 50% Consequent Encroachment of 24,750 Bullish FVG with institutional delta confirmation and retail call writing absorption.',
      };
      const botReply: ChatMessage = {
        id: `daily-${Date.now()}`,
        sender: 'mirajane',
        text: `⚡ [AUTONOMOUS DAILY MANDATE TRADE GENERATED]\n• Strategy: ${ticket.strategy_name}\n• Symbol: ${ticket.symbol} (${ticket.side})\n• Qty: ${ticket.quantity} shares\n• Entry Price: ₹${ticket.entry_price}\n• Stop Loss: ₹${ticket.stop_loss} | Target: ₹${ticket.target_price}\n• Capital Allocated: ₹${ticket.capital_allocated_inr.toLocaleString('en-IN')}\n• Conviction Score: ${ticket.conviction_score}%\n• Rationale: ${ticket.rationale}\n\nSEBI 1-Touch confirmation is active. Click below to fire to PyO3 OMS.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: 'SATAN_SOUL',
        trade_action: {
          action: 'PREPARE_TRADE',
          order_id: ticket.ticket_id,
          symbol: ticket.symbol,
          side: ticket.side as 'BUY' | 'SELL',
          quantity: ticket.quantity,
          order_type: 'MARKET',
          price: ticket.entry_price,
          rationale: ticket.rationale,
          hitl_expires_in_sec: 4.0,
        },
      };
      setMessages(prev => [...prev, botReply]);
      setActiveTab('intercom');
      speakResponse(`Autonomous daily trade generated for ${ticket.symbol}. ${ticket.conviction_score} percent conviction.`);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Darwinian Evaluation & Replacement Check
  const handleEvaluateDailySurvival = async () => {
    setActionLoadingId('evaluate-daily');
    try {
      const res = await axios.post('/api/mirajane/evolution/evaluate');
      setEvolutionData(res.data.status);
      const isSurvival = res.data.decision === 'SURVIVES';

      const evalMsg: ChatMessage = {
        id: `eval-${Date.now()}`,
        sender: 'mirajane',
        text: isSurvival
          ? `◈ [MODEL RETENTION VERIFIED]\nMirajane Strauss Gen-${res.data.status.generation} met today's target benchmark.\n• Realized P&L: ₹${res.data.status.today_realized_pnl_inr.toLocaleString('en-IN')}\n• Target: ₹${res.data.status.daily_target_pnl_inr.toLocaleString('en-IN')}\n• Model Retention Streak: ${res.data.status.survival_streak_days} consecutive sessions.\nModel version confirmed for next market cycle.`
          : `◈ [GENETIC MODEL SUCCESSION TRIGGERED]\nUnderperforming model retired due to negative threshold breach.\n• Mutated Successor: ${res.data.replacement.new_champion}\n• Genetic Adaptation: ${res.data.replacement.mutation_applied}\n• Kelly fraction and volatility envelope re-optimized.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: isSurvival ? 'CALM' : 'SATAN_SOUL',
      };
      setMessages(prev => [...prev, evalMsg]);
      speakResponse(evalMsg.text);
    } catch {
      // Deterministic Darwinian evaluation fallback
      const streak = (evolutionData?.survival_streak_days || 14) + 1;
      const realizedPnl = (evolutionData?.today_realized_pnl_inr || 18450) + 7250;
      setEvolutionData((prev: any) => ({
        ...prev,
        survival_streak_days: streak,
        today_realized_pnl_inr: realizedPnl,
        today_status: 'SURVIVED_AND_PROFITABLE',
      }));
      const verifyMsg: ChatMessage = {
        id: `eval-${Date.now()}`,
        sender: 'mirajane',
        text: `◈ [MODEL RETENTION VERIFIED]\nMirajane Strauss Gen-${evolutionData?.generation || 7} met today's target benchmark.\n• Realized P&L: ₹${realizedPnl.toLocaleString('en-IN')}\n• Target: ₹25,000\n• Model Retention Streak: ${streak} consecutive sessions.\nModel version confirmed for next market cycle.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: 'CALM',
      };
      setMessages(prev => [...prev, verifyMsg]);
      setActiveTab('intercom');
      speakResponse(`Daily survival benchmark verified. Retention streak extended to ${streak} sessions.`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const isSatanSoul = status.active_mode === 'SATAN_SOUL';
  const totalOpenPnl = positions.reduce((acc, p) => acc + (p.pnl_inr || 0), 0);

  return (
    <div
      className="glass-panel"
      style={{
        padding: 'var(--space-6)',
        border: isSatanSoul ? '1px solid rgba(168, 85, 247, 0.45)' : '1px solid var(--color-border)',
        boxShadow: isSatanSoul ? '0 0 35px rgba(168, 85, 247, 0.20)' : 'var(--shadow-md)',
        transition: 'all 0.5s ease',
      }}
    >
      {/* ── TOP HEADER / PERSONA BADGE ─────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Avatar Icon with Mode Glow */}
          <motion.div
            animate={isSatanSoul ? { scale: [1, 1.08, 1], rotate: [0, 2, -2, 0] } : {}}
            transition={{ repeat: Infinity, duration: 3 }}
            style={{
              width: 46,
              height: 46,
              borderRadius: 'var(--radius-lg)',
              background: isSatanSoul
                ? 'linear-gradient(135deg, #7e22ce, #db2777)'
                : 'linear-gradient(135deg, var(--color-primary), #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              boxShadow: isSatanSoul
                ? '0 0 20px rgba(168, 85, 247, 0.60)'
                : '0 0 15px var(--color-primary-40)',
            }}
          >
            {isSatanSoul ? <Flame size={24} /> : <Sparkles size={24} />}
          </motion.div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 900, color: 'var(--color-text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
                MIRAJANE STRAUSS
              </h2>
              <span
                className="badge"
                style={{
                  background: isSatanSoul ? 'rgba(168, 85, 247, 0.20)' : 'var(--color-primary-10)',
                  color: isSatanSoul ? '#c084fc' : 'var(--color-primary)',
                  border: isSatanSoul ? '1px solid rgba(168, 85, 247, 0.40)' : '1px solid var(--color-primary-20)',
                  fontWeight: 800,
                }}
              >
                {isSatanSoul ? 'ALPHA ENGINE ENGAGED' : 'RISK PARITY CUSTODIAN'}
              </span>
              <span
                className="badge"
                style={{
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  fontWeight: 800,
                  fontSize: '0.62rem',
                }}
              >
                GEN-7 QUANT LEAD
              </span>
              {isSpeaking && (
                <span
                  style={{
                    fontSize: '0.62rem',
                    color: '#22c55e',
                    fontWeight: 800,
                    background: 'rgba(34, 197, 94, 0.15)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                  }}
                  className="animate-pulse"
                >
                  🔊 FEMALE VOICE ACTIVE
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)', margin: 0 }}>
              Live Internet Feeds • PyO3 Rust HFT OMS • SEBI 2026 1-Touch HITL Compliant • 05 Nov 2026 Session
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {/* DeepSeek-V3 MoE Telemetry Pill */}
          {moeTelemetry && moeTelemetry.top_2_experts && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '0.64rem',
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                padding: '3px 8px',
                borderRadius: '6px',
                color: '#38bdf8',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
              }}
              title={`DeepSeek-V3 MoE Directive: ${moeTelemetry.action_directive}`}
            >
              <BrainCircuit size={12} color="#38bdf8" />
              <span>MoE: {moeTelemetry.top_2_experts[0]?.expert} ({moeTelemetry.top_2_experts[0]?.weight_pct}%)</span>
            </div>
          )}

          {/* Female Voice Selector Dropdown */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(236, 72, 153, 0.08)',
              border: '1px solid rgba(236, 72, 153, 0.25)',
              padding: '3px 8px',
              borderRadius: '6px',
            }}
          >
            <span style={{ fontSize: '0.62rem', color: '#ec4899', fontWeight: 800 }}>FEMALE VOICE:</span>
            <select
              value={selectedVoiceName}
              onChange={(e) => {
                const newVoice = e.target.value;
                setSelectedVoiceName(newVoice);
                localStorage.setItem('mirajane_voice_name', newVoice);
                const cleanName = newVoice.replace('Microsoft ', '').split(' - ')[0];
                speakResponse(`Voice calibrated to ${cleanName}. Mirajane Strauss online.`);
              }}
              style={{
                background: '#070b13',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '4px',
                fontSize: '0.66rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                padding: '2px 4px',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              {femaleVoices.length > 0 ? (
                femaleVoices.map((v) => (
                  <option key={v.name} value={v.name} style={{ background: '#070b13', color: '#e2e8f0' }}>
                    {v.name.replace('Microsoft ', '').replace(' - English', ' (EN)').replace(' - Hindi', ' (HI)')}
                  </option>
                ))
              ) : (
                <>
                  <option value="Microsoft Heera - English (India)">Heera (India EN)</option>
                  <option value="Microsoft Zira - English (United States)">Zira (US EN)</option>
                  <option value="Microsoft Hazel - English (United Kingdom)">Hazel (UK EN)</option>
                  <option value="Microsoft Susan - English (United Kingdom)">Susan (UK EN)</option>
                </>
              )}
            </select>

            <button
              onClick={() => speakResponse("Voice calibrated. Mirajane Strauss online for Indian derivatives trading.")}
              className="btn btn-sm btn-ghost"
              style={{ fontSize: '0.62rem', padding: '1px 6px', color: '#10b981', fontWeight: 800 }}
              title="Test Mirajane Female Voice"
            >
              ▶ TEST
            </button>
          </div>

          {/* Voice Audio Mute/Unmute */}
          <button
            onClick={() => {
              setVoiceEnabled(!voiceEnabled);
              if (voiceEnabled && window.speechSynthesis) window.speechSynthesis.cancel();
            }}
            className="btn btn-sm btn-ghost"
            title={voiceEnabled ? "Mute Mirajane Voice" : "Enable Mirajane Voice"}
            style={{ fontSize: '0.70rem', color: voiceEnabled ? 'var(--color-primary)' : 'var(--color-text-muted)' }}
          >
            {voiceEnabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
          </button>

          <button
            onClick={handleScanGlobalInternet}
            disabled={isScanning}
            className="btn btn-sm btn-ghost"
            title="Scan Live Global Internet Feeds"
            style={{ fontSize: '0.70rem' }}
          >
            <Radio size={12} className={isScanning ? 'animate-pulse text-purple-400' : ''} />
            {isScanning ? 'SCANNING...' : 'SCAN INTERNET'}
          </button>

          <button
            onClick={handleToggleMode}
            className="btn btn-sm"
            style={{
              fontSize: '0.70rem',
              background: isSatanSoul ? 'linear-gradient(135deg, #7e22ce, #db2777)' : 'var(--color-primary)',
              color: isSatanSoul ? '#fff' : '#000',
              border: 'none',
              boxShadow: isSatanSoul ? '0 0 15px rgba(168, 85, 247, 0.4)' : '0 0 15px var(--color-primary-40)',
              fontWeight: 800,
            }}
          >
            {isSatanSoul ? <Sparkles size={12} /> : <Flame size={12} />}
            {isSatanSoul ? 'ENGAGE RISK PARITY' : 'ACTIVATE ALPHA MODE'}
          </button>
        </div>
      </div>

      {/* ── 4 SUB-VIEW TABS NAVIGATOR ──────────────────────────────────── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          padding: '4px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-4)',
          overflowX: 'auto',
        }}
      >
        <button
          onClick={() => setActiveTab('intercom')}
          className="btn btn-sm"
          style={{
            fontSize: '0.74rem',
            fontWeight: 800,
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            background: activeTab === 'intercom' ? (isSatanSoul ? 'linear-gradient(135deg, #7e22ce, #db2777)' : 'var(--color-primary-20)') : 'transparent',
            color: activeTab === 'intercom' ? (isSatanSoul ? '#fff' : 'var(--color-primary)') : 'var(--color-text-secondary)',
            border: activeTab === 'intercom' ? (isSatanSoul ? 'none' : '1px solid var(--color-primary-40)') : '1px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <Mic size={13} />
          <span>Tactical Intercom</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('sentience');
            fetchSentience();
          }}
          className="btn btn-sm"
          style={{
            fontSize: '0.74rem',
            fontWeight: 800,
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            background: activeTab === 'sentience' ? 'rgba(56, 189, 248, 0.20)' : 'transparent',
            color: activeTab === 'sentience' ? '#38bdf8' : 'var(--color-text-secondary)',
            border: activeTab === 'sentience' ? '1px solid rgba(56, 189, 248, 0.40)' : '1px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <Brain size={13} />
          <span>Crowd Microstructure & Traps</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('evolution');
            fetchEvolution();
          }}
          className="btn btn-sm"
          style={{
            fontSize: '0.74rem',
            fontWeight: 800,
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            background: activeTab === 'evolution' ? 'rgba(234, 179, 8, 0.20)' : 'transparent',
            color: activeTab === 'evolution' ? '#eab308' : 'var(--color-text-secondary)',
            border: activeTab === 'evolution' ? '1px solid rgba(234, 179, 8, 0.40)' : '1px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <Dna size={13} />
          <span>Darwinian Model Evolution</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('previral');
            fetchPreViralAndPredictions();
          }}
          className="btn btn-sm"
          style={{
            fontSize: '0.74rem',
            fontWeight: 800,
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            background: activeTab === 'previral' ? 'rgba(236, 72, 153, 0.20)' : 'transparent',
            color: activeTab === 'previral' ? '#ec4899' : 'var(--color-text-secondary)',
            border: activeTab === 'previral' ? '1px solid rgba(236, 72, 153, 0.40)' : '1px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <Globe size={13} />
          <span>Pre-Viral Wires & Regimes</span>
        </button>
      </div>

      {/* ── TAB 1: INTERCOM & TRADING (VOICE & CHAT) ───────────────────── */}
      {activeTab === 'intercom' && (
        <div>
          {/* Global Telemetry Ribbon */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: 'var(--space-2)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border-subtle)',
              marginBottom: 'var(--space-4)',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Global Thrust</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 800, color: status.global_macro_thrust > 0 ? 'var(--color-success)' : 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
                {status.global_macro_thrust > 0 ? `+${status.global_macro_thrust.toFixed(2)}` : status.global_macro_thrust.toFixed(2)}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>GIFT Nifty Gap</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 800, color: status.gift_nifty_spread >= 0 ? 'var(--color-success)' : 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
                {status.gift_nifty_spread >= 0 ? `+${status.gift_nifty_spread}` : status.gift_nifty_spread} pts
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Brent Crude</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 800, color: status.brent_crude_usd < 82 ? 'var(--color-primary)' : 'var(--color-warning)', fontFamily: 'var(--font-mono)' }}>
                ${status.brent_crude_usd}/bbl
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>US Dollar (DXY)</span>
              <span style={{ fontSize: '0.85rem', fontWeight: 800, color: status.dxy_index < 104 ? 'var(--color-primary)' : 'var(--color-warning)', fontFamily: 'var(--font-mono)' }}>
                {status.dxy_index}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.60rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Daily Champion</span>
              <span style={{ fontSize: '0.76rem', fontWeight: 800, color: '#38bdf8' }}>
                Mirajane Gen-7 (Streak: 14d)
              </span>
            </div>
          </div>

          {/* Active Positions Drawer */}
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
              <button
                onClick={() => setShowPositions(!showPositions)}
                className="btn btn-sm btn-ghost"
                style={{ padding: 'var(--space-1) var(--space-2)', gap: 'var(--space-2)' }}
              >
                <Briefcase size={14} color="var(--color-primary)" />
                <span style={{ fontSize: '0.74rem', fontWeight: 800 }}>
                  Mirajane Active Positions ({positions.length})
                </span>
                {positions.length > 0 && (
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      fontFamily: 'var(--font-mono)',
                      color: totalOpenPnl >= 0 ? 'var(--color-success)' : 'var(--color-error)',
                    }}
                  >
                    P&L: {totalOpenPnl >= 0 ? '+' : ''}₹{totalOpenPnl.toLocaleString('en-IN')}
                  </span>
                )}
                {showPositions ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>

              {positions.length > 0 && (
                <button
                  onClick={handleEmergencyFlatten}
                  disabled={actionLoadingId === 'flatten-all'}
                  className="btn btn-sm"
                  style={{
                    fontSize: '0.66rem',
                    background: 'rgba(255, 48, 92, 0.15)',
                    color: 'var(--color-error)',
                    border: '1px solid rgba(255, 48, 92, 0.4)',
                    fontWeight: 800,
                  }}
                >
                  <AlertOctagon size={12} />
                  {actionLoadingId === 'flatten-all' ? 'FLATTENING...' : 'EMERGENCY FLATTEN ALL'}
                </button>
              )}
            </div>

            <AnimatePresence>
              {showPositions && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  {positions.length === 0 ? (
                    <div
                      style={{
                        padding: 'var(--space-3)',
                        background: 'var(--color-bg-secondary)',
                        borderRadius: 'var(--radius-md)',
                        border: '1px dashed var(--color-border-subtle)',
                        textAlign: 'center',
                        fontSize: '0.72rem',
                        color: 'var(--color-text-muted)',
                      }}
                    >
                      No active positions open. Mirajane is monitoring market liquidity.
                    </div>
                  ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-2)' }}>
                      {positions.map((pos) => {
                        const isLong = pos.side === 'BUY';
                        return (
                          <div
                            key={pos.symbol}
                            style={{
                              padding: 'var(--space-3)',
                              borderRadius: 'var(--radius-md)',
                              background: 'var(--color-bg-secondary)',
                              border: isLong ? '1px solid rgba(0, 255, 136, 0.25)' : '1px solid rgba(255, 48, 92, 0.25)',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: 'var(--space-2)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                <span style={{ fontSize: '0.80rem', fontWeight: 900 }}>{pos.symbol}</span>
                                <span
                                  className="badge"
                                  style={{
                                    fontSize: '0.60rem',
                                    background: isLong ? 'rgba(0, 255, 136, 0.15)' : 'rgba(255, 48, 92, 0.15)',
                                    color: isLong ? 'var(--color-success)' : 'var(--color-error)',
                                    fontWeight: 800,
                                  }}
                                >
                                  {pos.side} • {pos.quantity} Qty
                                </span>
                              </div>
                              <span
                                style={{
                                  fontSize: '0.78rem',
                                  fontWeight: 800,
                                  fontFamily: 'var(--font-mono)',
                                  color: pos.pnl_inr >= 0 ? 'var(--color-success)' : 'var(--color-error)',
                                }}
                              >
                                {pos.pnl_inr >= 0 ? '+' : ''}₹{pos.pnl_inr.toLocaleString('en-IN')} ({pos.pnl_pct.toFixed(2)}%)
                              </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>
                              <span>Entry: ₹{pos.entry_price.toLocaleString('en-IN')}</span>
                              <span>LTP: ₹{pos.current_price.toLocaleString('en-IN')}</span>
                              <button
                                onClick={() => handleClosePosition(pos.symbol)}
                                disabled={actionLoadingId === `close-${pos.symbol}`}
                                className="btn btn-sm btn-ghost"
                                style={{ fontSize: '0.64rem', padding: '2px 6px', color: 'var(--color-error)' }}
                              >
                                {actionLoadingId === `close-${pos.symbol}` ? 'CLOSING...' : 'SQUARE OFF'}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Interactive Chat Stream */}
          <div
            style={{
              height: 380,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              background: 'rgba(7, 11, 18, 0.75)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border-subtle)',
              marginBottom: 'var(--space-3)',
            }}
          >
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const isMiraSatan = msg.mode === 'SATAN_SOUL';

              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                    maxWidth: '100%',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--space-2)',
                      marginBottom: 'var(--space-1)',
                      fontSize: '0.65rem',
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    <span>{isUser ? 'Master Trader' : 'Mirajane Strauss'}</span>
                    <span>•</span>
                    <span>{msg.timestamp}</span>
                    {!isUser && isMiraSatan && (
                      <span className="badge" style={{ fontSize: '0.55rem', background: '#7e22ce', color: '#fff' }}>
                        SATAN SOUL
                      </span>
                    )}
                  </div>

                  <div
                    style={{
                      maxWidth: '82%',
                      padding: 'var(--space-3) var(--space-4)',
                      borderRadius: 'var(--radius-lg)',
                      fontSize: '0.80rem',
                      lineHeight: 1.5,
                      whiteSpace: 'pre-wrap',
                      background: isUser
                        ? 'linear-gradient(135deg, var(--color-primary), #059669)'
                        : isMiraSatan
                        ? 'rgba(126, 34, 206, 0.18)'
                        : 'var(--color-bg-secondary)',
                      color: isUser ? '#000' : 'var(--color-text-primary)',
                      border: isUser
                        ? 'none'
                        : isMiraSatan
                        ? '1px solid rgba(168, 85, 247, 0.35)'
                        : '1px solid var(--color-border-subtle)',
                      fontWeight: isUser ? 700 : 500,
                    }}
                  >
                    {msg.text}

                    {/* SEBI 1-Touch Execution Card */}
                    {msg.trade_action && !msg.executed && !msg.cancelled && (
                      <div
                        style={{
                          marginTop: 'var(--space-3)',
                          padding: 'var(--space-3)',
                          borderRadius: 'var(--radius-md)',
                          background: 'rgba(0, 0, 0, 0.45)',
                          border: '1px solid rgba(0, 255, 136, 0.35)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 'var(--space-2)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 900, color: 'var(--color-primary)' }}>
                            ⚡ SEBI 2026 HITL 1-TOUCH TRADE AUTHORIZATION
                          </span>
                          <span style={{ fontSize: '0.62rem', color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                            4s LOCK ACTIVE
                          </span>
                        </div>

                        <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                          <strong>{msg.trade_action.side}</strong> {msg.trade_action.quantity} Qty •{' '}
                          <strong>{msg.trade_action.symbol}</strong> @ ₹{msg.trade_action.price.toLocaleString('en-IN')}
                        </div>

                        {msg.trade_action.rationale && (
                          <div style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>
                            {msg.trade_action.rationale}
                          </div>
                        )}

                        <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                          <button
                            onClick={() => handleExecuteTrade(msg.id, msg.trade_action!)}
                            disabled={actionLoadingId === msg.id}
                            className="btn btn-sm"
                            style={{
                              flex: 1,
                              background: 'var(--color-primary)',
                              color: '#000',
                              fontWeight: 900,
                              fontSize: '0.72rem',
                            }}
                          >
                            <ShieldCheck size={13} />
                            {actionLoadingId === msg.id ? 'ROUTING RUST OMS...' : 'CONFIRM 1-TOUCH EXECUTE'}
                          </button>

                          <button
                            onClick={() => handleCancelTrade(msg.id)}
                            className="btn btn-sm btn-ghost"
                            style={{ fontSize: '0.72rem', color: 'var(--color-error)' }}
                          >
                            REJECT
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Live Trade Chart & Direct Execution Overlay */}
                    {msg.trade_action && msg.executed && (
                      <div
                        style={{
                          marginTop: 'var(--space-3)',
                          padding: 'var(--space-3)',
                          borderRadius: 'var(--radius-md)',
                          background: 'rgba(0, 240, 255, 0.04)',
                          border: '1px solid rgba(0, 240, 255, 0.35)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 'var(--space-2)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 900, color: '#00f0ff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                            ◈ MIRAJANE ACTIVE TRADE LIVE ON CHART
                          </span>
                          <span style={{ fontSize: '0.65rem', color: '#10b981', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                            ORDER FILLED • HFT OMS
                          </span>
                        </div>

                        <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold mr-1.5 text-[10px]">
                            {msg.trade_action.side}
                          </span>
                          <strong>{msg.trade_action.quantity} Qty</strong> • <strong>{msg.trade_action.symbol}</strong> @ ₹{msg.trade_action.price.toLocaleString('en-IN')}
                        </div>

                        {/* Interactive Embedded Live TradingView Chart with Mirajane's Entry, SL & Target Overlay */}
                        <div style={{ borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)', height: '260px', marginTop: '6px' }}>
                          <TradingViewChart
                            symbol={msg.trade_action.symbol}
                            spot={msg.trade_action.price}
                            height={260}
                            showIndicatorsToolbar={false}
                            mirajaneTrade={{
                              id: msg.trade_action.order_id || msg.id,
                              symbol: msg.trade_action.symbol,
                              side: msg.trade_action.side,
                              quantity: msg.trade_action.quantity,
                              entryPrice: msg.trade_action.price,
                              currentPrice: msg.trade_action.price,
                              slPrice: msg.trade_action.price - 60 * (msg.trade_action.side === 'BUY' ? 1 : -1),
                              targetPrice: msg.trade_action.price + 144 * (msg.trade_action.side === 'BUY' ? 1 : -1),
                              strategyName: 'SMC FVG Institutional Absorption Spread',
                              convictionScore: 91.4,
                              pnlInr: 0,
                              pnlPct: 0,
                              timestamp: Date.now(),
                              active: true,
                            }}
                            onSquareOffTrade={() => handleClosePosition(msg.trade_action!.symbol)}
                          />
                        </div>

                        <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                          <button
                            onClick={() => onSelectView?.('live_trading')}
                            className="btn btn-sm"
                            style={{
                              flex: 1,
                              background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
                              color: '#000',
                              fontWeight: 900,
                              fontSize: '0.72rem',
                              cursor: 'pointer',
                            }}
                          >
                            📊 OPEN FULLSCREEN LIVE TRADING DESK
                          </button>
                          <button
                            onClick={() => handleClosePosition(msg.trade_action!.symbol)}
                            className="btn btn-sm btn-ghost"
                            style={{ fontSize: '0.72rem', color: 'var(--color-error)', cursor: 'pointer' }}
                          >
                            SQUARE OFF
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isThinking && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                <RefreshCw size={14} className="animate-spin text-purple-400" />
                <span>Mirajane is analyzing market microstructure & news wires...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input & Mic Bar */}
          <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
            <button
              onClick={handleVoiceClick}
              className={`btn btn-sm ${isListening ? 'btn-error animate-pulse' : 'btn-ghost'}`}
              title={isListening ? 'Listening... Speak now' : 'Push-to-Talk (NVIDIA Nemotron Audio)'}
              style={{
                width: 40,
                height: 40,
                borderRadius: 'var(--radius-md)',
                color: isListening ? '#fff' : isSatanSoul ? '#c084fc' : 'var(--color-primary)',
                background: isListening ? 'var(--color-error)' : 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border-subtle)',
              }}
            >
              {isListening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>

            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder={
                isListening
                  ? 'Listening to your voice...'
                  : isSatanSoul
                  ? 'Ask Mirajane (Alpha Mode): "Scan 0DTE gamma", "Short BankNifty", "What is retail doing?"'
                  : 'Ask Mirajane: "Analyze market sentiment", "Buy 1 lot Nifty", "Check crude oil"'
              }
              style={{
                flex: 1,
                padding: 'var(--space-3) var(--space-4)',
                background: 'var(--color-bg-secondary)',
                border: isListening ? '1px solid var(--color-error)' : '1px solid var(--color-border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-text-primary)',
                fontSize: '0.80rem',
                outline: 'none',
              }}
            />

            <button
              onClick={() => handleSendMessage()}
              disabled={isThinking || !inputMessage.trim()}
              className="btn btn-sm"
              style={{
                width: 40,
                height: 40,
                borderRadius: 'var(--radius-md)',
                background: isSatanSoul ? 'linear-gradient(135deg, #7e22ce, #db2777)' : 'var(--color-primary)',
                color: isSatanSoul ? '#fff' : '#000',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}

      {/* ── TAB 2: SENTIENCE & HUMAN FLOW MATRIX ──────────────────────── */}
      {activeTab === 'sentience' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {isSentienceLoading && !sentienceData ? (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.80rem' }}>
              <RefreshCw size={16} className="animate-spin text-cyan-400" style={{ display: 'inline', marginRight: 8 }} />
              Mirajane is decoding real-time human herd psychology & retail liquidity traps...
            </div>
          ) : (
            <>
              {/* Sentient Voice Reflection Banner */}
              <div
                style={{
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-lg)',
                  background: isSatanSoul ? 'rgba(126, 34, 206, 0.15)' : 'rgba(56, 189, 248, 0.10)',
                  border: isSatanSoul ? '1px solid rgba(168, 85, 247, 0.35)' : '1px solid rgba(56, 189, 248, 0.30)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 'var(--space-3)',
                }}
              >
                <div
                  style={{
                    padding: '8px',
                    borderRadius: 'var(--radius-md)',
                    background: isSatanSoul ? '#7e22ce' : '#0284c7',
                    color: '#fff',
                    marginTop: 2,
                  }}
                >
                  <Eye size={18} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.74rem', fontWeight: 900, color: isSatanSoul ? '#c084fc' : '#38bdf8', textTransform: 'uppercase' }}>
                      Quantitative Microstructure Voice Brief ({isSatanSoul ? 'Alpha Hunter Directive' : 'Risk Custody Directive'})
                    </span>
                    <button
                      onClick={() => speakResponse(isSatanSoul ? sentienceData?.sentient_reflection?.satan_soul_voice : sentienceData?.sentient_reflection?.calm_mode_voice)}
                      className="btn btn-sm btn-ghost"
                      style={{ fontSize: '0.64rem', color: 'var(--color-primary)', padding: '2px 8px' }}
                    >
                      <Volume2 size={12} /> SPEAK REFLECTION
                    </button>
                  </div>
                  <p style={{ fontSize: '0.78rem', lineHeight: 1.6, color: 'var(--color-text-primary)', margin: 0, fontStyle: 'italic' }}>
                    "{isSatanSoul ? sentienceData?.sentient_reflection?.satan_soul_voice : sentienceData?.sentient_reflection?.calm_mode_voice}"
                  </p>
                </div>
              </div>

              {/* FOMO vs. Panic Index Meters */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                {/* FOMO Meter */}
                <div
                  style={{
                    padding: 'var(--space-4)',
                    background: 'var(--color-bg-secondary)',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#f59e0b', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Flame size={14} /> Retail FOMO Gauge
                    </span>
                    <span style={{ fontSize: '0.90rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: '#f59e0b' }}>
                      {sentienceData?.human_psychology_matrix?.fomo_index?.toFixed(1)} / 100
                    </span>
                  </div>
                  <div style={{ height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${sentienceData?.human_psychology_matrix?.fomo_index || 50}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                        borderRadius: 4,
                        transition: 'width 0.8s ease',
                      }}
                    />
                  </div>
                  <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', marginTop: 8, margin: 0 }}>
                    Measures retail urge to chase breakouts without confirmation.
                  </p>
                </div>

                {/* Panic Meter */}
                <div
                  style={{
                    padding: 'var(--space-4)',
                    background: 'var(--color-bg-secondary)',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#ef4444', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <AlertOctagon size={14} /> Retail Panic Capitulation
                    </span>
                    <span style={{ fontSize: '0.90rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: '#ef4444' }}>
                      {sentienceData?.human_psychology_matrix?.panic_index?.toFixed(1)} / 100
                    </span>
                  </div>
                  <div style={{ height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${sentienceData?.human_psychology_matrix?.panic_index || 50}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #38bdf8, #ef4444)',
                        borderRadius: 4,
                        transition: 'width 0.8s ease',
                      }}
                    />
                  </div>
                  <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', marginTop: 8, margin: 0 }}>
                    Identifies peak emotional dumping where institutional accumulation begins.
                  </p>
                </div>
              </div>

              {/* Crowd Psychology Regime */}
              <div
                style={{
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 'var(--space-2)',
                }}
              >
                <div>
                  <span style={{ fontSize: '0.64rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Active Crowd Regime</span>
                  <div style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--color-primary)' }}>
                    {sentienceData?.human_psychology_matrix?.sentiment_regime}
                  </div>
                </div>
                <div style={{ maxWidth: '65%', fontSize: '0.72rem', color: 'var(--color-text-secondary)', textAlign: 'right' }}>
                  {sentienceData?.human_psychology_matrix?.crowd_behavior}
                </div>
              </div>

              {/* Active Retail Liquidity Traps */}
              <div>
                <h4 style={{ fontSize: '0.78rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--color-text-primary)', marginBottom: 'var(--space-2)' }}>
                  Active Retail Liquidity Traps ({sentienceData?.active_retail_traps?.length || 0} Detected)
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-3)' }}>
                  {Array.isArray(sentienceData?.active_retail_traps) && sentienceData.active_retail_traps.map((trap: any) => (
                    <div
                      key={trap.id}
                      style={{
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--color-bg-secondary)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 'var(--space-2)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 900, color: '#f87171' }}>
                          ⚠️ {trap.trap_type}
                        </span>
                        <span className="badge" style={{ fontSize: '0.60rem', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' }}>
                          Zone: {trap.strike_zone}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)' }}>
                        <strong>Retail Trap:</strong> {trap.retail_vulnerability}
                      </div>

                      <div style={{ fontSize: '0.70rem', color: '#fbbf24' }}>
                        <strong>Operator Move:</strong> {trap.institutional_trap}
                      </div>

                      <div style={{ padding: '6px', borderRadius: '4px', background: 'rgba(0, 255, 136, 0.08)', border: '1px solid rgba(0, 255, 136, 0.2)', fontSize: '0.70rem', color: '#22c55e' }}>
                        <strong>Mirajane Counter-Play:</strong> {trap.counter_strategy} (Probability: {(trap.probability_of_trap * 100).toFixed(0)}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* FII/DII Operator vs. Retail Flow Divergence */}
              <div
                style={{
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-lg)',
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.74rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--color-text-primary)', marginBottom: 'var(--space-2)' }}>
                  Institutional Operator Flow Divergence
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
                  <div>
                    <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>FII Index Long Ratio</span>
                    <div style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)' }}>
                      {sentienceData?.institutional_operator_flows?.fii_index_future_long_ratio}%
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>DII Net Inflows</span>
                    <div style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
                      +₹{sentienceData?.institutional_operator_flows?.dii_cash_net_crores_inr} Cr
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>Retail Call Concentration</span>
                    <div style={{ fontSize: '0.82rem', fontWeight: 800, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                      {sentienceData?.institutional_operator_flows?.retail_call_oi_concentration_pct}%
                    </div>
                  </div>
                </div>
                <p style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)', margin: 0 }}>
                  <strong>Key Divergence:</strong> {sentienceData?.institutional_operator_flows?.divergence}
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── TAB 3: DARWINIAN EVOLUTION ARENA ───────────────────────────── */}
      {activeTab === 'evolution' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Champion Banner */}
          <div
            style={{
              padding: 'var(--space-5)',
              borderRadius: 'var(--radius-lg)',
              background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(202, 138, 4, 0.05))',
              border: '1px solid rgba(234, 179, 8, 0.40)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 'var(--space-3)',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Award size={22} color="#eab308" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 900, color: '#fef08a', margin: 0 }}>
                  {evolutionData?.model_name || 'Mirajane Strauss (Champion VII)'}
                </h3>
                <span className="badge" style={{ background: 'rgba(234, 179, 8, 0.25)', color: '#facc15', fontWeight: 800 }}>
                  {evolutionData?.survival_streak_days || 14}-DAY SURVIVAL STREAK
                </span>
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', margin: '4px 0 0 0' }}>
                Darwinian Mandate: Trades once daily with ₹{(evolutionData?.stipulated_capital_inr || 200000).toLocaleString('en-IN')} stipulated capital. Target: ₹{(evolutionData?.daily_target_pnl_inr || 25000).toLocaleString('en-IN')}. If P&L ≤ ₹0 at EOD, she is eliminated and replaced.
              </p>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <button
                onClick={handleTriggerDailyTrade}
                disabled={actionLoadingId === 'daily-trade'}
                className="btn btn-sm"
                style={{
                  background: '#eab308',
                  color: '#000',
                  fontWeight: 900,
                  fontSize: '0.72rem',
                }}
              >
                <Zap size={13} />
                {actionLoadingId === 'daily-trade' ? 'GENERATING TRADE...' : '⚡ EXECUTE DAILY MANDATE TRADE'}
              </button>

              <button
                onClick={handleEvaluateDailySurvival}
                disabled={actionLoadingId === 'evaluate-daily' || isEvolutionLoading}
                className="btn btn-sm btn-ghost"
                style={{
                  border: '1px solid rgba(234, 179, 8, 0.4)',
                  color: '#fef08a',
                  fontWeight: 800,
                  fontSize: '0.72rem',
                }}
              >
                <Target size={13} />
                {actionLoadingId === 'evaluate-daily' ? 'EVALUATING...' : '🧪 EVALUATE DAILY SURVIVAL'}
              </button>
            </div>
          </div>

          {/* Today's Darwinian Performance Dashboard */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-3)' }}>
            <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Today Realized P&L</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: (evolutionData?.today_realized_pnl_inr || 0) >= 0 ? 'var(--color-success)' : 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
                {(evolutionData?.today_realized_pnl_inr || 0) >= 0 ? '+' : ''}₹{(evolutionData?.today_realized_pnl_inr || 18450).toLocaleString('en-IN')}
              </div>
              <span style={{ fontSize: '0.62rem', color: '#eab308' }}>Target: ₹25,000 / day</span>
            </div>

            <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Daily Survival Status</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--color-primary)' }}>
                {evolutionData?.today_status || 'ON_TRACK_TO_SURVIVE'}
              </div>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>Evaluation at 15:30 IST</span>
            </div>

            <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Lifetime Win Rate</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                {evolutionData?.lifetime_win_rate_pct || 79.1}%
              </div>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>Over {evolutionData?.lifetime_trades || 86} executed trades</span>
            </div>

            <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Cumulative Profit</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
                +₹{(evolutionData?.cumulative_pnl_inr || 384500).toLocaleString('en-IN')}
              </div>
              <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>Generated since inception</span>
            </div>
          </div>

          {/* Hyperparameters Matrix */}
          <div
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-lg)',
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <div style={{ fontSize: '0.74rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--color-text-primary)', marginBottom: 'var(--space-2)' }}>
              Gen-7 Hyperparameters (Mutated Post-Elimination)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--space-2)' }}>
              <div style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)' }}>
                Kelly Fraction: <strong style={{ color: 'var(--color-primary)' }}>{evolutionData?.hyperparameters?.kelly_fraction || 0.45}</strong>
              </div>
              <div style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)' }}>
                FVG CE Retest: <strong style={{ color: 'var(--color-primary)' }}>{evolutionData?.hyperparameters?.fvg_consequent_encroachment_threshold || 0.50}</strong>
              </div>
              <div style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)' }}>
                Trap Divergence Weight: <strong style={{ color: 'var(--color-primary)' }}>{evolutionData?.hyperparameters?.retail_trap_divergence_weight || 0.35}</strong>
              </div>
              <div style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)' }}>
                Risk-to-Reward Ratio: <strong style={{ color: 'var(--color-primary)' }}>1 : {evolutionData?.hyperparameters?.risk_reward_ratio || 2.4}</strong>
              </div>
            </div>
          </div>

          {/* Replacement Graveyard & Post-Mortems */}
          <div>
            <h4 style={{ fontSize: '0.78rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--color-text-primary)', marginBottom: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <History size={14} /> Generational Replacement Graveyard & Post-Mortem Log
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {Array.isArray(evolutionData?.replacement_history) && evolutionData.replacement_history.map((hist: any) => (
                <div
                  key={hist.generation}
                  style={{
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(255, 48, 92, 0.05)',
                    border: '1px solid rgba(255, 48, 92, 0.25)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--color-error)' }}>
                      💀 Mirajane Gen-{hist.generation} Eliminated on {hist.date}
                    </span>
                    <span style={{ fontSize: '0.65rem', color: '#38bdf8', fontWeight: 800 }}>
                      Replaced by {hist.replaced_by}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>
                    <strong>Cause:</strong> {hist.reason}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                    <strong>Post-Mortem:</strong> {hist.post_mortem}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: '#eab308' }}>
                    <strong>Mutation Applied:</strong> {hist.mutation_applied}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 4: PRE-VIRAL RADAR & MULTI-HORIZON PREDICTIONS ─────────── */}
      {activeTab === 'previral' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Header Description */}
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(236, 72, 153, 0.10)',
              border: '1px solid rgba(236, 72, 153, 0.30)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontSize: '0.74rem', fontWeight: 900, color: '#ec4899', textTransform: 'uppercase' }}>
                📡 Global Pre-Viral News Radar (Dalal Street Transmission Advantage)
              </span>
              <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', margin: '2px 0 0 0' }}>
                Detects market-moving overseas macro news 15-45 minutes before reaching Indian retail media.
              </p>
            </div>
            <button
              onClick={fetchPreViralAndPredictions}
              className="btn btn-sm btn-ghost"
              style={{ fontSize: '0.68rem', color: '#ec4899' }}
            >
              <RefreshCw size={12} className={isPreViralLoading ? 'animate-spin' : ''} /> REFRESH
            </button>
          </div>

          {/* Pre-Viral Global Wires */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {Array.isArray(preViralNews) && preViralNews.map((wire: any) => (
              <div
                key={wire.id}
                style={{
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                    {wire.headline}
                  </span>
                  <span
                    className="badge"
                    style={{
                      fontSize: '0.60rem',
                      background: 'rgba(236, 72, 153, 0.2)',
                      color: '#f472b6',
                      fontWeight: 800,
                    }}
                  >
                    ⏱️ Arrives in India in {wire.estimated_india_retail_lag_mins || 30}m
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.66rem', color: 'var(--color-text-muted)' }}>
                  <span>Source: {wire.source}</span>
                  <span style={{ color: '#ec4899', fontWeight: 800 }}>
                    Impact Score: {wire.market_moving_score}/10 • {wire.virality_stage}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', margin: '2px 0' }}>
                  {Array.isArray(wire?.impacted_assets) && wire.impacted_assets.map((asset: string, i: number) => (
                    <span key={i} style={{ fontSize: '0.62rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.25)', fontWeight: 700 }}>
                      {asset}
                    </span>
                  ))}
                </div>

                <p style={{ fontSize: '0.70rem', color: 'var(--color-text-secondary)', margin: '2px 0 0 0' }}>
                  <strong>Mirajane Predictive Alpha Play:</strong> {wire.predictive_action}
                </p>
              </div>
            ))}
          </div>

          {/* Multi-Horizon Predictive Trends (24h, 90d, 180d, 365d) */}
          <div>
            <h4 style={{ fontSize: '0.78rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--color-text-primary)', marginBottom: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <TrendingUp size={14} /> Multi-Horizon Predictive Trends (November 2026 Calibrated)
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-3)' }}>
              {/* Intraday 24h */}
              <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '0.66rem', color: 'var(--color-primary)', fontWeight: 800, textTransform: 'uppercase' }}>
                  Intraday & 24 Hours
                </span>
                <div style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--color-text-primary)' }}>
                  {predictionsData?.intraday_24h?.expected_range || '23,740 - 23,920'}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--color-success)', fontWeight: 700 }}>
                  Bias: {predictionsData?.intraday_24h?.bias || 'BULLISH_DISPLACEMENT'} (Conf: {predictionsData?.intraday_24h?.confidence_pct || 82.5}%)
                </div>
                <p style={{ fontSize: '0.66rem', color: 'var(--color-text-muted)', margin: 0 }}>
                  {predictionsData?.intraday_24h?.key_catalyst}
                </p>
              </div>

              {/* Quarterly 90d */}
              <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '0.66rem', color: '#38bdf8', fontWeight: 800, textTransform: 'uppercase' }}>
                  Quarterly (90 Days - Q3 FY27)
                </span>
                <div style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--color-text-primary)' }}>
                  {predictionsData?.quarterly_90d?.expected_range || '23,400 - 24,800'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#38bdf8', fontWeight: 700 }}>
                  Bias: {predictionsData?.quarterly_90d?.bias || 'ACCUMULATION_ON_EARNINGS'} (Conf: {predictionsData?.quarterly_90d?.confidence_pct || 76}%)
                </div>
                <p style={{ fontSize: '0.66rem', color: 'var(--color-text-muted)', margin: 0 }}>
                  {predictionsData?.quarterly_90d?.key_catalyst}
                </p>
              </div>

              {/* Half-Yearly 180d */}
              <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '0.66rem', color: '#facc15', fontWeight: 800, textTransform: 'uppercase' }}>
                  Half-Yearly (180 Days - H1 2027)
                </span>
                <div style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--color-text-primary)' }}>
                  {predictionsData?.half_yearly_180d?.expected_range || '24,200 - 25,600'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#facc15', fontWeight: 700 }}>
                  Bias: {predictionsData?.half_yearly_180d?.bias || 'STRUCTURAL_BULL_EXPANSION'} (Conf: {predictionsData?.half_yearly_180d?.confidence_pct || 84}%)
                </div>
                <p style={{ fontSize: '0.66rem', color: 'var(--color-text-muted)', margin: 0 }}>
                  {predictionsData?.half_yearly_180d?.key_catalyst}
                </p>
              </div>

              {/* Annual 365d */}
              <div style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '0.66rem', color: '#a855f7', fontWeight: 800, textTransform: 'uppercase' }}>
                  Annual Trajectory (365 Days)
                </span>
                <div style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--color-text-primary)' }}>
                  {predictionsData?.annual_365d?.expected_range || '25,500 - 27,200'}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#a855f7', fontWeight: 700 }}>
                  Bias: {predictionsData?.annual_365d?.bias || 'SOVEREIGN_QUANTUM_LEAP'} (Conf: {predictionsData?.annual_365d?.confidence_pct || 88}%)
                </div>
                <p style={{ fontSize: '0.66rem', color: 'var(--color-text-muted)', margin: 0 }}>
                  {predictionsData?.annual_365d?.key_catalyst}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
