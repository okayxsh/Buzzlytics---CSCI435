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
    formData.append('file', file);

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
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-all ${
          dragOver ? 'border-honey-400 bg-honey-50 scale-[1.01]' :
          file ? 'border-forest-300 bg-forest-50' :
          'border-line-strong bg-sand/40 hover:border-honey-300 hover:bg-honey-50/60'
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

        {!file ? (
          <>
            <div className="mb-5 flex justify-center">
              <div className={`flex h-16 w-16 items-center justify-center rounded-2xl ${dragOver ? 'bg-honey-100 text-honey-600' : 'bg-cream text-forest-600 shadow-soft'}`}>
                <Upload size={28} strokeWidth={1.8} />
              </div>
            </div>
            <div className="font-display text-xl font-semibold text-ink">
              Drop your hive footage here
            </div>
            <div className="mt-1.5 text-sm text-ink-soft">
              or <span className="font-semibold text-forest-700">browse your files</span>
            </div>
            <div className="mt-4 text-xs font-medium text-ink-faint">
              Supports {ACCEPTED_FORMATS.join('  ·  ')}
            </div>
          </>
        ) : (
          <div className="flex items-center gap-4 rounded-xl border border-line bg-cream p-4 text-left shadow-soft" onClick={(e) => e.stopPropagation()}>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-honey-50 text-honey-600">
              <FileVideo size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-ink">{file.name}</div>
              <div className="mt-0.5 text-xs text-ink-faint tabular">{formatFileSize(file.size)}</div>
            </div>
            {!isUploading && (
              <button
                className="rounded-lg p-2 text-ink-faint transition-colors hover:bg-[#F6E6DF] hover:text-clay"
                onClick={handleRemoveFile}
                aria-label="Remove file"
              >
                <X size={18} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Upload progress */}
      {isUploading && (
        <div className="mt-6">
          <div className="h-2 w-full overflow-hidden rounded-full bg-sand">
            <div
              className="h-full rounded-full bg-forest-500 transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-2 text-right text-xs font-medium text-ink-soft tabular">
            Uploading… {progress}%
          </div>
        </div>
      )}

      {/* Actions */}
      {file && !isUploading && (
        <div className="mt-6 flex gap-3">
          <button className="btn-primary flex-1" onClick={handleUpload}>
            <Upload size={18} />
            Start analysis
          </button>
          <button className="btn-soft" onClick={handleRemoveFile}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
