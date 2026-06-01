import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Bug, Video, Radio, AlertTriangle } from 'lucide-react';
import UploadVideo from '../components/UploadVideo';
import VideoPlayer from '../components/VideoPlayer';
import StatsPanel from '../components/StatsPanel';
import HealthSummary from '../components/HealthSummary';
import { videoApi } from '../services/api';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Analysis() {
  const router = useRouter();
  const [videoFile, setVideoFile] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [videoId, setVideoId] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [annotatedVideoUrl, setAnnotatedVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  const pollStatus = useCallback(async (id) => {
    try {
      const response = await videoApi.getStatus(id);
      const { status, progress, result } = response.data;
      if (status === 'completed') {
        setProcessingStatus('done');
        setResultData(result);
        setAnnotatedVideoUrl(videoApi.getResult(id));
      } else if (status === 'failed') {
        setProcessingStatus('error');
        setError('Processing failed. Please try again.');
      } else {
        setTimeout(() => pollStatus(id), 2000);
      }
    } catch (err) {
      setProcessingStatus('error');
      setError('Failed to check processing status.');
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
    setVideoFile(null);
    setProcessingStatus('idle');
    setVideoId(null);
    setResultData(null);
    setAnnotatedVideoUrl(null);
    setError(null);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-amber-500/30">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 glass-panel border-b border-slate-200/50 px-6 py-4 flex justify-between items-center sharp-edge">
        <Link href="/" className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 border border-amber-500/20 sharp-edge">
            <Bug className="w-6 h-6 text-amber-500" />
          </div>
          <h1 className="text-xl font-bold tracking-tighter text-slate-900 uppercase hover:text-amber-600 transition-colors">Buzzlytics</h1>
        </Link>
        <nav className="flex gap-2">
          <Link href="/analysis" legacyBehavior>
            <button className={`px-5 py-2 text-sm font-bold uppercase tracking-wider border transition-colors sharp-edge ${router.pathname === '/analysis' ? 'bg-amber-500/10 border-amber-500/30 text-amber-600' : 'border-transparent text-slate-500 hover:text-slate-900 hover:bg-slate-200/50'}`}>
              <span className="flex items-center gap-2">
                <Video className="w-4 h-4" />
                Analysis
              </span>
            </button>
          </Link>
          <Link href="/webcam" legacyBehavior>
            <button className={`px-5 py-2 text-sm font-bold uppercase tracking-wider border transition-colors sharp-edge ${router.pathname === '/webcam' ? 'bg-amber-500/10 border-amber-500/30 text-amber-600' : 'border-transparent text-slate-500 hover:text-slate-900 hover:bg-slate-200/50'}`}>
              <span className="flex items-center gap-2">
                <Radio className="w-4 h-4" />
                Live Feed
              </span>
            </button>
          </Link>
        </nav>
      </header>

      {/* Main Analysis Content */}
      <div className="relative z-20 pt-32 pb-32 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="mb-12">
          <h2 className="text-4xl font-black uppercase tracking-tighter text-slate-900 mb-2">Video Telemetry</h2>
          <p className="text-slate-500 font-medium max-w-2xl">Upload hive footage to initiate neural network analysis for Varroa mite detection, activity tracking, and health estimation.</p>
        </div>

        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass-panel p-8 md:p-12 border-slate-200/80 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.05)] mb-12 sharp-edge"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 pb-6 border-b border-slate-200">
            <div className="flex items-center gap-5">
              <div className="w-14 h-14 bg-slate-900 flex items-center justify-center sharp-edge">
                <Video className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-black uppercase tracking-tight text-slate-900">Data Ingestion</h3>
                <p className="text-xs text-slate-500 font-bold uppercase tracking-[0.15em] mt-1">Module 01 // Upload</p>
              </div>
            </div>
            <div className="text-xs font-mono text-slate-400">SYS.STATUS: {processingStatus.toUpperCase()}</div>
          </div>

          {processingStatus === 'idle' && (
            <UploadVideo onUploadStart={handleUploadStart} onUploadComplete={handleUploadComplete} onUploadError={handleUploadError} />
          )}
          
          {processingStatus === 'uploading' && (
            <UploadVideo uploading onUploadStart={handleUploadStart} onUploadComplete={handleUploadComplete} onUploadError={handleUploadError} />
          )}

          {processingStatus === 'processing' && (
            <div className="py-24 text-center border-2 border-dashed border-amber-500/40 bg-amber-500/5 sharp-edge">
              <div className="relative w-16 h-16 mx-auto mb-8">
                <div className="absolute inset-0 border-4 border-slate-200 sharp-edge" />
                <div className="absolute inset-0 border-4 border-amber-500 border-t-transparent animate-spin sharp-edge" />
              </div>
              <div className="text-2xl font-black uppercase tracking-wider text-slate-900">Analyzing Footage</div>
              <div className="text-xs font-bold text-slate-500 mt-3 uppercase tracking-[0.2em]">Executing Neural Networks...</div>
            </div>
          )}

          {processingStatus === 'error' && (
            <div className="p-8 bg-rose-50 border border-rose-200 mb-6 sharp-edge">
              <div className="text-rose-600 font-black uppercase tracking-wide flex items-center gap-3 mb-4 text-lg">
                <AlertTriangle className="w-6 h-6" /> System Error
              </div>
              <div className="text-slate-700 mb-8 font-medium">{error}</div>
              <button className="px-8 py-3 bg-slate-900 text-white font-bold uppercase tracking-wider text-sm hover:bg-slate-800 transition-colors sharp-edge" onClick={handleReset}>
                Reset Sequence
              </button>
            </div>
          )}
        </motion.section>

        {processingStatus === 'done' && (
          <motion.div 
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 glass-panel p-6 md:p-8 border-slate-200/80 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.05)] sharp-edge flex flex-col">
                 <div className="flex justify-between items-center mb-8 border-b border-slate-200 pb-4">
                   <div>
                     <h3 className="font-black text-slate-900 uppercase tracking-tight text-xl">Visual Telemetry</h3>
                     <p className="text-xs text-slate-500 font-bold uppercase tracking-[0.15em] mt-1">Module 02 // Feed</p>
                   </div>
                   <div className="px-4 py-1.5 bg-emerald-500/10 text-emerald-600 text-xs font-bold uppercase tracking-[0.15em] border border-emerald-500/20 sharp-edge flex items-center gap-2">
                     <span className="w-2 h-2 bg-emerald-500 animate-pulse sharp-edge"></span> Live
                   </div>
                 </div>
                 <div className="flex-1">
                  <VideoPlayer videoUrl={annotatedVideoUrl} />
                 </div>
              </div>
              <div className="glass-panel p-6 md:p-8 border-slate-200/80 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.05)] sharp-edge">
                <HealthSummary data={resultData} />
              </div>
            </div>

            <div className="glass-panel p-6 md:p-8 border-slate-200/80 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.05)] sharp-edge">
              <div className="mb-8 border-b border-slate-200 pb-4">
                <h3 className="font-black text-slate-900 uppercase tracking-tight text-xl">Statistical Aggregation</h3>
                <p className="text-xs text-slate-500 font-bold uppercase tracking-[0.15em] mt-1">Module 03 // Metrics</p>
              </div>
              <StatsPanel data={resultData} />
            </div>

            <div className="flex justify-end pt-8">
              <button className="px-10 py-5 bg-slate-900 text-white font-black uppercase tracking-[0.15em] text-sm hover:bg-amber-500 hover:text-slate-900 transition-all duration-300 sharp-edge flex items-center gap-3 group" onClick={handleReset}>
                Initialize New Analysis
                <span className="group-hover:translate-x-2 transition-transform">→</span>
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
