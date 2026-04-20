import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
import { Navbar } from '@/components/Navbar'
import { UserProvider } from '@/lib/user-context'

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
  themeColor: '#10b981',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <UserProvider>
          <div className="flex min-h-dvh flex-col bg-gradient-to-br from-green-50 to-blue-50">
            <Navbar />
            <main className="flex-1 pb-[env(safe-area-inset-bottom)]">
              {children}
            </main>
          </div>
          <Toaster />
        </UserProvider>
      </body>
    </html>
  )
}
