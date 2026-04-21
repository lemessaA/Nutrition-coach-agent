"use client"

import * as React from "react"

export type Theme = "light" | "dark" | "system"
export type ResolvedTheme = "light" | "dark"

type ThemeContextValue = {
  theme: Theme
  resolvedTheme: ResolvedTheme
  setTheme: (t: Theme) => void
  toggle: () => void
}

const STORAGE_KEY = "nutrition-coach:theme"

const ThemeContext = React.createContext<ThemeContextValue | undefined>(undefined)

function readStoredTheme(): Theme {
  if (typeof window === "undefined") return "system"
  try {
    const v = window.localStorage.getItem(STORAGE_KEY)
    if (v === "light" || v === "dark" || v === "system") return v
  } catch {
    // ignore
  }
  return "system"
}

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light"
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function apply(theme: ResolvedTheme) {
  if (typeof document === "undefined") return
  const root = document.documentElement
  root.classList.toggle("dark", theme === "dark")
  root.style.colorScheme = theme
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) {
    // emerald-500 / slate-950 to keep the mobile status bar in sync
    meta.setAttribute("content", theme === "dark" ? "#0b1220" : "#10b981")
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>("system")
  const [resolvedTheme, setResolvedTheme] = React.useState<ResolvedTheme>("light")

  // Hydrate from storage once on mount.
  React.useEffect(() => {
    const stored = readStoredTheme()
    setThemeState(stored)
    const resolved = stored === "system" ? getSystemTheme() : stored
    setResolvedTheme(resolved)
    apply(resolved)
  }, [])

  // When `system`, react to OS-level changes.
  React.useEffect(() => {
    if (theme !== "system" || typeof window === "undefined") return
    const mq = window.matchMedia("(prefers-color-scheme: dark)")
    const listener = (e: MediaQueryListEvent) => {
      const next: ResolvedTheme = e.matches ? "dark" : "light"
      setResolvedTheme(next)
      apply(next)
    }
    mq.addEventListener("change", listener)
    return () => mq.removeEventListener("change", listener)
  }, [theme])

  const setTheme = React.useCallback((t: Theme) => {
    setThemeState(t)
    try {
      window.localStorage.setItem(STORAGE_KEY, t)
    } catch {
      // ignore
    }
    const resolved = t === "system" ? getSystemTheme() : t
    setResolvedTheme(resolved)
    apply(resolved)
  }, [])

  const toggle = React.useCallback(() => {
    // Cycle: light -> dark -> system -> light
    setTheme(theme === "light" ? "dark" : theme === "dark" ? "system" : "light")
  }, [theme, setTheme])

  const value = React.useMemo(
    () => ({ theme, resolvedTheme, setTheme, toggle }),
    [theme, resolvedTheme, setTheme, toggle],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = React.useContext(ThemeContext)
  if (!ctx) throw new Error("useTheme must be used inside <ThemeProvider>")
  return ctx
}

/**
 * Inline script that runs before React hydrates to prevent a flash of
 * wrong theme on first paint. Keep the implementation minimal and
 * synchronous.
 */
export const themeInitScript = `
(function(){try{
  var k='${STORAGE_KEY}';
  var t=localStorage.getItem(k);
  var m=window.matchMedia('(prefers-color-scheme: dark)').matches;
  var dark=(t==='dark')||((t==null||t==='system')&&m);
  var el=document.documentElement;
  el.classList.toggle('dark',dark);
  el.style.colorScheme=dark?'dark':'light';
}catch(e){}})();
`
