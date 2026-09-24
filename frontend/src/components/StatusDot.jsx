const LABELS = {
  idle: "idle",
  thinking: "thinking",
  searching: "searching knowledge base",
  guardrail: "checking guardrails",
  done: "done",
  error: "error",
};

export default function StatusDot({ status }) {
  return (
    <div className={`status-dot-row status-${status}`}>
      <span className="status-dot" />
      <span className="status-label">{LABELS[status] ?? status}</span>
    </div>
  );
}
