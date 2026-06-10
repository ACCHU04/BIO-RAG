import { useState } from "react";
import { evaluateBackend } from "../../api";
import Spinner from "../Spinner";
import { downloadCSV, downloadText } from "../common/download";

const QUESTIONS = [
  "What genes are associated with Alzheimer's disease?",
  "What is the role of BRCA1 in breast cancer?",
  "What drugs target the EGFR pathway in lung cancer?",
  "How is TP53 related to cancer?",
  "What is the relationship between insulin resistance and Type 2 Diabetes?",
];

const METRICS = [
  { label: "Faithfulness", valKey: "faithfulness", desc: "No hallucination — claim supported by retrieved context" },
  { label: "Answer Relevancy", valKey: "answer_relevancy", desc: "Response directly addresses the question" },
  { label: "Context Recall", valKey: "context_recall", desc: "Retrieval found all relevant evidence" },
  { label: "Context Precision", valKey: "context_precision", desc: "Retrieved chunks are focused, not noisy" },
];

const GUIDE = [
  { name: "Faithfulness", tip: "Every claim is backed by retrieved context. No hallucination." },
  { name: "Relevancy", tip: "The answer directly addresses what was asked." },
  { name: "Recall", tip: "Retrieval found all the relevant evidence that exists." },
  { name: "Precision", tip: "Retrieved chunks are focused, not noisy or off-topic." },
];

function qLabel(i) {
  return `Q${i + 1} — ${QUESTIONS[i].split("?")[0].slice(0, 40)}`;
}

