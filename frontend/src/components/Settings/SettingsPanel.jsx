import { useState } from "react";
import { downloadJSON } from "../common/download";

export default function SettingsPanel() {
  const [model, setModel] = useState("gemini-flash");
  const [topK, setTopK] = useState(5);
  const [temp, setTemp] = useState(0.2);
  const [rerank, setRerank] = useState(true);
  const [pubmed, setPubmed] = useState(true);
  const [saved, setSaved] = useState(false);

  function save() {
    const cfg = { model, topK, temperature: temp, reranking: rerank, pubmed_enabled: pubmed };
    downloadJSON(cfg, "biorag-config.json");
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function Toggle({ on, set }) {
    return (
      <button onClick={() => set(!on)}
        style={{ width: 42, height: 24, borderRadius: 99, background: on ? "var(--cyan)" : "var(--bg4)", border: "none", cursor: "pointer", transition: "all 0.2s", position: "relative", flexShrink: 0 }}>
        <span style={{ position: "absolute", width: 18, height: 18, background: "#fff", borderRadius: "50%", top: 3, left: on ? 21 : 3, transition: "left 0.2s" }} />
      </button>
    );
  }

  const sections = [
    {
      title: "Language Model",
      sub: "Primary LLM for synthesis and reasoning",
      content: (
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)", marginBottom: 8, letterSpacing: "0.08em", textTransform: "uppercase" }}>Model</div>
          <select className="input" value={model} onChange={e => setModel(e.target.value)}>
            <option value="gemini-flash">Gemini Flash (recommended)</option>
            <option value="gemini-flash-latest">Gemini Flash Latest</option>
            <option value="gemini-pro">Gemini Pro</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
        </div>
      ),
    },
    {
      title: "Retrieval",
      sub: "Context chunks and reranking",
      content: (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Top-K chunks</div>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--cyan)" }}>{topK}</span>
            </div>
            <input type="range" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} style={{ width: "100%", accentColor: "var(--cyan)" }} />
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--txt)" }}>FlashRank reranking</div>
              <div style={{ fontSize: 11, color: "var(--txt3)" }}>Re-order retrieved chunks by relevance</div>
            </div>
            <Toggle on={rerank} set={setRerank} />
          </div>
        </div>
      ),
    },
    {
      title: "Generation",
      sub: "Synthesis temperature",
      content: (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Temperature</div>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--cyan)" }}>{temp.toFixed(1)}</span>
          </div>
          <input type="range" min={0} max={1} step={0.1} value={temp} onChange={e => setTemp(+e.target.value)} style={{ width: "100%", accentColor: "var(--cyan)" }} />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)" }}>deterministic</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)" }}>creative</span>
          </div>
        </div>
      ),
    },
    {
      title: "External APIs",
      sub: "Live biomedical data sources",
      content: (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--txt)" }}>PubMed / NCBI</div>
            <div style={{ fontSize: 11, color: "var(--txt3)" }}>Live article retrieval via E-utilities</div>
          </div>
          <Toggle on={pubmed} set={setPubmed} />
        </div>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 680 }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 26, fontStyle: "italic", color: "var(--txt)" }}>Settings</h2>
        <p style={{ fontSize: 12, color: "var(--txt3)", marginTop: 3 }}>Configure retrieval, model, and pipeline behaviour</p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {sections.map(sec => (
          <div key={sec.title} className="glow-card">
            <div className="card-header">
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--txt)" }}>{sec.title}</div>
                <div style={{ fontSize: 11, color: "var(--txt3)", marginTop: 2 }}>{sec.sub}</div>
              </div>
            </div>
            <div className="card-body">{sec.content}</div>
          </div>
        ))}

        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
          <button className="btn btn-ghost">Reset defaults</button>
          <button className="btn btn-cyan" onClick={save}>
            {saved ? "\u2713 Exported!" : "Save & Export Config \u2192"}
          </button>
        </div>
      </div>
    </div>
  );
}
