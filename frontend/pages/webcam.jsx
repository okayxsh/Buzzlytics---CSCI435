import { useState, useEffect, useRef, useCallback } from 'react';
import { Camera, CameraOff, AlertCircle, Wifi, WifiOff, Radio } from 'lucide-react';
import StatsPanel from '../components/StatsPanel';
import HealthSummary from '../components/HealthSummary';
import { WS_URL } from '../services/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function WebcamPage() {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const [statsData, setStatsData] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const frameIntervalRef = useRef(null);
  const fpsCounterRef = useRef({ count: 0, lastTime: Date.now() });

  const stopStreaming = useCallback(() => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
    setConnecting(false);
  }, []);

  const startStreaming = useCallback(async () => {
    setError(null);
    setConnecting(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, frameRate: { ideal: 15 } },
      });
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setConnecting(false);
        setError(null);

        frameIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN && videoRef.current) {
            const canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoRef.current, 0, 0, 640, 480);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            const base64Data = dataUrl.split(',')[1];
            ws.send(JSON.stringify({ frame: base64Data }));
          }
        }, 100);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.annotated_frame && canvasRef.current) {
            const img = new Image();
            img.onload = () => {
              const ctx = canvasRef.current.getContext('2d');
              canvasRef.current.width = img.width;
              canvasRef.current.height = img.height;
              ctx.drawImage(img, 0, 0);

              fpsCounterRef.current.count += 1;
              const now = Date.now();
              if (now - fpsCounterRef.current.lastTime >= 1000) {
                setFps(fpsCounterRef.current.count);
                fpsCounterRef.current.count = 0;
                fpsCounterRef.current.lastTime = now;
              }
            };
            img.src = `data:image/jpeg;base64,${data.annotated_frame}`;
          }

          if (data.stats) {
            setStatsData(data.stats);
          }
        } catch (e) {
          // ignore parse errors for binary frames
        }
      };

      ws.onerror = () => {
        setError('Could not reach the analysis server. Make sure the backend is running.');
        setConnecting(false);
        stopStreaming();
      };

      ws.onclose = () => {
        setConnected(false);
        setConnecting(false);
      };
    } catch (err) {
      setConnecting(false);
      if (err.name === 'NotAllowedError') {
        setError('Camera access was denied. Allow camera permission and try again.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found. Connect a webcam and try again.');
      } else {
        setError(`Could not start the webcam: ${err.message}`);
      }
    }
  }, [stopStreaming]);

  const handleToggleConnection = useCallback(() => {
    if (connected) {
      stopStreaming();
      setFps(0);
      setStatsData(null);
    } else {
      startStreaming();
    }
  }, [connected, startStreaming, stopStreaming]);

  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, [stopStreaming]);

  return (
    <div className="relative min-h-screen">
      <Navbar />

      <div className="mx-auto max-w-[1240px] px-5 pb-24 pt-32 md:px-8">
        {/* heading */}
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <div className="eyebrow">Live feed</div>
            <h1 className="mt-3 font-display text-4xl font-medium leading-tight text-ink md:text-5xl">
              Watch the hive <span className="italic text-forest-700">as it happens.</span>
            </h1>
            <p className="mt-4 text-lg leading-relaxed text-ink-soft">
              Point a webcam at the entrance and Buzzlytics annotates every frame in real time,
              updating the colony’s vital signs as the bees come and go.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <button
              className={connected ? 'btn-soft' : 'btn-primary'}
              onClick={handleToggleConnection}
              disabled={connecting}
            >
              {connecting ? (
                'Connecting…'
              ) : connected ? (
                <><CameraOff className="h-4 w-4" /> Disconnect</>
              ) : (
                <><Camera className="h-4 w-4" /> Connect webcam</>
              )}
            </button>
            {connected && (
              <span className="pill text-forest-700">
                <Wifi className="h-3.5 w-3.5" />
                {fps} fps
              </span>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-8 flex items-start gap-3 rounded-2xl border border-[#E7C5B7] bg-[#F6E6DF] p-5 text-clay">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* live canvas */}
          <div className="card p-7 md:p-8 lg:col-span-2">
            <div className="mb-6 flex items-center justify-between border-b border-line pb-4">
              <div className="flex items-center gap-3">
                <Radio className="h-5 w-5 text-forest-700" />
                <h2 className="font-display text-xl font-semibold text-ink">Live view</h2>
              </div>
              {connected ? (
                <span className="pill text-forest-700">
                  <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" /> Live
                </span>
              ) : (
                <span className="pill text-ink-faint">
                  <WifiOff className="h-3.5 w-3.5" /> Offline
                </span>
              )}
            </div>

            <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-2xl border border-line bg-[#1b1a16]">
              <video ref={videoRef} style={{ display: 'none' }} muted playsInline />

              {connected ? (
                <canvas ref={canvasRef} className="h-full w-full object-contain" />
              ) : (
                <div className="px-6 py-20 text-center">
                  <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 text-honey-300">
                    <Camera className="h-8 w-8" />
                  </div>
                  <div className="font-display text-xl font-semibold text-cream">No camera connected</div>
                  <p className="mx-auto mt-2 max-w-xs text-sm text-[#cfc6b4]">
                    Hit “Connect webcam” to start watching the hive in real time.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* health sidebar */}
          <div className="card p-7 md:p-8">
            <HealthSummary data={statsData} />
          </div>
        </div>

        {statsData && (
          <div className="card mt-8 p-7 md:p-8">
            <div className="mb-7 border-b border-line pb-4">
              <h2 className="font-display text-xl font-semibold text-ink">Live readings</h2>
              <p className="text-sm text-ink-faint">Updating as the feed runs</p>
            </div>
            <StatsPanel data={statsData} />
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
}
