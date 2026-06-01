import { useState, useRef, useCallback } from 'react';
import { Upload, FileVideo, X } from 'lucide-react';
import { videoApi } from '../services/api';

const ACCEPTED_FORMATS = ['.mp4', '.avi', '.mov', '.webm'];
const ACCEPTED_MIME_TYPES = ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm', 'video/x-msvideo'];

export default function UploadVideo({ onUploadStart, onUploadComplete, onUploadError, uploading: uploadingProp }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);

  const isUploading = uploadingProp || uploading;

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const validateFile = (selectedFile) => {
    if (!selectedFile) return false;
    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_FORMATS.includes(ext)) {
      onUploadError?.(new Error(`Unsupported format. Accepted: ${ACCEPTED_FORMATS.join(', ')}`));
      return false;
    }
    return true;
  };

  const handleFileSelect = useCallback((selectedFile) => {
    if (validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleInputChange = useCallback((e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  }, [handleFileSelect]);

  const handleRemoveFile = useCallback(() => {
    setFile(null);
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);
    onUploadStart?.();

    const formData = new FormData();
    formData.append('video', file);

    try {
      const response = await videoApi.upload(formData, (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setProgress(percentCompleted);
      });
      setUploading(false);
      onUploadComplete?.(response);
    } catch (err) {
      setUploading(false);
      onUploadError?.(err);
    }
  }, [file, onUploadStart, onUploadComplete, onUploadError]);

  return (
    <div>
      <div
        className={`border-2 border-dashed p-12 text-center transition-all cursor-pointer relative sharp-edge ${
          dragOver ? 'border-amber-500 bg-amber-500/5 scale-[1.01]' : 
          file ? 'border-emerald-500 bg-emerald-500/5' : 
          'border-slate-300 bg-slate-50/50 hover:bg-amber-500/5 hover:border-amber-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_FORMATS.join(',')}
          onChange={handleInputChange}
          className="hidden"
        />

        <div className={`mb-4 flex justify-center ${dragOver || file ? 'text-amber-500' : 'text-slate-400'}`}>
          <Upload size={48} strokeWidth={1.5} />
        </div>

        {!file ? (
          <>
            <div className="text-lg font-black uppercase tracking-tight text-slate-800 mb-2">
              Drag and drop your footage
            </div>
            <div className="text-sm font-medium text-slate-500 mb-4 uppercase tracking-[0.1em]">
              or click to browse systems
            </div>
            <div className="text-xs text-slate-400 font-mono uppercase">
              Supported: {ACCEPTED_FORMATS.join(' | ')}
            </div>
          </>
        ) : (
          <div className="flex items-center gap-4 p-4 bg-white border border-slate-200 sharp-edge shadow-sm" onClick={(e) => e.stopPropagation()}>
            <FileVideo size={24} className="text-amber-500 shrink-0" />
            <div className="text-left flex-1 min-w-0">
              <div className="text-sm font-bold text-slate-800 truncate">{file.name}</div>
              <div className="text-xs text-slate-500 font-mono mt-1">{formatFileSize(file.size)}</div>
            </div>
            {!isUploading && (
              <button 
                className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 transition-colors sharp-edge"
                onClick={handleRemoveFile}
              >
                <X size={18} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Upload Progress */}
      {isUploading && (
        <div className="mt-6">
          <div className="w-full h-1.5 bg-slate-200 sharp-edge overflow-hidden">
            <div
              className="h-full bg-amber-500 sharp-edge transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-xs font-mono text-slate-500 mt-2 text-right uppercase">
            Uploading... {progress}%
          </div>
        </div>
      )}

      {/* Upload Button */}
      {file && !isUploading && (
        <div className="mt-6 flex gap-4">
          <button 
            className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-amber-500 text-slate-900 font-black uppercase tracking-widest text-sm hover:bg-amber-400 transition-colors sharp-edge"
            onClick={handleUpload}
          >
            <Upload size={18} />
            Initialize Upload
          </button>
          <button 
            className="px-6 py-4 bg-slate-100 text-slate-600 font-bold uppercase tracking-widest text-sm border border-slate-200 hover:bg-slate-200 hover:text-slate-900 transition-colors sharp-edge"
            onClick={handleRemoveFile}
          >
            Abort
          </button>
        </div>
      )}
    </div>
  );
}
