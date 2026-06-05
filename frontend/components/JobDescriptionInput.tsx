"use client";

interface Props {
  value: string;
  onChange: (v: string) => void;
  loading: boolean;
}

export default function JobDescriptionInput({ value, onChange, loading }: Props) {
  return (
    <div className="glass" style={{ padding: "20px" }}>
      <div className="section-label">Job Description</div>
      <div className="textarea-wrap">
        <textarea
          placeholder="Paste the full job description here..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={loading}
        />
        {value.length > 20 && (
          <span className="char-count">{value.length.toLocaleString()} chars</span>
        )}
      </div>
    </div>
  );
}
