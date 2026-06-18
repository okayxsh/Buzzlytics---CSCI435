import { useMemo } from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle, Info } from 'lucide-react';

export default function HealthSummary({ data }) {
  const { status, recommendations, statusIcon: StatusIcon } = useMemo(() => {
    if (!data) {
      return {
        status: 'unknown',
        recommendations: [],
        statusIcon: Info,
      };
    }

    const score = data.health_score ?? 0;
    const infectionRate = data.infection_rate ?? 0;
    const deadRatio = data.total_bees ? (data.dead_bees ?? 0) / data.total_bees * 100 : 0;
    const pollenRatio = data.total_bees ? (data.pollen_bees ?? 0) / data.total_bees * 100 : 0;
    const activityRate = data.activity_rate ?? 0;

    let currentStatus = 'healthy';
    const recs = [];

    if (score < 40 || infectionRate > 15 || deadRatio > 10) {
      currentStatus = 'critical';
    } else if (score < 70 || infectionRate > 5 || deadRatio > 5 || activityRate < 30) {
      currentStatus = 'warning';
    }

    if (infectionRate > 15) {
      recs.push({
        type: 'critical',
        icon: AlertOctagon,
        text: 'High varroa mite infestation detected. Consider mite treatment immediately.',
      });
    } else if (infectionRate > 5) {
      recs.push({
        type: 'warning',
        icon: AlertTriangle,
        text: 'Moderate varroa mite levels observed. Monitor closely and prepare treatment if levels rise.',
      });
    }

    if (deadRatio > 10) {
      recs.push({
        type: 'critical',
        icon: AlertOctagon,
        text: 'Elevated dead bee count. Inspect hive for disease or pesticide exposure.',
      });
    } else if (deadRatio > 5) {
      recs.push({
        type: 'warning',
        icon: AlertTriangle,
        text: 'Slightly elevated dead bee count. Continue monitoring for changes.',
      });
    }

    if (pollenRatio > 10) {
      recs.push({
        type: 'healthy',
        icon: CheckCircle,
        text: 'Good foraging activity observed.',
      });
    }

    if (activityRate < 30) {
      recs.push({
        type: 'warning',
        icon: AlertTriangle,
        text: 'Low activity levels. Monitor for potential queen issues.',
      });
    }

    if (recs.length === 0) {
      recs.push({
        type: 'healthy',
        icon: CheckCircle,
        text: 'Hive appears healthy with normal activity levels.',
      });
    }

    const icon = currentStatus === 'healthy'
      ? ShieldCheck
      : currentStatus === 'warning'
        ? AlertTriangle
        : AlertOctagon;

    return {
      status: currentStatus,
      recommendations: recs,
      statusIcon: icon,
    };
  }, [data]);

  const statusConfig = {
    healthy: {
      text: 'Healthy',
      subtext: 'The colony looks strong',
      color: 'text-forest-700',
      bg: 'bg-forest-50',
      border: 'border-forest-200',
    },
    warning: {
      text: 'Worth a look',
      subtext: 'A few readings are drifting',
      color: 'text-honey-600',
      bg: 'bg-honey-50',
      border: 'border-honey-200',
    },
    critical: {
      text: 'Needs attention',
      subtext: 'Act soon to avoid loss',
      color: 'text-clay',
      bg: 'bg-[#F6E6DF]',
      border: 'border-[#E7C5B7]',
    },
    unknown: {
      text: 'Standing by',
      subtext: 'Waiting for the first reading',
      color: 'text-ink-faint',
      bg: 'bg-sand',
      border: 'border-line',
    },
  };

  const current = statusConfig[status];

  return (
    <div className="flex h-full flex-col">
      {/* Main status */}
      <div className={`mb-7 flex items-start gap-4 rounded-2xl border p-5 ${current.bg} ${current.border}`}>
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-cream/70 ${current.color}`}>
          <StatusIcon size={24} />
        </div>
        <div>
          <div className="data-label mb-0.5">Overall status</div>
          <div className={`font-display text-2xl font-semibold ${current.color}`}>
            {current.text}
          </div>
          <div className="mt-0.5 text-sm text-ink-soft">{current.subtext}</div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="flex-1 space-y-3">
        <div className="mb-3 border-b border-line pb-2 text-sm font-semibold text-ink">What we noticed</div>
        {recommendations.length === 0 && (
          <div className="text-sm text-ink-faint">No notes yet.</div>
        )}
        {recommendations.map((rec, index) => {
          const RecIcon = rec.icon;
          const typeColor = rec.type === 'healthy' ? 'text-forest-600' : rec.type === 'warning' ? 'text-honey-600' : 'text-clay';
          const typeBg = rec.type === 'healthy' ? 'bg-forest-50' : rec.type === 'warning' ? 'bg-honey-50' : 'bg-[#F6E6DF]';
          const typeBorder = rec.type === 'healthy' ? 'border-forest-200' : rec.type === 'warning' ? 'border-honey-200' : 'border-[#E7C5B7]';

          return (
            <div key={index} className={`flex items-start gap-3 rounded-xl border p-3.5 ${typeBg} ${typeBorder}`}>
              <RecIcon size={16} className={`mt-0.5 shrink-0 ${typeColor}`} />
              <span className="text-sm font-medium leading-snug text-ink-soft">{rec.text}</span>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      {data && (
        <div className="mt-7 flex items-center justify-between border-t border-line pt-4 text-xs text-ink-faint">
          <span className="font-medium">Last reading</span>
          <span className="tabular">{new Date().toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}
