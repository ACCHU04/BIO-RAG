import { useState, useRef, useEffect } from "react";
import { incognitoChat } from "../../api";
import Spinner from "../Spinner";

function formatMessage(text) {
  if (!text) return null;
  const parts = text.split(/(\*\*.*?\*\*|`[^`]+`|```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const code = part.slice(3, -3).replace(/^\w+\n/, "");
      return (
        <pre key={i} className="incognito-code-block">
          <code>{code}</code>
        </pre>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i} className="incognito-inline-code">{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part.split("\n").map((line, j, arr) => (
      <span key={`${i}-${j}`}>
        {line}
        {j < arr.length - 1 && <br />}
      </span>
    ));
  });
}

/* ── SVG Icons ── */
function PaperclipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
    </svg>
  );
}
function ImageIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
      <circle cx="8.5" cy="8.5" r="1.5"/>
      <polyline points="21 15 16 10 5 21"/>
    </svg>
  );
}
function MicIcon({ active }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--red)" : "currentColor"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="23"/>
      <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
  );
}

export default function IncognitoPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [attachments, setAttachments] = useState([]);   // [{name, type, preview?, content}]
  const [isListening, setIsListening] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const fileRef = useRef(null);
  const imageRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* ── File/Document Upload ── */
  function handleFileUpload(e) {
    const files = Array.from(e.target.files || []);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = () => {
        setAttachments(prev => [...prev, {
          name: file.name,
          type: "document",
          content: reader.result,
          size: (file.size / 1024).toFixed(1) + " KB",
        }]);
      };
      reader.readAsText(file);
    });
    e.target.value = "";
  }

  /* ── Image Upload ── */
  function handleImageUpload(e) {
    const files = Array.from(e.target.files || []);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = () => {
        setAttachments(prev => [...prev, {
          name: file.name,
          type: "image",
          preview: reader.result,
          size: (file.size / 1024).toFixed(1) + " KB",
        }]);
      };
      reader.readAsDataURL(file);
    });
    e.target.value = "";
  }

  function removeAttachment(idx) {
    setAttachments(prev => prev.filter((_, i) => i !== idx));
  }

  /* ── Voice Input ── */
  function toggleVoice() {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser. Try Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join("");
      setInput(transcript);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      if (event.error !== "aborted") {
        setError(`Voice error: ${event.error}`);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }

  /* ── Send Message ── */
  async function send() {
    const hasText = input.trim().length > 0;
    const hasAttachments = attachments.length > 0;
    if ((!hasText && !hasAttachments) || loading) return;

    // Build user message content
    let content = input.trim();

    // Append document text content
    const docAttachments = attachments.filter(a => a.type === "document");
    if (docAttachments.length > 0) {
      const docTexts = docAttachments.map(a =>
        `\n\n📄 [Attached Document: ${a.name}]\n${a.content}`
      ).join("");
      content += docTexts;
    }

    // Append image descriptions
    const imgAttachments = attachments.filter(a => a.type === "image");
    if (imgAttachments.length > 0) {
      content += imgAttachments.map(a =>
        `\n\n🖼️ [Attached Image: ${a.name}]`
      ).join("");
    }

    const userMsg = {
      role: "user",
      content,
      attachments: attachments.length > 0 ? [...attachments] : undefined,
    };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setAttachments([]);
    setLoading(true);
    setError(null);

    // Reset textarea height
    if (inputRef.current) inputRef.current.style.height = "auto";

    try {
      // Send only role+content to backend
      const apiMessages = newMessages.map(m => ({ role: m.role, content: m.content }));
      const reply = await incognitoChat(apiMessages);
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);
    } catch (e) {
      setError("Failed to reach the server. Make sure python main.py is running.");
    }
    setLoading(false);
    inputRef.current?.focus();
  }

  function clearChat() {
    setMessages([]);
    setAttachments([]);
    setError(null);
    inputRef.current?.focus();
  }

  return (
    <div className="incognito-container">
      {/* Header */}
      <div className="incognito-header">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="incognito-header-icon">
            <svg width="22" height="22" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M1 8.5h16"/><ellipse cx="5" cy="8.5" rx="3.5" ry="2.5"/><ellipse cx="13" cy="8.5" rx="3.5" ry="2.5"/>
              <path d="M8.5 8.5h1"/><path d="M5 12v1.5M13 12v1.5"/>
              <path d="M1.5 8.5C2 5.5 4 3.5 9 3.5s7 2 7.5 5"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "var(--txt)" }}>Incognito Mode</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--violet)", marginTop: 2 }}>
              No restrictions · General AI · Multi-turn
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="pill pill-violet" style={{ fontSize: 9 }}>🕶 Incognito</span>
          {messages.length > 0 && (
            <button className="btn btn-ghost" style={{ padding: "5px 12px", fontSize: 11 }} onClick={clearChat}>
              ✕ New Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="incognito-messages">
        {messages.length === 0 && !loading && (
          <div className="incognito-empty">
            <div className="incognito-empty-icon">
              <svg width="48" height="48" viewBox="0 0 18 18" fill="none" stroke="var(--violet)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.5 }}>
                <path d="M1 8.5h16"/><ellipse cx="5" cy="8.5" rx="3.5" ry="2.5"/><ellipse cx="13" cy="8.5" rx="3.5" ry="2.5"/>
                <path d="M8.5 8.5h1"/><path d="M5 12v1.5M13 12v1.5"/>
                <path d="M1.5 8.5C2 5.5 4 3.5 9 3.5s7 2 7.5 5"/>
              </svg>
            </div>
            <p style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontStyle: "italic", color: "var(--txt2)", marginBottom: 8 }}>
              Ask me anything
            </p>
            <p style={{ color: "var(--txt3)", fontSize: 13, maxWidth: 400 }}>
              No domain restrictions. No guardrails. Just a direct conversation with Gemini — like ChatGPT.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 20, justifyContent: "center" }}>
              {[
                "How does CRISPR gene editing work?",
                "Explain the theory of relativity",
                "What causes antibiotic resistance?",
                "How do black holes form?",
                "Explain neural networks in deep learning",
              ].map((s, i) => (
                <button key={i} className="chip incognito-chip" onClick={() => { setInput(s); inputRef.current?.focus(); }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`incognito-bubble-row ${msg.role}`}>
            <div className={`incognito-bubble ${msg.role}`}>
              {msg.role === "assistant" && (
                <div className="incognito-bubble-label">
                  <svg width="12" height="12" viewBox="0 0 18 18" fill="none" stroke="var(--violet)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 8.5h16"/><ellipse cx="5" cy="8.5" rx="3.5" ry="2.5"/><ellipse cx="13" cy="8.5" rx="3.5" ry="2.5"/>
                    <path d="M8.5 8.5h1"/>
                  </svg>
                  <span>Gemini</span>
                </div>
              )}

              {/* Show image thumbnails in user messages */}
              {msg.attachments && msg.attachments.filter(a => a.type === "image").length > 0 && (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
                  {msg.attachments.filter(a => a.type === "image").map((a, j) => (
                    <img key={j} src={a.preview} alt={a.name}
                      style={{ maxWidth: 180, maxHeight: 120, borderRadius: 8, border: "1px solid var(--glass-border)" }}
                    />
                  ))}
                </div>
              )}

              {/* Show document badges in user messages */}
              {msg.attachments && msg.attachments.filter(a => a.type === "document").length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                  {msg.attachments.filter(a => a.type === "document").map((a, j) => (
                    <span key={j} className="pill pill-violet" style={{ fontSize: 9 }}>📄 {a.name}</span>
                  ))}
                </div>
              )}

              <div className="incognito-bubble-content">
                {formatMessage(msg.content.replace(/\n\n📄 \[Attached Document:[\s\S]*$/, "").replace(/\n\n🖼️ \[Attached Image:[\s\S]*$/, ""))}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="incognito-bubble-row assistant">
            <div className="incognito-bubble assistant">
              <div className="incognito-typing">
                <span className="incognito-dot" />
                <span className="incognito-dot" />
                <span className="incognito-dot" />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div style={{ padding: "0 20px" }}>
            <div className="alert alert-red fi">
              <span>⚠</span><span>{error}</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Attachment Preview Bar */}
      {attachments.length > 0 && (
        <div className="incognito-attach-bar">
          {attachments.map((a, i) => (
            <div key={i} className="incognito-attach-item">
              {a.type === "image" ? (
                <img src={a.preview} alt={a.name} className="incognito-attach-thumb" />
              ) : (
                <div className="incognito-attach-doc-icon">📄</div>
              )}
              <div className="incognito-attach-info">
                <div className="incognito-attach-name">{a.name}</div>
                <div className="incognito-attach-size">{a.size}</div>
              </div>
              <button className="incognito-attach-remove" onClick={() => removeAttachment(i)}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Input Bar */}
      <div className="incognito-input-bar">
        <div className="incognito-input-wrap">
          {/* Action buttons */}
          <div className="incognito-action-btns">
            <input ref={fileRef} type="file" accept=".txt,.md,.csv,.json,.py,.js,.html,.css,.log" multiple hidden onChange={handleFileUpload} />
            <button className="incognito-action-btn" title="Attach document" onClick={() => fileRef.current?.click()}>
              <PaperclipIcon />
            </button>

            <input ref={imageRef} type="file" accept="image/*" multiple hidden onChange={handleImageUpload} />
            <button className="incognito-action-btn" title="Attach image" onClick={() => imageRef.current?.click()}>
              <ImageIcon />
            </button>

            <button className={`incognito-action-btn${isListening ? " active" : ""}`} title={isListening ? "Stop listening" : "Voice input"} onClick={toggleVoice}>
              <MicIcon active={isListening} />
            </button>
          </div>

          <textarea
            ref={inputRef}
            className="incognito-input"
            rows={1}
            value={input}
            onChange={e => {
              setInput(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
            }}
            onKeyDown={e => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={isListening ? "🎤 Listening…" : "Type anything… no restrictions here"}
          />
          <button
            className="incognito-send-btn"
            onClick={send}
            disabled={loading || (!input.trim() && attachments.length === 0)}
          >
            {loading ? (
              <Spinner />
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            )}
          </button>
        </div>
        <div style={{ textAlign: "center", fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--txt3)", marginTop: 6, letterSpacing: "0.06em" }}>
          Enter to send · Shift+Enter for new line · 📎 Docs · 🖼️ Images · 🎤 Voice
        </div>
      </div>

      {/* Hidden file inputs */}
    </div>
  );
}
