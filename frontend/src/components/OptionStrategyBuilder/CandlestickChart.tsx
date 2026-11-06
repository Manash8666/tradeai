import React from 'react';
import { TradingViewChart } from '../TradingViewChart';

interface CandlestickChartProps {
  symbol?: string;
  spot?: number;
  height?: number;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  symbol = 'NIFTY',
  spot = 23806.95,
  height = 320,
}) => {
  return (
    <div className="w-full h-full flex flex-col">
      <TradingViewChart
        symbol={symbol}
        spot={spot}
        height={height}
        showIndicatorsToolbar={true}
        showSMCByDefault={true}
        showVolumeByDefault={true}
        showEMAsByDefault={true}
      />
    </div>
  );
};

export default CandlestickChart;
