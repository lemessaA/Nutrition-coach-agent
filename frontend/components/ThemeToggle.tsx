"use client"

import * as React from "react"
import { Sun, Moon, Monitor } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTheme, type Theme } from "@/lib/theme-context"

const LABELS: Record<Theme, string> = {
  light: "Light",
  dark: "Dark",
  system: "System",
}

const ICONS: Record<Theme, React.ComponentType<{ className?: string }>> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
}

type Variant = "icon" | "full"

type Props = {
  className?: string
  variant?: Variant
}

/**
 * Single-button theme toggle that cycles Light -> Dark -> System.
 *
 * - `variant="icon"`  : compact, 40x40 icon button (used in navbar)
 * - `variant="full"`  : shows icon + label (used inside the mobile drawer)
 */
export function ThemeToggle({ className, variant = "icon" }: Props) {
  const { theme, toggle } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  // Before hydration, render a neutral placeholder so the server-rendered
  // HTML matches what React produces on first client render.
  const safeTheme: Theme = mounted ? theme : "system"
  const Icon = ICONS[safeTheme]
  const label = LABELS[safeTheme]
  const nextTheme =
    safeTheme === "light" ? "dark" : safeTheme === "dark" ? "system" : "light"

  if (variant === "full") {
    return (
      <button
        type="button"
        onClick={toggle}
        className={cn(
          "flex w-full items-center gap-3 rounded-lg px-3 py-3 text-base font-medium text-foreground/80 transition-colors hover:bg-muted",
          className,
        )}
        title={`Switch to ${LABELS[nextTheme]} theme`}
        aria-label={`Switch to ${LABELS[nextTheme]} theme. Current: ${label}`}
      >
        <span className="relative inline-flex h-5 w-5 items-center justify-center">
          <Icon className="h-5 w-5" />
        </span>
        <span>Theme: {label}</span>
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={toggle}
      className={cn(
        "inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border/60 bg-background/60 text-foreground/80 transition-all hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
      title={`Theme: ${label} (click for ${LABELS[nextTheme]})`}
      aria-label={`Switch to ${LABELS[nextTheme]} theme. Current: ${label}`}
    >
      <span className="relative inline-flex h-5 w-5 items-center justify-center">
        <Sun
          className={cn(
            "absolute h-5 w-5 transition-all duration-300",
            safeTheme === "light"
              ? "rotate-0 scale-100 opacity-100"
              : "rotate-90 scale-0 opacity-0",
          )}
        />
        <Moon
          className={cn(
            "absolute h-5 w-5 transition-all duration-300",
            safeTheme === "dark"
              ? "rotate-0 scale-100 opacity-100"
              : "-rotate-90 scale-0 opacity-0",
          )}
        />
        <Monitor
          className={cn(
            "absolute h-5 w-5 transition-all duration-300",
            safeTheme === "system"
              ? "rotate-0 scale-100 opacity-100"
              : "rotate-90 scale-0 opacity-0",
          )}
        />
      </span>
    </button>
  )
}
