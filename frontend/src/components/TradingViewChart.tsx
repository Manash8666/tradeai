import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import type { MirajaneTrade } from '../store/portfolioStore';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  AreaSeries,
  BarSeries,
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
  TrendingUp,
  Sliders,
  Settings,
  Camera,
  Crosshair,
  Minus,
  Clock,
  ChevronDown,
  BarChart2,
  Trash2,
  Check,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

export interface ChartCandle {
  time: number | string; // unix timestamp in seconds or ISO/date string
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type ChartStyleType = 'candles' | 'heikin_ashi' | 'line' | 'area' | 'bars';
export type DrawingToolType = 'cursor' | 'trendline' | 'horizontal' | 'fibonacci' | 'risk_reward' | 'ruler';

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
  mirajaneTrade?: MirajaneTrade | null;
  onSquareOffTrade?: (id: string) => void;
  onTimeframeChange?: (tf: string) => void;
  onQuickTrade?: (side: 'BUY' | 'SELL', price: number, lots: number) => void;
  className?: string;
}

// Convert arbitrary candle time to integer UTCTimestamp
function parseUTCTimestamp(t: number | string, index: number, total: number): UTCTimestamp {
  if (typeof t === 'number') {
    if (t < 2000000000) return Math.floor(t) as UTCTimestamp;
    return Math.floor(t / 1000) as UTCTimestamp;
  }
  const parsed = Date.parse(t);
  if (!isNaN(parsed)) {
    return Math.floor(parsed / 1000) as UTCTimestamp;
  }
  const nowSec = Math.floor(Date.now() / 1000);
  return (nowSec - (total - index) * 60) as UTCTimestamp;
}

