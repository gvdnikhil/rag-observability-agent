import { useEffect, useState } from "react";
import { applyTheme, getInitialTheme } from "../lib/theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
      aria-label="Toggle light/dark mode"
      title={theme === "dark" ? "Switch to day file" : "Switch to night file"}
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}
