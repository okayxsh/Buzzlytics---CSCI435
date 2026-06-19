import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Activity } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="rounded-xl border border-line bg-cream px-3 py-2 shadow-lift">
      <div className="mb-1 text-xs font-medium text-ink-faint">Frame {label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-sm font-semibold text-ink">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          {entry.name === 'activity_ratio'
            ? `Activity: ${(entry.value * 100).toFixed(1)}%`
            : `Bees: ${entry.value}`}
        </div>
      ))}
    </div>
  );
};

export default function ActivityTimeline({ data, metric = 'activity_ratio' }) {
  const hasData = Array.isArray(data) && data.length > 0;

  if (!hasData) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-line bg-sand/40 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cream shadow-soft">
          <Activity size={22} className="text-ink-faint" />
        </div>
        <div className="text-sm font-medium text-ink-soft">No timeline data yet</div>
        <div className="text-xs text-ink-faint">Process a video to see activity over frames</div>
      </div>
    );
  }

  const isActivityRatio = metric === 'activity_ratio';
  const areaColor = isActivityRatio ? '#3E8B5C' : '#E8A33D';
  const areaColorLight = isActivityRatio ? '#EEF4ED' : '#FCF3E1';
  const dataKey = isActivityRatio ? 'activity_ratio' : 'total_bees';
  const yTickFormatter = isActivityRatio
    ? (v) => `${(v * 100).toFixed(0)}%`
    : (v) => v.toLocaleString();

  return (
    <div className="rounded-2xl border border-line bg-cream p-6 shadow-soft">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="font-display text-base font-semibold text-ink">
            {isActivityRatio ? 'Activity Rate' : 'Bee Count'} Over Frames
          </div>
          <div className="mt-0.5 text-xs text-ink-faint">
            {data.length} frame{data.length !== 1 ? 's' : ''} analysed
          </div>
        </div>
        <div
          className="flex h-9 w-9 items-center justify-center rounded-xl"
          style={{ backgroundColor: areaColorLight }}
        >
          <Activity size={18} style={{ color: areaColor }} />
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={areaColor} stopOpacity={0.25} />
              <stop offset="95%" stopColor={areaColor} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#E6DCC4"
            vertical={false}
          />
          <XAxis
            dataKey="frame"
            tick={{ fontSize: 11, fill: '#8A8470' }}
            tickLine={false}
            axisLine={false}
            label={{ value: 'Frame', position: 'insideBottomRight', offset: -4, fontSize: 11, fill: '#8A8470' }}
          />
          <YAxis
            tickFormatter={yTickFormatter}
            tick={{ fontSize: 11, fill: '#8A8470' }}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            name={dataKey}
            stroke={areaColor}
            strokeWidth={2}
            fill={`url(#grad-${dataKey})`}
            dot={false}
            activeDot={{ r: 4, fill: areaColor, strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
