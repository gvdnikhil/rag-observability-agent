import { useEffect, useState } from "react";

export default function ScoreBar({ score, threshold = 0.3 }) {
  const [width, setWidth] = useState(0);
  const pct = Math.max(0, Math.min(100, score * 100));
  const tier = score >= threshold + 0.15 ? "high" : score >= threshold ? "mid" : "low";

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
