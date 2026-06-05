"use client";

import { useEffect, useState } from "react";
import { ATSScore } from "@/lib/api";

const LEVEL_CLASS: Record<string, string> = {
  Low: "level-Low", Medium: "level-Medium", Good: "level-Good", Excellent: "level-Excellent",
};

interface Props {
  label: string;
  score: ATSScore;
  variant: "before" | "after";
}

export default function ScoreCard({ label, score, variant }: Props) {
  const cls = variant === "before" ? "score-card-before" : "score-card-after";
  const pct = Math.min(score.total, 100);
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 150);
    return () => clearTimeout(t);
  }, []);

  const r = 52;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (pct / 100) * circumference;

  const ringColor =
    pct >= 80 ? "#22c55e" :
    pct >= 60 ? "#a855f7" :
    "#ef4444";

  const components: [string, number][] = [
    ["Keywords", score.breakdown.keyword_match],
    ["Skills", score.breakdown.skills_coverage],
    ["Sections", score.breakdown.section_completeness],
    ["Title Fit", score.breakdown.title_alignment],
    ["Action Verbs", score.breakdown.action_verbs],
    ["Format", score.breakdown.format_health],
  ];

  return (
    <div className={`score-card ${cls}`}>
      <div className="score-card-header">
        <span className="score-card-label">{label}</span>
        <span className={`score-level ${LEVEL_CLASS[score.level] || "level-Medium"}`}>
          {score.level}
        </span>
      </div>

      <div className="score-ring-wrap">
        <svg viewBox="0 0 120 120" className="score-ring-svg">
          <circle cx="60" cy="60" r={r} className="score-ring-track" />
          <circle
            cx="60" cy="60" r={r}
            className="score-ring-fill"
            stroke={ringColor}
            strokeDasharray={circumference}
            strokeDashoffset={animated ? offset : circumference}
          />
        </svg>
        <div className="score-ring-value">
          <span className="pct">{pct.toFixed(1)}%</span>
          <span className="pct-label">Score</span>
        </div>
      </div>

      <div className="score-breakdown">
        {components.map(([name, val]) => (
          <div className="breakdown-row" key={name}>
            <span className="breakdown-label">{name}</span>
            <div className="breakdown-bar-wrap">
              <div className="breakdown-bar">
                <div className="breakdown-bar-fill" style={{ width: `${Math.min(val, 100)}%` }} />
              </div>
            </div>
            <span className="breakdown-value">{val.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
