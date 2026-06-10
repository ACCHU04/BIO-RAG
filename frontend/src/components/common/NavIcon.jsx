export default function NavIcon({ id }) {
  const icons = {
    query: <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="7" cy="7" r="5"/><path d="M16 16l-3.5-3.5"/></svg>,
    incognito: <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 8.5h16"/><ellipse cx="5" cy="8.5" rx="3.5" ry="2.5"/><ellipse cx="13" cy="8.5" rx="3.5" ry="2.5"/><path d="M8.5 8.5h1"/><path d="M5 12v1.5M13 12v1.5"/><path d="M1.5 8.5C2 5.5 4 3.5 9 3.5s7 2 7.5 5"/></svg>,
    docs:  <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h10l3 3v10H3V3z"/><path d="M11 3v4h4"/><path d="M6 9h7M6 12h5"/></svg>,
    trace: <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="4" r="2"/><circle cx="9" cy="14" r="2"/><circle cx="4" cy="9" r="2"/><circle cx="14" cy="9" r="2"/><path d="M7 4.5L5.5 7.5M7 13.5L5.5 10.5M11 4.5L12.5 7.5M11 13.5L12.5 10.5"/></svg>,
    eval:  <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 14l4-4 3 3 7-8"/><rect x="2" y="2" width="14" height="14" rx="2"/></svg>,
    settings: <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="9" r="2.5"/><path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M4.1 4.1l1.4 1.4M12.5 12.5l1.4 1.4M4.1 13.9l1.4-1.4M12.5 5.5l1.4-1.4"/></svg>,
  };
  return <span className="nav-item-icon">{icons[id] || null}</span>;
}
