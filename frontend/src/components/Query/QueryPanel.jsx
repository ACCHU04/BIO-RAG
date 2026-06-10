import { useState, useRef, useEffect } from "react";
import { queryBackend, exportPdf } from "../../api";
import Spinner from "../Spinner";
import PipelineBar from "./PipelineBar";
import { downloadJSON, downloadText, downloadCSV } from "../common/download";
import { PdfIcon, HistoryIcon } from "../common/Icons";

const samples = [
  "Genes linked to Alzheimer's & Type 2 Diabetes",
  "BRCA1 role in DNA damage repair",
  "EGFR inhibitors in lung cancer",
  "p53 mutation in tumour progression",
  "Insulin resistance in metabolic syndrome",
  "mTOR pathway in cancer",
];

function renderAnswer(text) {
  if (!text) return null;
  if (text.startsWith("\u26a0\ufe0f")) {
    const lines = text.split("\n");
    const warningLine = lines[0].replace("\u26a0\ufe0f ", "");
    const rest = lines.slice(1).join("\n").trim();
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="alert alert-amber" style={{ fontSize: 14, padding: "12px 16px" }}>
          <span>{'\u26a0\ufe0f'}</span>
          <span>{warningLine}</span>
        </div>
        {rest && (
          <div style={{ fontSize: 13, color: "var(--txt3)", lineHeight: 1.8, whiteSpace: "pre-wrap", fontFamily: "var(--font-mono)", background: "var(--bg3)", padding: 16, borderRadius: 8, border: "1px solid var(--line2)" }}>
            {rest.split(/\n(?=\[Chunk)/g).map((chunk, i) => {
              const header = chunk.match(/^\[Chunk.*?\]/);
              const body = header ? chunk.replace(header[0], "") : chunk;
              const chunks = rest.split(/\n(?=\[Chunk)/g);
              return (
                <div key={i} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: i < chunks.length - 1 ? "1px solid var(--line2)" : "none" }}>
                  {header && <div style={{ fontSize: 11, fontWeight: 600, color: "var(--cyan)", marginBottom: 6, letterSpacing: "0.02em" }}>{header[0]}</div>}
                  <div style={{ color: "var(--txt2)", lineHeight: 1.7 }}>{body.trim()}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }
  const lines = text.split("\n");
  const sections = [];
  let current = null;
  for (const line of lines) {
    if (line.startsWith("### ")) {
      if (current) sections.push(current);
      current = { type: "section", heading: line.replace("### ", ""), body: [] };
    } else if (line.startsWith("**") && line.endsWith("**")) {
      if (current) sections.push(current);
      current = { type: "bold", text: line.replace(/\*\*/g, ""), body: [] };
    } else if (line.startsWith("---") || line.trim() === "") {
      if (current && current.type !== "bold") current.body.push(line);
    } else {
      if (!current || current.type === "bold") {
        if (current) sections.push(current);
        current = { type: "section", heading: null, body: [] };
      }
      current.body.push(line);
    }
  }
  if (current) sections.push(current);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {sections.map((sec, i) => {
        if (sec.type === "bold") {
          return <p key={i} style={{ fontSize: 14, fontWeight: 600, color: "var(--txt2)", lineHeight: 1.7, margin: 0 }}>{sec.text}</p>;
        }
        const bodyText = sec.body.join("\n").trim();
        if (!bodyText) return null;
        return (
          <div key={i}>
            {sec.heading && (
              <h3 style={{ fontFamily: "var(--font-sans)", fontSize: 16, fontWeight: 700, color: "var(--cyan)", margin: "0 0 8px 0", letterSpacing: "-0.01em" }}>{sec.heading}</h3>
            )}
            <div style={{ fontSize: 15, color: "var(--txt2)", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>
              {bodyText.split(/\*\*(.*?)\*\*/g).map((part, j) =>
                j % 2 === 1 ? <strong key={j} style={{ fontWeight: 600 }}>{part}</strong> : part
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function QueryPanel({ result, onResult, offline }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pipeStage, setPipeStage] = useState(-1);
  const [donePipes, setDonePipes] = useState([]);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState(null);
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem("biorag_history") || "[]"); }
    catch { return []; }
  });
  const loadingRef = useRef(false);

  useEffect(() => {
    localStorage.setItem("biorag_history", JSON.stringify(history.slice(0, 20)));
  }, [history]);

  async function simulatePipeline() {
    for (let i = 0; i < 6; i++) {
      if (!loadingRef.current) return;
      setPipeStage(i);
      setDonePipes(prev => [...prev, i - 1].filter(x => x >= 0));
      await new Promise(r => setTimeout(r, 700));
    }
    if (loadingRef.current) {
      setPipeStage(-1);
    }
  }

  async function submit() {
    if (!query.trim() || loading) return;
    setLoading(true);
    loadingRef.current = true;
    setError(null);
    onResult(null);
    setDonePipes([]);
    setPipeStage(-1);
    simulatePipeline();
    try {
      const data = await queryBackend(query, { offline });
      onResult(data);
      setDonePipes([0, 1, 2, 3, 4, 5]);
      setPipeStage(-1);
      setHistory(prev => [{ q: query, time: Date.now() }, ...prev.filter(h => h.q !== query)].slice(0, 20));
    } catch {
      setError("Cannot reach API server. Make sure python main.py is running.");
    }
    setLoading(false);
    loadingRef.current = false;
  }

  return (
    <div style={{ display: "flex", gap: 22, height: "100%", minHeight: 0 }}>
      <div style={{ width: 340, flexShrink: 0, display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="glow-card" style={{ padding: 24 }}>
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontStyle: "italic", color: "var(--txt)", marginBottom: 4 }}>Research Query</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Agentic RAG · Gene · Drug · Disease</div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 8 }}>Sample queries</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {samples.map((s, i) => (
                <button key={i} className="chip" onClick={() => setQuery(s)}>{s}</button>
              ))}
            </div>
          </div>
          {history.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
                <HistoryIcon /> Previous queries
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3, maxHeight: 140, overflowY: "auto" }}>
                {history.map((h, i) => (
                  <button key={i} className="chip" onClick={() => setQuery(h.q)} style={{ textAlign: "left", fontSize: 10, padding: "5px 8px", display: "flex", gap: 6, alignItems: "center" }}>
                    <HistoryIcon />
                    <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{h.q}</span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 8, color: "var(--txt3)", flexShrink: 0 }}>
                      {new Date(h.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
          <div style={{ marginBottom: 14 }}>
            <textarea className="input" rows={5} value={query} onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit(); }}
              placeholder="What would you like to know about genes, drugs, or pathways?"
            />
            <div style={{ textAlign: "right", marginTop: 4, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)" }}>{'\u2318'}\u21b5 to run</div>
          </div>
          <button className="btn btn-cyan" onClick={submit} disabled={loading || !query.trim()} style={{ width: "100%", justifyContent: "center", fontSize: 13, padding: "13px" }}>
            {loading ? <><Spinner />Running agent\u2026</> : "Run Query \u2192"}
          </button>
          <div style={{ display: "flex", justifyContent: "center", gap: 6, marginTop: 2, fontFamily: "var(--font-mono)", fontSize: 9, color: offline ? "var(--amber)" : "var(--green)", letterSpacing: "0.06em" }}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: offline ? "var(--amber)" : "var(--green)", display: "inline-block", marginTop: 4 }} />
            {offline ? "Offline mode \u2014 local docs only" : "Online mode \u2014 PubMed + local"}
          </div>
        </div>

        {error && <div className="alert alert-red fi"><span>{'\u26a0'}</span><span>{error}</span></div>}

        {(pipeStage >= 0 || donePipes.length > 0) && (
          <div className="glow-card" style={{ padding: 18 }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 12 }}>Pipeline</div>
            <PipelineBar activeStage={pipeStage} doneStages={donePipes} />
          </div>
        )}

        {result && (
          <div className="glow-card fu" style={{ padding: 18 }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 14 }}>Run metrics</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
              {[
                { label: "Latency", val: `${result.latency_seconds}s`, color: result.latency_seconds < 5 ? "var(--green)" : "var(--amber)" },
                { label: "Corrections", val: result.self_corrections, color: result.self_corrections > 0 ? "var(--amber)" : "var(--txt)" },
                { label: "PubMed", val: result.pubmed_articles_used, color: "var(--blue)" },
                { label: "Local docs", val: result.local_docs_used, color: "var(--violet)" },
              ].map(m => (
                <div key={m.label} style={{ background: "var(--bg3)", borderRadius: 8, padding: "12px 14px" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 6 }}>{m.label}</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 24, fontWeight: 600, color: m.color }}>{m.val}</div>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
              {result.blocked && <span className="pill pill-red">Blocked</span>}
              {result.fallback && <span className="pill pill-amber">{'\u26a1'} Failover</span>}
              {!result.blocked && !result.fallback && <span className="pill pill-cyan">{'\u2713'} Complete</span>}
              {result.self_corrections > 0 && <span className="pill pill-amber">{result.self_corrections}\u00d7 corrected</span>}
            </div>
            <button className="btn btn-ghost" style={{ width: "100%", justifyContent: "center", marginBottom: 8 }}
              onClick={() => downloadJSON(result, `biorag-result-${Date.now()}.json`)}>
              {'\u2193'} Export JSON
            </button>
            <button
              id="export-pdf-btn"
              className="btn btn-cyan"
              style={{ width: "100%", justifyContent: "center", opacity: pdfLoading ? 0.7 : 1 }}
              disabled={pdfLoading}
              onClick={async () => {
                setPdfLoading(true);
                setPdfError(null);
                try {
                  await exportPdf(result);
                } catch (e) {
                  setPdfError(e.message || "PDF export failed.");
                } finally {
                  setPdfLoading(false);
                }
              }}
            >
              {pdfLoading ? <><Spinner />Generating PDF…</> : <><PdfIcon /> Export PDF</>}
            </button>
            {pdfError && (
              <div className="alert alert-red fi" style={{ marginTop: 8, fontSize: 11, padding: "8px 12px" }}>
                <span>{'\u26A0'}</span><span>{pdfError}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, minHeight: 0, overflowY: "auto" }}>
        {!result && !loading && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 20, minHeight: 400 }}>
            <div style={{ width: 90, height: 90, borderRadius: "50%", background: "var(--bg3)", border: "1px solid var(--line2)", display: "flex", alignItems: "center", justifyContent: "center", animation: "float 3s ease-in-out infinite" }}>
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="12" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="3 3"/><circle cx="20" cy="20" r="5" fill="var(--cyan)" opacity=".3"/><path d="M20 8v4M20 28v4M8 20h4M28 20h4" stroke="var(--cyan)" strokeWidth="1.5" strokeLinecap="round"/></svg>
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ fontFamily: "var(--font-serif)", fontSize: 24, fontStyle: "italic", color: "var(--txt2)", marginBottom: 8 }}>Ready for your query</p>
              <p style={{ color: "var(--txt3)", fontSize: 13 }}>Results and citations will appear here</p>
            </div>
          </div>
        )}

        {loading && !result && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 18, minHeight: 400 }}>
            <div style={{ position: "relative" }}>
              <div style={{ width: 70, height: 70, borderRadius: "50%", border: "2px solid var(--bg4)", borderTop: "2px solid var(--cyan)", animation: "spin 1.2s linear infinite" }} />
              <div style={{ position: "absolute", inset: 8, borderRadius: "50%", border: "1.5px solid var(--bg4)", borderBottom: "1.5px solid var(--violet)", animation: "spin 0.8s linear infinite reverse" }} />
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ fontFamily: "var(--font-serif)", fontSize: 20, fontStyle: "italic", color: "var(--txt2)", marginBottom: 6 }}>Agent is reasoning\u2026</p>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--txt3)", letterSpacing: "0.08em" }}>retrieve \u2192 evaluate \u2192 synthesize</p>
            </div>
          </div>
        )}

        {result && !loading && (
          <>
            {result.guardrail_warning && <div className="alert alert-amber fi"><span>{'\u26a0'}</span>{result.guardrail_warning}</div>}

            <div className="glow-card fu">
              <div className="card-header">
                <span className="card-title">Answer</span>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span className="pill pill-gray">{new Date().toLocaleTimeString()}</span>
                  <button className="btn btn-ghost" style={{ padding: "5px 12px" }}
                    onClick={() => downloadJSON({ query: result.query, answer: result.answer, sources: result.sources }, `biorag-answer-${Date.now()}.json`)}>
                    {'↓'} .json
                  </button>
                  <button
                    className="btn btn-cyan"
                    style={{ padding: "5px 14px", display: "flex", alignItems: "center", gap: 6, opacity: pdfLoading ? 0.7 : 1 }}
                    disabled={pdfLoading}
                    onClick={async () => {
                      setPdfLoading(true);
                      setPdfError(null);
                      try {
                        await exportPdf(result);
                      } catch (e) {
                        setPdfError(e.message || "PDF export failed.");
                      } finally {
                        setPdfLoading(false);
                      }
                    }}
                  >
                    {pdfLoading ? (
                      <><Spinner /> Generating…</>
                    ) : (
                      <><PdfIcon /> PDF</>
                    )}
                  </button>
                </div>
              </div>
              <div style={{ padding: "24px 26px" }}>
                {renderAnswer(result.answer)}
              </div>
            </div>

            {result.sources?.length > 0 && (
              <div className="glow-card fu" style={{ animationDelay: "0.12s" }}>
                <div className="card-header">
                  <span className="card-title">Sources ({result.sources.length})</span>
                  <button className="btn btn-ghost" style={{ padding: "5px 12px" }}
                    onClick={() => {
                      const rows = [["#", "Source"], ...result.sources.map((s, i) => [i + 1, s])];
                      downloadCSV(rows, `biorag-sources-${Date.now()}.csv`);
                    }}>
                    {'\u2193'} .csv
                  </button>
                </div>
                <div style={{ padding: "8px 0" }}>
                  {result.sources.map((s, i) => (
                    <div key={i} style={{ padding: "10px 22px", borderBottom: "1px solid var(--line)", display: "flex", gap: 12, alignItems: "center" }}>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)", width: 20 }}>{i + 1}</span>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--blue)", wordBreak: "break-all" }}>{s}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
