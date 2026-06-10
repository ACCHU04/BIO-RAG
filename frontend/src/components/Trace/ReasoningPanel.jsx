import { downloadText } from "../common/download";

function metaFor(s) {
  const t = s.toLowerCase();
  if (t.includes("retriev")) return { icon: "\u2193", color: "var(--blue)", bg: "var(--blue-bg)" };
  if (t.includes("evaluat")) return { icon: "\u25ce", color: "var(--violet)", bg: "var(--violet-bg)" };
  if (t.includes("correct") || t.includes("rephras")) return { icon: "\u21ba", color: "var(--amber)", bg: "var(--amber-bg)" };
  if (t.includes("pubmed") || t.includes("uniprot") || t.includes("target")) return { icon: "\u26a1", color: "var(--cyan)", bg: "var(--cyan-bg)" };
  if (t.includes("synth") || t.includes("answer")) return { icon: "\u2605", color: "var(--green)", bg: "var(--green-bg)" };
  return { icon: "\u00b7", color: "var(--txt3)", bg: "var(--bg4)" };
}

function EmptyState() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 20, minHeight: 400 }}>
      <div style={{ width: 90, height: 90, borderRadius: "50%", background: "var(--bg3)", border: "1px solid var(--line2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none"><path d="M20 4C11.2 4 4 11.2 4 20s7.2 16 16 16 16-7.2 16-16S28.8 4 20 4z" stroke="var(--txt3)" strokeWidth="1.5"/><path d="M20 12v10M20 28v1" stroke="var(--txt3)" strokeWidth="2" strokeLinecap="round"/></svg>
      </div>
      <div style={{ textAlign: "center" }}>
        <p style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontStyle: "italic", color: "var(--txt3)", marginBottom: 8 }}>No trace yet</p>
        <p style={{ fontSize: 13, color: "var(--txt3)" }}>Run a query to see the agent reasoning trace</p>
      </div>
    </div>
  );
}

export default function ReasoningPanel({ lastResult }) {
  if (!lastResult) return <EmptyState />;

  const steps = lastResult.reasoning_steps || [];

  return (
    <div style={{ display: "flex", gap: 24, height: "100%" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, minHeight: 0 }}>
        <div>
          <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 26, fontStyle: "italic", color: "var(--txt)" }}>Reasoning Trace</h2>
          <p style={{ fontSize: 12, color: "var(--txt3)", marginTop: 3 }}>Full agent decision chain</p>
        </div>
        <div style={{ background: "var(--bg3)", borderRadius: 8, padding: "12px 16px", borderLeft: "3px solid var(--cyan)" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--cyan)", marginBottom: 4, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>Query</div>
          <p style={{ fontSize: 13, color: "var(--txt2)", lineHeight: 1.7 }}>{lastResult.query}</p>
        </div>
        <div className="glow-card" style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div className="card-header">
            <span className="card-title">Steps ({steps.length})</span>
            <button className="btn btn-ghost" style={{ padding: "5px 12px" }}
              onClick={() => downloadText(steps.map((s, i) => `[${i + 1}] ${s}`).join("\n"), `biorag-trace-${Date.now()}.txt`)}>
              {'\u2193'} Export trace
            </button>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
            {steps.map((step, i) => {
              const m = metaFor(step);
              return (
                <div key={i} className="trace-line fu" style={{ animationDelay: `${i * 0.06}s` }}>
                  <div className="trace-node" style={{ color: m.color, background: m.bg, borderColor: m.color + "44" }}>
                    {m.icon}
                  </div>
                  <div style={{ flex: 1, paddingTop: 5 }}>
                    <p style={{ fontSize: 13, color: "var(--txt2)", lineHeight: 1.7 }}>{step}</p>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)" }}>step {i + 1} / {steps.length}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div style={{ width: 230, flexShrink: 0, display: "flex", flexDirection: "column", gap: 14 }}>
        <div className="glow-card" style={{ padding: 20 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 14 }}>Summary</div>
          {[
            { label: "Total steps", val: steps.length, color: "var(--txt)" },
            { label: "Self-corrections", val: lastResult.self_corrections, color: lastResult.self_corrections > 0 ? "var(--amber)" : "var(--txt)" },
            { label: "PubMed articles", val: lastResult.pubmed_articles_used, color: "var(--blue)" },
            { label: "Local docs used", val: lastResult.local_docs_used, color: "var(--violet)" },
          ].map(r => (
            <div key={r.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid var(--line)" }}>
              <span style={{ fontSize: 12, color: "var(--txt3)" }}>{r.label}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 15, fontWeight: 600, color: r.color }}>{r.val}</span>
            </div>
          ))}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
            {lastResult.fallback && <span className="pill pill-amber">Failover</span>}
            {lastResult.blocked && <span className="pill pill-red">Blocked</span>}
            {!lastResult.fallback && !lastResult.blocked && <span className="pill pill-cyan">Success</span>}
          </div>
        </div>

        <div className="glow-card" style={{ padding: 20 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 14 }}>Pipeline</div>
          {["Parse", "Retrieve", "Evaluate", "Tool Calls", "Synthesize", "Validate"].map((p, i) => (
            <div key={p} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
              <div style={{ width: 22, height: 22, borderRadius: "50%", background: "var(--bg4)", border: "1px solid var(--line2)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 700, color: "var(--txt3)", flexShrink: 0 }}>{i + 1}</div>
              <span style={{ fontSize: 12, color: "var(--txt2)" }}>{p}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
