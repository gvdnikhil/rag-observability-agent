import { useEffect, useState } from "react";

// Fixed cosmetic bands for retrieval relevance — independent of the guardrail's
// groundedness threshold, which now scores the *answer* against the context via
// NLI entailment, a different metric than a chunk's raw retrieval similarity.
export default function ScoreBar({ score }) {
  const [width, setWidth] = useState(0);
  const pct = Math.max(0, Math.min(100, score * 100));
  const tier = score >= 0.5 ? "high" : score >= 0.25 ? "mid" : "low";

  useEffect(() => {
    const id = requestAnimationFrame(() => setWidth(pct));
    return () => cancelAnimationFrame(id);
  }, [pct]);

  return (
    <div className="score-bar-row">
      <div className="score-bar-track">
        <div className={`score-bar-fill tier-${tier}`} style={{ width: `${width}%` }} />
      </div>
      <span className="score-bar-label">{score.toFixed(2)}</span>
    </div>
  );
}
