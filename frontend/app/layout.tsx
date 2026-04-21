import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
import { Navbar } from '@/components/Navbar'
import { UserProvider } from '@/lib/user-context'
import { ThemeProvider, themeInitScript } from '@/lib/theme-context'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Nutrition Coach AI',
  description:
    'Your personal AI nutrition coach for meal planning, nutrition advice, and healthy habits',
  applicationName: 'Nutrition Coach AI',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Nutrition Coach',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#10b981' },
    { media: '(prefers-color-scheme: dark)', color: '#0b1220' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className={inter.className}>
        <ThemeProvider>
          <UserProvider>
            <div className="app-bg flex min-h-dvh flex-col">
              <Navbar />
              <main className="flex-1 pb-[env(safe-area-inset-bottom)]">
                {children}
              </main>
            </div>
            <Toaster />
          </UserProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
