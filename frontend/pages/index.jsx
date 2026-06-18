import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Flower2, Bug, ShieldAlert, Activity, Radio,
  Sparkles, ScanSearch, Route, LineChart, ArrowRight,
  Cpu, Camera, HeartPulse, Crosshair, Leaf,
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

const CLASSES = [
  { icon: Activity, name: 'Bee', tone: 'text-forest-600', chip: 'bg-forest-50 border-forest-200', dot: 'bg-forest-500', desc: 'Healthy forager bees crawling and flying at the entrance — the baseline of a thriving colony.' },
  { icon: Flower2, name: 'Pollen-laden', tone: 'text-honey-600', chip: 'bg-honey-50 border-honey-200', dot: 'bg-honey-400', desc: 'Returning bees carrying pollen loads, a direct read on foraging success.' },
  { icon: ShieldAlert, name: 'Varroa-hit', tone: 'text-amberwarn', chip: 'bg-honey-50 border-honey-200', dot: 'bg-amberwarn', desc: 'Bees showing mite infestation — the single biggest driver of colony collapse.' },
  { icon: Bug, name: 'Wasp', tone: 'text-clay', chip: 'bg-[#F6E6DF] border-[#E7C5B7]', dot: 'bg-clay', desc: 'Wasps at the entrance — a robbing/predation threat to the colony.' },
];

const PIPELINE = [
  { icon: Sparkles, step: '01', name: 'Clarify the frame', tech: 'CLAHE · denoise', desc: 'Adaptive histogram equalization and non-local-means denoising rescue detail from the harsh, shifting light of a hive entrance.' },
  { icon: ScanSearch, step: '02', name: 'Find every bee', tech: 'YOLOv8', desc: 'A fine-tuned detection network locates each bee and sorts it into one of four health states, frame after frame.' },
  { icon: Route, step: '03', name: 'Follow them', tech: 'ByteTrack', desc: 'Persistent tracking gives every bee a stable identity, so counts stay honest and movement trails stay coherent.' },
  { icon: LineChart, step: '04', name: 'Read the colony', tech: 'Health score', desc: 'Rates, ratios and trends fold into one clinical score with plain-language guidance you can act on.' },
];

const FEATURES = [
  { icon: Camera, title: 'Recorded or live', body: 'Upload a clip for a full report, or open a webcam for instant annotated streaming over WebSockets.' },
  { icon: Crosshair, title: 'Bee-by-bee detail', body: 'Color-coded boxes and motion trails drawn on every frame of the output video.' },
  { icon: HeartPulse, title: 'Clinical scoring', body: 'A 0–100 health index with Healthy / Watch / Critical bands and threshold alerts.' },
  { icon: Activity, title: 'Live metrics', body: 'Counts, activity rate and infection rate update continuously as the feed runs.' },
  { icon: Cpu, title: 'Runs anywhere', body: 'GPU-accelerated when you have one, perfectly happy on a plain CPU. No cloud required.' },
  { icon: ShieldAlert, title: 'Early warning', body: 'Varroa and mortality thresholds surface trouble weeks ahead of a manual inspection.' },
];

