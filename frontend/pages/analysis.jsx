import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Video, AlertTriangle, UploadCloud, BarChart3, RotateCcw, ArrowRight } from 'lucide-react';
import UploadVideo from '../components/UploadVideo';
import VideoPlayer from '../components/VideoPlayer';
import StatsPanel from '../components/StatsPanel';
import HealthSummary from '../components/HealthSummary';
import { videoApi } from '../services/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Analysis() {
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [videoId, setVideoId] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [annotatedVideoUrl, setAnnotatedVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  const pollStatus = useCallback(async (id) => {
    try {
      const response = await videoApi.getStatus(id);
      const { status, result } = response.data;
      if (status === 'completed') {
        setProcessingStatus('done');
        setResultData(result);
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

  const handleUploadComplete = useCallback((uploadResponse) => {
    const id = uploadResponse.data?.video_id || uploadResponse.video_id;
    setVideoId(id);
    setProcessingStatus('processing');
    pollStatus(id);
  }, [pollStatus]);

  const handleUploadStart = useCallback(() => {
    setProcessingStatus('uploading');
    setError(null);
    setResultData(null);
    setAnnotatedVideoUrl(null);
  }, []);

  const handleUploadError = useCallback((err) => {
    setProcessingStatus('error');
    setError(err?.message || 'Upload failed. Please try again.');
  }, []);

  const handleReset = useCallback(() => {
    setProcessingStatus('idle');
    setVideoId(null);
    setResultData(null);
    setAnnotatedVideoUrl(null);
    setError(null);
  }, []);

  return (
    <div className="relative min-h-screen">
      <Navbar />

      <div className="mx-auto max-w-[1240px] px-5 pb-24 pt-32 md:px-8">
        {/* page heading */}
        <div className="max-w-2xl">
          <div className="eyebrow">Video analysis</div>
          <h1 className="mt-3 font-display text-4xl font-medium leading-tight text-ink md:text-5xl">
            Upload a clip, <span className="italic text-forest-700">read the colony.</span>
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-ink-soft">
            Drop in footage of your hive entrance. Buzzlytics cleans up each frame, finds and
            follows every bee, and hands back an annotated video with a full health report.
          </p>
        </div>

        {/* upload card */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="card mt-12 p-7 md:p-10"
        >
          <div className="mb-8 flex flex-col justify-between gap-4 border-b border-line pb-6 sm:flex-row sm:items-center">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-forest-700 text-cream">
                <UploadCloud className="h-6 w-6" />
              </div>
              <div>
                <h2 className="font-display text-xl font-semibold text-ink">Footage upload</h2>
                <p className="text-sm text-ink-faint">Step one · choose a video</p>
              </div>
            </div>
            <span className="pill self-start text-ink-soft">
              <span className="h-2 w-2 rounded-full bg-forest-500" />
              {processingStatus === 'idle' ? 'Ready' : processingStatus}
            </span>
          </div>

          {(processingStatus === 'idle' || processingStatus === 'uploading') && (
            <UploadVideo
              uploading={processingStatus === 'uploading'}
              onUploadStart={handleUploadStart}
              onUploadComplete={handleUploadComplete}
              onUploadError={handleUploadError}
            />
          )}

          {processingStatus === 'processing' && (
            <div className="rounded-2xl border border-honey-200 bg-honey-50/60 py-20 text-center">
              <div className="relative mx-auto mb-7 h-14 w-14">
                <div className="absolute inset-0 rounded-full border-4 border-honey-100" />
                <div className="absolute inset-0 animate-spin rounded-full border-4 border-honey-400 border-t-transparent" />
              </div>
              <div className="font-display text-2xl font-semibold text-ink">Reading the footage…</div>
              <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
                Detecting and tracking every bee, frame by frame. This usually takes a moment.
              </p>
            </div>
          )}

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

        {/* results */}
        {processingStatus === 'done' && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-8 space-y-8"
          >
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
              <div className="card flex flex-col p-7 md:p-8 lg:col-span-2">
                <div className="mb-6 flex items-center justify-between border-b border-line pb-4">
                  <div className="flex items-center gap-3">
                    <Video className="h-5 w-5 text-forest-700" />
                    <h2 className="font-display text-xl font-semibold text-ink">Annotated footage</h2>
                  </div>
                  <span className="pill text-forest-700">
                    <span className="h-2 w-2 animate-pulse-soft rounded-full bg-forest-500" /> Ready
                  </span>
                </div>
                <div className="flex-1">
                  <VideoPlayer videoUrl={annotatedVideoUrl} />
                </div>
              </div>

              <div className="card p-7 md:p-8">
                <HealthSummary data={resultData} />
              </div>
            </div>

            <div className="card p-7 md:p-8">
              <div className="mb-7 flex items-center gap-3 border-b border-line pb-4">
                <BarChart3 className="h-5 w-5 text-forest-700" />
                <h2 className="font-display text-xl font-semibold text-ink">The numbers</h2>
              </div>
              <StatsPanel data={resultData} />
            </div>

            <div className="flex justify-end pt-2">
              <button className="btn-honey" onClick={handleReset}>
                Analyze another clip <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </div>

      <Footer />
    </div>
  );
}
