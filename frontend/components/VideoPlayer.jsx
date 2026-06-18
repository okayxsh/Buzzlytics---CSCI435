import { useState, useRef, useCallback, useEffect } from 'react';
import { Play, Pause, Maximize, Download } from 'lucide-react';

export default function VideoPlayer({ videoUrl }) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const wrapperRef = useRef(null);

  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;
    if (playing) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setPlaying(!playing);
  }, [playing]);

  const toggleFullscreen = useCallback(() => {
    if (!wrapperRef.current) return;
    if (!fullscreen) {
      if (wrapperRef.current.requestFullscreen) {
        wrapperRef.current.requestFullscreen();
      } else if (wrapperRef.current.webkitRequestFullscreen) {
        wrapperRef.current.webkitRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    }
  }, [fullscreen]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
    };
  }, []);

  const handleDownload = useCallback(() => {
    if (!videoUrl) return;
    const a = document.createElement('a');
    a.href = videoUrl;
    a.download = 'buzzlytics-annotated-video.mp4';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, [videoUrl]);

  const handleVideoEnded = useCallback(() => {
    setPlaying(false);
  }, []);

  const handlePlay = useCallback(() => {
    setPlaying(true);
  }, []);

  const handlePause = useCallback(() => {
    setPlaying(false);
  }, []);

  if (!videoUrl) {
    return (
      <div className="flex items-center justify-center rounded-2xl border border-line bg-sand p-12 text-center text-sm font-medium text-ink-faint">
        No video to show yet
      </div>
    );
  }

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-line bg-[#1b1a16] shadow-soft" ref={wrapperRef}>
      <video
        ref={videoRef}
        src={videoUrl}
        onEnded={handleVideoEnded}
        onPlay={handlePlay}
        onPause={handlePause}
        className="block w-full"
        preload="metadata"
      />

      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
        <button
          className="flex h-11 w-11 items-center justify-center rounded-full bg-cream/95 text-forest-700 transition-colors hover:bg-honey-300 hover:text-ink"
          onClick={togglePlay}
          aria-label={playing ? 'Pause' : 'Play'}
        >
          {playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
        </button>
        <div className="flex items-center gap-2">
          <button
            className="flex h-11 w-11 items-center justify-center rounded-full bg-white/15 text-cream transition-colors hover:bg-white/30"
            onClick={handleDownload}
            aria-label="Download video"
          >
            <Download size={18} />
          </button>
          <button
            className="flex h-11 w-11 items-center justify-center rounded-full bg-white/15 text-cream transition-colors hover:bg-white/30"
            onClick={toggleFullscreen}
            aria-label="Fullscreen"
          >
            <Maximize size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
