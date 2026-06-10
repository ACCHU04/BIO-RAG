const API = "";

export async function queryBackend(query, { offline = false, includeReasoning = true } = {}) {
  const body = { query, include_reasoning: includeReasoning };
  if (offline) body.offline = true;
  const res = await fetch(`${API}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API}/health`);
  return res.ok;
}

export async function fetchDocuments() {
  const res = await fetch(`${API}/documents`);
  const data = await res.json();
  return data.documents || [];
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/documents/upload`, { method: "POST", body: form });
  return res.json();
}

export async function deleteDocument(id) {
  const res = await fetch(`${API}/documents/${id}`, { method: "DELETE" });
  return res.json();
}

export async function evaluateBackend() {
  const res = await fetch(`${API}/evaluate`, { method: "POST" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function exportPdf(queryResult, ragasScores = null) {
  const payload = {
    query:                queryResult.query,
    answer:               queryResult.answer,
    sources:              queryResult.sources || [],
    reasoning_steps:      queryResult.reasoning_steps || [],
    self_corrections:     queryResult.self_corrections || 0,
    pubmed_articles_used: queryResult.pubmed_articles_used || 0,
    local_docs_used:      queryResult.local_docs_used || 0,
    latency_seconds:      queryResult.latency_seconds || 0,
    fallback:             queryResult.fallback || false,
    blocked:              queryResult.blocked || false,
    guardrail_warning:    queryResult.guardrail_warning || null,
    ragas_scores:         ragasScores,
  };

  const res = await fetch(`${API}/export/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `BioRAG_Report_${Date.now()}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function incognitoChat(messages) {
  const res = await fetch(`${API}/incognito`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.reply;
}
