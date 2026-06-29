import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Activity,
  ArrowRight,
  Camera,
  Cpu,
  Crosshair,
  Flower2,
  HeartPulse,
  Leaf,
  LineChart,
  Route,
  ScanSearch,
  ShieldAlert,
  Sparkles,
  Video,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import HexField from '../components/HexField';

function Reveal({ children, delay = 0, className = '' }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 26 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-70px' }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function Eyebrow({ children }) {
  return (
    <div className="mb-4 inline-flex items-center gap-2.5">
      <Leaf className="h-4 w-4 text-forest-500" />
      <span className="eyebrow">{children}</span>
    </div>
  );
}

const SIGNALS = [
  {
    icon: Activity,
    name: 'Entrance bees',
    tone: 'text-forest-600',
    chip: 'bg-forest-50 border-forest-200',
    dot: 'bg-forest-500',
    desc: 'Counts and tracks bees moving through the hive entrance to estimate activity and traffic.',
  },
  {
    icon: Flower2,
    name: 'Pollen return',
    tone: 'text-honey-600',
    chip: 'bg-honey-50 border-honey-200',
    dot: 'bg-honey-400',
    desc: 'Flags pollen-carrying bees when the footage matches the entrance-camera training view.',
  },
  {
    icon: ShieldAlert,
    name: 'Varroa crop check',
    tone: 'text-amberwarn',
    chip: 'bg-honey-50 border-honey-200',
    dot: 'bg-amberwarn',
    desc: 'Uses a dedicated close-up detector for mite boxes, with the crop classifier kept as a fallback health check.',
  },
];

const PIPELINE = [
  {
    icon: Sparkles,
    step: '01',
    name: 'Clean the scene',
    tech: 'White balance + CLAHE',
    desc: 'Balances color and contrast so entrance footage is easier for the detector to read.',
  },
  {
    icon: ScanSearch,
    step: '02',
    name: 'Object detection',
    tech: 'Fine-tuned YOLOv8',
    desc: 'Locates bees and pollen-carrying bees in uploaded frames using weights trained for hive imagery.',
  },
  {
    icon: Route,
    step: '03',
    name: 'Object tracking',
    tech: 'ByteTrack IDs',
    desc: 'Assigns persistent IDs and counts bees across the video instead of treating each frame as isolated.',
  },
  {
    icon: LineChart,
    step: '04',
    name: 'Video + recognition',
    tech: 'Motion + Varroa model',
    desc: 'Runs frame-by-frame motion analysis and inspects close-up bee crops with the Varroa detector/classifier path.',
  },
];

const FEATURES = [
  { icon: Camera, title: 'Two upload paths', body: 'Analyze entrance videos or still frames without changing tools.' },
  { icon: Crosshair, title: 'Visible evidence', body: 'Annotated output shows bees, pollen labels, and close-up Varroa crop results without mixing the workflows.' },
  { icon: HeartPulse, title: 'Readable scoring', body: 'A 0-100 health score turns raw detections into a compact colony snapshot.' },
  { icon: Activity, title: 'Activity timeline', body: 'Video results include per-frame movement and bee-count trends for the report.' },
  { icon: Cpu, title: 'Local pipeline', body: 'FastAPI, OpenCV, and YOLO run locally with optional GPU acceleration.' },
  { icon: ShieldAlert, title: 'Close-up Varroa mode', body: 'A dedicated crop workflow keeps mite inspection separate from wide entrance footage.' },
];

