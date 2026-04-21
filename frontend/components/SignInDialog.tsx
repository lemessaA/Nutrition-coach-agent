"use client"

import { useEffect, useRef, useState } from "react"
import { Loader2, LogIn, X, AlertCircle, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUser } from "@/lib/user-context"

interface SignInDialogProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
}

export function SignInDialog({ open, onClose, onSuccess }: SignInDialogProps) {
  const { apiUrl, setUser, setProfile } = useUser()
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) {
      setError(null)
      setLoading(false)
      return
    }
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    setTimeout(() => inputRef.current?.focus(), 50)
    return () => {
      document.body.style.overflow = prev
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = email.trim().toLowerCase()
    if (!trimmed) {
      setError("Please enter your email.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const lookup = await fetch(
        `${apiUrl}/api/v1/profile/by-email?email=${encodeURIComponent(trimmed)}`
      )
      if (lookup.status === 404) {
        setError(
          "No account found for that email. Create a profile first to get started."
        )
        return
      }
      if (!lookup.ok) {
        const detail = await lookup.json().catch(() => ({}))
        throw new Error(detail.detail || "Could not sign in")
      }
      const user = await lookup.json()
      setUser({
        userId: user.id,
        email: user.email,
        fullName: user.full_name,
        role: user.role,
      })

      try {
        const healthRes = await fetch(
          `${apiUrl}/api/v1/profile/${user.id}/health`
        )
        if (healthRes.ok) setProfile(await healthRes.json())
        else setProfile(null)
      } catch {
        // profile health is optional
      }

      setEmail("")
      onSuccess?.()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 px-3 py-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-5 sm:p-6 shadow-2xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-blue-600 text-white">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <h2 className="text-lg font-bold gradient-text">Welcome back</h2>
              <p className="text-xs text-gray-500">
                Sign in with the email you used to create your profile.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="block text-sm font-medium text-gray-700">
            Email
            <input
              ref={inputRef}
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
              disabled={loading}
              required
            />
          </label>

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-2.5 text-sm text-red-800">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="mr-2 h-4 w-4" />
                Sign in
              </>
            )}
          </Button>
          <p className="text-center text-xs text-gray-500">
            Don't have a profile yet?{" "}
            <a
              href="/profile"
              onClick={onClose}
              className="font-medium text-green-700 hover:underline"
            >
              Create one
            </a>
            .
          </p>
        </form>
      </div>
    </div>
  )
}
