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
└── README.md
```

## Deploy to Cloudflare Pages

The frontend is a static Next.js export and works perfectly on Cloudflare Pages.

### Steps

1. Push the repo to GitHub
2. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
3. Select your repo and configure:

   | Setting | Value |
   |---------|-------|
   | Build command | `cd frontend && npm install && npm run build` |
   | Build output directory | `frontend/out/` |
   | Root directory | (leave blank — use repo root) |

4. Add environment variables (Production):

   | Variable | Value |
   |----------|-------|
   | `NEXT_PUBLIC_API_URL` | URL of your deployed backend (see below) |

5. Click **Save and Deploy**

### Backend

The Python/FastAPI backend **cannot** run on Cloudflare Pages. Deploy it on:

- [Railway](https://railway.app/) — `railway up` from `backend/`
- [Render](https://render.com/) — Web Service, start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- [Fly.io](https://fly.io/) — `fly launch` from `backend/`
- Any VPS with Docker or directly via uvicorn

Deploy the backend first, then set `NEXT_PUBLIC_API_URL` to its URL.

### SPA Routing

A `_redirects` file in `frontend/public/` ensures all routes serve `index.html` for client-side navigation. This is copied to the build output automatically.

## Usage

1. Open `http://localhost:3000`
2. Upload a resume (PDF, DOCX, or TXT)
3. Paste the full job description (50+ chars)
4. Click **Optimize Resume**
5. Review the score comparison, changes, tips
6. Add extra skills/keywords and re-optimize if needed
7. Download the optimized resume as PDF or DOCX
