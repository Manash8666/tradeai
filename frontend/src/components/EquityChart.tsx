import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';

interface EquityDataPoint {
  timestamp: string;
  equity: number;
}

interface EquityChartProps {
  data: EquityDataPoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const formattedDate = new Date(label).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });

    return (
      <div className="bg-ocean-800/90 border border-ocean-600 p-4 rounded-xl shadow-xl backdrop-blur-md">
        <p className="text-ocean-300 text-sm mb-1">{formattedDate}</p>
        <p className="text-gold-400 font-mono text-lg m-0">
          ₹ {payload[0].value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
      </div>
    );
  }
  return null;
};

export function EquityChart({ data }: EquityChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-ocean-400 font-mono text-sm">
        [ Waiting for Backtest Data ]
      </div>
    );
  }

  // Calculate min/max for tighter Y-Axis scaling
  const minEquity = Math.min(...data.map(d => d.equity)) * 0.999;
  const maxEquity = Math.max(...data.map(d => d.equity)) * 1.001;

  return (
    <div className="h-72 w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
          
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(val) => {
              const date = new Date(val);
              return `${date.getDate()} ${date.toLocaleString('default', { month: 'short' })}`;
            }}
            stroke="#64748B"
            tick={{ fill: '#64748B', fontSize: 12 }}
            tickMargin={10}
            axisLine={false}
          />
          
          <YAxis 
            domain={[minEquity, maxEquity]}
            tickFormatter={(val) => `₹${(val/1000).toFixed(0)}k`}
            stroke="#64748B"
            tick={{ fill: '#64748B', fontSize: 12 }}
            width={60}
            axisLine={false}
            tickLine={false}
          />
          
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#38BDF8', strokeWidth: 1, strokeDasharray: '4 4' }} />
          
          <ReferenceArea 
            x1={data[Math.floor(data.length * 0.2)]?.timestamp} 
            x2={data[Math.floor(data.length * 0.25)]?.timestamp} 
            strokeOpacity={0.3} 
            fill="#EF4444" 
            fillOpacity={0.1} 
          />
          <ReferenceArea 
            x1={data[Math.floor(data.length * 0.7)]?.timestamp} 
            x2={data[Math.floor(data.length * 0.73)]?.timestamp} 
            strokeOpacity={0.3} 
            fill="#F59E0B" 
            fillOpacity={0.15} 
          />
          <Line 
            type="monotone" 
            dataKey="equity" 
            stroke="#F59E0B" // gold-500
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6, fill: '#F59E0B', stroke: '#020617', strokeWidth: 2 }}
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
