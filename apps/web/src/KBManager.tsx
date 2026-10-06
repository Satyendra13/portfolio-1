import React, { useState, useEffect } from 'react';
import { Upload, Trash2, Search, FileText, CheckCircle, AlertCircle, HelpCircle } from 'lucide-react';

interface KBDocument {
  id: str;
  tenant_id: str;
  title: str;
  file_type: str;
  content_hash: str;
  created_at: string;
  chunk_count: number;
}

interface KBSearchHit {
  chunk_id: string;
  chunk_text: string;
  score: number;
}

export default function KBManager({ tenantId = 'acme_telecom' }: { tenantId?: string }) {
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [testQuery, setTestQuery] = useState<string>('');
  const [searchHits, setSearchHits] = useState<KBSearchHit[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const apiHost = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${apiHost}/v1/tenants/${tenantId}/kb/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch KB docs:', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [tenantId]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', fileToUpload);
    formData.append('title', fileToUpload.name);

    try {
      const res = await fetch(`${apiHost}/v1/tenants/${tenantId}/kb/documents`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        setFileToUpload(null);
        fetchDocuments();
      }
    } catch (err) {
      console.error('Failed to upload KB doc:', err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      const res = await fetch(`${apiHost}/v1/tenants/${tenantId}/kb/documents/${docId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        fetchDocuments();
      }
    } catch (err) {
      console.error('Failed to delete KB doc:', err);
    }
  };

  const handleTestSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testQuery.trim()) return;

    setIsSearching(true);
    try {
      const res = await fetch(`${apiHost}/v1/tenants/${tenantId}/kb/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: testQuery, top_k: 4 }),
      });
      if (res.ok) {
        const data = await res.json();
        setSearchHits(data.hits || []);
      }
    } catch (err) {
      console.error('Failed to search KB:', err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="w-full max-w-4xl glass-panel rounded-3xl p-6 space-y-6 text-slate-100">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center">
            <FileText className="w-5 h-5 mr-2 text-cyan-400" /> Knowledge Base Management ({tenantId})
          </h2>
          <p className="text-xs text-slate-400">Upload PDF, DOCX, TXT, MD or FAQ CSV documents for grounded speech</p>
        </div>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="flex items-center gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <input
          type="file"
          accept=".pdf,.docx,.txt,.md,.csv"
          onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
          className="text-xs text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700"
        />
        <button
          type="submit"
          disabled={!fileToUpload || isUploading}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold px-4 py-2 text-xs rounded-xl shadow-md transition disabled:opacity-50 flex items-center"
        >
          <Upload className="w-4 h-4 mr-1.5" />
          {isUploading ? 'Ingesting...' : 'Upload & Ingest'}
        </button>
      </form>

      {/* Documents List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Ingested Documents</h3>
        {documents.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No documents ingested for this tenant yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {documents.map((doc) => (
              <div key={doc.id} className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">{doc.title}</h4>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                    {doc.chunk_count} chunks • Hash: {doc.content_hash.substring(0, 8)}...
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-400 transition"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Test Search Tool */}
      <div className="border-t border-slate-800 pt-4 space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center">
          <HelpCircle className="w-4 h-4 mr-1 text-cyan-400" /> Test Knowledge Retrieval
        </h3>
        <form onSubmit={handleTestSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Type a policy or account question to test hybrid search..."
            value={testQuery}
            onChange={(e) => setTestQuery(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <button
            type="submit"
            disabled={isSearching}
            className="bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs px-4 py-2 rounded-xl transition flex items-center"
          >
            <Search className="w-4 h-4 mr-1" />
            {isSearching ? 'Searching...' : 'Test Retrieval'}
          </button>
        </form>

        {/* Hits Display */}
        {searchHits.length > 0 && (
          <div className="space-y-2 bg-slate-900/90 border border-slate-800 rounded-xl p-3">
            <h4 className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">Top Hybrid Retrieval Hits</h4>
            {searchHits.map((hit, idx) => (
              <div key={hit.chunk_id || idx} className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 text-xs">
                <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono mb-1">
                  <span>Chunk #{hit.chunk_id?.substring(0, 8)}</span>
                  <span className="text-emerald-400 font-bold">Score: {hit.score}</span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">{hit.chunk_text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
