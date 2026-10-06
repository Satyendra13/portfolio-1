import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  PhoneCall, PhoneOff, Mic, MicOff, Send, Upload, Trash2,
  FileText, Search, Settings, Database, X, ChevronRight,
  Volume2, Globe, Building2, Loader2
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Types ──────────────────────────────────────────────────
interface Turn {
  speaker: 'caller' | 'ai' | 'human';
  text: string;
  language: string;
  latency_ms?: number;
  intent?: string;
}

interface KBDoc {
  id: string;
  tenant_id: string;
  title: string;
  file_type: string;
  content_hash: string;
  created_at: string;
  chunk_count: number;
}

// ─── Audio Orb Component ────────────────────────────────────
function AudioOrb({ status }: { status: 'idle' | 'listening' | 'speaking' | 'processing' | 'human' }) {
  const colors = {
    idle: { bg: 'bg-slate-700', ring: 'border-slate-600', glow: '' },
    listening: { bg: 'bg-emerald-500', ring: 'border-emerald-400', glow: 'glow-success' },
    speaking: { bg: 'bg-cyan-500', ring: 'border-cyan-400', glow: 'glow-accent' },
    processing: { bg: 'bg-amber-500', ring: 'border-amber-400', glow: '' },
    human: { bg: 'bg-violet-500', ring: 'border-violet-400', glow: '' },
  };
  const c = colors[status];

  return (
    <div className="relative flex items-center justify-center">
      {/* Outer rings */}
      {status !== 'idle' && (
        <>
          <div className={`absolute w-32 h-32 rounded-full border ${c.ring} opacity-20 orb-ring`} />
          <div className={`absolute w-28 h-28 rounded-full border ${c.ring} opacity-30 orb-ring`} style={{ animationDelay: '0.5s' }} />
        </>
      )}

      {/* Main orb */}
      <div
        className={`relative w-20 h-20 rounded-full ${c.bg} ${c.glow} flex items-center justify-center transition-all duration-500 ${
          status !== 'idle' ? 'animate-breathe' : ''
        }`}
      >
        {/* Wave bars inside orb when speaking/listening */}
        {(status === 'speaking' || status === 'listening') && (
          <div className="flex items-center gap-[3px]">
            {[12, 20, 16, 24, 14, 18, 22].map((h, i) => (
              <div
                key={i}
                className="wave-bar bg-white/80"
                style={{ '--bar-h': `${h}px`, animationDelay: `${i * 0.1}s` } as React.CSSProperties}
              />
            ))}
          </div>
        )}
        {status === 'processing' && <Loader2 className="w-7 h-7 text-white animate-spin" />}
        {status === 'idle' && <Mic className="w-7 h-7 text-slate-400" />}
        {status === 'human' && <span className="text-2xl">👤</span>}
      </div>
    </div>
  );
}

// ─── Wave Visualizer (mini, for transcript) ─────────────────
function MiniWave() {
  return (
    <span className="inline-flex items-center gap-[2px] ml-2">
      {[6, 10, 8, 12, 7].map((h, i) => (
        <span
          key={i}
          className="wave-bar !w-[2px] !bg-cyan-400/60"
          style={{ '--bar-h': `${h}px`, animationDelay: `${i * 0.12}s` } as React.CSSProperties}
        />
      ))}
    </span>
  );
}

