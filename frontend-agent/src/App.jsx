import React, { useState, useEffect, useRef } from 'react';
import * as LivekitClient from 'livekit-client';
import { 
  Headphones, 
  UserCheck, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  PhoneCall, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Radio, 
  FileText, 
  Sparkles, 
  ShieldCheck, 
  RefreshCw,
  LogOut,
  ChevronRight,
  User,
  Inbox
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

export default function App() {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [agentStatus, setAgentStatus] = useState('available'); // 'available' | 'busy' | 'offline'
  const [wsConnected, setWsConnected] = useState(false);

  // Queue of escalations
  const [escalations, setEscalations] = useState([]);
  const [selectedEscalation, setSelectedEscalation] = useState(null);
  const [activeCallDetails, setActiveCallDetails] = useState(null);
  const [transcript, setTranscript] = useState([]);

  // In-Call state
  const [isInCall, setIsInCall] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [callDuration, setCallDuration] = useState(0);

  const roomRef = useRef(null);
  const wsRef = useRef(null);
  const timerRef = useRef(null);
  const transcriptEndRef = useRef(null);
  const audioElRef = useRef(null);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  // Load tenants on startup
  useEffect(() => {
    async function fetchTenants() {
      try {
        const res = await fetch(`${API_BASE}/tenants`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setTenants(data);
            setSelectedTenant(data[0]);
            return;
          }
        }
      } catch (e) {
        console.warn('Failed to load tenants:', e);
      }
      const demo = { id: 'apex-logistics', name: 'Apex Logistics Support' };
      setTenants([demo]);
      setSelectedTenant(demo);
    }
    fetchTenants();
  }, []);

  // Fetch pending escalations whenever selected tenant changes
  const fetchPendingEscalations = async (tenantId) => {
    if (!tenantId) return;
    try {
      const res = await fetch(`${API_BASE}/escalations/pending?tenant_id=${tenantId}`);
      if (res.ok) {
        const data = await res.json();
        setEscalations(data);
        if (data.length > 0 && !selectedEscalation) {
          selectEscalation(data[0]);
        }
      }
    } catch (e) {
      console.warn('Error fetching escalations:', e);
    }
  };

  useEffect(() => {
    if (selectedTenant) {
      fetchPendingEscalations(selectedTenant.id);
    }
  }, [selectedTenant]);

  // WebSocket for Real-time Escalation Push
  useEffect(() => {
    if (!selectedTenant) return;

    const wsUrl = `${WS_BASE}/ws/agent/${selectedTenant.id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      console.log('Agent WebSocket connected to tenant:', selectedTenant.id);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'new_escalation') {
          // Play subtle notification chime
          try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
            osc.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.15);
          } catch (err) {}

          setEscalations((prev) => {
            const exists = prev.some((x) => x.id === data.escalation_id);
            if (exists) return prev;
            const newEsc = {
              id: data.escalation_id,
              call_id: data.call_id,
              tenant_id: data.tenant_id,
              reason: data.reason,
              summary: data.summary,
              status: 'pending',
              created_at: data.created_at,
            };
            return [newEsc, ...prev];
          });
        }
        if (data.event === 'escalation_claimed') {
          setEscalations((prev) => prev.filter((x) => x.id !== data.escalation_id));
        }
      } catch (err) {
        console.error('WS message error:', err);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [selectedTenant]);

  // Duration timer
  useEffect(() => {
    if (isInCall) {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isInCall]);

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  const selectEscalation = async (esc) => {
    setSelectedEscalation(esc);
    try {
      const res = await fetch(`${API_BASE}/calls/${esc.call_id}/transcript`);
      if (res.ok) {
        const data = await res.json();
        setActiveCallDetails(data);
        setTranscript(data.turns || []);
      }
    } catch (e) {
      console.warn('Failed to load call transcript:', e);
    }
  };

  const acceptEscalation = async () => {
    if (!selectedEscalation) return;

    try {
      const res = await fetch(`${API_BASE}/escalations/${selectedEscalation.id}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: 'agent-alex-mercer' }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to accept escalation');
      }

      const { livekit_token, livekit_url, room_name } = await res.json();

      // Join the exact same LiveKit Room
      const room = new LivekitClient.Room({
        adaptiveStream: true,
        dynacast: true,
      });
      roomRef.current = room;

      room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === 'audio') {
          console.log(`Agent subscribed to audio from: ${participant.identity}`);
          const el = track.attach();
          el.id = `agent-listen-${participant.identity}`;
          el.autoplay = true;
          document.body.appendChild(el);
          audioElRef.current = el;
          el.play().catch(console.warn);
        }
      });

      // Live transcript events from data channel
      room.on(LivekitClient.RoomEvent.DataReceived, (payload) => {
        try {
          const decoded = new TextDecoder().decode(payload);
          const data = JSON.parse(decoded);
          if (data.type === 'caption') {
            setTranscript((prev) => [
              ...prev,
              { speaker: data.speaker, text: data.text, timestamp: new Date().toISOString() },
            ]);
          }
        } catch (e) {}
      });

      await room.connect(livekit_url, livekit_token);

      // Attach any already published audio tracks
      room.remoteParticipants.forEach((p) => {
        p.trackPublications.forEach((pub) => {
          if (pub.track && pub.track.kind === 'audio') {
            console.log(`Agent attaching pre-existing track from ${p.identity}`);
            const el = pub.track.attach();
            el.id = `agent-listen-${p.identity}`;
            el.autoplay = true;
            document.body.appendChild(el);
            audioElRef.current = el;
            el.play().catch(console.warn);
          }
        });
      });

      await room.localParticipant.setMicrophoneEnabled(true);

      setIsInCall(true);
      setIsMuted(false);
      setCallDuration(0);
      setAgentStatus('busy');

      // Remove from pending list
      setEscalations((prev) => prev.filter((x) => x.id !== selectedEscalation.id));

    } catch (err) {
      alert(`Could not join call: ${err.message}`);
    }
  };

  const toggleMute = async () => {
    if (roomRef.current?.localParticipant) {
      const nextMute = !isMuted;
      await roomRef.current.localParticipant.setMicrophoneEnabled(!nextMute);
      setIsMuted(nextMute);
    }
  };

  const endCall = async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    if (audioElRef.current) {
      audioElRef.current.remove();
      audioElRef.current = null;
    }
    if (selectedEscalation) {
      try {
        await fetch(`${API_BASE}/escalations/${selectedEscalation.id}/resolve`, { method: 'POST' });
        await fetch(`${API_BASE}/calls/${selectedEscalation.call_id}/end`, { method: 'POST' });
      } catch (e) {}
    }

    setIsInCall(false);
    setSelectedEscalation(null);
    setAgentStatus('available');
    if (selectedTenant) {
      fetchPendingEscalations(selectedTenant.id);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500/30">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 py-3.5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Headphones className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-tight text-white">AsistLine AI</span>
                <span className="bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Human Agent Portal
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Tier-2 Escalation & Live Handoff Desk</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Tenant switcher */}
            <div className="flex items-center space-x-2 bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs">
              <span className="text-slate-400 font-medium">Tenant:</span>
              <select
                disabled={isInCall}
                value={selectedTenant?.id || ''}
                onChange={(e) => {
                  const t = tenants.find((x) => x.id === e.target.value);
                  if (t) setSelectedTenant(t);
                }}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                {tenants.map((t) => (
                  <option key={t.id} value={t.id} className="bg-slate-900 text-white">
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Agent Status Selector */}
            <div className="flex items-center space-x-1.5 bg-slate-800/80 border border-slate-700/60 rounded-lg p-1 text-xs">
              <button
                onClick={() => setAgentStatus('available')}
                className={`px-2.5 py-1 rounded font-medium flex items-center space-x-1.5 transition ${
                  agentStatus === 'available' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse"></span>
                <span>Available</span>
              </button>
              <button
                onClick={() => setAgentStatus('busy')}
                className={`px-2.5 py-1 rounded font-medium flex items-center space-x-1.5 transition ${
                  agentStatus === 'busy' ? 'bg-amber-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-amber-300"></span>
                <span>Busy</span>
              </button>
              <button
                onClick={() => setAgentStatus('offline')}
                className={`px-2.5 py-1 rounded font-medium flex items-center space-x-1.5 transition ${
                  agentStatus === 'offline' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                <span>Offline</span>
              </button>
            </div>

            {/* Agent Profile */}
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800 text-xs">
              <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400">
                AM
              </div>
              <span className="font-medium text-slate-300 hidden sm:inline">Alex Mercer</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout: 3-column Desk */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        
        {/* Left Column: Incoming Escalation Queue */}
        <div className="lg:col-span-4 bg-slate-900/70 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between backdrop-blur-xl shadow-xl">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Inbox className="w-4 h-4 text-blue-400" />
                <h2 className="font-bold text-sm text-white">Escalation Queue</h2>
                <span className="bg-rose-500/20 text-rose-300 text-[10px] font-bold px-2 py-0.5 rounded-full border border-rose-500/30">
                  {escalations.length}
                </span>
              </div>
              <button
                onClick={() => selectedTenant && fetchPendingEscalations(selectedTenant.id)}
                className="text-slate-400 hover:text-white transition p-1"
                title="Refresh queue"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* WebSocket Status Indicator */}
            <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950/60 border border-slate-800/80 rounded-lg text-[11px] text-slate-400">
              <span>Real-time Push:</span>
              <span className="flex items-center space-x-1.5">
                <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400' : 'bg-rose-500'}`}></span>
                <span className={wsConnected ? 'text-emerald-400 font-semibold' : 'text-rose-400'}>
                  {wsConnected ? 'Active' : 'Disconnected'}
                </span>
              </span>
            </div>

            {/* Queue Cards */}
            <div className="space-y-3 overflow-y-auto max-h-[580px] pr-1">
              {escalations.length === 0 ? (
                <div className="text-center py-20 text-xs text-slate-500 space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto" />
                  <p>No pending escalations.</p>
                  <p className="text-[11px] text-slate-600">AI voice worker is resolving calls autonomously.</p>
                </div>
              ) : (
                escalations.map((esc) => {
                  const isSelected = selectedEscalation?.id === esc.id;
                  return (
                    <div
                      key={esc.id}
                      onClick={() => !isInCall && selectEscalation(esc)}
                      className={`p-4 rounded-xl border text-xs cursor-pointer transition relative group ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-500/10'
                          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="bg-rose-500/10 text-rose-300 font-semibold px-2 py-0.5 rounded text-[10px] border border-rose-500/20 truncate max-w-[170px]">
                          {esc.reason}
                        </span>
                        <span className="text-slate-500 text-[10px] flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(esc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </span>
                      </div>

                      <p className="text-slate-300 line-clamp-2 leading-relaxed mb-3 text-[11px]">
                        {esc.summary}
                      </p>

                      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
                        <span className="font-mono text-slate-500">Call: #{esc.call_id.slice(0, 8)}</span>
                        <span className="text-indigo-400 group-hover:translate-x-0.5 transition flex items-center font-medium">
                          Review <ChevronRight className="w-3 h-3 ml-0.5" />
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Center / Right Column: Call Detail & Live Transcript View */}
        <div className="lg:col-span-8 bg-slate-900/70 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-xl shadow-xl">
          {selectedEscalation ? (
            <div className="flex flex-col h-full justify-between space-y-6">
              {/* Header Banner: Call Context */}
              <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white text-sm">Escalated Inbound Call</span>
                    <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono text-[10px] px-2 py-0.5 rounded">
                      ID: {selectedEscalation.call_id}
                    </span>
                  </div>

                  {isInCall ? (
                    <div className="flex items-center space-x-3">
                      <span className="flex items-center space-x-1.5 text-xs text-emerald-400 font-semibold font-mono">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span>LIVE WITH CUSTOMER: {formatTime(callDuration)}</span>
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded font-semibold">
                      Ready for Hand-off
                    </span>
                  )}
                </div>

                {/* AI Generated 2-3 Line Summary Card */}
                <div className="p-3 bg-indigo-950/20 border border-indigo-500/20 rounded-lg text-xs space-y-1">
                  <div className="flex items-center space-x-1.5 text-indigo-400 font-semibold text-[11px]">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>AI Call Summary (Zero Repeat Guarantee)</span>
                  </div>
                  <p className="text-slate-200 leading-relaxed text-xs">
                    {selectedEscalation.summary}
                  </p>
                </div>
              </div>

              {/* Live Transcript Pane */}
              <div className="flex-1 flex flex-col justify-between bg-slate-950/60 border border-slate-800 rounded-xl p-4 min-h-[360px]">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs text-slate-400">
                  <span className="font-semibold text-slate-300 flex items-center space-x-1.5">
                    <FileText className="w-3.5 h-3.5 text-blue-400" />
                    <span>Live Call Transcript</span>
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {transcript.length} turns logged
                  </span>
                </div>

                {/* Turns scroll feed */}
                <div className="flex-1 overflow-y-auto max-h-[320px] my-3 space-y-2.5 pr-2 text-xs">
                  {transcript.length === 0 ? (
                    <div className="text-center py-12 text-slate-500 italic">
                      Loading transcript history...
                    </div>
                  ) : (
                    transcript.map((t, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-xl max-w-[85%] leading-relaxed ${
                          t.speaker === 'customer'
                            ? 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700/60'
                            : t.speaker === 'human'
                            ? 'ml-auto bg-emerald-600 text-white rounded-br-none shadow-md'
                            : 'ml-auto bg-indigo-600 text-white rounded-br-none shadow-md'
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] opacity-75 mb-1 font-semibold">
                          <span>
                            {t.speaker === 'customer' ? 'Customer' : t.speaker === 'human' ? 'You (Specialist)' : 'AI Voice Agent'}
                          </span>
                        </div>
                        <p>{t.text}</p>
                      </div>
                    ))
                  )}
                  <div ref={transcriptEndRef} />
                </div>

                {/* Footer In-Call Action Bar */}
                <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                  {!isInCall ? (
                    <button
                      id="acceptCallBtn"
                      onClick={acceptEscalation}
                      className="w-full py-3.5 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 active:scale-[0.99] transition text-white font-bold text-sm rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center space-x-2"
                    >
                      <PhoneCall className="w-4 h-4" />
                      <span>One-Click Accept & Join Call</span>
                    </button>
                  ) : (
                    <div className="w-full flex items-center justify-between space-x-4">
                      <button
                        onClick={toggleMute}
                        className={`px-5 py-2.5 rounded-xl text-xs font-semibold flex items-center space-x-2 transition ${
                          isMuted
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                        }`}
                      >
                        {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                        <span>{isMuted ? 'Unmute' : 'Mute'}</span>
                      </button>

                      <button
                        id="endCallBtn"
                        onClick={endCall}
                        className="px-6 py-2.5 bg-rose-600 hover:bg-rose-500 active:scale-95 text-white font-bold text-xs rounded-xl shadow-lg shadow-rose-600/30 transition flex items-center space-x-2"
                      >
                        <PhoneOff className="w-4 h-4" />
                        <span>Finish Call & Resolve</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center py-24 text-slate-500 space-y-3">
              <div className="w-16 h-16 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-600">
                <Inbox className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-base text-slate-300">No Escalation Selected</h3>
              <p className="text-xs max-w-sm text-slate-500">
                Select an escalated customer call from the queue on the left to review the AI summary and full conversation transcript before joining.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
