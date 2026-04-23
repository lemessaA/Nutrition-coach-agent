/**
 * Public backend base URL (no trailing slash). Set NEXT_PUBLIC_API_URL in
 * Vercel / .env.local for production; falls back to local dev.
 */
const DEFAULT = "http://localhost:8000"

export function getPublicApiUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL
  if (raw && raw.trim()) {
    return raw.replace(/\/+$/, "")
  }
  return DEFAULT
}
