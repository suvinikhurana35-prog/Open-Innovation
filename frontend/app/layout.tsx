import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/Navbar'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'JanNiti - India\'s Policy Literacy Platform',
  description: 'Understand Indian government schemes in simple language. AI-powered policy explanations, hidden condition detection, and scheme comparisons.',
  keywords: 'government schemes, India, policy, PM Kisan, Ayushman Bharat, scheme explainer, policy literacy',
  openGraph: {
    title: 'JanNiti - Understand Government Schemes',
    description: 'AI-powered platform explaining Indian government schemes in simple language',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-white dark:bg-gray-900 antialiased">
        <Providers>
          <Navbar />
          <main className="min-h-[calc(100vh-4rem)]">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}
