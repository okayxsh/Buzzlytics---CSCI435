import { useEffect, useState, useRef } from 'react';
import {
  Bug,
  Activity,
  Flower2,
  AlertTriangle,
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
      key: 'wasps',
      label: 'Wasps',
      icon: ShieldAlert,
      format: (v) => Math.round(v).toLocaleString(),
      getColor: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        return ratio > 5 ? 'critical' : ratio > 1 ? 'warning' : 'healthy';
      },
      getTrend: (v, d) => {
        const ratio = d.total_bees ? (v / d.total_bees) * 100 : 0;
        if (ratio > 5) return { dir: 'down', text: 'Threat' };
        if (ratio > 1) return { dir: 'neutral', text: 'Present' };
        return { dir: 'up', text: 'Clear' };
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
    healthy: { top: 'before:bg-forest-500', iconBg: 'bg-forest-50', iconColor: 'text-forest-600', barBg: 'bg-forest-500' },
    warning: { top: 'before:bg-honey-400', iconBg: 'bg-honey-50', iconColor: 'text-honey-600', barBg: 'bg-honey-400' },
    critical: { top: 'before:bg-clay', iconBg: 'bg-[#F6E6DF]', iconColor: 'text-clay', barBg: 'bg-clay' },
    neutral: { top: 'before:bg-line-strong', iconBg: 'bg-sand', iconColor: 'text-ink-soft', barBg: 'bg-forest-500' },
  };

  const trendStyles = {
    up: { bg: 'bg-forest-50', text: 'text-forest-700', border: 'border-forest-200' },
    down: { bg: 'bg-[#F6E6DF]', text: 'text-clay', border: 'border-[#E7C5B7]' },
    neutral: { bg: 'bg-sand', text: 'text-ink-soft', border: 'border-line-strong' },
  };

  if (!data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-2xl border border-line bg-cream p-6 opacity-60">
            <div className="mb-5 flex items-center justify-between">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sand">
                <Bug size={18} className="text-ink-faint" />
              </div>
            </div>
            <div className="data-label mb-1.5">Awaiting data</div>
            <div className="font-display text-3xl text-line-strong">—</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map(
        ({ key, label, icon: Icon, format, getColor, getTrend, isHealthScore }) => {
          const value = animatedValues[key] ?? 0;
          const status = getColor(data[key] ?? 0, data);
          const style = colorStyles[status];
          const trend = getTrend(data[key] ?? 0, data);
          const trStyle = trend ? trendStyles[trend.dir] : null;

          return (
            <div
              key={key}
              className={`group relative overflow-hidden rounded-2xl border border-line bg-cream p-6 shadow-soft transition-all duration-300 hover:-translate-y-1 hover:shadow-lift before:absolute before:inset-x-0 before:top-0 before:h-1 ${style.top} before:content-['']`}
            >
              <div className="mb-5 flex items-center justify-between">
                <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${style.iconBg} ${style.iconColor}`}>
                  <Icon size={20} />
                </div>
                {trend && (
                  <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${trStyle.bg} ${trStyle.text} ${trStyle.border}`}>
                    {trend.text}
                  </span>
                )}
              </div>
              <div className="data-label mb-1.5">{label}</div>
              <div className="font-display text-3xl font-semibold tabular text-ink">
                {format(value)}
              </div>
              {isHealthScore && (
                <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-sand">
                  <div
                    className={`h-full rounded-full ${style.barBg} transition-all duration-500 ease-out`}
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
