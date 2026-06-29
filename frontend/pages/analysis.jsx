import { useState, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Image as ImageIcon,
  Video,
  AlertTriangle,
  UploadCloud,
  BarChart3,
  RotateCcw,
  ArrowRight,
  Activity,
  ScanSearch,
  ShieldAlert,
  CheckCircle2,
  Camera,
  Info,
} from 'lucide-react';
import UploadVideo from '../components/UploadVideo';
import UploadImage from '../components/UploadImage';
import UploadVarroa from '../components/UploadVarroa';
import VideoPlayer from '../components/VideoPlayer';
import StatsPanel from '../components/StatsPanel';
import HealthSummary from '../components/HealthSummary';
import ActivityTimeline from '../components/ActivityTimeline';
import ProcessingInsight from '../components/ProcessingInsight';
import { videoApi } from '../services/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import ClassLegend from '../components/ClassLegend';

const TABS = [
  { id: 'video', label: 'Video', icon: Video },
  { id: 'image', label: 'Image', icon: ImageIcon },
  { id: 'varroa', label: 'Varroa', icon: ScanSearch },
];

const CV_CAPABILITIES = [
  {
    title: 'Object detection',
    text: 'YOLO detects bees and pollen-carrying bees.',
    icon: ScanSearch,
  },
  {
    title: 'Object tracking',
    text: 'The tracker assigns IDs and counts bees over time.',
    icon: Activity,
  },
  {
    title: 'Video processing',
    text: 'Frame-by-frame analysis includes moving-object and motion signals.',
    icon: Video,
  },
  {
    title: 'Object recognition',
    text: 'The Varroa classifier/detector identifies healthy vs infected bee crops.',
    icon: ShieldAlert,
  },
];

const WORKFLOW_GUIDANCE = {
  video: {
    title: 'Best fit: entrance-camera footage',
    note: 'Use bright, stable clips where bees are large enough to see pollen baskets. Dark wood, blur, compression, and wide angles will reduce pollen reliability.',
    checks: ['Stable entrance view', 'Good lighting', 'Visible bee legs'],
    icon: Video,
  },
  image: {
    title: 'Best fit: still entrance frame',
    note: 'Still images are useful for showing annotated detections and explaining the pollen model without waiting for a full video pass.',
    checks: ['Clear frame', 'Entrance angle', 'Minimal motion blur'],
    icon: Camera,
  },
  varroa: {
    title: 'Best fit: close-up bee crop',
    note: 'This is the correct workflow for Varroa demos. Wide entrance footage is not the right scale for reliable mite inspection.',
    checks: ['Close-up bee body', 'Sharp crop', 'Mite-sized details visible'],
    icon: ScanSearch,
  },
};

