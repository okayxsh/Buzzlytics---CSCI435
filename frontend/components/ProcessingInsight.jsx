import { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';

export default function ProcessingInsight({ messages, intervalMs = 3000 }) {
  const [index, setIndex] = useState(0);
  const safeMessages = messages?.length ? messages : ['Preparing analysis...'];

  useEffect(() => {
    if (safeMessages.length <= 1) return undefined;
    const timer = setInterval(() => {
      setIndex((current) => (current + 1) % safeMessages.length);
    }, intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs, safeMessages.length]);

  return (
    <div className="mt-3 flex min-h-[28px] items-center justify-center gap-2 text-xs font-medium text-ink-soft">
      <Activity className="h-3.5 w-3.5 animate-pulse text-forest-600" />
      <span key={index} className="transition-opacity duration-300">
        {safeMessages[index % safeMessages.length]}
      </span>
    </div>
  );
}
