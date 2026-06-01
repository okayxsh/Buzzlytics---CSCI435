import { useEffect, useState, useRef } from 'react';
import {
  Bug,
  Activity,
  Flower2,
  AlertTriangle,
  Skull,
  Percent,
  ShieldAlert,
  Heart,
} from 'lucide-react';

export default function StatsPanel({ data }) {
  const [animatedValues, setAnimatedValues] = useState({});
  const animationRefs = useRef({});

  const metrics = [
    {
      key: 'total_bees',
      label: 'Total Bees',
      icon: Bug,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: () => 'neutral',
      getTrend: () => null,
    },
    {
      key: 'active_bees',
      label: 'Active Bees',
      icon: Activity,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: (v, d) => {
        const rate = d.total_bees ? (v / d.total_bees) * 100 : 0;
        return rate < 30 ? 'critical' : rate < 50 ? 'warning' : 'healthy';
      },
      getTrend: (v, d) => {
        const rate = d.total_bees ? (v / d.total_bees) * 100 : 0;
        if (rate >= 50) return { dir: 'up', text: 'Good' };
        if (rate >= 30) return { dir: 'neutral', text: 'Fair' };
        return { dir: 'down', text: 'Low' };
      },
    },
    {
      key: 'pollen_bees',
      label: 'Pollen-Carrying',
      icon: Flower2,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        return ratio > 5 ? 'healthy' : 'warning';
      },
      getTrend: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        if (ratio > 10) return { dir: 'up', text: 'Strong' };
        if (ratio > 5) return { dir: 'neutral', text: 'Fair' };
        return { dir: 'down', text: 'Low' };
      },
    },
    {
      key: 'varroa_bees',
      label: 'Varroa-Infected',
      icon: AlertTriangle,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: (v, d) => {
        const rate = d.total_bees ? (v / d.total_bees) * 100 : 0;
        return rate > 15 ? 'critical' : rate > 5 ? 'warning' : 'healthy';
      },
      getTrend: (v, d) => {
        const rate = d.total_bees ? (v / d.total_bees) * 100 : 0;
        if (rate > 15) return { dir: 'down', text: 'High' };
        if (rate > 5) return { dir: 'neutral', text: 'Moderate' };
        return { dir: 'up', text: 'Low' };
      },
    },
    {
      key: 'dead_bees',
      label: 'Dead Bees',
      icon: Skull,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        return ratio > 10 ? 'critical' : ratio > 5 ? 'warning' : 'healthy';
      },
      getTrend: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        if (ratio > 10) return { dir: 'down', text: 'High' };
        if (ratio > 5) return { dir: 'neutral', text: 'Moderate' };
        return { dir: 'up', text: 'Low' };
      },
    },
    {
      key: 'activity_rate',
      label: 'Activity Rate',
      icon: Percent,
      format: (v) => `${v.toFixed(1)}%`,
      getColor: (v) => (v < 30 ? 'critical' : v < 50 ? 'warning' : 'healthy'),
      getTrend: (v) => {
        if (v >= 60) return { dir: 'up', text: 'High' };
        if (v >= 30) return { dir: 'neutral', text: 'Normal' };
        return { dir: 'down', text: 'Low' };
      },
    },
    {
      key: 'infection_rate',
      label: 'Infection Rate',
      icon: ShieldAlert,
      format: (v) => `${v.toFixed(1)}%`,
      getColor: (v) => (v > 15 ? 'critical' : v > 5 ? 'warning' : 'healthy'),
      getTrend: (v) => {
        if (v > 15) return { dir: 'down', text: 'Severe' };
        if (v > 5) return { dir: 'neutral', text: 'Moderate' };
        return { dir: 'up', text: 'Low' };
      },
    },
    {
      key: 'health_score',
      label: 'Health Score',
      icon: Heart,
      format: (v) => Math.round(v),
      getColor: (v) => (v < 40 ? 'critical' : v < 70 ? 'warning' : 'healthy'),
      getTrend: (v) => {
        if (v >= 80) return { dir: 'up', text: 'Excellent' };
        if (v >= 60) return { dir: 'neutral', text: 'Fair' };
        return { dir: 'down', text: 'Poor' };
      },
      isHealthScore: true,
    },
  ];

  // Animate values
  useEffect(() => {
    if (!data) return;

    metrics.forEach(({ key }) => {
      const target = data[key] ?? 0;
      const current = animatedValues[key] || 0;

      if (Math.abs(target - current) < 0.5) {
        setAnimatedValues((prev) => ({ ...prev, [key]: target }));
        return;
      }

      if (animationRefs.current[key]) {
        cancelAnimationFrame(animationRefs.current[key]);
      }

      const startValue = current;
      const diff = target - startValue;
      const duration = 600;
      const startTime = performance.now();

      const animate = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = startValue + diff * eased;

        setAnimatedValues((prev) => ({ ...prev, [key]: value }));

        if (progress < 1) {
          animationRefs.current[key] = requestAnimationFrame(animate);
        }
      };

      animationRefs.current[key] = requestAnimationFrame(animate);
    });

    return () => {
      Object.values(animationRefs.current).forEach((id) => {
        if (id) cancelAnimationFrame(id);
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const colorStyles = {
    healthy: { borderTop: 'border-t-emerald-500', iconBg: 'bg-emerald-500/10', iconColor: 'text-emerald-500', barBg: 'bg-emerald-500' },
    warning: { borderTop: 'border-t-amber-500', iconBg: 'bg-amber-500/10', iconColor: 'text-amber-500', barBg: 'bg-amber-500' },
    critical: { borderTop: 'border-t-rose-500', iconBg: 'bg-rose-500/10', iconColor: 'text-rose-500', barBg: 'bg-rose-500' },
    neutral: { borderTop: 'border-t-slate-400', iconBg: 'bg-slate-200', iconColor: 'text-slate-500', barBg: 'bg-slate-400' },
  };

  const trendStyles = {
    up: { bg: 'bg-emerald-500/10', text: 'text-emerald-600', border: 'border-emerald-500/20' },
    down: { bg: 'bg-rose-500/10', text: 'text-rose-600', border: 'border-rose-500/20' },
    neutral: { bg: 'bg-slate-200', text: 'text-slate-600', border: 'border-slate-300' },
  };

  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-slate-50 border border-slate-200 p-6 sharp-edge border-t-2 border-t-slate-200 opacity-50">
            <div className="flex justify-between items-center mb-4">
              <div className="w-10 h-10 bg-slate-200 flex items-center justify-center sharp-edge">
                <Bug size={18} className="text-slate-400" />
              </div>
            </div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">--</div>
            <div className="text-3xl font-black text-slate-300">--</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map(
        ({ key, label, icon: Icon, format, getColor, getTrend, isHealthScore }) => {
          const value = animatedValues[key] ?? 0;
          const status = getColor(data[key] ?? 0, data);
          const style = colorStyles[status];
          const trend = getTrend(data[key] ?? 0, data);
          const trStyle = trend ? trendStyles[trend.dir] : null;

          return (
            <div key={key} className={`bg-white border border-slate-200 p-6 sharp-edge border-t-2 ${style.borderTop} hover:-translate-y-1 transition-transform duration-300 shadow-sm hover:shadow-md`}>
              <div className="flex justify-between items-center mb-6">
                <div className={`w-10 h-10 flex items-center justify-center sharp-edge ${style.iconBg} ${style.iconColor}`}>
                  <Icon size={20} />
                </div>
                {trend && (
                  <span className={`px-2 py-1 text-[10px] font-black uppercase tracking-wider border sharp-edge ${trStyle.bg} ${trStyle.text} ${trStyle.border}`}>
                    {trend.text}
                  </span>
                )}
              </div>
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">
                {label}
              </div>
              <div className="text-3xl font-black text-slate-900 tracking-tight tabular-nums">
                {format(value)}
              </div>
              {isHealthScore && (
                <div className="w-full h-1 bg-slate-100 mt-4 sharp-edge overflow-hidden">
                  <div
                    className={`h-full ${style.barBg} transition-all duration-500 ease-out`}
                    style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
                  />
                </div>
              )}
            </div>
          );
        }
      )}
    </div>
  );
}
