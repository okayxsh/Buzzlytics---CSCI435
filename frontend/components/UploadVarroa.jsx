import { useState, useRef, useCallback } from 'react';
import { ScanSearch, Upload, X } from 'lucide-react';
import { varroaApi } from '../services/api';

const ACCEPTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp'];

export default function UploadVarroa({
  onUploadStart,
  onUploadComplete,
  onUploadError,
  uploading: uploadingProp,
}) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const isUploading = uploadingProp || uploading;

  const validateFile = (selectedFile) => {
    if (!selectedFile) return false;
    const ext = `.${selectedFile.name.split('.').pop().toLowerCase()}`;
    if (!ACCEPTED_FORMATS.includes(ext)) {
      onUploadError?.(new Error(`Unsupported format. Accepted: ${ACCEPTED_FORMATS.join(', ')}`));
      return false;
    }
    return true;
  };

  const handleFileSelect = useCallback((selectedFile) => {
    if (validateFile(selectedFile)) setFile(selectedFile);
  }, []);

  const handleRemoveFile = useCallback(() => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setUploading(true);
    onUploadStart?.();
    try {
      const response = await varroaApi.process(file);
      setUploading(false);
      onUploadComplete?.(response.data ?? response);
    } catch (err) {
      setUploading(false);
      onUploadError?.(err);
    }
  }, [file, onUploadStart, onUploadComplete, onUploadError]);

  return (
    <div>
      <div
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-all ${
          dragOver
            ? 'scale-[1.01] border-honey-400 bg-honey-50'
            : file
              ? 'border-forest-300 bg-forest-50'
              : 'border-line-strong bg-sand/40 hover:border-honey-300 hover:bg-honey-50/60'
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragOver(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const droppedFile = e.dataTransfer?.files?.[0];
          if (droppedFile) handleFileSelect(droppedFile);
        }}
        onClick={() => !file && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) => {
            const selectedFile = e.target.files?.[0];
            if (selectedFile) handleFileSelect(selectedFile);
          }}
          className="hidden"
        />

        {!file ? (
          <>
            <div className="mb-5 flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-cream text-forest-600 shadow-soft">
                <ScanSearch size={28} strokeWidth={1.8} />
              </div>
            </div>
            <div className="font-display text-xl font-semibold text-ink">
              Drop a close-up bee crop here
            </div>
            <div className="mt-1.5 text-sm text-ink-soft">
              Varroa mode expects one cropped bee image
            </div>
            <div className="mt-4 text-xs font-medium text-ink-faint">
              Supports {ACCEPTED_FORMATS.join(' / ')}
            </div>
          </>
        ) : (
          <div className="flex items-center gap-4 rounded-xl border border-line bg-cream p-4 text-left shadow-soft" onClick={(e) => e.stopPropagation()}>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-honey-50 text-honey-600">
              <ScanSearch size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-ink">{file.name}</div>
              <div className="mt-0.5 text-xs text-ink-faint">
                Close-up varroa inspection
              </div>
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

      {isUploading && (
        <div className="mt-6 flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-sand">
            <div className="h-full w-full animate-pulse rounded-full bg-forest-500 opacity-60" />
          </div>
          <div className="text-xs font-medium text-ink-soft">Classifying...</div>
        </div>
      )}

      {file && !isUploading && (
        <div className="mt-6 flex gap-3">
          <button className="btn-primary flex-1" onClick={handleUpload}>
            <Upload size={18} />
            Classify varroa crop
          </button>
          <button className="btn-soft" onClick={handleRemoveFile}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
