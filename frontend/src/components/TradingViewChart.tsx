import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
  type SeriesMarker,
} from 'lightweight-charts';
import {
  Maximize2,
  Minimize2,
  RefreshCw,
  Activity,
  Layers,
  Zap,
} from 'lucide-react';

export interface ChartCandle {
  time: number | string; // unix timestamp in seconds or ISO/date string
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradingViewChartProps {
  symbol?: string;
  candles?: ChartCandle[];
  spot?: number;
  height?: number | string;
  showIndicatorsToolbar?: boolean;
  showSMCByDefault?: boolean;
  showVolumeByDefault?: boolean;
  showEMAsByDefault?: boolean;
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  className?: string;
}

// Convert arbitrary candle time to integer UTCTimestamp
function parseUTCTimestamp(t: number | string, index: number, total: number): UTCTimestamp {
  if (typeof t === 'number') {
    // If it's already in seconds
    if (t < 2000000000) return Math.floor(t) as UTCTimestamp;
    // If in milliseconds
    return Math.floor(t / 1000) as UTCTimestamp;
  }
  const parsed = Date.parse(t);
  if (!isNaN(parsed)) {
    return Math.floor(parsed / 1000) as UTCTimestamp;
  }
  // Fallback synthetic ascending timestamp spaced by 60 seconds
  const nowSec = Math.floor(Date.now() / 1000);
  return (nowSec - (total - index) * 60) as UTCTimestamp;
}

// Calculate EMA series
function computeEMA(data: { time: UTCTimestamp; value: number }[], period: number) {
  if (data.length === 0) return [];
  const k = 2 / (period + 1);
  const result: { time: UTCTimestamp; value: number }[] = [];
  let ema = data[0].value;
  result.push({ time: data[0].time, value: Number(ema.toFixed(2)) });

  for (let i = 1; i < data.length; i++) {
    ema = data[i].value * k + ema * (1 - k);
    result.push({ time: data[i].time, value: Number(ema.toFixed(2)) });
  }
  return result;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol = 'NIFTY 50',
  candles: externalCandles,
  spot = 23806.95,
  height = 420,
  showIndicatorsToolbar = true,
  showSMCByDefault = true,
  showVolumeByDefault = true,
  showEMAsByDefault = true,
  timeframe = '1m',
  onTimeframeChange,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const markersPluginRef = useRef<any>(null);

  // Indicators state
  const [showEMA, setShowEMA] = useState(showEMAsByDefault);
  const [showVolume, setShowVolume] = useState(showVolumeByDefault);
  const [showSMC, setShowSMC] = useState(showSMCByDefault);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Active crosshair / hovered candle for dynamic HUD
  const [activeLegend, setActiveLegend] = useState<{
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    change: number;
    changePct: number;
    timeStr: string;
  } | null>(null);

  // Sanitize and sort candles
  const formattedData = useMemo(() => {
    let raw = externalCandles;
    if (!raw || raw.length === 0) {
      // Procedural realistic fallbacks if no candles passed
      const list: ChartCandle[] = [];
      let cur = spot - 25;
      const count = 50;
      const now = Math.floor(Date.now() / 1000);
      for (let i = 0; i < count; i++) {
        const delta = Math.sin(i * 0.4) * 8 + Math.cos(i * 1.8) * 5;
        const o = cur;
        const c = cur + delta;
        const h = Math.max(o, c) + Math.abs(Math.cos(i)) * 4;
        const l = Math.min(o, c) - Math.abs(Math.sin(i)) * 4;
        const vol = Math.floor(25000 + Math.abs(Math.sin(i)) * 40000);
        list.push({
          time: now - (count - i) * 60,
          open: Number(o.toFixed(2)),
          high: Number(h.toFixed(2)),
          low: Number(l.toFixed(2)),
          close: Number(c.toFixed(2)),
          volume: vol,
        });
        cur = c;
      }
      raw = list;
    }

    // Convert into strictly ascending UTCTimestamps
    const total = raw.length;
    const mapped = raw.map((c, idx) => ({
      time: parseUTCTimestamp(c.time, idx, total),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.volume || 1000,
    }));

    // Ensure deduplicated and strictly ascending timestamps
    const sorted = mapped.sort((a, b) => (a.time as number) - (b.time as number));
    const deduped: typeof sorted = [];
    let lastTime = -1;
    for (const item of sorted) {
      let t = item.time as number;
      if (t <= lastTime) {
        t = lastTime + 60; // bump 60s
        item.time = t as UTCTimestamp;
      }
      lastTime = t;
      deduped.push(item);
    }
    return deduped;
  }, [externalCandles, spot]);

  // Compute SMC Markers (FVG & Order Blocks)
  const smcMarkers = useMemo(() => {
    if (!showSMC || formattedData.length < 3) return [];
    const markers: SeriesMarker<UTCTimestamp>[] = [];
    const n = formattedData.length;

    for (let i = 2; i < n; i++) {
      const c2 = formattedData[i - 2];
      const c0 = formattedData[i];

      // Bullish FVG (Imbalance: Low of current > High of 2 bars ago)
      if (c0.low > c2.high + 1.5) {
        markers.push({
          time: c0.time as UTCTimestamp,
          position: 'belowBar',
          color: '#10b981',
          shape: 'arrowUp',
          text: 'FVG-BULL',
        });
      }
      // Bearish FVG (Imbalance: High of current < Low of 2 bars ago)
      else if (c0.high < c2.low - 1.5) {
        markers.push({
          time: c0.time as UTCTimestamp,
          position: 'aboveBar',
          color: '#f43f5e',
          shape: 'arrowDown',
          text: 'FVG-BEAR',
        });
      }

      // Order Blocks (Aggressive breakout origin candle)
      if (i < n - 1) {
        const c1 = formattedData[i - 1];
        if (c1.close < c1.open && (c0.close - c0.open) > (c0.high - c0.low) * 0.7 && c0.volume > 50000) {
          markers.push({
            time: c1.time as UTCTimestamp,
            position: 'belowBar',
            color: '#38bdf8',
            shape: 'circle',
            text: 'OB',
          });
        }
      }
    }
    return markers;
  }, [formattedData, showSMC]);

  // Initialize Lightweight-Charts Engine
  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up previous instance
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const container = containerRef.current;
    const chart = createChart(container, {
      width: container.clientWidth || 800,
      height: typeof height === 'number' ? height : container.clientHeight || 420,
      layout: {
        background: { type: ColorType.Solid, color: '#07090e' },
        textColor: '#94a3b8',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: 'rgba(56, 189, 248, 0.45)',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#0f172a',
        },
        horzLine: {
          color: 'rgba(56, 189, 248, 0.45)',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#0f172a',
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.07)',
        scaleMargins: {
          top: 0.08,
          bottom: 0.22,
        },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.07)',
        timeVisible: true,
        secondsVisible: false,
        barSpacing: 8,
        minBarSpacing: 3,
      },
      handleScale: {
        axisPressedMouseMove: { time: true, price: true },
        mouseWheel: true,
        pinch: true,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
    });

