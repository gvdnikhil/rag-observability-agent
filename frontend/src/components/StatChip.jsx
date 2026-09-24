import { useCountUp } from "./useCountUp";

export default function StatChip({ label, value, suffix = "" }) {
  const animated = useCountUp(value);
  return (
    <div className="stat-chip enter">
      <span className="stat-value">
        {animated}
        {suffix}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
