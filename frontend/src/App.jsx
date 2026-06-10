import { useState, useEffect } from "react";
import { checkHealth } from "./api";
import StatusDot from "./components/common/StatusDot";
import NavIcon from "./components/common/NavIcon";
import QueryPanel from "./components/Query/QueryPanel";
import IncognitoPanel from "./components/Incognito/IncognitoPanel";
import DocumentsPanel from "./components/Documents/DocumentsPanel";
import ReasoningPanel from "./components/Trace/ReasoningPanel";
import EvalPanel from "./components/Eval/EvalPanel";
import SettingsPanel from "./components/Settings/SettingsPanel";

const TABS = [
  { id: "query",     label: "Query",           sub: "Run Agent" },
  { id: "incognito", label: "Incognito",       sub: "Unrestricted AI" },
  { id: "docs",      label: "Documents",       sub: "Knowledge Base" },
  { id: "trace",     label: "Reasoning",       sub: "Decision Chain" },
  { id: "eval",      label: "Evaluation",      sub: "RAGAS" },
  { id: "settings",  label: "Settings",        sub: "Config" },
];

export default function App() {
  const [tab, setTab] = useState("query");
  const [result, setResult] = useState(null);
  const [serverOk, setServerOk] = useState(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    checkHealth().then(setServerOk).catch(() => setServerOk(false));
  }, []);

  const active = TABS.find(t => t.id === tab);

  return (
    <>
      <div className="bg-ambient" />
      <nav className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-title">BioRAG</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
            <span className="pill pill-cyan" style={{ fontSize: 9 }}>v3.0</span>
            <span className="pill pill-violet" style={{ fontSize: 9 }}>Gemini Flash</span>
          </div>
          <div className="sidebar-logo-sub" style={{ marginTop: 10 }}>Biomedical Agentic RAG</div>
        </div>

        <div className="sidebar-nav">
          <div className="nav-section-label">Core</div>
          {TABS.slice(0, 5).map(t => (
            <button key={t.id} className={`nav-item${tab === t.id ? " active" : ""}${t.id === "incognito" ? " incognito-nav" : ""}`} onClick={() => setTab(t.id)}>
              <NavIcon id={t.id} />
              <div style={{ flex: 1, textAlign: "left" }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{t.label}</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, opacity: 0.6, marginTop: 1, letterSpacing: "0.05em" }}>{t.sub}</div>
              </div>
              {t.id === "trace" && result && <span className="nav-badge">1</span>}
            </button>
          ))}
          <div className="nav-section-label">System</div>
          {TABS.slice(5).map(t => (
            <button key={t.id} className={`nav-item${tab === t.id ? " active" : ""}`} onClick={() => setTab(t.id)}>
              <NavIcon id={t.id} />
              <div style={{ flex: 1, textAlign: "left" }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{t.label}</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, opacity: 0.6, marginTop: 1, letterSpacing: "0.05em" }}>{t.sub}</div>
              </div>
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <StatusDot ok={serverOk} />
          <div style={{ marginTop: 8, fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--txt3)", letterSpacing: "0.06em" }}>
            ChromaDB · FlashRank · PubMed API
          </div>
          <div style={{ marginTop: 4, fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--txt3)" }}>PG FINAL · DATA SCIENCE & BIO</div>
        </div>
      </nav>

      <div className="main-wrap">
        <div className="topbar">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span className="topbar-breadcrumb">BioRAG</span>
              <span style={{ color: "var(--line3)", fontSize: 12 }}>{'\u203a'}</span>
              <span className="topbar-title">{active?.label}</span>
            </div>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center" }}>
            <span className="pill pill-gray" style={{ fontFamily: "var(--font-mono)" }}>:8742</span>
            <button onClick={() => setOffline(!offline)}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 99, border: "1px solid var(--glass-border)", background: offline ? "var(--amber-bg)" : "var(--cyan-bg)", color: offline ? "var(--amber)" : "var(--cyan)", fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase", cursor: "pointer", transition: "all var(--transition)" }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: offline ? "var(--amber)" : "var(--green)", display: "inline-block" }} />
              {offline ? "Offline" : "Online"}
            </button>
            {result && tab !== "trace" && (
              <button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 12 }} onClick={() => setTab("trace")}>
                {'\u2197'} View last trace
              </button>
            )}
          </div>
        </div>

        <div className="content">
          <div className="fu" key={tab} style={{ height: "100%" }}>
            {tab === "query"    && <QueryPanel result={result} onResult={setResult} offline={offline} />}
            {tab === "incognito" && <IncognitoPanel />}
            {tab === "docs"     && <DocumentsPanel />}
            {tab === "trace"    && <ReasoningPanel lastResult={result} />}
            {tab === "eval"     && <EvalPanel />}
            {tab === "settings" && <SettingsPanel />}
          </div>
        </div>
      </div>
    </>
  );
}
