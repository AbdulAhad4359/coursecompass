import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { Compass, BookOpen, Upload, ArrowUp, FileText, Check, MessageSquare, Settings, Download, ChevronRight, LoaderCircle, X, Plus } from 'lucide-react';
import { api } from './api';
import './style.css';

function App() {
  const [doc, setDoc] = useState(null), [health, setHealth] = useState(null), [error, setError] = useState('');
  const [messages, setMessages] = useState([]), [question, setQuestion] = useState(''), [busy, setBusy] = useState(false);
  const [useAI, setUseAI] = useState(false), [tab, setTab] = useState('chat'), [page, setPage] = useState(1), [pageData, setPageData] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(''), [loadingPage, setLoadingPage] = useState(false);
  const fileInput = useRef(), bottom = useRef(), urlRef = useRef('');
  useEffect(() => { api('/health').then(setHealth).catch(e => setError(e.message)); return () => { if (urlRef.current) URL.revokeObjectURL(urlRef.current); }; }, []);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [messages, busy]);
  useEffect(() => {
    if (!doc || tab !== 'sources') return;
    let active = true;
    setLoadingPage(true); setPageData(null);
    api(`/handbooks/pages/${page}`, { token: doc.session_id }).then(d => { if (active) setPageData(d); }).catch(e => { if (active) setError(e.message); }).finally(() => { if (active) setLoadingPage(false); });
    return () => { active = false; };
  }, [doc, page, tab]);
  async function loadDocument(file) {
    if (busy) return;
    if (file && file.size > 20 * 1024 * 1024) { setError('Select a PDF of 20 MB or smaller.'); return; }
    setBusy(true); setError('');
    try {
      const form = new FormData(); if (file) form.append('file', file);
      const next = await api(file ? '/handbooks/upload' : '/handbooks/demo', { method: 'POST', ...(file ? { body: form } : {}) });
      const old = doc;
      setDoc(next); setMessages([]); setPage(1); setPageData(null); setTab('chat');
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = ''; setPdfUrl('');
      if (old) api('/session', { method: 'DELETE', token: old.session_id }).catch(() => {});
    } catch (e) { setError(e.message); }
    finally { setBusy(false); if (fileInput.current) fileInput.current.value = ''; }
  }
  async function ask(text = question) {
    if (!text.trim() || busy || !doc) return;
    setQuestion(''); setError(''); setBusy(true);
    const entry = { question: text.trim(), pending: true };
    setMessages(m => [...m, entry]);
    try {
      const result = await api('/chat', { token: doc.session_id, method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: text.trim(), use_ai: useAI }) });
      setMessages(m => [...m.slice(0, -1), result]);
    } catch (e) { setMessages(m => [...m.slice(0, -1), { question: text, failed: e.message }]); }
    finally { setBusy(false); }
  }
  async function showPDF() {
    try { const blob = await api('/handbooks/pdf', { token: doc.session_id }); if (urlRef.current) URL.revokeObjectURL(urlRef.current); const url = URL.createObjectURL(blob); urlRef.current = url; setPdfUrl(url); }
    catch (e) { setError(e.message); }
  }
  function exportChat() {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ handbook: doc?.filename, messages }, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = 'coursecompass_chat.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="shell">
    <aside className="sidebar">
      <a className="brand" href="#"><span className="brand-icon"><Compass size={25}/></span><span>CourseCompass<small>YOUR ACADEMIC GUIDE</small></span></a>
      <button className="new-chat" disabled={busy} onClick={() => setMessages([])}><Plus size={17}/> New conversation</button>
      <p className="section-label">WORKSPACE</p>
      <nav>{[['chat', MessageSquare, 'Ask the handbook'], ['sources', BookOpen, 'Source explorer'], ['settings', Settings, 'Settings & help']].map(([id, Icon, title]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}><Icon size={18}/>{title}{tab === id && <ChevronRight size={15}/>}</button>)}</nav>
      <div className="source-card"><p className="section-label">YOUR KNOWLEDGE SOURCE</p><FileText size={27}/><strong>{doc?.filename || 'No handbook yet'}</strong><p>{doc ? `${doc.pages} pages · ${doc.chunks} passages` : 'Add a university handbook to get started.'}</p><input ref={fileInput} type="file" accept="application/pdf,.pdf" hidden onChange={e => e.target.files[0] && loadDocument(e.target.files[0])}/><button className="upload" disabled={busy} onClick={() => fileInput.current.click()}><Upload size={15}/> Upload handbook</button><button className="text-button" disabled={busy} onClick={() => loadDocument()}>Try the demo handbook <ChevronRight size={13}/></button><small>PDF · up to 20 MB</small></div>
      <div className="sidebar-bottom"><span className={`dot ${health ? 'online' : ''}`}/>{health ? 'FastAPI connected' : 'Backend not connected'}<p>Built for thoughtful academic planning.</p></div>
    </aside>
    <main><header><span>WORKSPACE <ChevronRight size={13}/> {tab === 'chat' ? 'Handbook assistant' : tab === 'sources' ? 'Source explorer' : 'Settings'}</span><span className="mode-badge"><span className="dot online"/>{useAI ? 'Gemini RAG' : 'Local evidence'}</span></header>
      {error && <div className="error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError('')}><X size={16}/></button></div>}
      <div className="content">
        {doc?.demo && <div className="notice">DEMO EDITION <span>This handbook is fictional. Upload your university PDF for real questions.</span></div>}
        {!!doc?.empty_pages.length && <div className="notice">Extraction incomplete <span>Pages {doc.empty_pages.join(', ')} may need OCR.</span></div>}
        {tab === 'chat' && <>
          <div className="heading"><div><p className="eyebrow">A LITTLE CLARITY FOR YOUR NEXT STEP</p><h1>Ask. Understand. Plan ahead.</h1><p>Find the rules that matter, with the pages to back them up.</p></div><span className="book-symbol"><BookOpen size={34}/></span></div>
          {!messages.length && <><div className="intro"><span className="mini-icon"><Compass size={24}/></span><div><h2>Your handbook, made easier.</h2><p>Ask about admissions or course prerequisites. I’ll look for supporting evidence and tell you when it isn’t enough.</p><div className="trust"><span><Check size={14}/> Page citations</span><span><Check size={14}/> Source transparency</span><span><Check size={14}/> No guessed eligibility</span></div></div></div>
          <p className="section-label">START WITH A QUESTION</p><div className="suggestions">{['What are the prerequisites for CS301?', 'I have 45% in Intermediate. Am I eligible for BSCS?', 'What minimum grade is required for CS102?'].map((q,i) => <button disabled={!doc || busy} key={q} onClick={() => ask(q)}><span>0{i+1}</span>{q}<ChevronRight size={17}/></button>)}</div>{!doc && <p className="empty-hint">← Upload a handbook or select the demo to begin.</p>}</>}
          <div className="conversation" aria-live="polite">{messages.map((m,i) => <article key={i}><div className="question"><span>YOU</span><p>{m.question}</p></div><div className="answer"><Compass size={22}/><div>{m.pending ? <p className="thinking"><LoaderCircle size={16} className="spin"/> Checking the handbook…</p> : m.failed ? <p className="failure">{m.failed}</p> : <><small className="answer-label">COURSECOMPASS · {m.mode} · {m.status.replaceAll('_',' ')}</small>{m.claims.map((c,j) => <div className="claim" key={j}><p>{c.text} <button className="citation" onClick={() => { setPage(c.page); setTab('sources'); }}>PDF p. {c.page}</button></p><details><summary>Supporting quote</summary><blockquote>{c.quote}</blockquote></details></div>)}{m.missing && <p className="answer-note">{m.missing}</p>}{m.hits.filter(h => !m.claims.length || m.claims.some(c => c.source_id === h.chunk.id)).map(h => <details className="evidence" key={h.chunk.id}><summary><FileText size={14}/> Source passage · PDF page {h.chunk.page}</summary><p>{h.chunk.text}</p><button className="text-button" onClick={() => { setPage(h.chunk.page); setTab('sources'); }}>Inspect page <ChevronRight size={14}/></button></details>)}</>}</div></div></article>)}</div><div ref={bottom}/>
          <form className="composer" onSubmit={e => { e.preventDefault(); ask(); }}><textarea aria-label="Your question" placeholder={doc ? 'Ask a question about your handbook…' : 'Load a handbook to start asking questions…'} maxLength={2000} value={question} disabled={!doc || busy} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); } }}/><div><span><FileText size={14}/>{doc ? 'Searching your handbook only' : 'No handbook selected'}</span><button aria-label="Send question" disabled={!doc || busy || !question.trim()}>{busy ? <LoaderCircle className="spin" size={20}/> : <ArrowUp size={20}/>}</button></div></form>
          <p className="footnote">Answers reflect the uploaded edition. Always verify important decisions with your university.</p>{messages.length > 0 && <button className="text-button" onClick={exportChat}><Download size={15}/> Export conversation</button>}
        </>}
        {tab === 'sources' && <><p className="eyebrow">FOLLOW THE EVIDENCE</p><h1>Source explorer</h1><p className="muted">PDF page positions start at 1 and may differ from printed page numbers.</p>{!doc ? <div className="intro">Load a handbook from the sidebar.</div> : <><div className="source-tools"><label>PDF page <input aria-label="PDF page" type="number" min="1" max={doc.pages} value={page} onChange={e => setPage(Math.min(doc.pages, Math.max(1, Number(e.target.value) || 1)))}/><span> of {doc.pages}</span></label><button className="upload" onClick={showPDF}><BookOpen size={15}/> Open original PDF</button></div>{loadingPage ? <p>Loading page…</p> : pageData?.passages.length ? pageData.passages.map(p => <div className="page-text" key={p.id}><small>{p.id} · PDF label {p.label}</small><p>{p.text}</p></div>) : <p>No text extracted from this page. Inspect the original PDF or run OCR.</p>}{pdfUrl && <><a href={pdfUrl} target="_blank" rel="noreferrer">Open PDF in a new tab</a><iframe title="Original handbook PDF" src={`${pdfUrl}#page=${page}`}/></>}</>}</>}
        {tab === 'settings' && <><p className="eyebrow">MAKE IT WORK FOR YOU</p><h1>Settings & help</h1><div className="settings-card"><h2>Answer mode</h2><label className="toggle"><input type="checkbox" checked={useAI} disabled={!health?.ai_configured || busy} onChange={e => setUseAI(e.target.checked)}/> Generate concise answers with Gemini</label><p>Gemini sends your question and retrieved passages to Google. Local evidence mode searches and displays passages without sending them to an AI provider.</p>{!health?.ai_configured && <div className="notice">Gemini is not configured.<span>Add GEMINI_API_KEY to backend/.env and restart the backend, then refresh this page.</span></div>}{health?.configuration_error && <p className="failure">{health.configuration_error}</p>}<small>Model: {health?.model || 'not configured'}. API keys stay on the backend.</small></div><div className="settings-card"><h2>How this project works</h2><p>React → FastAPI → page-aware PDF extraction → TF-IDF retrieval → optional Gemini generation → source and quote validation.</p><p>Admission searches exclude scholarship/directory passages and require a program-specific rule. If that evidence cannot be retrieved, the assistant abstains.</p><p>Scanned pages, complex tables, cross-page rules and unrecognized program abbreviations can be missed. Quote validation does not guarantee correct interpretation. Ask self-contained questions; chat history is not sent to the model.</p><p>Handbooks live in backend memory for one hour of inactivity. Restarting the backend clears them. This is a local demonstration app, not a production enrollment service.</p></div></>}
      </div>
    </main>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