    chartRef.current = chart;

    // 1. Candlestick Series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#f43f5e',
      borderVisible: true,
      borderColor: '#10b981',
      borderUpColor: '#10b981',
      borderDownColor: '#f43f5e',
      wickUpColor: '#10b981',
      wickDownColor: '#f43f5e',
    });
    candleSeriesRef.current = candleSeries;

    // 2. Volume Series (Histogram on overlay scale)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // 3. EMA 9 (Cyan)
    const ema9Series = chart.addSeries(LineSeries, {
      color: '#06b6d4',
      lineWidth: 2,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      lastValueVisible: false,
    });
    ema9SeriesRef.current = ema9Series;

    // 4. EMA 21 (Amber)
    const ema21Series = chart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 2,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      lastValueVisible: false,
    });
    ema21SeriesRef.current = ema21Series;

    // Subscribe to Crosshair Movement for HUD
    chart.subscribeCrosshairMove((param) => {
      if (
        param.point === undefined ||
        !param.time ||
        param.point.x < 0 ||
        param.point.x > container.clientWidth ||
        param.point.y < 0 ||
        param.point.y > container.clientHeight
      ) {
        // Fallback to latest candle
        if (formattedData.length > 0) {
          const last = formattedData[formattedData.length - 1];
          const prev = formattedData.length > 1 ? formattedData[formattedData.length - 2] : last;
          const diff = last.close - prev.close;
          const pct = prev.close > 0 ? (diff / prev.close) * 100 : 0;
          const d = new Date((last.time as number) * 1000);
          setActiveLegend({
            open: last.open,
            high: last.high,
            low: last.low,
            close: last.close,
            volume: last.volume,
            change: diff,
            changePct: pct,
            timeStr: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          });
        }
        return;
      }

      const candleData = param.seriesData.get(candleSeries) as any;
      if (candleData) {
        const diff = candleData.close - candleData.open;
        const pct = candleData.open > 0 ? (diff / candleData.open) * 100 : 0;
        const d = new Date((param.time as number) * 1000);
        const volData = param.seriesData.get(volumeSeries) as any;
        setActiveLegend({
          open: candleData.open,
          high: candleData.high,
          low: candleData.low,
          close: candleData.close,
          volume: volData ? volData.value : 0,
          change: diff,
          changePct: pct,
          timeStr: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
      }
    });

    // Resize Observer for auto-responsive container
    const resizeObserver = new ResizeObserver((entries) => {
      if (entries.length === 0 || !entries[0].contentRect) return;
      const { width, height: h } = entries[0].contentRect;
      if (width > 0 && h > 0) {
        chart.applyOptions({ width, height: h });
      }
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [height]);

  // Push Data into Series
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || formattedData.length === 0) return;

    // 1. Candlestick Data
    candleSeriesRef.current.setData(
      formattedData.map((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );

    // 2. Volume Data
    if (showVolume) {
      volumeSeriesRef.current.setData(
        formattedData.map((c) => ({
          time: c.time as UTCTimestamp,
          value: c.volume,
          color: c.close >= c.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(244, 63, 94, 0.35)',
        }))
      );
    } else {
      volumeSeriesRef.current.setData([]);
    }

    // 3. EMAs Data
    if (showEMA) {
      const closeValues = formattedData.map((c) => ({
        time: c.time as UTCTimestamp,
        value: c.close,
      }));
      const ema9Data = computeEMA(closeValues, 9);
      const ema21Data = computeEMA(closeValues, 21);

      if (ema9SeriesRef.current) ema9SeriesRef.current.setData(ema9Data);
      if (ema21SeriesRef.current) ema21SeriesRef.current.setData(ema21Data);
    } else {
      if (ema9SeriesRef.current) ema9SeriesRef.current.setData([]);
      if (ema21SeriesRef.current) ema21SeriesRef.current.setData([]);
    }

    // 4. SMC Markers
    if (markersPluginRef.current) {
      markersPluginRef.current.setMarkers(smcMarkers);
    } else if (candleSeriesRef.current) {
      try {
        markersPluginRef.current = createSeriesMarkers(candleSeriesRef.current, smcMarkers);
      } catch (err) {
        console.warn('SMC Markers initialization notice:', err);
      }
    }

    // Default HUD to latest bar
    const last = formattedData[formattedData.length - 1];
    const prev = formattedData.length > 1 ? formattedData[formattedData.length - 2] : last;
    const diff = last.close - prev.close;
    const pct = prev.close > 0 ? (diff / prev.close) * 100 : 0;
    const d = new Date((last.time as number) * 1000);
    setActiveLegend({
      open: last.open,
      high: last.high,
      low: last.low,
      close: last.close,
      volume: last.volume,
      change: diff,
      changePct: pct,
      timeStr: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });
  }, [formattedData, showVolume, showEMA, smcMarkers]);

  // Fit Content on Data Change or Mount
  const handleFitContent = useCallback(() => {
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, []);

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
  };

  const timeframes = ['1m', '3m', '5m', '15m', '1h', '1D'];

  return (
    <div
      className={`relative w-full flex flex-col bg-[#07090e] rounded-xl border border-white/[0.08] overflow-hidden select-none ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none border-none h-screen' : ''
      } ${className}`}
      style={{ height: isFullscreen ? '100vh' : typeof height === 'number' ? `${height}px` : height }}
    >
      {/* ── TOP INSTITUTIONAL HUD & TOOLBAR ── */}
      <div className="w-full px-3 py-2 bg-[#090d16] border-b border-white/[0.06] flex flex-wrap items-center justify-between gap-3 text-xs font-mono shrink-0">
        {/* Left: Symbol & Timeframe Switcher */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-slate-100 tracking-wider text-xs">
              {symbol}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-slate-300 font-semibold uppercase">
              Spot
            </span>
          </div>

          {/* Timeframe Badges */}
          <div className="flex items-center bg-black/40 rounded-lg p-0.5 border border-white/[0.05]">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange?.(tf)}
                className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer ${
                  timeframe === tf
                    ? 'bg-emerald-500 text-black shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Center: Dynamic OHLCV Legend Display */}
        {activeLegend && (
          <div className="hidden lg:flex items-center gap-3 text-[11px] text-slate-400">
            <span>
              O: <strong className="text-slate-200">{activeLegend.open.toFixed(2)}</strong>
            </span>
            <span>
              H: <strong className="text-emerald-400">{activeLegend.high.toFixed(2)}</strong>
            </span>
            <span>
              L: <strong className="text-rose-400">{activeLegend.low.toFixed(2)}</strong>
            </span>
            <span>
              C: <strong className={activeLegend.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{activeLegend.close.toFixed(2)}</strong>
            </span>
            <span className={activeLegend.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
              {activeLegend.change >= 0 ? '+' : ''}{activeLegend.change.toFixed(2)} ({activeLegend.changePct >= 0 ? '+' : ''}{activeLegend.changePct.toFixed(2)}%)
            </span>
            <span>
              Vol: <strong className="text-slate-200">{(activeLegend.volume / 1000).toFixed(1)}k</strong>
            </span>
          </div>
        )}

        {/* Right: Quant Overlays & Controls */}
        {showIndicatorsToolbar && (
          <div className="flex items-center gap-1.5">
            {/* EMA Toggle */}
            <button
              onClick={() => setShowEMA((v) => !v)}
              className={`px-2 py-1 rounded text-[10px] font-semibold flex items-center gap-1 transition-all cursor-pointer border ${
                showEMA
                  ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                  : 'bg-white/[0.03] text-slate-400 border-white/[0.06] hover:text-white'
              }`}
              title="Exponential Moving Averages (EMA 9 & 21)"
            >
              <Activity className="w-3 h-3 text-cyan-400" />
              EMA 9/21
            </button>

            {/* Volume Toggle */}
            <button
              onClick={() => setShowVolume((v) => !v)}
              className={`px-2 py-1 rounded text-[10px] font-semibold flex items-center gap-1 transition-all cursor-pointer border ${
                showVolume
                  ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                  : 'bg-white/[0.03] text-slate-400 border-white/[0.06] hover:text-white'
              }`}
              title="Sub-Pane Volume Histogram"
            >
              <Zap className="w-3 h-3 text-amber-400" />
              Vol
            </button>

            {/* SMC Toggle */}
            <button
              onClick={() => setShowSMC((v) => !v)}
              className={`px-2 py-1 rounded text-[10px] font-semibold flex items-center gap-1 transition-all cursor-pointer border ${
                showSMC
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                  : 'bg-white/[0.03] text-slate-400 border-white/[0.06] hover:text-white'
              }`}
              title="Smart Money Concepts (Fair Value Gaps & Order Blocks)"
            >
              <Layers className="w-3 h-3 text-emerald-400" />
              SMC Flow
            </button>

            {/* Reset / Fit Content */}
            <button
              onClick={handleFitContent}
              className="p-1 rounded bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] transition-all cursor-pointer border border-white/[0.06]"
              title="Fit Chart to Content"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>

            {/* Fullscreen Toggle */}
            <button
              onClick={toggleFullscreen}
              className="p-1 rounded bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] transition-all cursor-pointer border border-white/[0.06]"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Chart'}
            >
              {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}
      </div>

      {/* ── CANVAS MOUNT CONTAINER ── */}
      <div ref={containerRef} className="flex-1 w-full h-full relative" />

      {/* Subtle Bottom Watermark */}
      <div className="absolute bottom-2 left-3 pointer-events-none text-[9px] font-mono text-white/[0.12] flex items-center gap-2 select-none">
        <span>60 FPS HARDWARE ACCELERATED</span>
        <span>•</span>
        <span>TRADINGVIEW ENGINE</span>
      </div>
    </div>
  );
};
export default TradingViewChart;
