import { useState, useRef, useCallback } from 'react';
import { Upload, ImageIcon, X } from 'lucide-react';
import { imageApi } from '../services/api';

const ACCEPTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'];
const ACCEPTED_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/bmp',
  'image/tiff',
];

export default function UploadImage({ onUploadStart, onUploadComplete, onUploadError, uploading: uploadingProp }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
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
      setResult(null);
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
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    onUploadStart?.();

    try {
      const response = await imageApi.process(file);
      const data = response.data ?? response;
      setResult(data);
      setUploading(false);
      onUploadComplete?.(data);
    } catch (err) {
      setUploading(false);
      onUploadError?.(err);
    }
  }, [file, onUploadStart, onUploadComplete, onUploadError]);

  return (
    <div>
      {/* Drop zone */}
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
          accept="image/*"
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
              Drop your hive image here
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
              <ImageIcon size={22} />
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

      {/* Upload spinner */}
      {isUploading && (
        <div className="mt-6 flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-sand">
            <div className="h-full w-full animate-pulse rounded-full bg-forest-500 opacity-60" />
          </div>
          <div className="text-xs font-medium text-ink-soft">Analysing…</div>
        </div>
      )}

      {/* Actions */}
      {file && !isUploading && !result && (
        <div className="mt-6 flex gap-3">
          <button className="btn-primary flex-1" onClick={handleUpload}>
            <Upload size={18} />
            Analyse image
          </button>
          <button className="btn-soft" onClick={handleRemoveFile}>
            Cancel
          </button>
        </div>
      )}

      {/* Result panel */}
      {result && (
        <div className="mt-6 space-y-4">
          {/* Annotated image */}
          {result.annotated_image && (
            <div className="overflow-hidden rounded-2xl border border-line shadow-soft">
              <img
                src={`data:image/jpeg;base64,${result.annotated_image}`}
                alt="Annotated hive frame"
                className="w-full object-contain"
              />
            </div>
          )}

          {/* Summary + motion */}
          <div className="rounded-2xl border border-line bg-cream p-5 shadow-soft">
            {result.summary && (
              <div className="mb-3">
                <div className="data-label mb-1">Summary</div>
                <p className="text-sm text-ink-soft leading-relaxed">{result.summary}</p>
              </div>
            )}
            {result.motion !== undefined && result.motion !== null && (
              <div>
                <div className="data-label mb-1">Motion Score</div>
                <div className="font-display text-2xl font-semibold text-ink">
                  {typeof result.motion === 'number'
                    ? result.motion.toFixed(2)
                    : result.motion}
                </div>
              </div>
            )}
          </div>

          {/* Reset */}
          <div className="flex gap-3">
            <button className="btn-soft flex-1" onClick={handleRemoveFile}>
              Analyse another image
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
