/** @type {import('next').NextConfig} */

/**
 * Allow marketplace listing images served from the same host as the API (`/uploads/...`).
 */
function imageRemotePatterns() {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  try {
    const u = new URL(base)
    const protocol = u.protocol === "https:" ? "https" : "http"
    /** @type {{ protocol: string; hostname: string; port?: string; pathname: string }} */
    const pattern = {
      protocol,
      hostname: u.hostname,
      pathname: "/uploads/**",
    }
    if (u.port) {
      pattern.port = u.port
    }
    return [pattern]
  } catch {
    return [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/uploads/**",
      },
    ]
  }
}

const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: imageRemotePatterns(),
  },
}

module.exports = nextConfig
