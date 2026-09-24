import { useEffect, useRef, useState } from "react";

export function useCountUp(target, duration = 500) {
  const [value, setValue] = useState(0);
  const raf = useRef(null);

  useEffect(() => {
    const start = performance.now();
    const from = 0;
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (t < 1) raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration]);

  return value;
}
