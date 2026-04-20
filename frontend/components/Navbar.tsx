"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import {
  Sparkles,
  MessageSquare,
  User as UserIcon,
  Utensils,
  Apple,
  BarChart3,
  Menu,
  X,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useUser } from "@/lib/user-context"

type NavItem = {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const NAV_ITEMS: NavItem[] = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/meal-plan", label: "Meal Plan", icon: Utensils },
  { href: "/analyze-food", label: "Analyze", icon: Apple },
  { href: "/market", label: "Market", icon: BarChart3 },
  { href: "/profile", label: "Profile", icon: UserIcon },
]

export function Navbar() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const { userId, fullName, email, ready } = useUser()

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      document.body.style.overflow = prev
    }
  }, [open])

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname?.startsWith(href))

  const identityLabel = ready
    ? userId
      ? fullName || email || `User #${userId}`
      : "Guest"
    : ""

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-gray-200/60 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container mx-auto flex h-14 items-center justify-between gap-4 px-4">
          <Link href="/" className="flex items-center gap-2 font-bold">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-blue-600 text-white shadow-sm">
              <Sparkles className="h-4 w-4" />
            </span>
            <span className="hidden sm:inline gradient-text text-lg">
              Nutrition Coach
            </span>
            <span className="sm:hidden gradient-text text-base">Coach</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                    active
                      ? "bg-green-100 text-green-900"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="flex items-center gap-2">
            <span
              className={cn(
                "hidden sm:inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
                userId
                  ? "border-green-200 bg-green-50 text-green-800"
                  : "border-gray-200 bg-gray-50 text-gray-600"
              )}
            >
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  userId ? "bg-green-500" : "bg-gray-400"
                )}
              />
              {identityLabel}
            </span>
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
              className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-gray-700 hover:bg-gray-100 md:hidden"
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </header>

      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30 md:hidden"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "fixed top-14 right-0 z-40 flex h-[calc(100dvh-3.5rem)] w-72 max-w-[85vw] flex-col gap-1 border-l border-gray-200 bg-white p-4 shadow-xl transition-transform duration-200 md:hidden",
          open ? "translate-x-0" : "translate-x-full"
        )}
        aria-hidden={!open}
      >
        <div className="mb-2 flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm">
          <span className="font-medium text-gray-700">Signed in as</span>
          <span
            className={cn(
              "truncate font-semibold",
              userId ? "text-green-700" : "text-gray-500"
            )}
          >
            {identityLabel}
          </span>
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-3 text-base font-medium transition-colors",
                active
                  ? "bg-green-100 text-green-900"
                  : "text-gray-700 hover:bg-gray-100"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          )
        })}
      </aside>
    </>
  )
}
