"use client";

import { useState } from "react";
import { ATSScore, renderPdf, renderDocx, Resume } from "@/lib/api";
import ScoreCard from "./ScoreCard";

interface Props {
  beforeScore: ATSScore;
  afterScore: ATSScore;
  changes: string[];
  optimizedResume: Resume;
  originalResume: Resume;
  jdText: string;
  onReoptimize: (extra_skills: string[], extra_keywords: string[]) => Promise<void>;
}

export default function ResultsView({ beforeScore, afterScore, changes, optimizedResume, originalResume, jdText, onReoptimize }: Props) {
  const [pdfLoading, setPdfLoading] = useState(false);
  const [reoptLoading, setReoptLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"summary" | "keywords" | "skills" | "recommendations">("summary");

  const [extraSkills, setExtraSkills] = useState<string[]>([]);
  const [extraKeywords, setExtraKeywords] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [keywordInput, setKeywordInput] = useState("");

  const covered = beforeScore.missing_keywords.filter(
    (k) => !afterScore.missing_keywords.includes(k)
  );

  const origSkills = new Set(originalResume.skills.map((s) => s.toLowerCase()));
  const addedSkills = optimizedResume.skills.filter((s) => !origSkills.has(s.toLowerCase()));

  const handleDownload = async (format: "pdf" | "docx") => {
    setPdfLoading(true);
    try {
      const blob = await (format === "pdf" ? renderPdf(optimizedResume) : renderDocx(optimizedResume));
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const name = (optimizedResume.contact.name || "Resume").replace(/[^a-zA-Z0-9_-]/g, "_");
      a.href = url;
      a.download = `${name}_ATS.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert("Download failed: " + e.message);
    } finally {
      setPdfLoading(false);
    }
  };

  const addTag = (list: string[], setter: (v: string[]) => void, input: string, setInput: (v: string) => void) => {
    const val = input.trim();
    if (val && !list.some((t) => t.toLowerCase() === val.toLowerCase())) {
      setter([...list, val]);
    }
    setInput("");
  };

  const removeTag = (list: string[], setter: (v: string[]) => void, index: number) => {
    setter(list.filter((_, i) => i !== index));
  };

  const handleReoptimize = async () => {
    setReoptLoading(true);
    try {
      await onReoptimize(extraSkills, extraKeywords);
    } finally {
      setReoptLoading(false);
    }
  };

  const tabs = [
    { id: "summary" as const, label: "Summary" },
    { id: "keywords" as const, label: "Keywords" },
    { id: "skills" as const, label: "Skills" },
    { id: "recommendations" as const, label: "Tips" },
  ];

  return (
    <div className="glass results-section">
      <h2>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        Results
      </h2>

      <div className="score-row">
        <ScoreCard label="Original Score" score={beforeScore} variant="before" />
        <div className="score-vs">VS</div>
        <ScoreCard label="Optimized Score" score={afterScore} variant="after" />
      </div>

      <div className="tabs-container">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? "active" : ""}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "summary" && (
        <div className="result-block">
          {changes.length > 0 && (
            <>
              <div className="result-block-title">Changes Made</div>
              <ul className="changes-list">
                {changes.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </>
          )}
          {optimizedResume.summary && originalResume.summary !== optimizedResume.summary && (
            <div style={{ marginTop: 16 }}>
              <div className="result-block-title">Rewritten Summary</div>
              <div className="summary-box">{optimizedResume.summary}</div>
            </div>
          )}
        </div>
      )}

      {activeTab === "keywords" && (
        <div className="result-block">
          {covered.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div className="result-block-title">
                <span style={{ color: "#86efac" }}>{'\u2713'}</span> Keywords Now Covered ({covered.length})
              </div>
              <div className="kw-list">
                {covered.map((k) => <span key={k} className="kw-tag kw-matched">{k}</span>)}
              </div>
            </div>
          )}
          {afterScore.missing_keywords.length > 0 && (
            <div>
              <div className="result-block-title">
                <span style={{ color: "#fca5a5" }}>○</span> Still Missing ({afterScore.missing_keywords.length})
              </div>
              <div className="kw-list">
                {afterScore.missing_keywords.map((k) => <span key={k} className="kw-tag kw-missing">{k}</span>)}
              </div>
            </div>
          )}
          {covered.length === 0 && afterScore.missing_keywords.length === 0 && (
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No keywords extracted from the JD.</div>
          )}

          <div className="section-divider">
            <div className="result-block-title">Add Extra Keywords</div>
            <div className="input-row">
              <input
                placeholder="Type a keyword and press Add\u2026"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addTag(extraKeywords, setExtraKeywords, keywordInput, setKeywordInput)}
              />
              <button className="input-add-btn" onClick={() => addTag(extraKeywords, setExtraKeywords, keywordInput, setKeywordInput)}>Add</button>
            </div>
            {extraKeywords.length > 0 && (
              <div className="kw-list">
                {extraKeywords.map((k, i) => (
                  <span key={i} className="kw-tag kw-matched" style={{ cursor: "pointer" }} onClick={() => removeTag(extraKeywords, setExtraKeywords, i)}>
                    {k} {'\u2715'}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "skills" && (
        <div className="result-block">
          {addedSkills.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div className="result-block-title">
                <span style={{ color: "#86efac" }}>+</span> Skills Aligned / Added ({addedSkills.length})
              </div>
              <div className="kw-list">
                {addedSkills.map((s) => <span key={s} className="kw-tag kw-matched">{s}</span>)}
              </div>
            </div>
          )}
          <div>
            <div className="result-block-title" style={{ color: "var(--text-secondary)" }}>
              Full Skill Set ({optimizedResume.skills.length})
            </div>
            <div className="kw-list">
              {optimizedResume.skills.map((s) => (
                <span key={s} className="kw-tag kw-tag-neutral">{s}</span>
              ))}
            </div>
          </div>

          <div className="section-divider">
            <div className="result-block-title">Add Skills You Want Included</div>
            <div className="input-row">
              <input
                placeholder="Type a skill and press Add\u2026"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addTag(extraSkills, setExtraSkills, skillInput, setSkillInput)}
              />
              <button className="input-add-btn" onClick={() => addTag(extraSkills, setExtraSkills, skillInput, setSkillInput)}>Add</button>
            </div>
            {extraSkills.length > 0 && (
              <div className="kw-list">
                {extraSkills.map((s, i) => (
                  <span key={i} className="kw-tag kw-matched" style={{ cursor: "pointer" }} onClick={() => removeTag(extraSkills, setExtraSkills, i)}>
                    {s} {'\u2715'}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "recommendations" && (
        <div className="result-block">
          {afterScore.recommendations.length > 0 ? (
            <ul className="rec-list">
              {afterScore.recommendations.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No recommendations &mdash; your resume looks strong!</div>
          )}
        </div>
      )}

      {/* Re-optimize */}
      <div className="reoptimize-area">
        <button className="btn-primary" onClick={handleReoptimize} disabled={reoptLoading || (extraSkills.length === 0 && extraKeywords.length === 0)}>
          {reoptLoading ? (
            <>
              <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2, margin: 0 }} />
              Re-optimizing\u2026
            </>
          ) : (
            "Re-optimize with Added Skills & Keywords"
          )}
        </button>
      </div>

      {/* Download */}
      <div className="download-area">
        <button className="btn-download" onClick={() => handleDownload("pdf")} disabled={pdfLoading}>
          {pdfLoading ? (
            <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2, margin: 0 }} />
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          )}
          Download PDF
        </button>
        <button className="btn-download" onClick={() => handleDownload("docx")} disabled={pdfLoading}>
          {pdfLoading ? (
            <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2, margin: 0 }} />
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          )}
          Download DOCX
        </button>
      </div>
    </div>
  );
}
