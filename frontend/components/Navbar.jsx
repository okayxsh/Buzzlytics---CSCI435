import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Video, Radio, Menu, X } from 'lucide-react';

const LINKS = [
  { href: '/#capabilities', label: 'Capabilities' },
  { href: '/#how', label: 'How It Works' },
  { href: '/#about', label: 'About' },
];

const APPS = [
  { href: '/analysis', label: 'Analysis', icon: Video },
  { href: '/webcam', label: 'Live Feed', icon: Radio },
];

function Mark() {
  return (
    <span className="relative flex h-9 w-9 items-center justify-center">
      <svg viewBox="0 0 100 100" className="h-9 w-9">
        <polygon
          points="50,6 88,28 88,72 50,94 12,72 12,28"
          fill="#FCF3E1"
          stroke="#2C7048"
          strokeWidth="5"
          strokeLinejoin="round"
        />
        <circle cx="50" cy="50" r="13" fill="#D98A1F" />
        <circle cx="50" cy="50" r="5" fill="#1E5436" />
      </svg>
    </span>
  );
}

export default function Navbar() {
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'border-b border-line bg-paper/85 backdrop-blur-md'
          : 'border-b border-transparent'
      }`}
    >
      <div className="mx-auto flex h-[72px] max-w-[1240px] items-center justify-between px-5 md:px-8">
        <Link href="/" className="group flex items-center gap-3">
          <Mark />
          <div className="leading-tight">
            <div className="font-display text-[1.35rem] font-semibold text-ink">
              Buzzlytics
            </div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-ink-faint">
              Hive Health
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-9 lg:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-ink-soft transition-colors hover:text-forest-700"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {APPS.map(({ href, label, icon: Icon }) => {
            const active = router.pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-all ${
                  active
                    ? 'bg-forest-700 text-cream shadow-soft'
                    : 'border border-line-strong text-ink-soft hover:border-forest-300 hover:text-forest-700 hover:bg-forest-50'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </div>

        <button
          className="flex h-10 w-10 items-center justify-center rounded-full border border-line-strong text-ink-soft md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-line bg-paper px-5 py-5 md:hidden">
          <div className="flex flex-col gap-1">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="rounded-xl px-2 py-3 text-sm font-medium text-ink-soft hover:bg-forest-50"
              >
                {l.label}
              </Link>
            ))}
            <div className="mt-3 flex gap-2">
              {APPS.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-line-strong px-4 py-3 text-sm font-semibold text-ink-soft"
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
