import { Info } from 'lucide-react';

const CLASSES = [
  { name: 'Bee', color: 'rgb(0,200,0)' },
  { name: 'Pollen', color: 'rgb(255,220,0)' },
  { name: 'Varroa', color: 'rgb(220,0,0)' },
];

export default function ClassLegend({ showReliabilityNote = false }) {
  return (
    <div className="rounded-xl border border-line bg-sand px-4 py-3">
      <div className="flex flex-wrap items-center gap-4">
        <span className="data-label shrink-0 text-ink-soft">Detection classes</span>
        {CLASSES.map(({ name, color }) => (
          <span key={name} className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 shrink-0 rounded-sm"
              style={{ background: color }}
            />
            <span className="text-sm font-medium text-ink-soft">{name}</span>
          </span>
        ))}
      </div>
      {showReliabilityNote && (
        <div className="mt-3 flex items-start gap-2 border-t border-line pt-3 text-xs leading-relaxed text-ink-faint">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-honey-600" />
          Pollen works best on bright entrance-camera footage similar to the training data.
          Varroa is demonstrated separately with close-up bee crops.
        </div>
      )}
    </div>
  );
}