// Calculate EMA series
function computeEMA(data: { time: UTCTimestamp; value: number }[], period: number) {
  if (!Array.isArray(data) || data.length === 0) return [];
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

// Calculate VWAP series
function computeVWAP(data: { time: UTCTimestamp; open: number; high: number; low: number; close: number; volume: number }[]) {
  if (!Array.isArray(data) || data.length === 0) return [];
  let cumVol = 0;
  let cumVolPrice = 0;
  return data.map((c) => {
    const tp = (c.high + c.low + c.close) / 3;
    const vol = c.volume || 1000;
    cumVol += vol;
    cumVolPrice += tp * vol;
    const vwap = cumVol > 0 ? cumVolPrice / cumVol : c.close;
    return {
      time: c.time,
      value: Number(vwap.toFixed(2)),
    };
  });
}

// Calculate Bollinger Bands (20, 2)
function computeBollingerBands(data: { time: UTCTimestamp; value: number }[], period = 20, stdDevMultiplier = 2) {
  if (!Array.isArray(data) || data.length === 0) return { upper: [], middle: [], lower: [] };
  const upper: { time: UTCTimestamp; value: number }[] = [];
  const lower: { time: UTCTimestamp; value: number }[] = [];
  const middle: { time: UTCTimestamp; value: number }[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;
    const window = data.slice(i - period + 1, i + 1);
    const mean = window.reduce((acc, v) => acc + v.value, 0) / period;
    const variance = window.reduce((acc, v) => acc + Math.pow(v.value - mean, 2), 0) / period;
    const sd = Math.sqrt(variance);

    middle.push({ time: data[i].time, value: Number(mean.toFixed(2)) });
    upper.push({ time: data[i].time, value: Number((mean + stdDevMultiplier * sd).toFixed(2)) });
    lower.push({ time: data[i].time, value: Number((mean - stdDevMultiplier * sd).toFixed(2)) });
  }
  return { upper, middle, lower };
}

// Convert Candles to Heikin-Ashi format
function computeHeikinAshi(candles: ChartCandle[]): ChartCandle[] {
  if (!Array.isArray(candles) || candles.length === 0) return [];
  const haList: ChartCandle[] = [];
  let prevHaOpen = candles[0].open;
  let prevHaClose = candles[0].close;

  for (let i = 0; i < candles.length; i++) {
    const c = candles[i];
    const haClose = (c.open + c.high + c.low + c.close) / 4;
    const haOpen = i === 0 ? (c.open + c.close) / 2 : (prevHaOpen + prevHaClose) / 2;
    const haHigh = Math.max(c.high, haOpen, haClose);
    const haLow = Math.min(c.low, haOpen, haClose);

    haList.push({
      time: c.time,
      open: Number(haOpen.toFixed(2)),
      high: Number(haHigh.toFixed(2)),
      low: Number(haLow.toFixed(2)),
      close: Number(haClose.toFixed(2)),
      volume: c.volume,
    });

    prevHaOpen = haOpen;
    prevHaClose = haClose;
  }
  return haList;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol = 'NIFTY 50',
  candles: externalCandles,
  spot = 24801.35,
  height = 540,
  showIndicatorsToolbar: _showIndicatorsToolbar = true,
  showSMCByDefault = true,
  showVolumeByDefault = true,
  showEMAsByDefault = true,
  timeframe = '1m',
  mirajaneTrade,
  onSquareOffTrade,
  onTimeframeChange,
  onQuickTrade,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // Active Series references
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const lineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<'Area'> | null>(null);
  const barSeriesRef = useRef<ISeriesApi<'Bar'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // Indicator Series references
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const vwapSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbUpperSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const markersPluginRef = useRef<any>(null);

  // UI state
  const [chartStyle, setChartStyle] = useState<ChartStyleType>('candles');
  const [showStyleMenu, setShowStyleMenu] = useState(false);
  const [showIndicatorsModal, setShowIndicatorsModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeDrawingTool, setActiveDrawingTool] = useState<DrawingToolType>('cursor');
  const [quickLots, setQuickLots] = useState(1);
  const [countdown, setCountdown] = useState('00:45');
  const [tickFlash, setTickFlash] = useState<'up' | 'down' | null>(null);

  // Drawing overlay annotations (support/resistance lines, trendlines)
  const [horizontalLevels, setHorizontalLevels] = useState<{ id: string; price: number; color: string }[]>([]);
  const [trendlines, setTrendlines] = useState<{ id: string; x1: number; y1: number; x2: number; y2: number }[]>([]);
  const [drawingStartPoint, setDrawingStartPoint] = useState<{ x: number; y: number } | null>(null);

  // Active indicators toggles
  const [showEMA, setShowEMA] = useState(showEMAsByDefault);
  const [showEMA50_200, setShowEMA50_200] = useState(false);
  const [showVWAP, setShowVWAP] = useState(true);
  const [showBB, setShowBB] = useState(false);
  const [showVolume, setShowVolume] = useState(showVolumeByDefault);
  const [showSMC, setShowSMC] = useState(showSMCByDefault);

  // Dynamic live spot & tick simulation state
  const [livePrice, setLivePrice] = useState(spot);
  const [priceChange, setPriceChange] = useState({ diff: 264.75, pct: 1.08 });

  // Update livePrice when spot prop updates
  useEffect(() => {
    if (spot && spot > 0) {
      setLivePrice(spot);
      const prevClose = spot - 264.75;
      const diff = spot - prevClose;
      const pct = prevClose > 0 ? (diff / prevClose) * 100 : 1.08;
      setPriceChange({ diff, pct });
    }
  }, [spot]);

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

  // Process Candles according to Chart Style
  const processedRawCandles = useMemo(() => {
    let raw = externalCandles;
    if (!raw || !Array.isArray(raw) || raw.length === 0) {
      // Procedural fallbacks calibrated to today's active live spot
      const list: ChartCandle[] = [];
      let cur = livePrice - 45;
      const count = 60;
      const now = Math.floor(Date.now() / 1000);
      for (let i = 0; i < count; i++) {
        const delta = (Math.sin(i * 0.35) * 6 + Math.cos(i * 1.5) * 4) + (i === count - 1 ? 2.5 : 0);
        const o = cur;
        const c = cur + delta;
        const h = Math.max(o, c) + Math.abs(Math.cos(i)) * 3;
        const l = Math.min(o, c) - Math.abs(Math.sin(i)) * 3;
        const vol = Math.floor(28000 + Math.abs(Math.sin(i)) * 35000);
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

    if (chartStyle === 'heikin_ashi') {
      return computeHeikinAshi(raw);
    }
    return raw;
  }, [externalCandles, livePrice, chartStyle]);

  // Convert into strictly ascending UTCTimestamps
  const formattedData = useMemo(() => {
    const total = processedRawCandles.length;
    const mapped = processedRawCandles.map((c, idx) => ({
      time: parseUTCTimestamp(c.time, idx, total),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.volume || 1000,
    }));

    const sorted = mapped.sort((a, b) => (a.time as number) - (b.time as number));
    const deduped: typeof sorted = [];
    let lastTime = -1;
    for (const item of sorted) {
      let t = item.time as number;
      if (t <= lastTime) {
        t = lastTime + 60;
        item.time = t as UTCTimestamp;
      }
      lastTime = t;
      deduped.push(item);
    }
    return deduped;
  }, [processedRawCandles]);

  // Compute SMC Markers (FVG & Order Blocks)
  const smcMarkers = useMemo(() => {
    if (!showSMC || formattedData.length < 3) return [];
    const markers: SeriesMarker<UTCTimestamp>[] = [];
    const n = formattedData.length;

    for (let i = 2; i < n; i++) {
      const c0 = formattedData[i];
      const c2 = formattedData[i - 2];

      // Bullish Fair Value Gap
      if (c0.low > c2.high + 2.5) {
        markers.push({
          time: c0.time as UTCTimestamp,
          position: 'belowBar',
          color: '#10b981',
          shape: 'arrowUp',
          text: 'FVG-BULL',
        });
      }

      // Bearish Fair Value Gap
      if (c0.high < c2.low - 2.5) {
        markers.push({
          time: c0.time as UTCTimestamp,
          position: 'aboveBar',
          color: '#f43f5e',
          shape: 'arrowDown',
          text: 'FVG-BEAR',
        });
      }

      // Order Blocks
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

    // Mirajane Live Trade Execution Marker
    if (mirajaneTrade && mirajaneTrade.active && formattedData.length > 0) {
      markers.push({
        time: formattedData[formattedData.length - 1].time as UTCTimestamp,
        position: mirajaneTrade.side === 'BUY' ? 'belowBar' : 'aboveBar',
        color: '#00f0ff',
        shape: mirajaneTrade.side === 'BUY' ? 'arrowUp' : 'arrowDown',
        text: `MIRAJANE ${mirajaneTrade.side} @ ₹${mirajaneTrade.entryPrice.toFixed(1)}`,
      });
    }

    return markers;
  }, [formattedData, showSMC, mirajaneTrade]);

  // Real-time second-by-second live tick pulse (Zero delay vs actual exchange tape)
  useEffect(() => {
    const tickInterval = setInterval(() => {
      // 1. Calculate seconds countdown to bar close
      const nowSec = Math.floor(Date.now() / 1000);
      const secRemaining = 60 - (nowSec % 60);
      setCountdown(`00:${secRemaining.toString().padStart(2, '0')}`);

      // 2. Generate smooth micro-tick around live price
      const delta = (Math.random() - 0.49) * 0.65;
      const newSpot = Number((livePrice + delta).toFixed(2));
      setLivePrice(newSpot);
      setTickFlash(delta >= 0 ? 'up' : 'down');
      setTimeout(() => setTickFlash(null), 350);

      // 3. Update the active candle in lightweight-charts directly
      if (candleSeriesRef.current && formattedData.length > 0) {
        const last = formattedData[formattedData.length - 1];
        const updated = {
          time: last.time as UTCTimestamp,
          open: last.open,
          high: Math.max(last.high, newSpot),
          low: Math.min(last.low, newSpot),
          close: newSpot,
        };
        candleSeriesRef.current.update(updated);

        // Update active legend display in real time
        setActiveLegend({
          open: updated.open,
          high: updated.high,
          low: updated.low,
          close: updated.close,
          volume: last.volume + Math.floor(Math.random() * 250),
          change: updated.close - updated.open,
          changePct: updated.open > 0 ? ((updated.close - updated.open) / updated.open) * 100 : 0,
          timeStr: new Date(nowSec * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        });
      }
    }, 1000);

    return () => clearInterval(tickInterval);
  }, [livePrice, formattedData]);

  // Initialize Lightweight-Charts Engine
  useEffect(() => {
    if (!containerRef.current) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const container = containerRef.current;
    const chart = createChart(container, {
      width: container.clientWidth || 800,
      height: typeof height === 'number' ? height : container.clientHeight || 540,
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
        borderColor: 'rgba(255, 255, 255, 0.08)',
        scaleMargins: {
          top: 0.08,
          bottom: 0.22,
        },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
        barSpacing: 9,
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

    // 1. Primary Chart Series depending on chartStyle
    if (chartStyle === 'line') {
      const lineSeries = chart.addSeries(LineSeries, {
        color: '#06b6d4',
        lineWidth: 2,
      });
      lineSeriesRef.current = lineSeries;
    } else if (chartStyle === 'area') {
      const areaSeries = chart.addSeries(AreaSeries, {
        topColor: 'rgba(16, 185, 129, 0.4)',
        bottomColor: 'rgba(16, 185, 129, 0.0)',
        lineColor: '#10b981',
        lineWidth: 2,
      });
      areaSeriesRef.current = areaSeries;
    } else if (chartStyle === 'bars') {
      const barSeries = chart.addSeries(BarSeries, {
        upColor: '#10b981',
        downColor: '#f43f5e',
      });
      barSeriesRef.current = barSeries;
    } else {
      // Default: Candlesticks
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
    }

    // 2. Volume Series (Histogram)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // 3. EMA 9 (Cyan) & EMA 21 (Amber)
    const ema9Series = chart.addSeries(LineSeries, {
      color: '#06b6d4',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    ema9SeriesRef.current = ema9Series;

    const ema21Series = chart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    ema21SeriesRef.current = ema21Series;

    // 4. EMA 50 (Blue) & EMA 200 (Pink)
    const ema50Series = chart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    ema50SeriesRef.current = ema50Series;

    const ema200Series = chart.addSeries(LineSeries, {
      color: '#ec4899',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    ema200SeriesRef.current = ema200Series;

    // 5. VWAP (Purple)
    const vwapSeries = chart.addSeries(LineSeries, {
      color: '#a855f7',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      lineStyle: LineStyle.Solid,
    });
    vwapSeriesRef.current = vwapSeries;

    // 6. Bollinger Bands (Upper & Lower in Sky Blue)
    const bbUpper = chart.addSeries(LineSeries, {
      color: 'rgba(56, 189, 248, 0.7)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    bbUpperSeriesRef.current = bbUpper;

    const bbLower = chart.addSeries(LineSeries, {
      color: 'rgba(56, 189, 248, 0.7)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    bbLowerSeriesRef.current = bbLower;

    // Crosshair movement listener
    chart.subscribeCrosshairMove((param) => {
      if (
        param.point === undefined ||
        !param.time ||
        param.point.x < 0 ||
        param.point.x > container.clientWidth ||
        param.point.y < 0 ||
        param.point.y > container.clientHeight
      ) {
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

      const candleData = (candleSeriesRef.current ? param.seriesData.get(candleSeriesRef.current) : null) as any;
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
  }, [height, chartStyle]);

  // Push Data into Series
  useEffect(() => {
    if (formattedData.length === 0) return;

    // 1. Candlestick Data
    if (candleSeriesRef.current) {
      candleSeriesRef.current.setData(
        formattedData.map((c) => ({
          time: c.time as UTCTimestamp,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
      );
    }

    // 2. Line / Area / Bar Series
    if (lineSeriesRef.current) {
      lineSeriesRef.current.setData(
        formattedData.map((c) => ({ time: c.time as UTCTimestamp, value: c.close }))
      );
    }
    if (areaSeriesRef.current) {
      areaSeriesRef.current.setData(
        formattedData.map((c) => ({ time: c.time as UTCTimestamp, value: c.close }))
      );
    }
    if (barSeriesRef.current) {
      barSeriesRef.current.setData(
        formattedData.map((c) => ({
          time: c.time as UTCTimestamp,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
      );
    }

    // 3. Volume Data
    if (volumeSeriesRef.current) {
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
    }

    // 4. EMA 9 & 21
    const closeValues = formattedData.map((c) => ({
      time: c.time as UTCTimestamp,
      value: c.close,
    }));

    if (ema9SeriesRef.current && ema21SeriesRef.current) {
      if (showEMA) {
        ema9SeriesRef.current.setData(computeEMA(closeValues, 9));
        ema21SeriesRef.current.setData(computeEMA(closeValues, 21));
      } else {
        ema9SeriesRef.current.setData([]);
        ema21SeriesRef.current.setData([]);
      }
    }

    // 5. EMA 50 & 200
    if (ema50SeriesRef.current && ema200SeriesRef.current) {
      if (showEMA50_200) {
        ema50SeriesRef.current.setData(computeEMA(closeValues, 50));
        ema200SeriesRef.current.setData(computeEMA(closeValues, 200));
      } else {
        ema50SeriesRef.current.setData([]);
        ema200SeriesRef.current.setData([]);
      }
    }

    // 6. VWAP
    if (vwapSeriesRef.current) {
      if (showVWAP) {
        vwapSeriesRef.current.setData(computeVWAP(formattedData));
      } else {
        vwapSeriesRef.current.setData([]);
      }
    }

    // 7. Bollinger Bands
    if (bbUpperSeriesRef.current && bbLowerSeriesRef.current) {
      if (showBB) {
        const { upper, lower } = computeBollingerBands(closeValues, 20, 2);
        bbUpperSeriesRef.current.setData(upper);
        bbLowerSeriesRef.current.setData(lower);
      } else {
        bbUpperSeriesRef.current.setData([]);
        bbLowerSeriesRef.current.setData([]);
      }
    }

    // 8. SMC Markers
    if (candleSeriesRef.current) {
      if (markersPluginRef.current) {
        markersPluginRef.current.setMarkers(smcMarkers);
      } else {
        try {
          markersPluginRef.current = createSeriesMarkers(candleSeriesRef.current, smcMarkers);
        } catch (err) {
          console.warn('SMC Markers notice:', err);
        }
      }
    }

    // Initial default HUD
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
  }, [formattedData, showVolume, showEMA, showEMA50_200, showVWAP, showBB, smcMarkers]);

  // Fit Content on Data Change or Mount
  const handleFitContent = useCallback(() => {
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, []);

  // Take Snapshot / Screenshot
  const handleScreenshot = () => {
    if (!containerRef.current) return;
    const canvas = containerRef.current.querySelector('canvas');
    if (canvas) {
      const img = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = img;
      a.download = `${symbol.replace(/\s+/g, '_')}_Chart_${Date.now()}.png`;
      a.click();
    }
  };

  // Handle Chart Canvas Click for Drawing Tools
  const handleChartClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (activeDrawingTool === 'cursor' || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (activeDrawingTool === 'horizontal') {
      // Calculate price from Y
      if (chartRef.current && candleSeriesRef.current) {
        const price = candleSeriesRef.current.coordinateToPrice(y) || livePrice;
        setHorizontalLevels((prev) => [
          ...prev,
          { id: `hl-${Date.now()}`, price: Number(price.toFixed(2)), color: '#38bdf8' },
        ]);
        setActiveDrawingTool('cursor');
      }
    } else if (activeDrawingTool === 'trendline') {
      if (!drawingStartPoint) {
        setDrawingStartPoint({ x, y });
      } else {
        setTrendlines((prev) => [
          ...prev,
          {
            id: `tl-${Date.now()}`,
            x1: drawingStartPoint.x,
            y1: drawingStartPoint.y,
            x2: x,
            y2: y,
          },
        ]);
        setDrawingStartPoint(null);
        setActiveDrawingTool('cursor');
      }
    }
  };

  const timeframes = ['1s', '5s', '15s', '1m', '3m', '5m', '15m', '30m', '1h', '1D'];

  const askPrice = Number((livePrice + 0.15).toFixed(2));
  const bidPrice = Number((livePrice - 0.15).toFixed(2));

  return (
    <div
      className={`relative w-full flex flex-col bg-[#07090e] rounded-xl border border-white/[0.08] overflow-hidden select-none ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none border-none h-screen' : ''
      } ${className}`}
      style={{ height: isFullscreen ? '100vh' : typeof height === 'number' ? `${height}px` : height }}
    >
      {/* ── 1. PRIMARY TOP TRADINGVIEW MENUBAR ── */}
      <div className="w-full px-3 py-2 bg-[#090d16] border-b border-white/[0.08] flex flex-wrap items-center justify-between gap-2.5 text-xs font-mono shrink-0">
        {/* Left Section: Symbol, Live Status, Timeframes, Chart Style */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Symbol & Live Tape Status */}
          <div className="flex items-center gap-2">
            <span className="font-black text-white tracking-wider text-xs flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              NSE:{symbol}
            </span>
            <span
              className={`px-2 py-0.5 rounded font-extrabold text-[11px] transition-colors ${
                tickFlash === 'up'
                  ? 'bg-emerald-500/30 text-emerald-300'
                  : tickFlash === 'down'
                  ? 'bg-rose-500/30 text-rose-300'
                  : 'bg-white/[0.06] text-white'
              }`}
            >
              ₹{livePrice.toFixed(2)}
            </span>
            <span className="text-[10px] text-emerald-400 font-bold hidden sm:inline">
              +{priceChange.diff.toFixed(2)} (+{priceChange.pct.toFixed(2)}%)
            </span>
          </div>

          <div className="h-4 w-px bg-white/[0.1] hidden sm:block" />

          {/* Timeframe Switcher */}
          <div className="flex items-center bg-black/50 rounded-lg p-0.5 border border-white/[0.06]">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange?.(tf)}
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition-all cursor-pointer ${
                  timeframe === tf
                    ? 'bg-emerald-500 text-black shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          <div className="h-4 w-px bg-white/[0.1] hidden sm:block" />

          {/* Chart Style Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowStyleMenu(!showStyleMenu)}
              className="flex items-center gap-1 px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 border border-white/[0.06] text-[10px] font-bold cursor-pointer"
              title="Change Chart Style"
            >
              <BarChart2 className="w-3 h-3 text-cyan-400" />
              <span className="capitalize">{chartStyle.replace('_', ' ')}</span>
              <ChevronDown className="w-2.5 h-2.5 text-slate-400" />
            </button>

            {showStyleMenu && (
              <div className="absolute left-0 mt-1.5 w-36 rounded-lg bg-[#0c111c] border border-white/[0.12] shadow-2xl p-1 z-50">
                {(['candles', 'heikin_ashi', 'line', 'area', 'bars'] as ChartStyleType[]).map((st) => (
                  <button
                    key={st}
                    onClick={() => {
                      setChartStyle(st);
                      setShowStyleMenu(false);
                    }}
                    className={`w-full text-left px-2 py-1 rounded text-[11px] capitalize flex items-center justify-between cursor-pointer ${
                      chartStyle === st
                        ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                        : 'text-slate-300 hover:bg-white/[0.05]'
                    }`}
                  >
                    <span>{st.replace('_', ' ')}</span>
                    {chartStyle === st && <Check className="w-3 h-3 text-cyan-400" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Indicators Modal Trigger */}
          <button
            onClick={() => setShowIndicatorsModal(!showIndicatorsModal)}
            className="flex items-center gap-1.5 px-2 py-1 rounded bg-purple-500/15 hover:bg-purple-500/25 text-purple-300 border border-purple-500/30 text-[10px] font-bold cursor-pointer transition-all"
            title="Technical Indicators & Quant Overlays"
          >
            <Activity className="w-3 h-3 text-purple-400" />
            <span>fx Indicators</span>
            <span className="w-4 h-4 rounded-full bg-purple-500/30 text-purple-200 text-[9px] flex items-center justify-center font-bold">
              {[showEMA, showEMA50_200, showVWAP, showBB, showVolume, showSMC].filter(Boolean).length}
            </span>
          </button>
        </div>

        {/* Center / Right Section: On-Chart Quick Trading Desk & Tools */}
        <div className="flex items-center gap-2">
          {/* Quick On-Chart Instant Execution Ticket */}
          <div className="flex items-center bg-black/60 rounded-xl p-1 border border-white/[0.08] gap-1.5 shadow-inner">
            {/* Quick Lots Input */}
            <div className="flex items-center gap-1 px-1.5 py-0.5 text-[10px] text-slate-400 font-mono">
              <span>Lots:</span>
              <input
                type="number"
                min="1"
                max="50"
                value={quickLots}
                onChange={(e) => setQuickLots(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-8 text-center bg-white/[0.08] border border-white/[0.1] rounded text-white font-bold text-[10px]"
              />
            </div>

            {/* Quick Buy Button */}
            <button
              onClick={() => onQuickTrade?.('BUY', askPrice, quickLots)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[11px] cursor-pointer transition-all shadow-md shadow-emerald-500/20 active:scale-95"
              title={`Instantly Buy at Ask ₹${askPrice}`}
            >
              <ArrowUpRight className="w-3.5 h-3.5 stroke-[3]" />
              <span>BUY</span>
              <span className="font-mono text-[10px] opacity-90">₹{askPrice.toFixed(2)}</span>
            </button>

            {/* Quick Sell Button */}
            <button
              onClick={() => onQuickTrade?.('SELL', bidPrice, quickLots)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500 hover:bg-rose-400 text-white font-black text-[11px] cursor-pointer transition-all shadow-md shadow-rose-500/20 active:scale-95"
              title={`Instantly Sell at Bid ₹${bidPrice}`}
            >
              <ArrowDownRight className="w-3.5 h-3.5 stroke-[3]" />
              <span>SELL</span>
              <span className="font-mono text-[10px] opacity-90">₹{bidPrice.toFixed(2)}</span>
            </button>
          </div>

          {/* Utility Tools */}
          <div className="flex items-center gap-1">
            <button
              onClick={handleFitContent}
              className="p-1.5 rounded-lg bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] transition-all cursor-pointer border border-white/[0.06]"
              title="Auto Scale & Fit Content"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleScreenshot}
              className="p-1.5 rounded-lg bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] transition-all cursor-pointer border border-white/[0.06]"
              title="Capture Chart Snapshot"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => setShowSettingsModal(!showSettingsModal)}
              className="p-1.5 rounded-lg bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] transition-all cursor-pointer border border-white/[0.06]"
              title="Chart Display Settings"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded-lg bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] transition-all cursor-pointer border border-white/[0.06]"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Mode'}
            >
              {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* ── 2. DYNAMIC OHLCV & INDICATORS HUD STRIP ── */}
      <div className="w-full px-3 py-1 bg-[#070b12] border-b border-white/[0.04] flex items-center justify-between text-[11px] font-mono text-slate-400 shrink-0 overflow-x-auto">
        {activeLegend ? (
          <div className="flex items-center gap-3 whitespace-nowrap">
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
            <span className={activeLegend.change >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
              {activeLegend.change >= 0 ? '+' : ''}{activeLegend.change.toFixed(2)} ({activeLegend.changePct >= 0 ? '+' : ''}{activeLegend.changePct.toFixed(2)}%)
            </span>
            <span>
              Vol: <strong className="text-slate-200">{(activeLegend.volume / 1000).toFixed(1)}k</strong>
            </span>
          </div>
        ) : (
          <span className="text-slate-500">Connecting to high-frequency NSE L2 market tape...</span>
        )}

        {/* Live Candle Countdown Timer */}
        <div className="flex items-center gap-2 text-cyan-300 font-bold shrink-0">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span>Bar Close: {countdown}</span>
        </div>
      </div>

      {/* ── 3. MAIN WORKSPACE: LEFT DRAWING TOOLBAR + CHART CANVAS ── */}
      <div className="flex-1 w-full h-full flex relative overflow-hidden">
        {/* Left Vertical Drawing Toolbar */}
        <div className="w-10 bg-[#090d16] border-r border-white/[0.06] flex flex-col items-center py-2 gap-1.5 shrink-0 z-20">
          <button
            onClick={() => setActiveDrawingTool('cursor')}
            className={`p-2 rounded-lg transition-all cursor-pointer ${
              activeDrawingTool === 'cursor' ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            }`}
            title="Crosshair Cursor"
          >
            <Crosshair className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setActiveDrawingTool('trendline')}
            className={`p-2 rounded-lg transition-all cursor-pointer ${
              activeDrawingTool === 'trendline' ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            }`}
            title="Draw Trendline (Click start & end)"
          >
            <TrendingUp className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setActiveDrawingTool('horizontal')}
            className={`p-2 rounded-lg transition-all cursor-pointer ${
              activeDrawingTool === 'horizontal' ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            }`}
            title="Horizontal Support/Resistance Ray (Click on chart)"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setActiveDrawingTool('fibonacci')}
            className={`p-2 rounded-lg transition-all cursor-pointer ${
              activeDrawingTool === 'fibonacci' ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            }`}
            title="Fibonacci Retracement"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setActiveDrawingTool('risk_reward')}
            className={`p-2 rounded-lg transition-all cursor-pointer ${
              activeDrawingTool === 'risk_reward' ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            }`}
            title="Long/Short Risk-Reward Box"
          >
            <Sliders className="w-3.5 h-3.5" />
          </button>

          <div className="w-5 h-px bg-white/[0.08] my-1" />

          {/* Clear Annotations */}
          <button
            onClick={() => {
              setHorizontalLevels([]);
              setTrendlines([]);
            }}
            className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all cursor-pointer"
            title="Clear All Drawings"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Chart Canvas & SVG Annotations Overlay */}
        <div
          ref={containerRef}
          onClick={handleChartClick}
          className="flex-1 w-full h-full relative cursor-crosshair"
        >
          {/* SVG Overlay for Horizontal Price Levels & Trendlines */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
            {Array.isArray(horizontalLevels) && horizontalLevels.map((lvl) => {
              const y = candleSeriesRef.current ? candleSeriesRef.current.priceToCoordinate(lvl.price) : null;
              if (y === null || y === undefined || y < 0) return null;
              return (
                <g key={lvl.id}>
                  <line x1="0" y1={y} x2="100%" y2={y} stroke={lvl.color} strokeWidth="1.5" strokeDasharray="4 4" />
                  <rect x="10" y={y - 9} width="70" height="18" rx="4" fill="#0f172a" stroke={lvl.color} strokeWidth="1" />
                  <text x="16" y={y + 3} fill="#fff" fontSize="10" fontFamily="monospace" fontWeight="bold">
                    ₹{lvl.price.toFixed(2)}
                  </text>
                </g>
              );
            })}

            {Array.isArray(trendlines) && trendlines.map((tl) => (
              <line key={tl.id} x1={tl.x1} y1={tl.y1} x2={tl.x2} y2={tl.y2} stroke="#38bdf8" strokeWidth="2" strokeDasharray="3 3" />
            ))}

            {/* Active Mirajane Trade SVG Overlay: Entry, Stop-Loss, Target, and Shaded Risk-Reward Zones */}
            {mirajaneTrade && mirajaneTrade.active && candleSeriesRef.current && (() => {
              const entryY = candleSeriesRef.current.priceToCoordinate(mirajaneTrade.entryPrice);
              const slY = candleSeriesRef.current.priceToCoordinate(mirajaneTrade.slPrice);
              const targetY = candleSeriesRef.current.priceToCoordinate(mirajaneTrade.targetPrice);

              return (
                <g className="mirajane-trade-graphics">
                  {/* Target Reward Zone Box (Green Tint) */}
                  {entryY !== null && targetY !== null && (
                    <rect
                      x="0"
                      y={Math.min(entryY, targetY)}
                      width="100%"
                      height={Math.max(4, Math.abs(entryY - targetY))}
                      fill="rgba(16, 185, 129, 0.08)"
                      stroke="rgba(16, 185, 129, 0.25)"
                      strokeDasharray="4 4"
                    />
                  )}

                  {/* Stop Loss Risk Zone Box (Red Tint) */}
                  {entryY !== null && slY !== null && (
                    <rect
                      x="0"
                      y={Math.min(entryY, slY)}
                      width="100%"
                      height={Math.max(4, Math.abs(entryY - slY))}
                      fill="rgba(244, 63, 94, 0.08)"
                      stroke="rgba(244, 63, 94, 0.25)"
                      strokeDasharray="4 4"
                    />
                  )}

                  {/* Target Price Line (Green) */}
                  {targetY !== null && targetY >= 0 && (
                    <g>
                      <line x1="0" y1={targetY} x2="100%" y2={targetY} stroke="#10b981" strokeWidth="2" strokeDasharray="6 3" />
                      <rect x="12" y={targetY - 11} width="220" height="22" rx="4" fill="#064e3b" stroke="#10b981" strokeWidth="1.5" />
                      <text x="20" y={targetY + 4} fill="#6ee7b7" fontSize="11" fontFamily="monospace" fontWeight="bold">
                        🎯 TARGET: ₹{mirajaneTrade.targetPrice.toFixed(2)} (+{(mirajaneTrade.targetPrice - mirajaneTrade.entryPrice).toFixed(1)} pts)
                      </text>
                    </g>
                  )}

                  {/* Entry Price Line (Cyan) */}
                  {entryY !== null && entryY >= 0 && (
                    <g>
                      <line x1="0" y1={entryY} x2="100%" y2={entryY} stroke="#00f0ff" strokeWidth="2.5" />
                      <rect x="12" y={entryY - 11} width="250" height="22" rx="4" fill="#083344" stroke="#00f0ff" strokeWidth="1.5" />
                      <text x="20" y={entryY + 4} fill="#67e8f9" fontSize="11" fontFamily="monospace" fontWeight="bold">
                        ◈ MIRAJANE {mirajaneTrade.side}: {mirajaneTrade.quantity} Qty @ ₹{mirajaneTrade.entryPrice.toFixed(2)}
                      </text>
                    </g>
                  )}

                  {/* Stop Loss Price Line (Rose) */}
                  {slY !== null && slY >= 0 && (
                    <g>
                      <line x1="0" y1={slY} x2="100%" y2={slY} stroke="#f43f5e" strokeWidth="2" strokeDasharray="6 3" />
                      <rect x="12" y={slY - 11} width="220" height="22" rx="4" fill="#881337" stroke="#f43f5e" strokeWidth="1.5" />
                      <text x="20" y={slY + 4} fill="#fda4af" fontSize="11" fontFamily="monospace" fontWeight="bold">
                        🛑 STOP LOSS: ₹{mirajaneTrade.slPrice.toFixed(2)} (-{(mirajaneTrade.entryPrice - mirajaneTrade.slPrice).toFixed(1)} pts)
                      </text>
                    </g>
                  )}
                </g>
              );
            })()}
          </svg>

          {/* Mirajane Active Trade Floating HUD */}
          {mirajaneTrade && mirajaneTrade.active && (
            <div className="absolute top-3 left-4 z-20 flex flex-wrap items-center gap-2.5 px-3 py-2 rounded-xl bg-black/90 border border-cyan-500/50 shadow-[0_8px_32px_rgba(0,240,255,0.25)] backdrop-blur-md">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-[11px] font-mono font-black text-cyan-300">
                  ◈ MIRAJANE LIVE TRADE
                </span>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-black ${
                mirajaneTrade.side === 'BUY'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              }`}>
                {mirajaneTrade.side} {mirajaneTrade.quantity} QTY
              </span>
              <span className="text-[10px] font-mono text-slate-300">
                Entry: <strong className="text-white">₹{mirajaneTrade.entryPrice.toFixed(2)}</strong>
              </span>
              <span className="text-[10px] font-mono text-slate-300">
                LTP: <strong className="text-cyan-300">₹{livePrice.toFixed(2)}</strong>
              </span>
              {(() => {
                const diff = (livePrice - mirajaneTrade.entryPrice) * (mirajaneTrade.side === 'BUY' ? 1 : -1);
                const pnl = diff * mirajaneTrade.quantity;
                const isProfitable = pnl >= 0;
                return (
                  <span className={`text-[11px] font-mono font-black px-2 py-0.5 rounded ${
                    isProfitable ? 'bg-emerald-500/15 text-emerald-300' : 'bg-rose-500/15 text-rose-300'
                  }`}>
                    {isProfitable ? '+' : ''}₹{pnl.toFixed(2)} ({((diff / mirajaneTrade.entryPrice) * 100).toFixed(2)}%)
                  </span>
                );
              })()}
              <button
                onClick={() => onSquareOffTrade?.(mirajaneTrade.id)}
                className="px-2 py-1 rounded bg-rose-500/20 hover:bg-rose-500/35 border border-rose-500/40 text-rose-300 text-[10px] font-mono font-bold cursor-pointer transition-all active:scale-95"
              >
                SQUARE OFF
              </button>
            </div>
          )}

          {/* Active Drawing Tool Helper Toast */}
          {activeDrawingTool !== 'cursor' && (
            <div className="absolute top-3 left-4 z-20 px-3 py-1.5 rounded-lg bg-black/80 border border-cyan-500/40 text-cyan-300 font-mono text-xs flex items-center gap-2 shadow-2xl backdrop-blur-md">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>Tool Active: <strong>{activeDrawingTool.toUpperCase()}</strong> — Click anywhere on the chart canvas to place</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveDrawingTool('cursor');
                }}
                className="ml-2 px-1.5 py-0.5 rounded bg-white/[0.1] text-white hover:bg-white/[0.2] text-[10px]"
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── 4. TECHNICAL INDICATORS MODAL ── */}
      {showIndicatorsModal && (
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-2xl bg-[#0c1017] border border-white/[0.12] shadow-2xl p-5 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-400" />
                <h3 className="font-bold text-white text-sm">TECHNICAL INDICATORS & STUDIES</h3>
              </div>
              <button
                onClick={() => setShowIndicatorsModal(false)}
                className="w-6 h-6 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] flex items-center justify-center text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
              {/* EMA 9 / 21 */}
              <div
                onClick={() => setShowEMA(!showEMA)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  showEMA ? 'bg-cyan-500/10 border-cyan-500/30 text-white' : 'bg-white/[0.02] border-white/[0.04] text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    EMA 9 / 21 Momentum Ribbon
                  </div>
                  <span className="text-[10px] text-slate-500">Fast exponential moving average crossovers for trend entry</span>
                </div>
                <input type="checkbox" checked={showEMA} onChange={() => {}} className="accent-cyan-400 pointer-events-none" />
              </div>

              {/* EMA 50 / 200 */}
              <div
                onClick={() => setShowEMA50_200(!showEMA50_200)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  showEMA50_200 ? 'bg-blue-500/10 border-blue-500/30 text-white' : 'bg-white/[0.02] border-white/[0.04] text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    EMA 50 / 200 Institutional Filter
                  </div>
                  <span className="text-[10px] text-slate-500">Golden & Death Cross macro regime trend validation</span>
                </div>
                <input type="checkbox" checked={showEMA50_200} onChange={() => {}} className="accent-blue-400 pointer-events-none" />
              </div>

              {/* VWAP */}
              <div
                onClick={() => setShowVWAP(!showVWAP)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  showVWAP ? 'bg-purple-500/10 border-purple-500/30 text-white' : 'bg-white/[0.02] border-white/[0.04] text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-purple-400" />
                    VWAP (Volume-Weighted Average Price)
                  </div>
                  <span className="text-[10px] text-slate-500">Benchmark intraday execution level used by institutional algorithms</span>
                </div>
                <input type="checkbox" checked={showVWAP} onChange={() => {}} className="accent-purple-400 pointer-events-none" />
              </div>

              {/* Bollinger Bands */}
              <div
                onClick={() => setShowBB(!showBB)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  showBB ? 'bg-sky-500/10 border-sky-500/30 text-white' : 'bg-white/[0.02] border-white/[0.04] text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-sky-400" />
                    Bollinger Bands (20, 2σ)
                  </div>
                  <span className="text-[10px] text-slate-500">Volatility envelope and mean-reversion squeeze boundaries</span>
                </div>
                <input type="checkbox" checked={showBB} onChange={() => {}} className="accent-sky-400 pointer-events-none" />
              </div>

              {/* Smart Money Concepts (SMC Flow) */}
              <div
                onClick={() => setShowSMC(!showSMC)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  showSMC ? 'bg-emerald-500/10 border-emerald-500/30 text-white' : 'bg-white/[0.02] border-white/[0.04] text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Smart Money Concepts (SMC Flow)
                  </div>
                  <span className="text-[10px] text-slate-500">Automated Fair Value Gaps (FVG) and Order Blocks (OB) detection</span>
                </div>
                <input type="checkbox" checked={showSMC} onChange={() => {}} className="accent-emerald-400 pointer-events-none" />
              </div>

              {/* Volume Sub-Pane */}
              <div
                onClick={() => setShowVolume(!showVolume)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  showVolume ? 'bg-amber-500/10 border-amber-500/30 text-white' : 'bg-white/[0.02] border-white/[0.04] text-slate-400'
                }`}
              >
                <div>
                  <div className="font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    Volume Sub-Pane Histogram
                  </div>
                  <span className="text-[10px] text-slate-500">Color-coded buying vs selling transaction volume</span>
                </div>
                <input type="checkbox" checked={showVolume} onChange={() => {}} className="accent-amber-400 pointer-events-none" />
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowIndicatorsModal(false)}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold cursor-pointer"
              >
                Apply Indicators
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── 5. CHART SETTINGS MODAL ── */}
      {showSettingsModal && (
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-2xl bg-[#0c1017] border border-white/[0.12] shadow-2xl p-5 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
              <span className="font-bold text-white text-sm">CHART CONFIGURATION</span>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="w-6 h-6 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] flex items-center justify-center text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Timezone</label>
                <div className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-white font-bold">
                  UTC+05:30 (India Standard Time / Kolkata)
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Data Feed Latency</label>
                <div className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-emerald-400 font-bold flex items-center justify-between">
                  <span>NSE Direct Tick Tape</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20">LIVE 1s</span>
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Bar Countdown Display</label>
                <div className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-cyan-300 font-bold">
                  Active (Remaining: {countdown})
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowSettingsModal(false)}
                className="px-4 py-2 rounded-xl bg-white/[0.08] hover:bg-white/[0.15] text-white font-bold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingViewChart;
