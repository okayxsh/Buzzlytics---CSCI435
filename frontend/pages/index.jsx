import React from 'react';
import { motion } from 'framer-motion';
import { Bug, Video, Radio } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-amber-500/30 overflow-hidden relative">
      
      {/* Dynamic Background Grid */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5 }}
          className="absolute inset-0 bg-[url('/hero-bg.png')] bg-cover bg-center opacity-30 mix-blend-multiply" 
        />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-amber-100/40 via-transparent to-transparent" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_0%,#000_70%,transparent_100%)]" />
      </div>

      {/* Header */}
      <header className="relative z-50 px-8 py-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 border border-amber-500/20 sharp-edge">
            <Bug className="w-6 h-6 text-amber-500" />
          </div>
          <h1 className="text-xl font-bold tracking-tighter text-slate-900 uppercase">Buzzlytics</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-100px)] px-6">
        
        {/* Title Section */}
        <div className="text-center max-w-5xl mx-auto mb-20">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 border border-amber-500/30 bg-amber-500/5 text-amber-600 text-xs font-bold uppercase tracking-[0.2em] backdrop-blur-sm sharp-edge"
          >
            <span className="w-2 h-2 bg-amber-500 sharp-edge animate-pulse"></span>
            System Online
          </motion.div>
          
          <h2 className="text-6xl md:text-8xl font-black text-slate-900 tracking-tighter mb-8 uppercase leading-[0.9]">
            <motion.span 
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="block"
            >
              Precision
            </motion.span>
            <motion.span 
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="block text-transparent bg-clip-text bg-gradient-to-br from-amber-500 to-amber-600"
            >
              Hive Analysis
            </motion.span>
          </h2>
          
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="text-lg md:text-xl text-slate-600 font-medium max-w-2xl mx-auto leading-relaxed"
          >
            Deploy advanced neural networks to extract real-time telemetry, detect Varroa mites, and evaluate colony health with mechanical accuracy.
          </motion.p>
        </div>

        {/* Action Modules */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-5xl relative z-20">
          
          <Link href="/analysis" legacyBehavior>
            <motion.a
              initial={{ opacity: 0, x: -40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.8 }}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group relative flex flex-col p-8 md:p-12 glass-panel border-slate-200 shadow-xl sharp-edge cursor-pointer overflow-hidden transition-all duration-300 hover:border-amber-500/50 hover:shadow-2xl"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-amber-500/0 via-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-300">
                <span className="text-amber-500 font-black">→</span>
              </div>
              
              <div className="w-16 h-16 bg-slate-900 flex items-center justify-center sharp-edge mb-8 group-hover:bg-amber-500 transition-colors duration-300">
                <Video className="w-8 h-8 text-white group-hover:text-slate-900 transition-colors" />
              </div>
              
              <h3 className="text-3xl font-black uppercase tracking-tight text-slate-900 mb-4">Video Telemetry</h3>
              <p className="text-slate-600 font-medium leading-relaxed mb-8 flex-1">
                Upload recorded hive footage for comprehensive post-processing analysis. Detect mites, count bees, and generate static health reports.
              </p>
              
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400 group-hover:text-amber-600 transition-colors">
                Module 01 // Initialize
              </div>
            </motion.a>
          </Link>

          <Link href="/webcam" legacyBehavior>
            <motion.a
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.9 }}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group relative flex flex-col p-8 md:p-12 glass-panel border-slate-200 shadow-xl sharp-edge cursor-pointer overflow-hidden transition-all duration-300 hover:border-emerald-500/50 hover:shadow-2xl"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/0 via-emerald-500/0 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-300">
                <span className="text-emerald-500 font-black">→</span>
              </div>
              
              <div className="w-16 h-16 bg-slate-900 flex items-center justify-center sharp-edge mb-8 group-hover:bg-emerald-500 transition-colors duration-300">
                <Radio className="w-8 h-8 text-white group-hover:text-slate-900 transition-colors" />
              </div>
              
              <h3 className="text-3xl font-black uppercase tracking-tight text-slate-900 mb-4">Live Monitoring</h3>
              <p className="text-slate-600 font-medium leading-relaxed mb-8 flex-1">
                Connect directly to active hive cameras. Stream real-time frames through the inference engine for live tracking and immediate alerts.
              </p>
              
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400 group-hover:text-emerald-600 transition-colors flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-emerald-500 sharp-edge animate-pulse"></span>
                Module 02 // Connect
              </div>
            </motion.a>
          </Link>
          
        </div>
        
        {/* Footer accoutrements */}
        <div className="absolute bottom-10 left-10 text-[10px] font-mono text-slate-400 uppercase tracking-widest pointer-events-none">
          SYS.VER: 2.0.4 <br/>
          ENV: PRODUCTION
        </div>
        <div className="absolute bottom-10 right-10 w-32 h-32 border-r border-b border-amber-500/20 sharp-edge pointer-events-none" />

      </main>
    </div>
  );
}