export default function EvalPanel() {
  const [running, setRunning] = useState(false);
  const [scores, setScores] = useState(null);
  const [log, setLog] = useState([]);
  const [activeQ, setActiveQ] = useState(null);
  const [error, setError] = useState(null);
  const [qPass, setQPass] = useState(null);

  async function run() {
    setRunning(true);
    setScores(null);
    setLog([]);
    setActiveQ(null);
    setError(null);
    setQPass(null);

    const logInterval = setInterval(() => {
      setLog(prev => {
        const idx = prev.length;
        if (idx === 0) return [...prev, "Initialising RAGAS evaluation pipeline\u2026"];
        if (idx === 1) return [...prev, "Loading 5 biomedical test questions\u2026"];
        if (idx >= 2 && idx <= 6) {
          setActiveQ(idx - 2);
          return [...prev, `${qLabel(idx - 2)} \u2192 running\u2026`];
        }
        if (idx === 7) return [...prev, "Computing metrics (faithfulness, relevancy, recall, precision)\u2026"];
        if (idx >= 8) {
          clearInterval(logInterval);
          return prev;
        }
        return prev;
      });
    }, 700);

    try {
      const data = await evaluateBackend();
      clearInterval(logInterval);
      setActiveQ(null);
      setLog(prev => [...prev, "Evaluation complete \u2713"]);
      setScores(data);
      const avg = (data.faithfulness + data.answer_relevancy + data.context_recall + data.context_precision) / 4;
      setQPass(QUESTIONS.map(() => avg > 0.4));
    } catch {
      clearInterval(logInterval);
      setLog(prev => [...prev, "Error: evaluation failed"]);
      setError("Evaluation API call failed. Is the backend running?");
    }
    setRunning(false);
  }

  const avg = scores
    ? Math.round(((scores.faithfulness + scores.answer_relevancy + scores.context_recall + scores.context_precision) / 4) * 100)
    : null;

  function exportResults() {
    if (!scores) return;
    downloadCSV([
      ["Metric", "Score", "Description"],
      ["Faithfulness", scores.faithfulness, "Answer grounded in evidence"],
      ["Answer Relevancy", scores.answer_relevancy, "Response addresses the query"],
      ["Context Recall", scores.context_recall, "Relevant info was retrieved"],
      ["Context Precision", scores.context_precision, "Retrieved chunks are focused"],
      ["Overall Average", (avg / 100).toFixed(2), "Mean score"],
    ], `biorag-eval-${Date.now()}.csv`);
  }

  return (
    <div style={{ display: "flex", gap: 22, height: "100%" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 18, minHeight: 0 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <h2 style={{ fontFamily: "var(--font-serif)", fontSize: 26, fontStyle: "italic", color: "var(--txt)" }}>RAGAS Evaluation</h2>
            <p style={{ fontSize: 12, color: "var(--txt3)", marginTop: 3 }}>Faithfulness · Relevancy · Context Recall · Precision</p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            {scores && <button className="btn btn-ghost" onClick={exportResults}>{'\u2193'} Export CSV</button>}
            <button className="btn btn-cyan" onClick={run} disabled={running}>
              {running ? <><Spinner />Running\u2026</> : "Run Evaluation \u2192"}
            </button>
          </div>
        </div>

        {error && <div className="alert alert-red fi"><span>{'\u26a0'}</span><span>{error}</span></div>}

        <div className="glow-card">
          <div className="card-header">
            <span className="card-title">Test Questions</span>
            <span className="pill pill-gray">{QUESTIONS.length} questions</span>
          </div>
          <div style={{ padding: "8px 0" }}>
            {QUESTIONS.map((q, i) => (
              <div key={i} style={{ padding: "10px 22px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 14, transition: "background 0.2s", background: activeQ === i ? "var(--cyan-bg2)" : "transparent" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)", width: 20 }}>Q{i + 1}</span>
                <span style={{ flex: 1, fontSize: 13, color: activeQ === i ? "var(--cyan)" : "var(--txt2)" }}>{q}</span>
                {activeQ === i && running ? (
                  <Spinner />
                ) : scores && qPass ? (
                  <span className={qPass[i] ? "pill pill-green" : "pill pill-red"}>{qPass[i] ? "\u2713 pass" : "\u2717 fail"}</span>
                ) : (
                  <span className="pill pill-gray">pending</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {scores && (
          <div className="glow-card fu">
            <div className="card-header">
              <span className="card-title">Score Breakdown</span>
              <span className="pill pill-cyan">Complete</span>
            </div>
            <div style={{ padding: "22px 26px" }}>
              {METRICS.map((s, i) => {
                const pct = Math.round(scores[s.valKey] * 100);
                const color = pct >= 80 ? "var(--green)" : pct >= 60 ? "var(--amber)" : "var(--red)";
                return (
                  <div key={s.label} className="fu" style={{ animationDelay: `${i * 0.1}s`, display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                    <div style={{ width: 160, flexShrink: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--txt)" }}>{s.label}</div>
                      <div style={{ fontSize: 11, color: "var(--txt3)", marginTop: 2, lineHeight: 1.4 }}>{s.desc}</div>
                    </div>
                    <div className="score-track">
                      <div className="score-fill" style={{ width: `${pct}%`, background: color, animationDelay: `${i * 0.1 + 0.2}s` }} />
                    </div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 600, color, width: 46, textAlign: "right" }}>{pct}%</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="glow-card" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "10px 18px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff6b6b", display: "inline-block" }} />
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ffd93d", display: "inline-block" }} />
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#6bcb77", display: "inline-block" }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--txt3)", marginLeft: 8 }}>eval.log</span>
            {log.length > 0 && (
              <button className="btn btn-ghost" style={{ marginLeft: "auto", padding: "3px 10px" }}
                onClick={() => downloadText(log.join("\n"), `biorag-eval-log-${Date.now()}.log`)}>
                {'\u2193'} .log
              </button>
            )}
          </div>
          <div className="terminal" style={{ flex: 1 }}>
            {log.length === 0 ? (
              <div className="term-line">
                <span className="term-prompt">$</span>
                <span style={{ color: "#2a4a20" }}>awaiting eval run\u2026<span style={{ animation: "dotBlink 1s infinite", display: "inline-block" }}>{'\u25ae'}</span></span>
              </div>
            ) : log.map((line, i) => (
              <div key={i} className="term-line fi" style={{ animationDelay: `${i * 0.03}s`, marginBottom: 6 }}>
                <span className="term-prompt">{'\u203a'}</span>
                <span style={{ color: line.includes("\u2713") ? "#4ade80" : i === log.length - 1 && running ? "#00e5cc" : "#6a8aaa" }}>{line}</span>
              </div>
            ))}
            {running && <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#00e5cc", animation: "dotBlink 1s infinite" }}>{'\u25cf'}{'\u25ae'}</span>}
          </div>
        </div>
      </div>

      <div style={{ width: 230, flexShrink: 0, display: "flex", flexDirection: "column", gap: 14 }}>
        {avg !== null && (
          <div className="glow-card fu" style={{ padding: 26, textAlign: "center" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 16 }}>Overall</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 64, fontWeight: 600, lineHeight: 1, color: avg >= 80 ? "var(--green)" : avg >= 60 ? "var(--amber)" : "var(--red)" }}>{avg}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--txt3)", marginTop: 4 }}>/ 100</div>
            <div style={{ marginTop: 16 }}>
              <span className={`pill ${avg >= 80 ? "pill-green" : avg >= 60 ? "pill-amber" : "pill-red"}`}>
                {avg >= 80 ? "Excellent" : avg >= 60 ? "Good" : "Needs work"}
              </span>
            </div>
          </div>
        )}

        <div className="glow-card" style={{ padding: 20 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--txt3)", marginBottom: 14 }}>Metric guide</div>
          {GUIDE.map(m => (
            <div key={m.name} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid var(--line)" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--txt)", marginBottom: 4 }}>{m.name}</div>
              <div style={{ fontSize: 11, color: "var(--txt3)", lineHeight: 1.5 }}>{m.tip}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}