const READOUT = [
  { k: 'Active', v: 184, tone: 'text-forest-600' },
  { k: 'Pollen', v: 47, tone: 'text-honey-600' },
  { k: 'Varroa', v: 6, tone: 'text-amberwarn' },
  { k: 'Wasp', v: 2, tone: 'text-clay' },
];

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <Navbar />

      {/* ---------- HERO ---------- */}
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
              A computer-vision project · CSCI 435
            </motion.div>

            <h1 className="mt-7 font-display text-[3.1rem] font-medium leading-[1.02] tracking-tight text-ink sm:text-6xl lg:text-[4.4rem]">
              <motion.span
                className="block"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.05 }}
              >
                Listen to the
              </motion.span>
              <motion.span
                className="block italic text-forest-700"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.16 }}
              >
                hive’s pulse.
              </motion.span>
            </h1>

            <motion.p
              className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.7, delay: 0.3 }}
            >
              Buzzlytics watches the entrance of your hive and turns ordinary video into
              living colony-health diagnostics — counting, tracking and scoring every bee so
              you notice <span className="text-ink underline underline-honey decoration-honey-300">varroa, loss and decline</span> before the colony does.
            </motion.p>

            <motion.div
              className="mt-9 flex flex-wrap items-center gap-3"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.42 }}
            >
              <Link href="/analysis" className="btn-primary">
                Analyze a video <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/webcam" className="btn-soft">
                <Radio className="h-4 w-4" /> Open live feed
              </Link>
            </motion.div>

            <motion.div
              className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-ink-faint"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.55 }}
            >
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-forest-400" /> 4 bee classes</span>
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-honey-400" /> Real-time tracking</span>
              <span className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-clay" /> No cloud needed</span>
            </motion.div>
          </div>

          {/* soft health reading card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 22 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            {/* floating accent */}
            <div className="absolute -right-3 -top-5 z-10 hidden rotate-3 rounded-2xl border border-honey-200 bg-cream px-4 py-2.5 text-sm font-semibold text-honey-600 shadow-lift sm:block">
              Hive 07 · this morning
            </div>

            <div className="card overflow-hidden p-0">
              <div className="flex items-center justify-between border-b border-line bg-sand px-6 py-4">
                <span className="font-display text-lg font-semibold text-ink">Colony report</span>
                <span className="flex items-center gap-2 text-sm font-semibold text-forest-700">
                  <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" /> Live
                </span>
              </div>

              <div className="px-6 py-7">
                <div className="flex items-center gap-6">
                  {/* score ring */}
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
                    <div className="data-label">Overall health</div>
                    <div className="mt-1 font-display text-2xl font-semibold text-forest-700">Healthy</div>
                    <p className="mt-1.5 text-sm leading-snug text-ink-soft">
                      Strong foraging, mites well below the treatment line.
                    </p>
                  </div>
                </div>

                <div className="mt-7 grid grid-cols-4 overflow-hidden rounded-xl border border-line">
                  {READOUT.map((r, i) => (
                    <div key={r.k} className={`px-2 py-3.5 text-center ${i !== 0 ? 'border-l border-line' : ''} ${i % 2 ? 'bg-sand/60' : 'bg-cream'}`}>
                      <div className={`font-display text-2xl font-semibold tabular ${r.tone}`}>{r.v}</div>
                      <div className="mt-0.5 text-[11px] font-medium text-ink-faint">{r.k}</div>
                    </div>
                  ))}
                </div>

                <div className="mt-5 flex items-center justify-between text-sm text-ink-faint">
                  <span>Activity <span className="font-semibold text-ink-soft">71%</span></span>
                  <span>Infection <span className="font-semibold text-ink-soft">2.4%</span></span>
                  <span className="flex items-center gap-1.5 text-forest-600"><Camera className="h-3.5 w-3.5" /> recording</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ---------- CAPABILITIES ---------- */}
      <section id="capabilities" className="relative py-24">
        <div className="mx-auto max-w-[1240px] px-5 md:px-8">
          <Reveal className="max-w-2xl">
            <Eyebrow>What it sees</Eyebrow>
            <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
              Four kinds of bee, <span className="italic text-forest-700">one honest read</span> on the colony.
            </h2>
            <p className="mt-5 text-lg leading-relaxed text-ink-soft">
              Every bee crossing the entrance is sorted into one of four states. It is the
              <em> mix</em> of those states — not the raw count — that tells you how the hive is really doing.
            </p>
          </Reveal>

          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {CLASSES.map((c, i) => (
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

      {/* ---------- HOW IT WORKS ---------- */}
      <section id="how" className="relative overflow-hidden border-y border-line bg-sand py-24">
        <div className="absolute inset-0 comb-tex opacity-40" aria-hidden="true" />
        <div className="relative mx-auto max-w-[1240px] px-5 md:px-8">
          <Reveal>
            <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div className="max-w-xl">
                <Eyebrow>From frame to verdict</Eyebrow>
                <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
                  A short journey, <span className="italic text-forest-700">run on every frame.</span>
                </h2>
              </div>
              <p className="max-w-sm text-ink-soft">
                Four classic computer-vision stages, chained into one continuous loop that
                keeps watching as long as the footage rolls.
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

      {/* ---------- FEATURES ---------- */}
      <section className="relative py-24">
        <div className="mx-auto max-w-[1240px] px-5 md:px-8">
          <Reveal className="max-w-2xl">
            <Eyebrow>Built for the apiary</Eyebrow>
            <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
              Everything a keeper needs, <span className="italic text-forest-700">nothing they don’t.</span>
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

      {/* ---------- ABOUT ---------- */}
      <section id="about" className="relative overflow-hidden border-t border-line py-24">
        <div className="relative mx-auto grid max-w-[1240px] items-center gap-16 px-5 md:px-8 lg:grid-cols-2">
          <Reveal>
            <Eyebrow>Why we built it</Eyebrow>
            <h2 className="font-display text-4xl font-medium leading-tight text-ink md:text-[2.9rem]">
              Bees feed a third of our plates — <span className="italic text-forest-700">and we still check them by hand.</span>
            </h2>
            <div className="mt-6 space-y-5 text-lg leading-relaxed text-ink-soft">
              <p>
                Most keepers still diagnose hive health by cracking open boxes and counting
                bees by eye. It is slow, disruptive, and trouble often shows up only once it
                is too late to fix.
              </p>
              <p>
                Buzzlytics trades that guesswork for quiet, continuous observation. A camera at
                the entrance is enough: each frame is cleaned up, every bee is found and
                followed, and the whole scene is distilled into a single health score with
                clear next steps.
              </p>
            </div>
            <Link href="/analysis" className="btn-honey mt-9">
              See it on your footage <ArrowRight className="h-4 w-4" />
            </Link>
          </Reveal>

          <Reveal delay={0.15}>
            <div className="grid grid-cols-2 gap-5">
              {[
                { v: '4', l: 'Bee classes', s: 'Bee · Pollen · Varroa · Wasp', tone: 'text-forest-700' },
                { v: '0–100', l: 'Health index', s: 'A single clinical score', tone: 'text-honey-600' },
                { v: '~60', l: 'Frames / sec', s: 'When a GPU is available', tone: 'text-forest-700' },
                { v: '24/7', l: 'Watching', s: 'No manual inspection', tone: 'text-honey-600' },
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

      {/* ---------- CTA ---------- */}
      <section className="relative overflow-hidden px-5 pb-24">
        <Reveal>
          <div className="relative mx-auto max-w-[1240px] overflow-hidden rounded-3xl border border-forest-700 bg-forest-700 px-6 py-20 text-center shadow-lift md:px-8">
            <div className="absolute inset-0 comb-tex opacity-30" aria-hidden="true" />
            <div className="absolute -left-16 -top-16 h-64 w-64 rounded-full bg-forest-600/60 blur-3xl" />
            <div className="absolute -bottom-16 -right-10 h-64 w-64 rounded-full bg-honey-500/30 blur-3xl" />
            <div className="relative mx-auto max-w-2xl">
              <h2 className="font-display text-4xl font-medium leading-tight text-cream md:text-5xl">
                Point a camera at the hive.<br />
                <span className="italic text-honey-200">Let it do the watching.</span>
              </h2>
              <p className="mx-auto mt-6 max-w-lg text-lg leading-relaxed text-forest-100">
                Upload a clip or open a live feed and watch Buzzlytics annotate, track and
                score your colony in real time.
              </p>
              <div className="mt-10 flex flex-wrap justify-center gap-3">
                <Link href="/analysis" className="btn-honey">
                  Analyze a video <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/webcam"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-forest-300/40 bg-forest-600/40 px-7 py-3.5 text-sm font-semibold text-cream transition-all hover:bg-forest-600/70"
                >
                  <Radio className="h-4 w-4" /> Open live feed
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
