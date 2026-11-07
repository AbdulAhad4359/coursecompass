# CourseCompass — FastAPI + React

Version 3: separate React frontend and FastAPI backend. Preserves admission-relevance fixes, page citations, quote validation, PDF upload and optional Gemini generation. **This version does not use Streamlit.**

## Windows quick start

Install **Python 3.11 or 3.12** and **Node.js 22.12+ or 24 LTS**. Extract the ZIP completely. Open `coursecompass_fullstack` in VS Code: you should see `backend` and `frontend` inside it.

With Python 3.11 installed, you can double-click `start_backend.bat` and `start_frontend.bat`. Keep both windows open, then visit **http://localhost:5173**. Installation requires internet.

## Manual VS Code commands

Terminal 1, starting in `coursecompass_fullstack`:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use `py -3.12` instead if that is your installed Python version. No activation script needed.

Open Terminal 2 at the project root:

```powershell
cd frontend
npm ci
npm run dev
```

- React app: **http://localhost:5173**
- FastAPI Swagger docs: **http://127.0.0.1:8000/docs**
- Health check: **http://127.0.0.1:8000/api/health**

Click **Try the demo handbook** or upload your own PDF. Stop both servers with Ctrl+C. Do not use the previous Streamlit commands.

macOS/Linux: in `backend`, run `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. In a second terminal, enter `frontend` and run `npm ci`, `npm run dev`.

## Gemini configuration (optional)

Copy `backend/.env.example` to `backend/.env`:

```dotenv
GEMINI_API_KEY=your_actual_key
GEMINI_MODEL=gemini-flash-latest
```

Restart the backend, refresh React, and enable Gemini under **Settings & help**. Get a key at https://aistudio.google.com/apikey. If your account cannot use the default alias, choose an available generateContent model with structured-output support. Access and quota depend on your account; API usage may incur costs.

The key stays on the backend. Never put it in frontend code. Gemini mode sends your question and retrieved passages to Google. Local evidence mode searches locally and displays passages; it does not generate an eligibility verdict. Live Gemini was not tested without a key.

## Project structure

| File/folder | Purpose |
|---|---|
| `backend/app/main.py` | FastAPI routes, file upload, isolated document sessions |
| `backend/app/rag.py` | PDF extraction, retrieval, Gemini and citation checks |
| `backend/data/demo_handbook.pdf` | Fictional five-page demonstration source |
| `backend/tests` | RAG, admission and API regression tests |
| `frontend/src/main.jsx` | React chat, source explorer, settings and PDF preview |
| `frontend/src/api.js` | API client, timeouts and errors |
| `frontend/src/style.css` | Responsive styling |
| `frontend/vite.config.js` | Development/preview API proxy |
| `frontend/package-lock.json` | Reproducible npm dependency installation |

React -> FastAPI -> page-aware PDF chunks -> TF-IDF retrieval -> optional Gemini -> validated source quotes -> cited answers. No ChromaDB or neural embeddings are used; vectors are sparse TF-IDF in memory. Chunks are 320 words with 80-word overlap and never cross pages. Up to four eligible passages are returned. Scores are heuristic, not confidence.

## API routes

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Connectivity and non-secret configuration |
| POST | `/api/handbooks/demo` | New session with fictional demo PDF |
| POST | `/api/handbooks/upload` | Multipart upload field `file` |
| GET | `/api/handbooks/current` | Session document metadata |
| GET | `/api/handbooks/pages/{page}` | Page text and labels |
| GET | `/api/handbooks/pdf` | Original PDF bytes |
| POST | `/api/chat` | JSON question and `use_ai` boolean |
| DELETE | `/api/session` | Remove document session |

Document creation returns `session_id`. Supply it in `X-Session-ID` for document/chat routes. Sessions are isolated in backend memory, expire after one hour of inactivity, and are limited to 20 concurrent sessions. Restart clears all sessions. Full browser refresh clears the frontend conversation and token; re-upload the PDF. This is a local demo with one backend worker, not a production enrollment service.

Vite proxies `/api` to port 8000. FastAPI permits configured local origins through CORS. For public hosting add authentication, HTTPS, upload/rate limits, persistent storage and a production reverse proxy. The current service is bound to loopback by the launchers.

## Features and limits

- PDF upload: 20 MB, at most 600 pages. Original PDF preview and page inspection.
- Clickable page buttons for generated claims, expandable source quotes and JSON conversation export.
- BSCS/Computer Science and selected other program aliases; admission filters exclude scholarships/directories and standalone-number matches.
- Explicit insufficiency when program-specific evidence is not found. Missing evidence does not prove a requirement is absent.
- Source citations use 1-based PDF positions, which may differ from printed page numbers.
- No OCR: scanned pages and complex tables can fail extraction. Conservative admission filters may miss cross-page rules, mixed admission/scholarship chunks or unsupported aliases.
- Quote validation detects invented quotations, but does not guarantee correct interpretation or complete evidence retrieval.
- Previous chat messages are display history only; questions should be self-contained.
- API keys and PDFs are not included in conversation exports. Keys are loaded from backend configuration.
- Optional Google Fonts fall back to system fonts when offline.

The demo handbook is fictional. Your UCP handbook from the previous local app is not bundled or evaluated here; upload it again. Old editions do not establish current admission policy. There is no live transcript, seat or enrollment integration.

## Verify and present

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

From `frontend`:

```powershell
npm run build
npm run preview
```

Preview uses port 4173 and proxies `/api`; the backend must remain running. `dist` is frontend output only.

Demo sequence: show both terminals and Swagger docs; load the fictional handbook; ask `What are the prerequisites for CS301?`; inspect PDF page 4; ask `I have 45% in Intermediate. Am I eligible for BSCS?` and show correct abstention because this demo lacks that rule; upload your actual handbook; enable Gemini with your own key; inspect cited evidence and export chat.

## Troubleshooting

- `requirements.txt` missing: enter `backend`; `package.json` missing: enter `frontend`.
- `npm` unrecognized: install Node.js and reopen VS Code.
- Backend disconnected: start FastAPI on port 8000 and refresh the frontend.
- Port occupied: stop earlier servers. Vite fails rather than silently selecting a different port.
- Session expired: reload demo or upload again.
- Invalid model: use an ID rather than a display name/URL. Outer spaces and `models/` prefix are accepted.
- Gemini not configured: set backend `.env`, restart backend, refresh browser, enable Gemini.

References: https://fastapi.tiangolo.com/tutorial/request-files/ · https://fastapi.tiangolo.com/tutorial/cors/ · https://vite.dev/guide/ · https://ai.google.dev/gemini-api/docs/structured-output
