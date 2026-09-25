import { useEffect, useRef, useState } from "react";

function TypingIndicator({ label }) {
  return (
    <div className="bubble assistant typing-bubble enter">
      <span className="typing-dots">
        <span />
        <span />
        <span />
      </span>
      <span className="typing-label">{label}</span>
    </div>
  );
}

export default function ChatPanel({
  messages,
  onSend,
  busy,
  busyLabel,
  emptyHint = (
    <>
      Ask something like <em>"What deployment modes does Nimbus support?"</em> or{" "}
      <em>"What's the weather today?"</em> to see the guardrail refuse an ungrounded question.
    </>
  ),
  placeholder = "Ask about the knowledge base…",
}) {
  const [input, setInput] = useState("");
  const [pressed, setPressed] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  function submit(e) {
    e.preventDefault();
    if (!input.trim() || busy) return;
    onSend(input.trim());
    setInput("");
    setPressed(true);
    setTimeout(() => setPressed(false), 180);
  }

  return (
    <div className="chat-panel">
      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && <div className="empty-hint enter">{emptyHint}</div>}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role} enter`} style={{ animationDelay: `${Math.min(i, 4) * 30}ms` }}>
            {m.content}
          </div>
        ))}
        {busy && <TypingIndicator label={busyLabel} />}
      </div>

      <form className="chat-input-row" onSubmit={submit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()} className={pressed ? "pressed" : ""}>
          Send
        </button>
      </form>
    </div>
  );
}
