export function PdfIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <rect x="8" y="11" width="8" height="5.5" rx="1.2" fill="var(--red)" stroke="none"/>
      <text x="12" y="15" textAnchor="middle" fill="white" fontSize="5" fontWeight="bold" fontFamily="Arial">PDF</text>
      <path d="M12 18v-4M10 16l2-2 2 2" strokeWidth="1.8"/>
    </svg>
  );
}

export function HistoryIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9"/>
      <polyline points="12 7 12 12 16 14"/>
      <path d="M3 12a9 9 0 0 1 5.5-8.2"/>
    </svg>
  );
}
