import { useState, useEffect, useRef } from "react";
import { fetchDocuments, uploadDocument, deleteDocument } from "../../api";
import Spinner from "../Spinner";
import { downloadCSV } from "../common/download";

export default function DocumentsPanel() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [flash, setFlash] = useState(null);
  const [search, setSearch] = useState("");
  const fileRef = useRef(null);

  async function load() {
    setLoading(true);
    try {
      const list = await fetchDocuments();
      setDocs(list);
    } catch {
      setFlash({ t: "red", m: "Cannot reach API." });
    }
    setLoading(false);
  }

  async function upload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const d = await uploadDocument(file);
      setFlash({ t: "cyan", m: `"${d.doc_id}" added — ${d.chunks_added} chunks indexed.` });
      load();
    } catch {
      setFlash({ t: "red", m: "Upload failed." });
    }
    setUploading(false);
    e.target.value = "";
  }

  async function del(id) {
    try {
      const d = await deleteDocument(id);
      setFlash({ t: "cyan", m: `Deleted "${id}" — ${d.chunks_deleted} chunks removed.` });
      load();
    } catch {
      setFlash({ t: "red", m: "Delete failed." });
    }
  }

  useEffect(() => { load(); }, []);

  const filtered = docs.filter(d => !search || d.doc_id.toLowerCase().includes(search.toLowerCase()) || d.source.toLowerCase().includes(search.toLowerCase()));
  const totalChunks = docs.reduce((a, d) => a + d.chunk_count, 0);
  const estPages = Math.round(totalChunks * 512 / 250);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, height: "100%" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 26, fontStyle: "italic", color: "var(--txt)" }}>Document Store</h2>
          <p style={{ fontSize: 12, color: "var(--txt3)", marginTop: 3 }}>Dynamic knowledge base — no index rebuild required</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-ghost" onClick={() => downloadCSV([["doc_id", "source", "chunks"], ...docs.map(d => [d.doc_id, d.source, d.chunk_count])], "biorag-documents.csv")}>{'\u2193'} Export CSV</button>
          <button className="btn btn-ghost" onClick={load}>{'\u21ba'} Refresh</button>
          <button className="btn btn-cyan" onClick={() => fileRef.current?.click()} disabled={uploading}>
            {uploading ? <><Spinner />Uploading\u2026</> : "+ Upload PDF / TXT / MD"}
          </button>
          <input ref={fileRef} type="file" accept=".pdf,.txt,.md" style={{ display: "none" }} onChange={upload} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        {[
          { label: "Documents", val: docs.length, color: "var(--txt)", glow: "transparent" },
          { label: "Total chunks", val: totalChunks.toLocaleString(), color: "var(--blue)", glow: "var(--blue-bg)" },
          { label: "Est. pages", val: estPages.toLocaleString(), color: "var(--cyan)", glow: "var(--cyan-bg)" },
        ].map(s => (
          <div key={s.label} className="stat-card" style={{ "--glow": s.glow }}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ color: s.color }}>{s.val}</div>
          </div>
        ))}
      </div>

      {flash && (
        <div className={`alert alert-${flash.t} fi`} style={{ justifyContent: "space-between" }}>
          <span>{flash.m}</span>
          <button onClick={() => setFlash(null)} style={{ background: "none", color: "inherit", fontSize: 16, cursor: "pointer" }}>{'\u00d7'}</button>
        </div>
      )}

      <div style={{ position: "relative" }}>
        <input className="input" placeholder="Search documents\u2026" value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 38 }} />
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="var(--txt3)" strokeWidth="1.5" strokeLinecap="round" style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)" }}>
          <circle cx="6" cy="6" r="4"/><path d="M13 13l-3-3"/>
        </svg>
      </div>

      <div className="glow-card" style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <div className="doc-row doc-header">
          {["Document ID", "File", "Chunks", "Actions"].map(h => (
            <div key={h} style={{ fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)" }}>{h}</div>
          ))}
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 200 }}><Spinner /></div>
          ) : filtered.length === 0 ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 200, gap: 12 }}>
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none"><rect x="8" y="4" width="24" height="32" rx="3" stroke="var(--txt3)" strokeWidth="1.5"/><path d="M14 14h12M14 20h8" stroke="var(--txt3)" strokeWidth="1.5" strokeLinecap="round"/></svg>
              <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: 18, color: "var(--txt3)" }}>{search ? "No matches" : "No documents indexed"}</p>
              <p style={{ fontSize: 12, color: "var(--txt3)" }}>{search ? "Try a different search term" : "Upload PDFs to build your knowledge base"}</p>
            </div>
          ) : filtered.map((doc, i) => (
            <div key={doc.doc_id} className="doc-row fu" style={{ animationDelay: `${i * 0.04}s` }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 600, color: "var(--cyan)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{doc.doc_id}</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--txt3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{doc.source.split("/").pop()}</div>
              <div><span className="pill pill-blue">{doc.chunk_count}</span></div>
              <div><button className="btn-danger" onClick={() => del(doc.doc_id)}>Delete</button></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
