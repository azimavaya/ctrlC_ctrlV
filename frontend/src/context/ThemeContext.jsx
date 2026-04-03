/**
 * ThemeContext.jsx — Provides dark/light mode toggle for the app.
 * Persists the user's preference to localStorage so it survives page reloads.
 * Sets a data-theme attribute on <html> that CSS variables respond to.
 */
import { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  // Initialize from localStorage; defaults to light mode if no preference saved
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem("pca-dark-mode");
    return saved === "true";
  });

  // Sync the data-theme attribute and localStorage whenever `dark` changes
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("pca-dark-mode", dark);
  }, [dark]);

  return (
    <ThemeContext.Provider value={{ dark, toggleDark: () => setDark(v => !v) }}>
      {children}
    </ThemeContext.Provider>
  );
}

/** Custom hook — shorthand for consuming ThemeContext */
export const useTheme = () => useContext(ThemeContext);
