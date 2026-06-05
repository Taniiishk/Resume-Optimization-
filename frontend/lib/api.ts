const API = "http://127.0.0.1:8001";

export interface ContactInfo {
  name: string; email: string; phone: string; location: string;
  linkedin: string; github: string; portfolio: string;
}
export interface ExperienceItem {
  title: string; company: string; location: string;
  start_date: string; end_date: string; bullets: string[];
}
export interface EducationItem {
  degree: string; school: string; location: string;
  start_date: string; end_date: string; gpa: string; details: string[];
}
export interface ProjectItem {
  name: string; link: string; tech: string[]; bullets: string[];
}
export interface CertificationItem {
  name: string; issuer: string; date: string;
}
export interface Resume {
  contact: ContactInfo;
  summary: string;
  skills: string[];
  experience: ExperienceItem[];
  education: EducationItem[];
  projects: ProjectItem[];
  certifications: CertificationItem[];
  raw_text: string;
}

export interface ScoreBreakdown {
  keyword_match: number; skills_coverage: number; section_completeness: number;
  title_alignment: number; action_verbs: number; format_health: number;
}
export interface ATSScore {
  total: number; breakdown: ScoreBreakdown;
  matched_keywords: string[]; missing_keywords: string[];
  matched_skills: string[]; missing_skills: string[];
  recommendations: string[]; level: string;
}
export interface OptimizeResponse {
  optimized_resume: Resume; before_score: ATSScore;
  after_score: ATSScore; changes_summary: string[];
}

export async function parseResume(file: File): Promise<Resume> {
  const fd = new FormData();
  fd.set("file", file);
  const res = await fetch(`${API}/api/parse-resume`, { method: "POST", body: fd });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Parse failed"); }
  const data = await res.json();
  return data.resume;
}

export async function optimize(
  resume: Resume, jdText: string,
  extra_skills?: string[], extra_keywords?: string[],
): Promise<OptimizeResponse> {
  const res = await fetch(`${API}/api/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume, jd_text: jdText, extra_skills, extra_keywords }),
  });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Optimization failed"); }
  return res.json();
}

export async function renderPdf(resume: Resume): Promise<Blob> {
  const res = await fetch(`${API}/api/render-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume }),
  });
  if (!res.ok) throw new Error("PDF render failed");
  return res.blob();
}

export async function renderDocx(resume: Resume): Promise<Blob> {
  const res = await fetch(`${API}/api/render-docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume }),
  });
  if (!res.ok) throw new Error("DOCX render failed");
  return res.blob();
}
