# ATS Resume Optimizer

Upload your resume, paste a job description, and let AI rewrite your summary, align your skills, and weave in the right keywords — all while keeping every fact true to your experience.

## Features

- **AI-powered optimization** — Gemini rewrites your resume summary, skills, and keyword coverage to target the job description
- **ATS scoring** — 6-dimension breakdown (keywords, skills, sections, title fit, action verbs, format health) with an overall score
- **Before/after comparison** — see exactly what changed and what keywords were added
- **Editable skills & keywords** — add your own desired skills/keywords and re-optimize
- **Export** — download the optimized resume as PDF or DOCX
- **Interactive score rings** — animated circular progress visualization
- **Premium dark theme** — glassmorphism, animated gradient orbs, micro-interactions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (static export), TypeScript, CSS |
| Backend | Python, FastAPI, uvicorn |
| AI | Google Gemini API |
| PDF generation | ReportLab |
| DOCX generation | python-docx |
| Serving | Custom Node.js HTTP server |

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Copy .env.example to .env and add your GEMINI_API_KEY
copy .env.example .env
```

Edit `backend/.env` and set:

```
GEMINI_API_KEY=your_key_here
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

### Run

```bash
# Terminal 1 — backend
start_backend.bat

# Terminal 2 — frontend (static server)
start.bat
# or: node serve-static.js
```

- Backend API: `http://127.0.0.1:8001`
- Frontend: `http://localhost:3000`

## Project Structure

```
rem/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # FastAPI endpoints
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models
│   │   └── services/
│   │       ├── optimizer.py       # Gemini prompt + post-processing
│   │       ├── pdf_renderer.py    # ReportLab PDF export
│   │       ├── docx_renderer.py   # python-docx export
│   │       ├── ats_scorer.py      # ATS scoring algorithm
│   │       └── resume_parser.py   # File extraction + validation
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── globals.css            # All styling
│   │   └── page.tsx               # Main page
│   ├── components/
│   │   ├── ResultsView.tsx        # Results panel with tabs
│   │   ├── ScoreCard.tsx          # Animated score ring
│   │   ├── ResumeUploader.tsx     # Drag/drop file upload
│   │   └── JobDescriptionInput.tsx # JD textarea
│   └── lib/
│       └── api.ts                 # API client functions
├── serve-static.js                # Node.js static file server
├── start.bat                      # Launch both servers
├── start_backend.bat              # Launch backend only
├── render.yaml                    # Render blueprint deployment
└── README.md
```

## Deploy to Render (Both Backend & Frontend — Free)

Both services deploy together from the same repo using the included `render.yaml` blueprint.

### Steps

1. Push the repo to GitHub
2. **Backend**: Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint** → connect repo — `render.yaml` auto-creates the backend web service
3. **Frontend**: Go to **New** → **Static Site** → connect repo:

   | Setting | Value |
   |---------|-------|
   | Root directory | `frontend` |
   | Build command | `npm install && npm run build` |
   | Publish directory | `out` |

4. **Add env vars** in both services:

   | Service | Variable | Value |
   |---------|----------|-------|
   | Backend | `GEMINI_API_KEY` | your key from `.env.example` |
   | Frontend | `NEXT_PUBLIC_API_URL` | `https://ats-resume-backend.onrender.com` |

5. Both deploy and your site is live.

## Usage

1. Open `http://localhost:3000`
2. Upload a resume (PDF, DOCX, or TXT)
3. Paste the full job description (50+ chars)
4. Click **Optimize Resume**
5. Review the score comparison, changes, tips
6. Add extra skills/keywords and re-optimize if needed
7. Download the optimized resume as PDF or DOCX
