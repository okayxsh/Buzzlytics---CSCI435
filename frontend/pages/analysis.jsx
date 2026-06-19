import { useState, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Image as ImageIcon,
  Video,
  Camera,
  AlertTriangle,
  UploadCloud,
  BarChart3,
  RotateCcw,
  ArrowRight,
  Activity,
} from 'lucide-react';
import UploadVideo from '../components/UploadVideo';
import UploadImage from '../components/UploadImage';
import VideoPlayer from '../components/VideoPlayer';
import StatsPanel from '../components/StatsPanel';
import HealthSummary from '../components/HealthSummary';
import ActivityTimeline from '../components/ActivityTimeline';
import { videoApi } from '../services/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const TABS = [
  { id: 'video', label: 'Video', icon: Video },
  { id: 'image', label: 'Image', icon: ImageIcon },
  { id: 'webcam', label: 'Webcam', icon: Camera },
];

export default function Analysis() {
  const [activeTab, setActiveTab] = useState('video');

  // Shared result state
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [videoId, setVideoId] = useState(null);
  const [resultData, setResultData] = useState(null);      // raw API result
  const [summaryData, setSummaryData] = useState(null);    // analytics dict for StatsPanel/HealthSummary
  const [timelineData, setTimelineData] = useState([]);    // array for ActivityTimeline
  const [annotatedVideoUrl, setAnnotatedVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  // ─── Video handlers ───────────────────────────────────────────────────────

  const pollStatus = useCallback(async (id) => {
    try {
      const response = await videoApi.getStatus(id);
      const { status, result } = response.data;
      if (status === 'completed') {
        setProcessingStatus('done');
        setResultData(result);
        // result = { total_frames, avg_bees, final_summary, timeline }
        setSummaryData(result?.final_summary ?? null);
        setTimelineData(Array.isArray(result?.timeline) ? result.timeline : []);
        setAnnotatedVideoUrl(videoApi.getResult(id));
      } else if (status === 'failed') {
        setProcessingStatus('error');
        setError('Processing failed. Please try a different clip.');
      } else {
        setTimeout(() => pollStatus(id), 2000);
      }
    } catch (err) {
      setProcessingStatus('error');
      setError('We lost contact while checking on the analysis.');
    }
  }, []);

  const handleVideoUploadComplete = useCallback((uploadResponse) => {
    // UploadVideo passes the raw axios response
    const id = uploadResponse.data?.video_id || uploadResponse.video_id;
    setVideoId(id);
    setProcessingStatus('processing');
    pollStatus(id);
  }, [pollStatus]);

  const handleVideoUploadStart = useCallback(() => {
    setProcessingStatus('uploading');
    setError(null);
    setResultData(null);
    setSummaryData(null);
    setTimelineData([]);
    setAnnotatedVideoUrl(null);
  }, []);

  // ─── Image handlers ───────────────────────────────────────────────────────

  const handleImageUploadStart = useCallback(() => {
    setProcessingStatus('uploading');
    setError(null);
    setResultData(null);
    setSummaryData(null);
    setTimelineData([]);
    setAnnotatedVideoUrl(null);
  }, []);

  const handleImageUploadComplete = useCallback((data) => {
    // UploadImage passes the UNWRAPPED data object: { summary, motion, annotated_image }
    setResultData(data);
    setSummaryData(data?.summary ?? null);
    setTimelineData([]); // single image — no timeline
    setProcessingStatus('done');
  }, []);

  // ─── Shared error / reset ─────────────────────────────────────────────────

  const handleUploadError = useCallback((err) => {
    setProcessingStatus('error');
    setError(err?.message || 'Upload failed. Please try again.');
  }, []);

  const handleReset = useCallback(() => {
    setProcessingStatus('idle');
    setVideoId(null);
    setResultData(null);
    setSummaryData(null);
    setTimelineData([]);
    setAnnotatedVideoUrl(null);
    setError(null);
  }, []);

  // ─── Tab switch — clear stale results ─────────────────────────────────────

  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
    handleReset();
  }, [handleReset]);

  // ─── Derived ──────────────────────────────────────────────────────────────

  const isVideoTab = activeTab === 'video';
  const isImageTab = activeTab === 'image';
  const isWebcamTab = activeTab === 'webcam';

  return (
    <div className="relative min-h-screen">
      <Navbar />

      <div className="mx-auto max-w-[1240px] px-5 pb-24 pt-32 md:px-8">
        {/* Page heading */}
        <div className="max-w-2xl">
          <div className="eyebrow">Hive analysis</div>
          <h1 className="mt-3 font-display text-4xl font-medium leading-tight text-ink md:text-5xl">
            Upload footage,{' '}
            <span className="italic text-forest-700">read the colony.</span>
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-ink-soft">
            Drop in a video, a still frame, or go live with a webcam. Buzzlytics cleans up
            every frame, finds and follows every bee, and hands back a full health report.
          </p>
        </div>

        {/* ── Input-mode tab bar ───────────────────────────────────────────── */}
        <div className="mt-10 flex gap-1 rounded-2xl border border-line bg-sand/60 p-1.5 sm:w-fit">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => handleTabChange(id)}
              className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all ${
                activeTab === id
                  ? 'bg-cream text-ink shadow-soft'
                  : 'text-ink-soft hover:text-ink'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {/* ── Webcam tab — links to dedicated page ────────────────────────── */}
        {isWebcamTab && (
          <motion.section
            key="webcam"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="card mt-8 flex flex-col items-center justify-center gap-6 p-12 text-center"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-forest-50 text-forest-600 shadow-soft">
              <Camera className="h-8 w-8" />
            </div>
            <div>
              <div className="font-display text-2xl font-semibold text-ink">
                Live webcam analysis
              </div>
              <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-ink-soft">
                Point a webcam at the hive entrance for real-time detection and live colony
                statistics.
              </p>
            </div>
            <Link href="/webcam" className="btn-primary">
              <Camera className="h-4 w-4" /> Open webcam view
            </Link>
          </motion.section>
        )}

        {/* ── Upload card (Video or Image tab) ─────────────────────────────── */}
        {(isVideoTab || isImageTab) && (
          <motion.section
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="card mt-8 p-7 md:p-10"
          >
            <div className="mb-8 flex flex-col justify-between gap-4 border-b border-line pb-6 sm:flex-row sm:items-center">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-forest-700 text-cream">
                  <UploadCloud className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="font-display text-xl font-semibold text-ink">
                    {isVideoTab ? 'Footage upload' : 'Image upload'}
                  </h2>
                  <p className="text-sm text-ink-faint">
                    Step one · choose {isVideoTab ? 'a video' : 'an image'}
                  </p>
                </div>
              </div>
              <span className="pill self-start text-ink-soft">
                <span className="h-2 w-2 rounded-full bg-forest-500" />
                {processingStatus === 'idle' ? 'Ready' : processingStatus}
              </span>
            </div>

            {/* Upload component — shown while idle or uploading */}
            {(processingStatus === 'idle' || processingStatus === 'uploading') && (
              <>
                {isVideoTab && (
                  <UploadVideo
                    uploading={processingStatus === 'uploading'}
                    onUploadStart={handleVideoUploadStart}
                    onUploadComplete={handleVideoUploadComplete}
                    onUploadError={handleUploadError}
                  />
                )}
                {isImageTab && (
                  <UploadImage
                    uploading={processingStatus === 'uploading'}
                    onUploadStart={handleImageUploadStart}
                    onUploadComplete={handleImageUploadComplete}
                    onUploadError={handleUploadError}
                  />
                )}
              </>
            )}

            {/* Processing spinner (video only — image is synchronous) */}
            {processingStatus === 'processing' && (
              <div className="rounded-2xl border border-honey-200 bg-honey-50/60 py-20 text-center">
                <div className="relative mx-auto mb-7 h-14 w-14">
                  <div className="absolute inset-0 rounded-full border-4 border-honey-100" />
                  <div className="absolute inset-0 animate-spin rounded-full border-4 border-honey-400 border-t-transparent" />
                </div>
                <div className="font-display text-2xl font-semibold text-ink">
                  Reading the footage…
                </div>
                <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
                  Detecting and tracking every bee, frame by frame. This usually takes a moment.
                </p>
              </div>
            )}

            {/* Error state */}
            {processingStatus === 'error' && (
              <div className="rounded-2xl border border-[#E7C5B7] bg-[#F6E6DF] p-8">
                <div className="mb-3 flex items-center gap-3 font-display text-xl font-semibold text-clay">
                  <AlertTriangle className="h-6 w-6" /> Something went wrong
                </div>
                <p className="mb-7 text-ink-soft">{error}</p>
                <button className="btn-primary" onClick={handleReset}>
                  <RotateCcw className="h-4 w-4" /> Try again
                </button>
              </div>
            )}
          </motion.section>
        )}

        {/* ── Results dashboard (shown once analysis is done) ──────────────── */}
        {processingStatus === 'done' && summaryData && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-8 space-y-8"
          >
            {/* Annotated video player — video tab only */}
            {isVideoTab && annotatedVideoUrl && (
              <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                <div className="card flex flex-col p-7 md:p-8 lg:col-span-2">
                  <div className="mb-6 flex items-center justify-between border-b border-line pb-4">
                    <div className="flex items-center gap-3">
                      <Video className="h-5 w-5 text-forest-700" />
                      <h2 className="font-display text-xl font-semibold text-ink">
                        Annotated footage
                      </h2>
                    </div>
                    <span className="pill text-forest-700">
                      <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" />{' '}
                      Ready
                    </span>
                  </div>
                  <div className="flex-1">
                    <VideoPlayer videoUrl={annotatedVideoUrl} />
                  </div>
                </div>

                <div className="card p-7 md:p-8">
                  <HealthSummary data={summaryData} />
                </div>
              </div>
            )}

            {/* Health summary without video — image tab */}
            {isImageTab && (
              <div className="card p-7 md:p-8">
                <HealthSummary data={summaryData} />
              </div>
            )}

            {/* Stats counters */}
            <div className="card p-7 md:p-8">
              <div className="mb-7 flex items-center gap-3 border-b border-line pb-4">
                <BarChart3 className="h-5 w-5 text-forest-700" />
                <h2 className="font-display text-xl font-semibold text-ink">The numbers</h2>
              </div>
              <StatsPanel data={summaryData} />
            </div>

            {/* Activity timeline — video only (image passes [] which shows placeholder) */}
            <div className="card p-7 md:p-8">
              <div className="mb-6 flex items-center gap-3 border-b border-line pb-4">
                <Activity className="h-5 w-5 text-forest-700" />
                <h2 className="font-display text-xl font-semibold text-ink">
                  Entrance activity
                </h2>
              </div>
              <ActivityTimeline data={timelineData} metric="activity_ratio" />
            </div>

            {/* Reset CTA */}
            <div className="flex justify-end pt-2">
              <button className="btn-honey" onClick={handleReset}>
                Analyze another {isVideoTab ? 'clip' : 'image'}{' '}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </div>

      <Footer />
    </div>
  );
}
