"use client";

import { useState } from "react";
import ResumeUploader from "@/components/ResumeUploader";
import JobDescriptionInput from "@/components/JobDescriptionInput";
import ResultsView from "@/components/ResultsView";
import { parseResume, optimize, OptimizeResponse, Resume } from "@/lib/api";

export default function Home() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [parsedResume, setParsedResume] = useState<Resume | null>(null);
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<OptimizeResponse | null>(null);

  const handleFile = (file: File) => {
    setResumeFile(file);
    setParsedResume(null);
    setResult(null);
    setError("");
  };

  const handleOptimize = async () => {
    if (!resumeFile || !jdText.trim()) return;
    setResult(null);
    setError("");
    setLoading(true);
    try {
      let resume = parsedResume;
      if (!resume) {
        setStatus("Parsing resume\u2026");
        resume = await parseResume(resumeFile);
        setParsedResume(resume);
      }
      setStatus("Analyzing with Gemini AI\u2026");
      const resp = await optimize(resume, jdText);
      setResult(resp);
      setStatus("");
    } catch (e: any) {
      setError(e.message);
      setStatus("");
    } finally {
      setLoading(false);
    }
  };

  const canOptimize = resumeFile && jdText.trim().length > 50 && !loading;

  return (
    <>
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
      <div className="container">
        {/* Hero */}
        <div className="hero">
          <div className="hero-badge">Make Your Resume ATS Friendly</div>
          <h1>Turn any resume into a<br />perfect match for the job</h1>
          <p>
            Upload your resume, paste a job description, and let AI rewrite your summary,
            align your skills, and weave in the right keywords &mdash; all while keeping
            every fact true to your experience.
          </p>
        </div>

        {/* Input grid */}
        <div className="input-grid">
          <ResumeUploader onFile={handleFile} loading={loading} />
          <JobDescriptionInput value={jdText} onChange={setJdText} loading={loading} />
        </div>

        {/* Optimize button */}
        <div style={{ marginBottom: 20 }}>
          <button className="btn-primary" disabled={!canOptimize} onClick={handleOptimize}>
            {loading ? (
              <>
                <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2, margin: 0 }} />
                <span>{status || "Working\u2026"}</span>
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
                <span>Optimize Resume</span>
              </>
            )}
          </button>
        </div>

        {/* Parsed file info */}
        {parsedResume && !result && !loading && (
          <div className="glass" style={{ padding: "16px 20px" }}>
            <div className="file-info">
              <span className="file-info-pill">{'\u2713'} Parsed</span>
              {parsedResume.contact.name && (
                <>
                  <strong>{parsedResume.contact.name}</strong>
                  <span className="divider">{'\u00B7'}</span>
                </>
              )}
              <span>{parsedResume.skills.length} skills</span>
              <span className="divider">{'\u00B7'}</span>
              <span>{parsedResume.experience.length} roles</span>
              <span className="divider">{'\u00B7'}</span>
              <span>{parsedResume.raw_text.length.toLocaleString()} chars</span>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && !result && (
          <div className="glass" style={{ padding: 0, marginTop: 20, border: "none" }}>
            <div className="loading-overlay">
              <div className="spinner" />
              <div className="loading-text">{status}</div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && <div className="error-box">{error}</div>}

        {/* Results */}
        {result && (
          <ResultsView
            beforeScore={result.before_score}
            afterScore={result.after_score}
            changes={result.changes_summary}
            optimizedResume={result.optimized_resume}
            originalResume={parsedResume!}
            jdText={jdText}
            onReoptimize={async (skills, keywords) => {
              setLoading(true);
              setError("");
              setStatus("Re-optimizing with your additions\u2026");
              try {
                const r = await optimize(parsedResume!, jdText, skills, keywords);
                setResult(r);
                setStatus("");
              } catch (e: any) {
                setError(e.message);
                setStatus("");
              } finally {
                setLoading(false);
              }
            }}
          />
        )}

        {/* Footer */}
        <div className="footer">
          ATS Resume Optimizer &mdash; built with Next.js, FastAPI &amp; Gemini
        </div>
      </div>
    </>
  );
}
