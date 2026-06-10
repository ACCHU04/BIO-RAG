export default function StatusDot({ ok }) {
  const color = ok === null ? "#fbbf24" : ok ? "#4ade80" : "#f87171";
  const label = ok === null ? "connecting\u2026" : ok ? "online" : "offline";
  return (
    <div className="status-row">
      <span className="status-dot" style={{ background: color, boxShadow: ok ? `0 0 0 3px ${color}22` : "none" }} />
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--txt3)" }}>
        api {label}
      </span>
    </div>
  );
}