export default function Analysis() {
  const [activeTab, setActiveTab] = useState('video');

  // Shared result state
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [videoId, setVideoId] = useState(null);
  const [resultData, setResultData] = useState(null);      // raw API result
  const [summaryData, setSummaryData] = useState(null);    // analytics dict for StatsPanel/HealthSummary
  const [timelineData, setTimelineData] = useState([]);    // array for ActivityTimeline
  const [annotatedVideoUrl, setAnnotatedVideoUrl] = useState(null);
  const [annotatedImageUrl, setAnnotatedImageUrl] = useState(null);
  const [varroaData, setVarroaData] = useState(null);
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
    setAnnotatedImageUrl(null);
    setVarroaData(null);
  }, []);

  // ─── Image handlers ───────────────────────────────────────────────────────

  const handleImageUploadStart = useCallback(() => {
    setProcessingStatus('uploading');
    setError(null);
    setResultData(null);
    setSummaryData(null);
    setTimelineData([]);
    setAnnotatedVideoUrl(null);
    setAnnotatedImageUrl(null);
    setVarroaData(null);
  }, []);

  const handleImageUploadComplete = useCallback((data) => {
    // UploadImage passes the UNWRAPPED data object: { summary, motion, annotated_image }
    setResultData(data);
    setSummaryData(data?.summary ?? null);
    setAnnotatedImageUrl(data?.annotated_image || null);
    setTimelineData([]); // single image — no timeline
    setProcessingStatus('done');
  }, []);

  const handleVarroaUploadStart = useCallback(() => {
    setProcessingStatus('uploading');
    setError(null);
    setResultData(null);
    setSummaryData(null);
    setTimelineData([]);
    setAnnotatedVideoUrl(null);
    setAnnotatedImageUrl(null);
    setVarroaData(null);
  }, []);

  const handleVarroaUploadComplete = useCallback((data) => {
    setResultData(data);
    setVarroaData(data);
    setTimelineData([]);
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
    setAnnotatedImageUrl(null);
    setVarroaData(null);
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
  const isVarroaTab = activeTab === 'varroa';
  const guidance = WORKFLOW_GUIDANCE[activeTab];
  const GuidanceIcon = guidance.icon;

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
            Drop in a video or a still frame. Buzzlytics cleans up every frame, finds and
            follows every bee, and can inspect close-up bee crops for varroa.
          </p>
        </div>

        {/* ── Input-mode tab bar ───────────────────────────────────────────── */}
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {CV_CAPABILITIES.map(({ title, text, icon: Icon }) => (
            <div key={title} className="rounded-2xl border border-line bg-cream p-4 shadow-soft">
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-forest-50 text-forest-700">
                <Icon className="h-4 w-4" />
              </div>
              <div className="font-display text-base font-semibold text-ink">{title}</div>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{text}</p>
            </div>
          ))}
        </div>

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

        <div className="mt-5 grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
          <div className="rounded-2xl border border-line bg-cream p-5 shadow-soft">
            <div className="flex gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-forest-50 text-forest-700">
                <GuidanceIcon className="h-5 w-5" />
              </div>
              <div>
                <div className="font-display text-lg font-semibold text-ink">{guidance.title}</div>
                <p className="mt-1 text-sm leading-relaxed text-ink-soft">{guidance.note}</p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-line bg-sand/70 p-5">
            <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-ink-faint">
              <Info className="h-3.5 w-3.5" />
              Demo checklist
            </div>
            <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1">
              {guidance.checks.map((item) => (
                <div key={item} className="flex items-center gap-2 text-sm font-medium text-ink-soft">
                  <CheckCircle2 className="h-4 w-4 text-forest-600" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Upload card (Video, Image, or Varroa tab) ───────────────────── */}
        {(isVideoTab || isImageTab || isVarroaTab) && (
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
                    {isVideoTab ? 'Footage upload' : isImageTab ? 'Image upload' : 'Varroa crop upload'}
                  </h2>
                  <p className="text-sm text-ink-faint">
                    Step one · choose {isVideoTab ? 'a video' : isImageTab ? 'an image' : 'a close-up crop'}
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
                {isVarroaTab && (
                  <UploadVarroa
                    uploading={processingStatus === 'uploading'}
                    onUploadStart={handleVarroaUploadStart}
                    onUploadComplete={handleVarroaUploadComplete}
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
                <ProcessingInsight
                  messages={[
                    'Sampling frames so the demo stays responsive.',
                    'Running YOLO on raw frames for bee and pollen detections.',
                    'Assigning ByteTrack IDs so repeated bees are not double-counted.',
                    'Measuring motion activity with the background model.',
                    'Writing the annotated result video for playback.',
                  ]}
                />
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
        {processingStatus === 'done' && (summaryData || varroaData) && (
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
                  <div className="mt-5">
                    <ClassLegend showReliabilityNote />
                  </div>
                </div>

                <div className="card p-7 md:p-8">
                  <HealthSummary data={summaryData} />
                </div>
              </div>
            )}

            {/* Health summary + annotated image — image tab */}
            {isImageTab && (
              <div className="space-y-4">
                {annotatedImageUrl ? (
                  <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                    <div className="card flex flex-col p-7 md:p-8 lg:col-span-2">
                      <div className="mb-6 flex items-center justify-between border-b border-line pb-4">
                        <div className="flex items-center gap-3">
                          <ImageIcon className="h-5 w-5 text-forest-700" />
                          <h2 className="font-display text-xl font-semibold text-ink">
                            Annotated image
                          </h2>
                        </div>
                        <span className="pill text-forest-700">
                          <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" />{' '}
                          Ready
                        </span>
                      </div>
                      <img
                        src={`data:image/jpeg;base64,${annotatedImageUrl}`}
                        alt="Annotated"
                        className="w-full rounded-xl"
                      />
                      <div className="mt-5">
                        <ClassLegend showReliabilityNote />
                      </div>
                    </div>
                    <div className="card p-7 md:p-8">
                      <HealthSummary data={summaryData} />
                    </div>
                  </div>
                ) : (
                  <>
                    <ClassLegend showReliabilityNote />
                    <div className="card p-7 md:p-8">
                      <HealthSummary data={summaryData} />
                    </div>
                  </>
                )}
              </div>
            )}

            {isVarroaTab && varroaData && (
              <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                <div className="card flex flex-col p-7 md:p-8 lg:col-span-2">
                  <div className="mb-6 flex items-center justify-between border-b border-line pb-4">
                    <div className="flex items-center gap-3">
                      <ScanSearch className="h-5 w-5 text-forest-700" />
                      <h2 className="font-display text-xl font-semibold text-ink">
                        Close-up varroa inspection
                      </h2>
                    </div>
                    <span className={`pill ${varroaData.prediction?.is_varroa ? 'text-clay' : 'text-forest-700'}`}>
                      <span className={`h-2 w-2 rounded-full ${varroaData.prediction?.is_varroa ? 'bg-clay' : 'bg-forest-500'}`} />
                      {varroaData.prediction?.is_varroa ? 'Varroa flagged' : 'No varroa flag'}
                    </span>
                  </div>
                  {varroaData.annotated_image && (
                    <img
                      src={`data:image/jpeg;base64,${varroaData.annotated_image}`}
                      alt="Varroa crop analysis"
                      className="mx-auto h-auto max-h-[680px] w-full max-w-[420px] rounded-xl object-contain"
                    />
                  )}
                </div>

                <div className="card p-7 md:p-8">
                  <div className="mb-6 flex items-center gap-3 border-b border-line pb-4">
                    <ShieldAlert className="h-5 w-5 text-forest-700" />
                    <h2 className="font-display text-xl font-semibold text-ink">Varroa result</h2>
                  </div>
                  <div className="space-y-5">
                    <div>
                      <div className="data-label mb-1.5">Model prediction</div>
                      <div className="font-display text-4xl font-semibold capitalize text-ink">
                        {varroaData.prediction?.label || 'Unknown'}
                      </div>
                    </div>
                    <div>
                      <div className="data-label mb-1.5">Analysis method</div>
                      <div className="font-display text-2xl font-semibold capitalize text-ink">
                        {varroaData.prediction?.method === 'detector'
                          ? 'YOLO mite detector'
                          : 'Crop classifier'}
                      </div>
                      {varroaData.prediction?.method === 'detector' && (
                        <div className="mt-1 text-sm text-ink-faint">
                          {varroaData.detections?.length || 0} mite box
                          {(varroaData.detections?.length || 0) === 1 ? '' : 'es'} found
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="data-label mb-1.5">Confidence</div>
                      <div className="font-display text-3xl font-semibold tabular text-ink">
                        {`${((varroaData.prediction?.confidence || 0) * 100).toFixed(1)}%`}
                      </div>
                    </div>
                    {varroaData.ground_truth && (
                      <div>
                        <div className="data-label mb-1.5">Dataset reference count</div>
                        <div className="font-display text-3xl font-semibold tabular text-ink">
                          {varroaData.ground_truth.mite_count}
                        </div>
                      </div>
                    )}
                    <p className="text-sm leading-relaxed text-ink-soft">
                      This mode is for close-up bee crop inspection. Red boxes are YOLO mite detections from the dedicated Varroa detector; the crop classifier remains available as a fallback health check if detector weights are unavailable.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Stats counters */}
            {!isVarroaTab && (
              <div className="card p-7 md:p-8">
                <div className="mb-7 flex items-center gap-3 border-b border-line pb-4">
                  <BarChart3 className="h-5 w-5 text-forest-700" />
                  <h2 className="font-display text-xl font-semibold text-ink">The numbers</h2>
                </div>
                <StatsPanel data={summaryData} />
              </div>
            )}

            {/* Activity timeline — video only (image passes [] which shows placeholder) */}
            {!isVarroaTab && (
              <div className="card p-7 md:p-8">
                <div className="mb-6 flex items-center gap-3 border-b border-line pb-4">
                  <Activity className="h-5 w-5 text-forest-700" />
                  <h2 className="font-display text-xl font-semibold text-ink">
                    Entrance activity
                  </h2>
                </div>
                <ActivityTimeline data={timelineData} metric="activity_ratio" />
              </div>
            )}

            {/* Reset CTA */}
            <div className="flex justify-end pt-2">
              <button className="btn-honey" onClick={handleReset}>
                Analyze another {isVideoTab ? 'clip' : isImageTab ? 'image' : 'crop'}{' '}
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
