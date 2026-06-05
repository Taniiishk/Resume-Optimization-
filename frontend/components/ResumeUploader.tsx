"use client";

import { useCallback, useRef, useState } from "react";

function UploadIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function FileIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

interface Props {
  onFile: (file: File) => void;
  loading: boolean;
}

export default function ResumeUploader({ onFile, loading }: Props) {
  const [filename, setFilename] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handle = useCallback((file: File | undefined) => {
    if (!file) return;
    const ok = file.name.endsWith(".pdf") || file.name.endsWith(".docx") || file.name.endsWith(".txt");
    if (!ok) { alert("Please upload a PDF, DOCX, or TXT file."); return; }
    setFilename(file.name);
    onFile(file);
  }, [onFile]);

  return (
    <div className="glass">
      <div className="upload-section-inner">
        <div className="section-label">Upload Resume</div>
        <div
          className={`upload-zone ${filename ? "has-file" : ""} ${dragOver ? "drag-over" : ""}`}
          onClick={() => !loading && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handle(e.dataTransfer.files[0]); }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => handle(e.target.files?.[0])}
            disabled={loading}
          />
          {filename ? (
            <div className="upload-filename">
              <FileIcon />
              {filename}
            </div>
          ) : (
            <>
              <div className="upload-icon-wrap"><UploadIcon /></div>
              <div className="upload-text-main">Drop your resume here</div>
              <div className="upload-text-sub">or click to browse &middot; PDF, DOCX, or TXT</div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
