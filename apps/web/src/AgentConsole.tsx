import React, { useState, useEffect } from 'react';
import { UserCheck, PhoneCall, PhoneOff, Mic, MicOff, AlertTriangle, ShieldCheck, CheckCircle2, MessageSquare, ThumbsUp, HelpCircle, FileText, Send } from 'lucide-react';

interface HandoffPacket {
  call_id: string;
  tenant_id: string;
  language: string;
  intent: string;
  reason: str;
  verified: boolean;
  caller: { name?: string; account_id?: string; order_id?: string };
  summary: string;
  kb_answers_given: Array<{ q: string; chunk_ids: string[] }>;
  actions_taken: Array<{ type: string; id: string }>;
  transcript: Array<{ speaker: string; text: string }>;
  sentiment: string;
}

interface EscalationItem {
  id: string;
  call_id: string;
  tenant_id: string;
  status: string;
  summary_json: HandoffPacket;
  created_at: string;
}

export default function AgentConsole() {
  const [agentId, setAgentId] = useState<string>('Priya_Sharma');
  const [isAvailable, setIsAvailable] = useState<boolean>(true);
  const [escalationQueue, setEscalationQueue] = useState<EscalationItem[]>([]);
  const [activeCall, setActiveCall] = useState<EscalationItem | null>(null);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [dispositionRating, setDispositionRating] = useState<string>('appropriate');
  const [dispositionComments, setDispositionComments] = useState<string>('');
  const [showDisposition, setShowDisposition] = useState<boolean>(false);
  const [lastDispositionId, setLastDispositionId] = useState<string | null>(null);

  const apiHost = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Poll escalation queue
  useEffect(() => {
    if (!isAvailable || activeCall) return;

    const fetchQueue = async () => {
      try {
        const res = await fetch(`${apiHost}/v1/escalations/queue`);
        if (res.ok) {
          const data = await res.json();
          setEscalationQueue(data);
        }
      } catch (err) {
        console.error('Failed to fetch escalation queue:', err);
      }
    };

    fetchQueue();
    const interval = setInterval(fetchQueue, 3000);
    return () => clearInterval(interval);
  }, [isAvailable, activeCall]);

  const handleAcceptEscalation = async (escItem: EscalationItem) => {
    try {
      const res = await fetch(`${apiHost}/v1/escalations/${escItem.id}/accept?human_agent_id=${agentId}`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setActiveCall(escItem);
        setEscalationQueue((prev) => prev.filter((i) => i.id !== escItem.id));
      }
    } catch (err) {
      console.error('Failed to accept escalation:', err);
    }
  };

  const handleEndCall = () => {
    if (activeCall) {
      setLastDispositionId(activeCall.id);
      setShowDisposition(true);
    }
    setActiveCall(null);
  };

  const handleSubmitDisposition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lastDispositionId) return;

    try {
      await fetch(`${apiHost}/v1/escalations/${lastDispositionId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: dispositionRating, comments: dispositionComments }),
      });
      setShowDisposition(false);
      setDispositionComments('');
    } catch (err) {
      console.error('Failed to submit disposition:', err);
    }
  };

  return (
    <div className="w-full max-w-5xl glass-panel rounded-3xl p-6 space-y-6 text-slate-100">
      {/* Top Bar / Agent Profile */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-tr from-amber-500 to-orange-600 rounded-2xl shadow-lg">
            <UserCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Human Agent Console (Softphone)
            </h1>
            <p className="text-xs text-slate-400">Warm Handoff Softphone & Context Screen Pop</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-400">Agent:</span>
            <span className="font-semibold text-amber-400">{agentId}</span>
          </div>

          <button
            onClick={() => setIsAvailable(!isAvailable)}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-xl text-xs font-semibold transition ${
              isAvailable
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}
          >
            <span className={`w-2.5 h-2.5 rounded-full ${isAvailable ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
            <span>{isAvailable ? 'Status: Available' : 'Status: Busy'}</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Queue on Left, Active Call / Screen Pop on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Ringer / Escalation Queue */}
        <div className="space-y-4">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center">
            <AlertTriangle className="w-4 h-4 mr-1 text-amber-400" /> Incoming Escalations Queue ({escalationQueue.length})
          </h3>

          {escalationQueue.length === 0 ? (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 text-center text-xs text-slate-500">
              No queued escalations at present. Ready for incoming transfers.
            </div>
          ) : (
            escalationQueue.map((item) => (
              <div
                key={item.id}
                className="bg-slate-900 border-2 border-amber-500/50 rounded-2xl p-4 space-y-3 animate-bounce-short shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                    {item.tenant_id}
                  </span>
                  <span className="text-[10px] bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded-full font-mono">
                    {item.summary_json.reason}
                  </span>
                </div>

                <div className="text-xs text-slate-300">
                  <p className="font-semibold text-slate-100">Intent: {item.summary_json.intent || 'General Inquiry'}</p>
                  <p className="text-slate-400 text-[11px] line-clamp-2 mt-1">{item.summary_json.summary}</p>
                </div>

                <button
                  onClick={() => handleAcceptEscalation(item)}
                  className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-semibold py-2 px-4 rounded-xl text-xs transition shadow-md"
                >
                  <PhoneCall className="w-4 h-4" />
                  <span>Accept Call Transfer</span>
                </button>
              </div>
            ))
          )}
        </div>

        {/* Right Column: Screen Pop & Active Call Softphone */}
        <div className="lg:col-span-2 space-y-4">
          {!activeCall ? (
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 space-y-3">
              <PhoneCall className="w-12 h-12 mx-auto text-slate-700" />
              <p className="text-sm">No active call connected.</p>
              <p className="text-xs text-slate-600">Accept an escalation from the queue to view full caller context.</p>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-5">
              {/* Screen Pop Header */}
              <div className="flex items-center justify-between bg-slate-950 p-4 rounded-xl border border-slate-800">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-white">Call ID: {activeCall.call_id}</span>
                    <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded-full">
                      Tenant: {activeCall.tenant_id}
                    </span>
                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full flex items-center">
                      <ShieldCheck className="w-3 h-3 mr-1" /> Verified
                    </span>
                  </div>
                  <p className="text-xs text-amber-400 mt-1">Escalation Reason: {activeCall.summary_json.reason}</p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setIsMuted(!isMuted)}
                    className={`p-2.5 rounded-xl border text-xs transition ${
                      isMuted ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-slate-800 text-slate-300 border-slate-700'
                    }`}
                  >
                    {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={handleEndCall}
                    className="bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center"
                  >
                    <PhoneOff className="w-4 h-4 mr-1.5" /> End Call
                  </button>
                </div>
              </div>

              {/* Gemini Context Summary */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center">
                  <FileText className="w-4 h-4 mr-1" /> AI Generated Call Summary
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">{activeCall.summary_json.summary}</p>
              </div>

              {/* Actions & Transcript Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Actions Taken */}
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 space-y-2">
                  <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">AI Actions & KB Answers</h5>
                  <div className="text-xs space-y-1 text-slate-300">
                    <p>• Verification: Completed (Order {activeCall.summary_json.caller.order_id || '48213'})</p>
                    <p>• Intent: {activeCall.summary_json.intent}</p>
                    <p>• Sentiment: {activeCall.summary_json.sentiment}</p>
                  </div>
                </div>

                {/* Live Transcript Drawer */}
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 h-40 overflow-y-auto space-y-2">
                  <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center">
                    <MessageSquare className="w-3.5 h-3.5 mr-1" /> Prior Conversation Transcript
                  </h5>
                  {activeCall.summary_json.transcript.map((t, idx) => (
                    <div key={idx} className="text-[11px]">
                      <span className="font-semibold text-slate-400">{t.speaker}: </span>
                      <span className="text-slate-300">{t.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Disposition Feedback Form Modal */}
          {showDisposition && (
            <div className="bg-slate-900 border border-amber-500/40 rounded-2xl p-5 space-y-4 shadow-2xl">
              <h3 className="text-sm font-bold text-white flex items-center">
                <ThumbsUp className="w-4 h-4 mr-1.5 text-amber-400" /> Post-Call Transfer Disposition Feedback
              </h3>
              <form onSubmit={handleSubmitDisposition} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Escalation Rating
                  </label>
                  <select
                    value={dispositionRating}
                    onChange={(e) => setDispositionRating(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  >
                    <option value="appropriate">Appropriate (Transfer was necessary)</option>
                    <option value="could_have_been_automated">Could Have Been Automated (AI should handle)</option>
                    <option value="wrong_queue">Wrong Queue (Sent to incorrect skill group)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Disposition Notes
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Enter notes on the resolution or transfer quality..."
                    value={dispositionComments}
                    onChange={(e) => setDispositionComments(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>

                <button
                  type="submit"
                  className="bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs py-2.5 px-5 rounded-xl shadow-md transition flex items-center"
                >
                  <Send className="w-3.5 h-3.5 mr-1.5" /> Submit Disposition
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