const READOUT = [
  { k: 'Active', v: 184, tone: 'text-forest-600' },
  { k: 'Pollen', v: 47, tone: 'text-honey-600' },
  { k: 'Flags', v: 0, tone: 'text-amberwarn' },
];

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <Navbar />

      <section className="relative overflow-hidden pt-[72px]">
        <HexField />
        <div className="relative mx-auto grid max-w-[1240px] items-center gap-16 px-5 py-20 md:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:py-28">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="pill text-forest-700"
            >
              <span className="h-2 w-2 animate-pulse-soft rounded-full bg-honey-400" />
              Computer vision project - CSCI 435
            </motion.div>

            <h1 className="mt-7 font-display text-[3.1rem] font-medium leading-[1.02] tracking-tight text-ink sm:text-6xl lg:text-[4.4rem]">
              <motion.span
                className="block"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.05 }}
              >
                Read the hive
              </motion.span>
              <motion.span
                className="block italic text-forest-700"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.16 }}
              >
                frame by frame.
              </motion.span>
            </h1>

            <motion.p
              className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.7, delay: 0.3 }}
            >
              Buzzlytics turns hive entrance footage into a readable computer-vision report:
              bees are detected, pollen return is measured, movement is tracked, and close-up
              crops can be checked for <span className="text-ink underline underline-honey decoration-honey-300">Varroa risk</span>.
            </motion.p>

            <motion.div
              className="mt-9 flex flex-wrap items-center gap-3"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.42 }}
            >
              <Link href="/analysis" className="btn-primary">
                Analyze footage <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/analysis" className="btn-soft">
                <ScanSearch className="h-4 w-4" /> Inspect a crop
              </Link>
            </motion.div>

            <motion.div
              className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-ink-faint"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.55 }}
            >
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-forest-400" /> Video, image, crop</span>
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-honey-400" /> Four CV tasks</span>
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-clay" /> Local demo ready</span>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 22 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div className="absolute -right-3 -top-5 z-10 hidden rotate-3 rounded-2xl border border-honey-200 bg-cream px-4 py-2.5 text-sm font-semibold text-honey-600 shadow-lift sm:block">
              Demo clip
            </div>

            <div className="card overflow-hidden p-0">
              <div className="flex items-center justify-between border-b border-line bg-sand px-6 py-4">
                <span className="font-display text-lg font-semibold text-ink">Analysis report</span>
                <span className="flex items-center gap-2 text-sm font-semibold text-forest-700">
                  <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" /> Ready
                </span>
              </div>

              <div className="px-6 py-7">
                <div className="flex items-center gap-6">
                  <div className="relative h-28 w-28 shrink-0">
                    <svg viewBox="0 0 120 120" className="h-28 w-28 -rotate-90">
                      <circle cx="60" cy="60" r="52" fill="none" stroke="#EFE7D5" strokeWidth="12" />
                      <motion.circle
                        cx="60" cy="60" r="52" fill="none" stroke="#2C7048" strokeWidth="12"
                        strokeLinecap="round" strokeDasharray={2 * Math.PI * 52}
                        initial={{ strokeDashoffset: 2 * Math.PI * 52 }}
                        animate={{ strokeDashoffset: 2 * Math.PI * 52 * (1 - 0.87) }}
                        transition={{ duration: 1.3, delay: 0.7, ease: 'easeOut' }}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="font-display text-3xl font-semibold tabular text-ink">87</span>
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-faint">of 100</span>
                    </div>
                  </div>
                  <div>
                    <div className="data-label">Overall status</div>
                    <div className="mt-1 font-display text-2xl font-semibold text-forest-700">Healthy</div>
                    <p className="mt-1.5 text-sm leading-snug text-ink-soft">
                      Strong entrance activity with a clean close-up crop result.
                    </p>
                  </div>
                </div>

                <div className="mt-7 grid grid-cols-3 overflow-hidden rounded-xl border border-line">
                  {READOUT.map((r, i) => (
                    <div key={r.k} className={`px-2 py-3.5 text-center ${i !== 0 ? 'border-l border-line' : ''} ${i % 2 ? 'bg-sand/60' : 'bg-cream'}`}>
                      <div className={`font-display text-2xl font-semibold tabular ${r.tone}`}>{r.v}</div>
                      <div className="mt-0.5 text-[11px] font-medium text-ink-faint">{r.k}</div>
                    </div>
                  ))}
                </div>

                <div className="mt-5 flex items-center justify-between text-sm text-ink-faint">
                  <span>Activity <span className="font-semibold text-ink-soft">71%</span></span>
                  <span>Pollen <span className="font-semibold text-ink-soft">25.5%</span></span>
                  <span className="flex items-center gap-1.5 text-forest-600"><Video className="h-3.5 w-3.5" /> uploaded</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="capabilities" className="relative py-24">
        <div className="mx-auto max-w-[1240px] px-5 md:px-8">
          <Reveal className="max-w-2xl">
            <Eyebrow>What it reads</Eyebrow>
            <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
              Three visual signals, <span className="italic text-forest-700">one clearer story</span> about the hive.
            </h2>
            <p className="mt-5 text-lg leading-relaxed text-ink-soft">
              The system does not hide behind a single number. It shows the evidence:
              entrance traffic, pollen return, motion over time, and close-up Varroa inspection.
            </p>
          </Reveal>

          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {SIGNALS.map((c, i) => (
              <Reveal key={c.name} delay={i * 0.08}>
                <div className="card group h-full p-7 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-lift">
                  <div className={`inline-flex h-14 w-14 items-center justify-center rounded-2xl border ${c.chip}`}>
                    <c.icon className={`h-7 w-7 ${c.tone}`} />
                  </div>
                  <div className="mt-6 flex items-center gap-2.5">
                    <span className={`h-2.5 w-2.5 rounded-full ${c.dot}`} />
                    <h3 className="font-display text-xl font-semibold text-ink">{c.name}</h3>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-ink-soft">{c.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="how" className="relative overflow-hidden border-y border-line bg-sand py-24">
        <div className="absolute inset-0 comb-tex opacity-40" aria-hidden="true" />
        <div className="relative mx-auto max-w-[1240px] px-5 md:px-8">
          <Reveal>
            <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div className="max-w-xl">
                <Eyebrow>From frame to finding</Eyebrow>
                <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
                  A compact pipeline, <span className="italic text-forest-700">built for defence.</span>
                </h2>
              </div>
              <p className="max-w-sm text-ink-soft">
                The app demonstrates object detection, tracking, video processing, and Varroa recognition in one workflow.
              </p>
            </div>
          </Reveal>

          <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {PIPELINE.map((p, i) => (
              <Reveal key={p.name} delay={i * 0.1}>
                <div className="relative h-full">
                  {i < PIPELINE.length - 1 && (
                    <div className="absolute -right-3 top-12 hidden h-px w-6 bg-line-strong lg:block" />
                  )}
                  <div className="card h-full p-7">
                    <div className="flex items-center justify-between">
                      <span className="font-display text-5xl font-medium italic text-line-strong">{p.step}</span>
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-forest-700 text-cream">
                        <p.icon className="h-6 w-6" />
                      </div>
                    </div>
                    <h3 className="mt-6 font-display text-xl font-semibold text-ink">{p.name}</h3>
                    <span className="mt-2 inline-block rounded-full bg-forest-50 px-3 py-1 text-xs font-semibold text-forest-700">
                      {p.tech}
                    </span>
                    <p className="mt-4 text-sm leading-relaxed text-ink-soft">{p.desc}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="relative py-24">
        <div className="mx-auto max-w-[1240px] px-5 md:px-8">
          <Reveal className="max-w-2xl">
            <Eyebrow>Built for the demo</Eyebrow>
            <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
              Clear outputs, <span className="italic text-forest-700">without overclaiming the model.</span>
            </h2>
          </Reveal>

          <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <Reveal key={f.title} delay={(i % 3) * 0.08}>
                <div className="group flex h-full gap-5 rounded-2xl border border-line bg-cream p-6 transition-all duration-300 hover:border-forest-200 hover:shadow-soft">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-honey-50 text-honey-600 transition-colors group-hover:bg-honey-400 group-hover:text-ink">
                    <f.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-display text-lg font-semibold text-ink">{f.title}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{f.body}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="about" className="relative overflow-hidden border-t border-line py-24">
        <div className="relative mx-auto grid max-w-[1240px] items-center gap-16 px-5 md:px-8 lg:grid-cols-2">
          <Reveal>
            <Eyebrow>Why we built it</Eyebrow>
            <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
              Hive checks are visual, slow, and easy to misread.
            </h2>
            <div className="mt-6 space-y-5 text-lg leading-relaxed text-ink-soft">
              <p>
                Most keepers still diagnose colony health by opening boxes and judging activity by eye.
                It is useful, but disruptive, subjective, and hard to turn into repeatable evidence.
              </p>
              <p>
                Buzzlytics turns that inspection into a computer-vision workflow. A video or still frame
                is cleaned, bees are detected and tracked, pollen return is estimated, and close-up crops
                are checked separately for Varroa.
              </p>
            </div>
            <Link href="/analysis" className="btn-honey mt-9">
              See it on your footage <ArrowRight className="h-4 w-4" />
            </Link>
          </Reveal>

          <Reveal delay={0.15}>
            <div className="grid grid-cols-2 gap-5">
              {[
                { v: '3', l: 'Input modes', s: 'Video, image, close-up crop', tone: 'text-forest-700' },
                { v: '0-100', l: 'Health index', s: 'A compact colony score', tone: 'text-honey-600' },
                { v: '4+', l: 'CV tasks', s: 'Enhance, detect, track, analyze', tone: 'text-forest-700' },
                { v: '3', l: 'Model paths', s: 'Bee detector, mite detector, crop classifier', tone: 'text-honey-600' },
              ].map((s) => (
                <div key={s.l} className="card p-7">
                  <div className={`font-display text-4xl font-semibold tabular ${s.tone}`}>{s.v}</div>
                  <div className="mt-2 text-sm font-semibold text-ink">{s.l}</div>
                  <div className="mt-1 text-sm text-ink-faint">{s.s}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <section className="relative overflow-hidden px-5 pb-24">
        <Reveal>
          <div className="relative mx-auto max-w-[1240px] overflow-hidden rounded-3xl border border-forest-700 bg-forest-700 px-6 py-20 text-center shadow-lift md:px-8">
            <div className="absolute inset-0 comb-tex opacity-30" aria-hidden="true" />
            <div className="relative mx-auto max-w-2xl">
              <h2 className="font-display text-4xl font-medium leading-tight text-cream md:text-5xl">
                Bring a clean hive clip.<br />
                <span className="italic text-honey-200">Leave with visual evidence.</span>
              </h2>
              <p className="mx-auto mt-6 max-w-lg text-lg leading-relaxed text-forest-100">
                Upload entrance footage, inspect still frames, or run a close-up Varroa crop
                through the dedicated mite detector.
              </p>
              <div className="mt-10 flex flex-wrap justify-center gap-3">
                <Link href="/analysis" className="btn-honey">
                  Analyze footage <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/analysis"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-forest-300/40 bg-forest-600/40 px-7 py-3.5 text-sm font-semibold text-cream transition-all hover:bg-forest-600/70"
                >
                  <ScanSearch className="h-4 w-4" /> Inspect a crop
                </Link>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <Footer />
    </div>
  );
}
