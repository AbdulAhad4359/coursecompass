"""Local presentation API. One isolated handbook per opaque browser session."""
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import monotonic
from uuid import uuid4
import os
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .rag import Handbook, answer, normalize_model

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
app = FastAPI(title='CourseCompass API', version='3.0.0', description='PDF-backed admission and prerequisite questions with validated page citations.')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('FRONTEND_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','), allow_methods=['GET','POST','DELETE'], allow_headers=['Content-Type','X-Session-ID'])

@dataclass
class Session:
    book: Handbook
    data: bytes
    demo: bool
    touched: float

sessions: dict[str, Session] = {}
lock = RLock()
TTL = 3600
MAX_SESSIONS = 20

def get_session(token):
    with lock:
        for sid in list(sessions):
            if monotonic() - sessions[sid].touched > TTL:
                del sessions[sid]
        item = sessions.get(token or '')
        if not item:
            raise HTTPException(404, 'Handbook session expired or missing. Reload the demo or upload your PDF again.')
        item.touched = monotonic()
        return item

def metadata(item):
    return {'filename': item.book.filename, 'pages': item.book.page_count, 'chunks': len(item.book.chunks), 'empty_pages': item.book.empty_pages, 'demo': item.demo}

def create_session(data, name, demo):
    try:
        book = Handbook(data, name)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    item = Session(book, data, demo, monotonic())
    with lock:
        for sid in list(sessions):
            if monotonic() - sessions[sid].touched > TTL:
                del sessions[sid]
        if len(sessions) >= MAX_SESSIONS:
            raise HTTPException(503, 'Session capacity reached. Remove an old session or retry later.')
        sid = str(uuid4())
        sessions[sid] = item
    return {'session_id': sid, **metadata(item)}

@app.get('/api/health')
def health():
    configured = bool(os.getenv('GEMINI_API_KEY', '').strip())
    error = None
    try:
        model = normalize_model(os.getenv('GEMINI_MODEL', 'gemini-flash-latest'))
    except ValueError as exc:
        model, error = '', str(exc)
    return {'status': 'ok', 'ai_configured': configured and not error, 'model': model, 'configuration_error': error}

@app.post('/api/handbooks/demo')
def demo():
    return create_session((ROOT/'data/demo_handbook.pdf').read_bytes(), 'demo_handbook.pdf', True)

@app.post('/api/handbooks/upload')
def upload(file: UploadFile = File(...)):
    try:
        data = file.file.read(20 * 1024 * 1024 + 1)
    finally:
        file.file.close()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, 'PDF must be 20 MB or smaller.')
    if not data.startswith(b'%PDF-'):
        raise HTTPException(422, 'Please select a valid PDF file.')
    name = (file.filename or 'handbook.pdf').replace('\\', '/').split('/')[-1]
    return create_session(data, name, False)

@app.get('/api/handbooks/current')
def current(x_session_id: str | None = Header(default=None)):
    return metadata(get_session(x_session_id))

@app.get('/api/handbooks/pdf')
def pdf(x_session_id: str | None = Header(default=None)):
    return Response(get_session(x_session_id).data, media_type='application/pdf', headers={'Cache-Control': 'no-store'})

@app.get('/api/handbooks/pages/{page}')
def page_text(page: int, x_session_id: str | None = Header(default=None)):
    book = get_session(x_session_id).book
    if page < 1 or page > book.page_count:
        raise HTTPException(404, 'Page is outside this handbook.')
    return {'page': page, 'passages': [{'id': c.id, 'label': c.label, 'text': c.text} for c in book.chunks if c.page == page]}

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    use_ai: bool = False

@app.post('/api/chat')
def chat(request: ChatRequest, x_session_id: str | None = Header(default=None)):
    item = get_session(x_session_id)
    question = request.question.strip()
    if not question:
        raise HTTPException(422, 'Enter a question.')
    key = os.getenv('GEMINI_API_KEY', '').strip() if request.use_ai else ''
    if request.use_ai and not key:
        raise HTTPException(409, 'Add GEMINI_API_KEY to backend/.env and restart the backend, or turn off Gemini mode.')
    # The synchronous route runs in FastAPI's thread pool, not the event loop.
    return answer(item.book, question, key, os.getenv('GEMINI_MODEL', 'gemini-flash-latest'))

@app.delete('/api/session')
def remove_session(x_session_id: str | None = Header(default=None)):
    with lock:
        sessions.pop(x_session_id or '', None)
    return {'deleted': True}
