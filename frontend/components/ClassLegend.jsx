const CLASSES = [
  { name: 'Bee', color: 'rgb(0,200,0)' },
  { name: 'Pollen', color: 'rgb(255,220,0)' },
  { name: 'Varroa', color: 'rgb(220,0,0)' },
  { name: 'Wasp', color: 'rgb(255,140,0)' },
];

export default function ClassLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-xl border border-line bg-sand px-4 py-3">
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
  );
}
