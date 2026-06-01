import { useState, useEffect, useRef, useCallback } from 'react';
import { Bug, Video, Radio, Camera, CameraOff, AlertCircle, Wifi, WifiOff } from 'lucide-react';
import StatsPanel from '../components/StatsPanel';
import HealthSummary from '../components/HealthSummary';
import { WS_URL } from '../services/api';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function WebcamPage() {
  const router = useRouter();
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
      // Access webcam
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, frameRate: { ideal: 15 } },
      });
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Connect WebSocket
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setConnecting(false);
        setError(null);

        // Start capturing frames at ~10 FPS
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

          // If annotated frame is returned, draw it on canvas
          if (data.annotated_frame && canvasRef.current) {
            const img = new Image();
            img.onload = () => {
              const ctx = canvasRef.current.getContext('2d');
              canvasRef.current.width = img.width;
              canvasRef.current.height = img.height;
              ctx.drawImage(img, 0, 0);

              // Update FPS counter
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

          // If stats data is returned
          if (data.stats) {
            setStatsData(data.stats);
          }
        } catch (e) {
          // Ignore parse errors for binary frames
        }
      };

      ws.onerror = () => {
        setError('WebSocket connection error. Make sure the backend is running.');
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
        setError('Camera access denied. Please allow camera permissions and try again.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found. Please connect a webcam and try again.');
      } else {
        setError(`Failed to start webcam: ${err.message}`);
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

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, [stopStreaming]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="header">
        <div className="header-logo">
          <Bug size={28} style={{ color: 'var(--color-healthy)' }} />
          <h1>Buzzlytics</h1>
        </div>
        <nav className="header-nav">
          <Link href="/" legacyBehavior>
            <button className={`nav-tab ${router.pathname === '/' ? 'active' : ''}`}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Video size={15} />
                Video Upload
              </span>
            </button>
          </Link>
          <Link href="/webcam" legacyBehavior>
            <button className={`nav-tab ${router.pathname === '/webcam' ? 'active' : ''}`}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Radio size={15} />
                Live Webcam
              </span>
            </button>
          </Link>
        </nav>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="dashboard-section">
          <div className="dashboard-section-title">Live Webcam Monitoring</div>

          {/* Controls */}
          <div className="webcam-controls" style={{ marginBottom: 16 }}>
            <button
              className={`btn ${connected ? 'btn-danger' : 'btn-primary'}`}
              onClick={handleToggleConnection}
              disabled={connecting}
            >
              {connecting ? (
                'Connecting...'
              ) : connected ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <CameraOff size={16} />
                  Disconnect
                </span>
              ) : (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <Camera size={16} />
                  Connect Webcam
                </span>
              )}
            </button>

            {connected && (
              <span className="webcam-fps">
                FPS: <span className="webcam-fps-value">{fps}</span>
              </span>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="error-message" style={{ marginBottom: 16 }}>
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <div className="section-row">
            {/* Video Area */}
            <div>
              <div className="webcam-canvas-wrapper">
                {/* Hidden video element for capturing webcam */}
                <video
                  ref={videoRef}
                  style={{ display: 'none' }}
                  muted
                  playsInline
                />

                {connected ? (
                  <canvas ref={canvasRef} />
                ) : (
                  <div className="webcam-placeholder">
                    <Camera size={48} className="webcam-placeholder-icon" />
                    <div className="webcam-placeholder-title">No Webcam Connected</div>
                    <div className="webcam-placeholder-sub">
                      Click "Connect Webcam" to start live monitoring
                    </div>
                  </div>
                )}

                {/* Status Badge */}
                {connected && (
                  <div className="webcam-status-badge connected">
                    <Wifi size={12} />
                    LIVE
                  </div>
                )}
                {!connected && !connecting && streamRef.current === null && (
                  <div style={{ position: 'absolute', top: 12, right: 12 }}>
                    <div className="webcam-status-badge disconnected">
                      <WifiOff size={12} />
                      OFFLINE
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Health Summary Sidebar */}
            <HealthSummary data={statsData} />
          </div>

          {/* Stats */}
          {statsData && (
            <div style={{ marginTop: 24 }}>
              <div className="dashboard-section-title">Real-Time Metrics</div>
              <StatsPanel data={statsData} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
