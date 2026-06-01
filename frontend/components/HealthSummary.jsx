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
      text: 'Optimal',
      subtext: 'Parameters nominal',
      color: 'text-emerald-500',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30'
    },
    warning: {
      text: 'Warning',
      subtext: 'Deviations detected',
      color: 'text-amber-500',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30'
    },
    critical: {
      text: 'Critical',
      subtext: 'Immediate action required',
      color: 'text-rose-500',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30'
    },
    unknown: {
      text: 'Standby',
      subtext: 'Awaiting telemetry',
      color: 'text-slate-400',
      bg: 'bg-slate-100',
      border: 'border-slate-200'
    }
  };

  const current = statusConfig[status];

  return (
    <div className="flex flex-col h-full">
      {/* Header / Main Status */}
      <div className={`flex items-start gap-4 mb-8 p-4 border sharp-edge ${current.bg} ${current.border}`}>
        <div className={`w-12 h-12 flex items-center justify-center border sharp-edge bg-white/50 backdrop-blur-sm ${current.border} ${current.color}`}>
          <StatusIcon size={24} />
        </div>
        <div>
          <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">System Status</div>
          <div className={`text-2xl font-black uppercase tracking-tight ${current.color}`}>
            {current.text}
          </div>
          <div className="text-xs font-mono text-slate-600 mt-1 uppercase">
            &gt; {current.subtext}
          </div>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="flex-1 space-y-3">
        <div className="text-xs font-bold text-slate-900 uppercase tracking-widest border-b border-slate-200 pb-2 mb-4">Diagnostics Log</div>
        {recommendations.length === 0 && (
          <div className="text-sm font-mono text-slate-400 uppercase">No active logs.</div>
        )}
        {recommendations.map((rec, index) => {
          const RecIcon = rec.icon;
          const typeColor = rec.type === 'healthy' ? 'text-emerald-500' : rec.type === 'warning' ? 'text-amber-500' : 'text-rose-500';
          const typeBg = rec.type === 'healthy' ? 'bg-emerald-50' : rec.type === 'warning' ? 'bg-amber-50' : 'bg-rose-50';
          const typeBorder = rec.type === 'healthy' ? 'border-emerald-200' : rec.type === 'warning' ? 'border-amber-200' : 'border-rose-200';
          
          return (
            <div key={index} className={`flex items-start gap-3 p-3 border sharp-edge ${typeBg} ${typeBorder}`}>
              <RecIcon size={16} className={`mt-0.5 shrink-0 ${typeColor}`} />
              <span className="text-sm text-slate-700 font-medium leading-snug">{rec.text}</span>
            </div>
          );
        })}
      </div>

      {/* Footer / Timestamp */}
      {data && (
        <div className="mt-8 pt-4 border-t border-slate-200 flex justify-between items-center text-[10px] font-mono text-slate-400 uppercase">
          <span>Sys.Time:</span>
          <span>{new Date().toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}
