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
      <div className="bg-slate-100 border border-slate-200 sharp-edge p-12 text-center text-slate-400 font-mono text-sm uppercase tracking-widest">
        Video Signal Unavailable
      </div>
    );
  }

  return (
    <div className="relative bg-slate-900 border border-slate-800 overflow-hidden sharp-edge group" ref={wrapperRef}>
      <video
        ref={videoRef}
        src={videoUrl}
        onEnded={handleVideoEnded}
        onPlay={handlePlay}
        onPause={handlePause}
        className="w-full block"
        preload="metadata"
      />

      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <div className="flex items-center gap-2">
          <button 
            className="w-10 h-10 bg-white/10 hover:bg-amber-500 text-white hover:text-slate-900 flex items-center justify-center transition-colors sharp-edge border border-white/20 hover:border-amber-500" 
            onClick={togglePlay} 
            title={playing ? 'Pause' : 'Play'}
          >
            {playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-1" />}
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button 
            className="w-10 h-10 bg-white/10 hover:bg-white/30 text-white flex items-center justify-center transition-colors sharp-edge border border-white/20" 
            onClick={handleDownload} 
            title="Download Telemetry"
          >
            <Download size={18} />
          </button>
          <button 
            className="w-10 h-10 bg-white/10 hover:bg-white/30 text-white flex items-center justify-center transition-colors sharp-edge border border-white/20" 
            onClick={toggleFullscreen} 
            title="Fullscreen"
          >
            <Maximize size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
