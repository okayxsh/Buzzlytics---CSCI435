import { motion } from 'framer-motion';

/**
 * Ambient meadow backdrop: faint sage honeycomb weave, warm light blooms,
 * and a few softly drifting hexagons. Decorative only.
 */
export default function HexField({ blooms = true }) {
  const hexes = [
    { size: 110, top: '14%', left: '6%', delay: 0, anim: 'animate-drift' },
    { size: 70, top: '68%', left: '12%', delay: 1.4, anim: 'animate-drift-slow' },
    { size: 150, top: '18%', left: '84%', delay: 0.7, anim: 'animate-drift-slow' },
    { size: 58, top: '72%', left: '80%', delay: 2.1, anim: 'animate-drift' },
  ];

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      {/* honeycomb weave */}
      <div className="absolute inset-0 comb-tex opacity-70 mask-soft" />

      {/* warm light blooms */}
      {blooms && (
        <>
          <div className="absolute -left-32 top-0 h-[460px] w-[460px] rounded-full bg-honey-200/40 blur-[120px]" />
          <div className="absolute right-0 top-1/3 h-[420px] w-[420px] rounded-full bg-forest-200/40 blur-[130px]" />
        </>
      )}

      {/* drifting hexagons */}
      {hexes.map((h, i) => (
        <motion.svg
          key={i}
          className={h.anim}
          style={{ position: 'absolute', top: h.top, left: h.left, animationDelay: `${h.delay}s` }}
          width={h.size}
          height={h.size}
          viewBox="0 0 100 100"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ duration: 1.4, delay: h.delay * 0.3 }}
        >
          <polygon
            points="50,4 92,28 92,72 50,96 8,72 8,28"
            fill="#2C7048"
            fillOpacity="0.04"
            stroke="#2C7048"
            strokeOpacity="0.16"
            strokeWidth="1.4"
            strokeLinejoin="round"
          />
        </motion.svg>
      ))}
    </div>
  );
}
