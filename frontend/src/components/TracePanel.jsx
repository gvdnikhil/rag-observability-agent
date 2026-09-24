import ScoreBar from "./ScoreBar";
import StatChip from "./StatChip";

function Skeleton() {
  return (
    <div className="trace-skeleton">
      {[0, 1, 2].map((i) => (
        <div key={i} className="skeleton-line" style={{ animationDelay: `${i * 120}ms` }} />
      ))}
    </div>
  );
}

export default function TracePanel({ trace, summary, busy }) {
  if (!trace) {
    return (
      <div className="trace-panel">
        <h3>Trace</h3>
        {busy ? <Skeleton /> : <p className="empty-hint">Ask a question to see the agent's trace here — every retrieval, tool call, latency, and guardrail check.</p>}
      </div>
    );
  }

  const verdict = summary?.guardrail_verdict;

  return (
    <div className={`trace-panel ${busy ? "trace-stale" : ""}`}>
      <h3>Trace</h3>

      <div className="stat-row">
        <StatChip label="llm calls" value={summary?.llm_calls ?? 0} />
        <StatChip label="latency" value={summary?.total_latency_ms ?? 0} suffix="ms" />
        <StatChip label="tokens" value={summary?.total_tokens ?? 0} />
        <StatChip label="chunks" value={summary?.chunks_retrieved ?? 0} />
      </div>

      {verdict && (
        <div className={`verdict-badge enter ${verdict.blocked ? "blocked" : "passed"}`}>
          {verdict.blocked ? "✕ guardrail blocked" : "✓ grounded"}
          {typeof verdict.best_score === "number" && (
            <span className="verdict-score"> · best match {verdict.best_score.toFixed(2)}</span>
          )}
        </div>
      )}

      {trace.tool_calls?.length > 0 && (
        <section className="trace-section">
          <h4>tool calls</h4>
          <div className="chip-row">
            {trace.tool_calls.map((tc, i) => (
              <span key={i} className="tool-chip enter" style={{ animationDelay: `${i * 60}ms` }}>
                {tc.name}("{tc.arguments?.query}")
              </span>
            ))}
          </div>
        </section>
      )}

      {trace.retrieved?.length > 0 && (
        <section className="trace-section">
          <h4>retrieved chunks</h4>
          <div className="chunk-list">
            {trace.retrieved.map((r, i) => (
              <div key={i} className="chunk-card enter" style={{ animationDelay: `${i * 70}ms` }}>
                <div className="chunk-head">
                  <span className="chunk-source">{r.source}</span>
                  <ScoreBar score={r.score} />
                </div>
                <p className="chunk-text">{r.text}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {trace.steps?.length > 0 && (
        <section className="trace-section">
          <h4>timeline</h4>
          <div className="timeline-list">
            {trace.steps.map((s, i) => (
              <div key={i} className="timeline-row enter" style={{ animationDelay: `${i * 80}ms` }}>
                <span className="timeline-dot" />
                <span>llm call #{i + 1}</span>
                <span className="timeline-meta">{s.latency_ms}ms</span>
                {s.made_tool_call && <span className="timeline-meta accent">→ tool call</span>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
