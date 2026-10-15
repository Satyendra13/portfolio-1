import React, { useState, useEffect, useRef } from 'react';
import * as LivekitClient from 'livekit-client';
import { 
  Phone, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Volume2, 
  ShieldCheck, 
  Globe, 
  Sparkles, 
  Headphones, 
  UserCheck, 
  ArrowRight,
  Clock,
  Radio
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [language, setLanguage] = useState('en');
  
  // Call States: 'idle' | 'connecting' | 'active' | 'transferring' | 'ended'
  const [callState, setCallState] = useState('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [captions, setCaptions] = useState([]);
  const [activeSpecialist, setActiveSpecialist] = useState(null);

  const roomRef = useRef(null);
  const timerRef = useRef(null);
  const captionsEndRef = useRef(null);
  const audioElRef = useRef(null);
  const callIdRef = useRef(null);

  // Auto-scroll captions
  useEffect(() => {
    captionsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [captions]);

  // Fetch tenants on mount
  useEffect(() => {
    async function loadTenants() {
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
      } catch (err) {
        console.warn('Could not load tenants from API, using fallback:', err);
      }
      // Fallback tenant for demo
      const fallback = {
        id: 'apex-logistics',
        name: 'Apex Logistics Support',
        script_config: {
          welcome_message: {
            en: 'Thank you for calling Apex Logistics. This call is recorded and answered by an AI assistant. How may I help you today?',
            hi: 'एपेक्स लॉजिस्टिक्स में कॉल करने के लिए धन्यवाद। गुणवत्ता और प्रशिक्षण के लिए यह कॉल रिकॉर्ड की जाती है। मैं आपकी क्या मदद कर सकता हूँ?'
          }
        }
      };
      setTenants([fallback]);
      setSelectedTenant(fallback);
    }
    loadTenants();
  }, []);

  // Duration Timer
  useEffect(() => {
    if (callState === 'active' || callState === 'transferring') {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [callState]);

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  const startCall = async () => {
    if (!selectedTenant) return;
    setCallState('connecting');
    setCaptions([]);
    setCallDuration(0);
    setActiveSpecialist(null);

    try {
      // 1. Create call session on backend
      let roomName = `room-${selectedTenant.id.slice(0, 8)}-${Math.random().toString(36).substring(2, 7)}`;
      let callId = 'call-temp';

      try {
        const callRes = await fetch(`${API_BASE}/calls/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tenant_id: selectedTenant.id,
            language: language,
          }),
        });
        if (callRes.ok) {
          const callData = await callRes.json();
          roomName = callData.livekit_room_name;
          callId = callData.id;
          callIdRef.current = callData.id;
        }
      } catch (e) {
        console.warn('Backend call/start error, proceeding with room:', roomName);
      }

      // 2. Fetch LiveKit Token
      const tokenRes = await fetch(`${API_BASE}/livekit/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: roomName,
          participant_identity: `customer-${Math.random().toString(36).substring(2, 7)}`,
          participant_name: 'Customer (Web)',
          role: 'customer',
        }),
      });

      if (!tokenRes.ok) {
        throw new Error('Failed to obtain LiveKit token');
      }

      const { token, server_url } = await tokenRes.json();

      // 3. Connect to LiveKit Room
      const room = new LivekitClient.Room({
        adaptiveStream: true,
        dynacast: true,
      });
      roomRef.current = room;

      const attachAudioTrack = (track, identity) => {
        const audioId = `audio-${identity}`;
        const existing = document.getElementById(audioId);
        if (existing) {
          try {
            existing.pause();
            existing.remove();
          } catch (e) {}
        }
        const el = track.attach();
        el.id = audioId;
        el.autoplay = true;
        el.muted = false;
        el.volume = 1.0;
        document.body.appendChild(el);
        audioElRef.current = el;
        el.play().catch((err) => {
          console.warn('Browser autoplay prevented audio play:', err);
        });
      };

      // Track subscribed (hear AI or human agent)
      room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === 'audio') {
          console.log(`Audio track subscribed from ${participant.identity}`);
          attachAudioTrack(track, participant.identity);

          if (participant.identity.startsWith('agent-')) {
            setActiveSpecialist(participant.name || 'Tier-2 Human Specialist');
            setCallState('active');
          }
        }
      });

      room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
        if (track.kind === 'audio') {
          const audioId = `audio-${participant.identity}`;
          const existing = document.getElementById(audioId);
          if (existing) {
            try {
              existing.pause();
              existing.srcObject = null;
              existing.remove();
            } catch (e) {}
          }
        }
      });

      // Data received (captions & state transitions)
      room.on(LivekitClient.RoomEvent.DataReceived, (payload) => {
        try {
          const decoded = new TextDecoder().decode(payload);
          const data = JSON.parse(decoded);
          if (data.type === 'caption') {
            setCaptions((prev) => [...prev, { speaker: data.speaker, text: data.text, time: new Date() }]);
            if (data.speaker === 'ai') {
              setIsAiSpeaking(true);
              setTimeout(() => setIsAiSpeaking(false), 3000);
            }
          }
          if (data.type === 'status_update') {
            if (data.status === 'escalating') {
              setCallState('transferring');
            }
          }
        } catch (e) {
          console.error('Data channel parse error:', e);
        }
      });

      room.on(LivekitClient.RoomEvent.ParticipantConnected, (participant) => {
        if (participant.identity.startsWith('agent-')) {
          setActiveSpecialist(participant.name || 'Senior Human Agent');
          setCallState('active');
          setCaptions((prev) => [
            ...prev,
            { speaker: 'system', text: `Connected to ${participant.name || 'a human specialist'}.`, time: new Date() }
          ]);
        }
      });

      room.on(LivekitClient.RoomEvent.Disconnected, () => {
        setCallState('ended');
      });

      await room.connect(server_url, token);

      // Attach any remote audio tracks that were already published before connect finished
      room.remoteParticipants.forEach((participant) => {
        participant.trackPublications.forEach((publication) => {
          if (publication.track && publication.track.kind === 'audio') {
            console.log(`Attaching pre-existing remote audio track from ${participant.identity}`);
            attachAudioTrack(publication.track, participant.identity);
          }
        });
      });

      // 4. Publish Microphone audio
      try {
        await room.localParticipant.setMicrophoneEnabled(true, {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        });
        console.log('Customer microphone published successfully.');
      } catch (micErr) {
        console.error('Microphone access failed:', micErr);
        alert('Microphone access was denied or not found. Please enable your microphone permissions in the browser to speak with the AI agent.');
      }
      setIsMuted(false);
      setCallState('active');


    } catch (err) {
      console.error('Call connection error:', err);
      alert(`Could not start call: ${err.message}`);
      setCallState('idle');
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
    if (callIdRef.current) {
      fetch(`${API_BASE}/calls/${callIdRef.current}/end`, { method: 'POST' }).catch(console.warn);
      callIdRef.current = null;
    }
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    document.querySelectorAll('audio[id^="audio-"]').forEach((el) => {
      try {
        el.pause();
        el.srcObject = null;
        el.remove();
      } catch (e) {}
    });
    audioElRef.current = null;
    setCallState('ended');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500/30">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-50 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Headphones className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">AsistLine AI</span>
                <span className="bg-indigo-500/10 text-indigo-400 text-[11px] font-semibold px-2 py-0.5 rounded-full border border-indigo-500/20">
                  Customer Portal
                </span>
              </div>
              <p className="text-xs text-slate-400">Real-Time BPO Inbound Voice Support</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Tenant Selector */}
            <div className="hidden sm:flex items-center space-x-2 bg-slate-800/70 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs">
              <span className="text-slate-400 font-medium">Brand:</span>
              <select
                disabled={callState !== 'idle'}
                value={selectedTenant?.id || ''}
                onChange={(e) => {
                  const t = tenants.find((x) => x.id === e.target.value);
                  if (t) setSelectedTenant(t);
                }}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer disabled:opacity-50"
              >
                {tenants.map((t) => (
                  <option key={t.id} value={t.id} className="bg-slate-900 text-white">
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Language Toggle */}
            <div className="flex items-center space-x-1 bg-slate-800/70 border border-slate-700/60 rounded-lg p-1 text-xs">
              <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-0.5" />
              <button
                disabled={callState !== 'idle'}
                onClick={() => setLanguage('en')}
                className={`px-2 py-1 rounded font-medium transition ${
                  language === 'en' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                EN
              </button>
              <button
                disabled={callState !== 'idle'}
                onClick={() => setLanguage('hi')}
                className={`px-2 py-1 rounded font-medium transition ${
                  language === 'hi' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                हिन्दी
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-6 flex flex-col justify-center items-center">
        {callState === 'idle' && (
          <div className="w-full max-w-lg bg-slate-900/70 border border-slate-800 rounded-3xl p-8 sm:p-10 shadow-2xl backdrop-blur-xl text-center space-y-8 animate-fadeIn">
            {/* Header Badge */}
            <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3.5 py-1.5 rounded-full text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Direct WebRTC AI Support Available</span>
            </div>

            {/* Title & Description */}
            <div className="space-y-3">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                {selectedTenant?.name || 'Customer Support'}
              </h1>
              <p className="text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">
                Speak with our verified AI assistant for instant order lookups, returns, shipping inquiries, and seamless human escalation.
              </p>
            </div>

            {/* Big Glow Call Button */}
            <div className="pt-2">
              <button
                id="callSupportBtn"
                onClick={startCall}
                className="group relative inline-flex items-center justify-center w-28 h-28 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-400 text-white shadow-2xl shadow-emerald-500/40 hover:scale-105 active:scale-95 transition duration-300 focus:outline-none"
              >
                <div className="absolute inset-0 rounded-full border-2 border-emerald-400/40 animate-ping opacity-30"></div>
                <div className="flex flex-col items-center space-y-1">
                  <Phone className="w-9 h-9 transition-transform group-hover:rotate-12 duration-200" />
                  <span className="text-[11px] font-bold uppercase tracking-wider">Call Now</span>
                </div>
              </button>
            </div>

            {/* California Legal Disclosure */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-4 text-left flex items-start space-x-3 text-xs text-slate-400">
              <ShieldCheck className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-300 block mb-0.5">California Two-Party Consent Disclosure</span>
                Calls may be recorded for quality, training, and verification purposes. You are connecting to an AI voice assistant grounded in verified company policy.
              </div>
            </div>
          </div>
        )}

        {(callState === 'connecting' || callState === 'active' || callState === 'transferring') && (
          <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch animate-fadeIn">
            {/* Left: Active Voice Orb & Controls */}
            <div className="md:col-span-5 bg-slate-900/80 border border-slate-800/90 rounded-3xl p-6 flex flex-col justify-between items-center text-center backdrop-blur-xl relative overflow-hidden shadow-2xl">
              {/* Status Header */}
              <div className="w-full flex items-center justify-between text-xs pb-4 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${callState === 'transferring' ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-pulse'}`}></span>
                  <span className="font-medium text-slate-300">
                    {callState === 'connecting' && 'Connecting WebRTC...'}
                    {callState === 'transferring' && 'Transferring to Agent...'}
                    {callState === 'active' && (activeSpecialist ? 'Human Specialist' : 'AI Assistant Active')}
                  </span>
                </div>
                <div className="flex items-center space-x-1.5 font-mono text-slate-400 font-semibold">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>{formatTime(callDuration)}</span>
                </div>
              </div>

              {/* Pulsing Visualizer Orb */}
              <div className="my-10 relative flex items-center justify-center">
                {/* Ripples */}
                {callState === 'active' && (
                  <>
                    <div className="absolute w-44 h-44 rounded-full bg-indigo-500/10 animate-ripple"></div>
                    <div className="absolute w-56 h-56 rounded-full bg-blue-500/5 animate-ripple delay-300"></div>
                  </>
                )}
                {callState === 'transferring' && (
                  <div className="absolute w-48 h-48 rounded-full bg-amber-500/20 animate-ping"></div>
                )}

                <div
                  className={`w-36 h-36 rounded-full flex flex-col items-center justify-center shadow-2xl transition duration-500 ${
                    callState === 'transferring'
                      ? 'bg-gradient-to-tr from-amber-600 to-yellow-500 shadow-amber-500/30'
                      : isAiSpeaking
                      ? 'bg-gradient-to-tr from-indigo-600 to-purple-500 shadow-indigo-500/50 scale-105'
                      : 'bg-gradient-to-tr from-slate-800 to-indigo-900/60 shadow-slate-900 border border-slate-700/60'
                  }`}
                >
                  {callState === 'transferring' ? (
                    <UserCheck className="w-12 h-12 text-white animate-bounce" />
                  ) : activeSpecialist ? (
                    <UserCheck className="w-12 h-12 text-emerald-300" />
                  ) : (
                    <Radio className={`w-12 h-12 ${isAiSpeaking ? 'text-white animate-pulse' : 'text-slate-400'}`} />
                  )}
                  <span className="text-[10px] font-bold tracking-wider uppercase mt-1 text-slate-200">
                    {callState === 'transferring' ? 'Escalating' : isAiSpeaking ? 'Speaking' : 'Listening'}
                  </span>
                </div>
              </div>

              {/* Brand info */}
              <div className="space-y-1 mb-6">
                <h3 className="font-bold text-white text-base">{selectedTenant?.name}</h3>
                <p className="text-xs text-slate-400">
                  {activeSpecialist ? `Connected with ${activeSpecialist}` : 'BPO Tier-1 Voice Assistant'}
                </p>
              </div>

              {/* In-Call Controls */}
              <div className="w-full flex items-center justify-center space-x-4 pt-4 border-t border-slate-800">
                <button
                  id="muteBtn"
                  onClick={toggleMute}
                  className={`p-3.5 rounded-2xl transition font-medium text-xs flex items-center space-x-2 ${
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
                  className="px-6 py-3.5 bg-rose-600 hover:bg-rose-500 active:scale-95 text-white font-semibold text-xs rounded-2xl shadow-lg shadow-rose-600/30 transition flex items-center space-x-2"
                >
                  <PhoneOff className="w-4 h-4" />
                  <span>End Call</span>
                </button>
              </div>
            </div>

            {/* Right: Real-time Live Captions & Log */}
            <div className="md:col-span-7 bg-slate-900/70 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between backdrop-blur-xl shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs">
                <div className="flex items-center space-x-2 text-slate-300 font-semibold">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span>Live Captions & AI Transcript</span>
                </div>
                <span className="bg-indigo-500/10 text-indigo-400 text-[10px] font-mono px-2 py-0.5 rounded border border-indigo-500/20">
                  LiveKit WebRTC Data Channel
                </span>
              </div>

              {/* Captions scroll box */}
              <div className="flex-1 my-4 overflow-y-auto max-h-96 space-y-3 pr-2 text-xs">
                {captions.length === 0 ? (
                  <div className="text-slate-500 italic text-center py-16">
                    Awaiting audio stream... Captions will appear in real time.
                  </div>
                ) : (
                  captions.map((cap, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                        cap.speaker === 'customer'
                          ? 'ml-auto bg-indigo-600 text-white rounded-br-none shadow-md'
                          : cap.speaker === 'system'
                          ? 'mx-auto bg-amber-500/10 text-amber-300 border border-amber-500/20 text-center font-medium'
                          : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700/60'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] opacity-70 mb-1 font-semibold uppercase tracking-wider">
                        <span>
                          {cap.speaker === 'customer' ? 'You' : cap.speaker === 'system' ? 'System' : 'AI Assistant'}
                        </span>
                        <span>
                          {cap.time ? new Date(cap.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                        </span>
                      </div>
                      <p>{cap.text}</p>
                    </div>
                  ))
                )}
                <div ref={captionsEndRef} />
              </div>

              {/* Grounding guarantee footer */}
              <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl text-[11px] text-slate-400 flex items-center justify-between">
                <span>Grounded RAG: Answering strictly from verified Knowledge Base.</span>
                <span className="text-indigo-400 font-mono text-[10px]">Barge-in: &lt;300ms</span>
              </div>
            </div>
          </div>
        )}

        {callState === 'ended' && (
          <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 rounded-3xl p-8 text-center backdrop-blur-xl shadow-2xl space-y-6 animate-fadeIn">
            <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto text-slate-300">
              <PhoneOff className="w-8 h-8 text-rose-400" />
            </div>

            <div className="space-y-1">
              <h2 className="text-2xl font-bold text-white">Call Finished</h2>
              <p className="text-xs text-slate-400">Thank you for contacting {selectedTenant?.name}.</p>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-500 block mb-1">Duration</span>
                <span className="font-mono text-base font-bold text-white">{formatTime(callDuration)}</span>
              </div>
              <div>
                <span className="text-slate-500 block mb-1">Turns Captured</span>
                <span className="font-mono text-base font-bold text-indigo-400">{captions.length}</span>
              </div>
            </div>

            <button
              onClick={() => {
                setCallState('idle');
                setCaptions([]);
              }}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm rounded-xl text-white shadow-lg shadow-indigo-600/30 transition active:scale-[0.98]"
            >
              Start Another Call
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 text-center py-4 text-xs text-slate-600">
        AsistLine AI Phase 1 — WebRTC LiveKit Voice Agent — US/California Support POC
      </footer>
    </div>
  );
}
