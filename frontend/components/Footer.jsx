import Link from 'next/link';
import { Github, ArrowUpRight } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-line bg-sand">
      <div className="absolute inset-0 comb-tex opacity-50" aria-hidden="true" />
      <div className="relative mx-auto max-w-[1240px] px-5 py-16 md:px-8">
        <div className="grid gap-12 md:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-3">
              <svg viewBox="0 0 100 100" className="h-9 w-9">
                <polygon points="50,6 88,28 88,72 50,94 12,72 12,28" fill="#FCF3E1" stroke="#2C7048" strokeWidth="5" strokeLinejoin="round" />
                <circle cx="50" cy="50" r="13" fill="#D98A1F" />
                <circle cx="50" cy="50" r="5" fill="#1E5436" />
              </svg>
              <div className="font-display text-2xl font-semibold text-ink">Buzzlytics</div>
            </div>
            <p className="mt-5 max-w-sm leading-relaxed text-ink-soft">
              Computer vision that watches the entrance of your hive and turns everyday
              video into honest, early colony-health signals — so trouble is caught long
              before the inspection that would have missed it.
            </p>
            <div className="mt-6 pill text-forest-700">
              <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" />
              All systems healthy
            </div>
          </div>

          <div>
            <div className="data-label mb-5">Platform</div>
            <ul className="space-y-3 text-sm text-ink-soft">
              <li><Link href="/analysis" className="transition-colors hover:text-forest-700">Video Analysis</Link></li>
              <li><Link href="/webcam" className="transition-colors hover:text-forest-700">Live Webcam Feed</Link></li>
              <li><Link href="/#capabilities" className="transition-colors hover:text-forest-700">Capabilities</Link></li>
              <li><Link href="/#how" className="transition-colors hover:text-forest-700">How It Works</Link></li>
            </ul>
          </div>

          <div>
            <div className="data-label mb-5">Project</div>
            <ul className="space-y-3 text-sm text-ink-soft">
              <li><Link href="/#about" className="transition-colors hover:text-forest-700">About</Link></li>
              <li>
                <a href="https://docs.ultralytics.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 transition-colors hover:text-forest-700">
                  YOLOv8 Docs <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </li>
              <li>
                <a href="#" className="inline-flex items-center gap-1.5 transition-colors hover:text-forest-700">
                  <Github className="h-3.5 w-3.5" /> Repository
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-14 flex flex-col gap-3 border-t border-line-strong pt-6 text-sm text-ink-faint md:flex-row md:items-center md:justify-between">
          <span>© 2026 Buzzlytics — CSCI 435</span>
          <span className="font-medium">OpenCV · YOLOv8 · ByteTrack · FastAPI · Next.js</span>
        </div>
      </div>
    </footer>
  );
}