// ─── KB Sidebar ─────────────────────────────────────────────
function KBSidebar({ tenantId, isOpen, onClose }: { tenantId: string; isOpen: boolean; onClose: () => void }) {
  const [docs, setDocs] = useState<KBDoc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [searchQ, setSearchQ] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [tab, setTab] = useState<'docs' | 'search'>('docs');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/v1/tenants/${tenantId}/kb/documents`);
      if (res.ok) setDocs(await res.json());
    } catch {}
  }, [tenantId]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  const uploadFile = async (file: File) => {
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('title', file.name);
    try {
      const res = await fetch(`${API}/v1/tenants/${tenantId}/kb/documents`, { method: 'POST', body: fd });
      if (res.ok) fetchDocs();
    } catch (e) { console.error('Upload failed:', e); }
    finally { setUploading(false); }
  };

  const deleteDoc = async (id: string) => {
    try {
      await fetch(`${API}/v1/tenants/${tenantId}/kb/documents/${id}`, { method: 'DELETE' });
      fetchDocs();
    } catch {}
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQ.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API}/v1/tenants/${tenantId}/kb/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQ, top_k: 3 }),
      });
      if (res.ok) { const d = await res.json(); setSearchResults(d.hits || []); }
    } catch {} finally { setSearching(false); }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  if (!isOpen) return null;

  const fileExts: Record<string, string> = { md: '📝', txt: '📄', pdf: '📕', csv: '📊', docx: '📘' };

  return (
    <div className="h-full flex flex-col animate-slide-right" style={{ width: 360 }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold">Knowledge Base</span>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/[0.06]">
        {(['docs', 'search'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2.5 text-xs font-medium transition ${
              tab === t ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {t === 'docs' ? 'Documents' : 'Test Search'}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {tab === 'docs' ? (
          <>
            {/* Drop zone */}
            <div
              className={`drop-zone rounded-xl p-6 text-center cursor-pointer transition ${dragOver ? 'drag-over' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md,.csv"
                className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) uploadFile(f); }}
              />
              {uploading ? (
                <Loader2 className="w-6 h-6 text-cyan-400 mx-auto animate-spin" />
              ) : (
                <Upload className="w-6 h-6 text-cyan-400/60 mx-auto mb-2" />
              )}
              <p className="text-xs text-slate-400">
                {uploading ? 'Ingesting & chunking...' : 'Drop files or click to upload'}
              </p>
              <p className="text-[10px] text-slate-600 mt-1">PDF, DOCX, TXT, MD, CSV</p>
            </div>

            {/* Doc list */}
            {docs.length === 0 ? (
              <p className="text-xs text-slate-600 text-center py-4">No documents yet</p>
            ) : (
              docs.map(doc => (
                <div key={doc.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.04] hover:border-white/[0.08] transition group">
                  <span className="text-lg">{fileExts[doc.file_type] || '📄'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate">{doc.title}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{doc.chunk_count} chunks</p>
                  </div>
                  <button
                    onClick={() => deleteDoc(doc.id)}
                    className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </>
        ) : (
          <>
            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                placeholder="Test a query against KB..."
                className="flex-1 bg-white/[0.04] border border-white/[0.06] rounded-lg px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600"
              />
              <button
                type="submit"
                disabled={searching}
                className="px-3 py-2 bg-cyan-500/15 text-cyan-400 rounded-lg text-xs font-medium hover:bg-cyan-500/25 transition disabled:opacity-50"
              >
                {searching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              </button>
            </form>
            {searchResults.map((hit, i) => (
              <div key={i} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.04] space-y-1">
                <div className="flex justify-between text-[10px]">
                  <span className="text-slate-500 font-mono">Chunk {hit.chunk_id?.slice(0, 8)}</span>
                  <span className="text-emerald-400 font-semibold">{(hit.score * 100).toFixed(0)}%</span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed">{hit.chunk_text?.slice(0, 200)}</p>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Main App ───────────────────────────────────────────────
export default function App() {
  // State
  const [tenantId, setTenantId] = useState('acme_telecom');
  const [language, setLanguage] = useState('en');
  const [isCalling, setIsCalling] = useState(false);
  const [callId, setCallId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'listening' | 'speaking' | 'processing' | 'human'>('idle');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [textInput, setTextInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [isListeningMic, setIsListeningMic] = useState(false);
  const [autoListen, setAutoListen] = useState(true);

  // Refs
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const turnsRef = useRef<Turn[]>([]);
  const callingRef = useRef(false);
  const callIdRef = useRef<string | null>(null);
  const tenantIdRef = useRef(tenantId);
  const languageRef = useRef(language);
  const autoListenRef = useRef(true);
  const statusRef = useRef<string>('idle');
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Keep refs in sync
  useEffect(() => { turnsRef.current = turns; }, [turns]);
  useEffect(() => { callingRef.current = isCalling; }, [isCalling]);
  useEffect(() => { callIdRef.current = callId; }, [callId]);
  useEffect(() => { tenantIdRef.current = tenantId; }, [tenantId]);
  useEffect(() => { languageRef.current = language; }, [language]);
  useEffect(() => { autoListenRef.current = autoListen; }, [autoListen]);
  useEffect(() => { statusRef.current = status; }, [status]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  // ── TTS ─────────────────────────────────────────────────
  const speak = useCallback((text: string, lang: string) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
    u.rate = 1.0;
    u.onstart = () => setStatus('speaking');
    u.onend = () => {
      if (callingRef.current) {
        setStatus('listening');
        // Auto-start mic after AI finishes speaking
        if (autoListenRef.current) {
          setTimeout(() => {
            if (callingRef.current && statusRef.current !== 'processing') {
              startContinuousListening();
            }
          }, 300);
        }
      }
    };
    u.onerror = () => { if (callingRef.current) setStatus('listening'); };
    window.speechSynthesis.speak(u);
  }, []);

  // ── Continuous Speech Recognition ───────────────────────
  const startContinuousListening = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR || !callingRef.current) return;

    // Don't start if already listening or processing
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
      recognitionRef.current = null;
    }

    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = languageRef.current === 'hi' ? 'hi-IN' : 'en-US';

    rec.onstart = () => {
      setIsListeningMic(true);
      if (callingRef.current) setStatus('listening');
    };

    rec.onresult = (e: any) => {
      const text = e.results[0]?.[0]?.transcript;
      if (text?.trim()) {
        processUtterance(text);
      }
    };

    rec.onerror = () => setIsListeningMic(false);

    rec.onend = () => {
      setIsListeningMic(false);
      recognitionRef.current = null;
      // Re-start listening if still in call and auto-listen is on and not processing
      if (callingRef.current && autoListenRef.current && statusRef.current === 'listening') {
        setTimeout(() => {
          if (callingRef.current && statusRef.current === 'listening') {
            startContinuousListening();
          }
        }, 200);
      }
    };

    recognitionRef.current = rec;
    try { rec.start(); } catch {}
  }, []);

  // ── Process user utterance via backend ──────────────────
  const processUtterance = useCallback(async (text: string) => {
    if (!text.trim() || !callingRef.current || !callIdRef.current) return;

    // Stop recognition + TTS during processing
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
      recognitionRef.current = null;
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();

    setStatus('processing');
    setIsListeningMic(false);

    const callerTurn: Turn = { speaker: 'caller', text, language: languageRef.current };
    const updated = [...turnsRef.current, callerTurn];
    setTurns(updated);
    turnsRef.current = updated;

    try {
      const transcript = updated.map(t => ({ speaker: t.speaker, text: t.text, language: t.language }));
      const res = await fetch(`${API}/v1/calls/${callIdRef.current}/converse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantIdRef.current,
          text,
          language: languageRef.current,
          transcript,
        }),
      });

      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();

      const aiText = data.ai_response || 'I could not process that.';
      const aiLang = data.language || languageRef.current;

      if (aiLang !== languageRef.current) setLanguage(aiLang);

      const aiTurn: Turn = {
        speaker: 'ai',
        text: aiText,
        language: aiLang,
        latency_ms: Math.round(data.latency_ms || 0),
        intent: data.intent,
      };

      const withAi = [...turnsRef.current, aiTurn];
      setTurns(withAi);
      turnsRef.current = withAi;

      if (data.escalated) {
        setStatus('human');
      } else {
        speak(aiText, aiLang);
      }
    } catch (err) {
      console.error('Converse error:', err);
      const errTurn: Turn = { speaker: 'ai', text: 'Sorry, there was a connection issue. Please try again.', language: languageRef.current };
      const withErr = [...turnsRef.current, errTurn];
      setTurns(withErr);
      turnsRef.current = withErr;
      setStatus('listening');
      if (autoListenRef.current && callingRef.current) {
        setTimeout(() => startContinuousListening(), 500);
      }
    }
  }, [speak, startContinuousListening]);

  // ── Start Call ──────────────────────────────────────────
  const startCall = async () => {
    try {
      const res = await fetch(`${API}/v1/calls/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId, language, caller_name: 'Browser Caller' }),
      });
      const data = await res.json();
      setCallId(data.call_id);
      callIdRef.current = data.call_id;
      setIsCalling(true);
      callingRef.current = true;
      setCallDuration(0);

      // Timer
      timerRef.current = setInterval(() => setCallDuration(p => p + 1), 1000);

      // Greeting
      const greeting = tenantId === 'acme_telecom'
        ? (language === 'hi' ? 'एक्मे टेलीकॉम में कॉल करने के लिए धन्यवाद। मैं आपकी क्या मदद कर सकता हूँ?' : 'Thank you for calling Acme Telecom. How can I help you today?')
        : (language === 'hi' ? 'क्विककार्ट सपोर्ट में आपका स्वागत है! मैं आपकी क्या मदद कर सकती हूँ?' : 'Welcome to QuickCart! How can I assist you today?');

      const greetTurn: Turn = { speaker: 'ai', text: greeting, language, latency_ms: 80 };
      setTurns([greetTurn]);
      turnsRef.current = [greetTurn];
      speak(greeting, language);
    } catch (err) {
      console.error('Failed to start call:', err);
    }
  };

  // ── End Call ────────────────────────────────────────────
  const endCall = async () => {
    callingRef.current = false;
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (recognitionRef.current) { try { recognitionRef.current.stop(); } catch {} recognitionRef.current = null; }
    if (timerRef.current) clearInterval(timerRef.current);

    if (callIdRef.current) {
      try { await fetch(`${API}/v1/calls/${callIdRef.current}/end`, { method: 'POST' }); } catch {}
    }

    setIsCalling(false);
    setStatus('idle');
    setCallId(null);
    callIdRef.current = null;
    setIsListeningMic(false);
    setCallDuration(0);
  };

  // ── Text send ──────────────────────────────────────────
  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    processUtterance(textInput.trim());
    setTextInput('');
  };

  // ── Format timer ───────────────────────────────────────
  const fmt = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  // ── Status text ────────────────────────────────────────
  const statusText: Record<string, string> = {
    idle: 'Ready to connect',
    listening: 'Listening...',
    speaking: 'AI Speaking...',
    processing: 'Thinking...',
    human: 'Human Agent Connected',
  };

  const statusColor: Record<string, string> = {
    idle: 'text-slate-500',
    listening: 'text-emerald-400',
    speaking: 'text-cyan-400',
    processing: 'text-amber-400',
    human: 'text-violet-400',
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
      {/* ─── Top Bar ──────────────────────────────────── */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">A</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white tracking-tight">AsistLine <span className="text-cyan-400">AI</span></h1>
            <p className="text-[10px] text-slate-500 -mt-0.5">Voice Agent Console</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isCalling && (
            <span className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <span className={`w-1.5 h-1.5 rounded-full ${status === 'idle' ? 'bg-slate-500' : 'bg-emerald-400 dot-pulse'}`} />
              {fmt(callDuration)}
            </span>
          )}

          <button
            onClick={() => setSidebarOpen(p => !p)}
            className={`p-2 rounded-lg transition ${
              sidebarOpen ? 'bg-cyan-500/15 text-cyan-400' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
            }`}
            title="Knowledge Base"
          >
            <Database className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* ─── Main Content ─────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── Left: Voice Conversation ────────────── */}
        <div className="flex-1 flex flex-col">

          {/* Config bar (pre-call only) */}
          {!isCalling && (
            <div className="flex items-center gap-4 px-6 py-3 border-b border-white/[0.06] animate-fade-in">
              <div className="flex items-center gap-2">
                <Building2 className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={tenantId}
                  onChange={e => setTenantId(e.target.value)}
                  className="bg-transparent text-xs text-slate-300 border border-white/[0.08] rounded-lg px-2.5 py-1.5 cursor-pointer hover:border-white/[0.15] transition"
                >
                  <option value="acme_telecom">Acme Telecom</option>
                  <option value="quickcart">QuickCart</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={language}
                  onChange={e => setLanguage(e.target.value)}
                  className="bg-transparent text-xs text-slate-300 border border-white/[0.08] rounded-lg px-2.5 py-1.5 cursor-pointer hover:border-white/[0.15] transition"
                >
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                </select>
              </div>
              <label className="flex items-center gap-2 text-xs text-slate-400 ml-auto cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoListen}
                  onChange={e => setAutoListen(e.target.checked)}
                  className="w-3.5 h-3.5 accent-cyan-500 rounded"
                />
                Auto-listen
              </label>
            </div>
          )}

          {/* Orb + Status area */}
          <div className="flex flex-col items-center justify-center py-10 flex-shrink-0">
            <AudioOrb status={status} />
            <p className={`mt-5 text-sm font-medium ${statusColor[status]} transition-colors`}>
              {statusText[status]}
            </p>
            {isCalling && isListeningMic && status === 'listening' && (
              <p className="text-[10px] text-emerald-400/60 mt-1 flex items-center">
                <Mic className="w-3 h-3 mr-1" /> Microphone active
              </p>
            )}
          </div>

          {/* Transcript */}
          <div className="flex-1 overflow-y-auto px-6 pb-4">
            {turns.length === 0 && !isCalling ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-sm text-slate-500">Start a call to begin the conversation</p>
                <p className="text-xs text-slate-600 mt-1">Your voice will be recognized automatically</p>
              </div>
            ) : (
              <div className="max-w-2xl mx-auto space-y-3">
                {turns.map((t, i) => (
                  <div key={i} className={`flex ${t.speaker === 'caller' ? 'justify-end' : 'justify-start'} bubble-enter`}>
                    <div
                      className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-[13px] leading-relaxed ${
                        t.speaker === 'caller'
                          ? 'bg-cyan-600/20 text-cyan-50 rounded-br-md border border-cyan-500/20'
                          : t.speaker === 'human'
                          ? 'bg-violet-600/15 text-violet-100 rounded-bl-md border border-violet-500/20'
                          : 'bg-white/[0.04] text-slate-200 rounded-bl-md border border-white/[0.06]'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-semibold uppercase tracking-wider opacity-50">
                          {t.speaker === 'caller' ? 'You' : t.speaker === 'human' ? 'Human Agent' : 'AI'}
                        </span>
                        {t.intent && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/[0.06] text-slate-400">
                            {t.intent}
                          </span>
                        )}
                      </div>
                      <p>{t.text}</p>
                      {t.latency_ms !== undefined && t.latency_ms > 0 && (
                        <span className="text-[9px] text-emerald-400/60 font-mono mt-1 block">
                          {t.latency_ms}ms
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {status === 'processing' && (
                  <div className="flex justify-start bubble-enter">
                    <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-white/[0.04] border border-white/[0.06]">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                        <span className="text-xs text-slate-400">Thinking</span>
                        <MiniWave />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={transcriptEndRef} />
              </div>
            )}
          </div>

          {/* Bottom Controls */}
          <div className="border-t border-white/[0.06] px-6 py-3">
            {!isCalling ? (
              <button
                onClick={startCall}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium hover:from-cyan-400 hover:to-blue-500 transition-all active:scale-[0.98] glow-accent"
              >
                <PhoneCall className="w-4 h-4" />
                Start Conversation
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <form onSubmit={handleSend} className="flex-1 flex gap-2">
                  <input
                    value={textInput}
                    onChange={e => setTextInput(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-600"
                  />
                  <button
                    type="submit"
                    disabled={!textInput.trim()}
                    className="p-2.5 rounded-xl bg-cyan-500/15 text-cyan-400 hover:bg-cyan-500/25 transition disabled:opacity-30"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>

                {/* Manual mic toggle (when auto-listen is off) */}
                {!autoListen && (
                  <button
                    onClick={() => {
                      if (isListeningMic && recognitionRef.current) {
                        recognitionRef.current.stop();
                      } else {
                        startContinuousListening();
                      }
                    }}
                    className={`p-2.5 rounded-xl border transition ${
                      isListeningMic
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 animate-pulse'
                        : 'border-white/[0.08] text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {isListeningMic ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>
                )}

                <button
                  onClick={endCall}
                  className="p-2.5 rounded-xl bg-red-500/15 text-red-400 hover:bg-red-500/25 border border-red-500/20 transition active:scale-95"
                  title="End Call"
                >
                  <PhoneOff className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* ─── Right: KB Sidebar ───────────────────── */}
        {sidebarOpen && (
          <div className="border-l border-white/[0.06] bg-[#0d1220]">
            <KBSidebar tenantId={tenantId} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
          </div>
        )}
      </div>
    </div>
  );
}
