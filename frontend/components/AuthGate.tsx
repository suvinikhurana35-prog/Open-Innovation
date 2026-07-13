'use client'

/**
 * AuthGate — requires the user to be signed in before using JanNiti's features.
 *
 * Public routes: /login and /register (and the home page, which shows the hero
 * and a prominent "Login" prompt). Every feature route (/explainer, /compare,
 * /chatbot, /profile) is gated: an unauthenticated visitor is shown a sign-in
 * prompt instead of the feature.
 */
import { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { useI18n } from '@/lib/i18n'
import { LogIn } from 'lucide-react'

const PUBLIC_ROUTES = ['/login', '/register', '/']

export function AuthGate({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const { t } = useI18n()
  const pathname = usePathname() || '/'

  // While auth state is loading, render nothing (prevents a flash of the gate).
  if (isLoading) return null

  const isPublic = PUBLIC_ROUTES.includes(pathname)
  if (isAuthenticated || isPublic) return <>{children}</>

  // Gated feature route + not signed in -> show sign-in prompt.
  return (
    <div className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-lg dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
          <LogIn className="h-7 w-7 text-blue-600" />
        </div>
        <h2 className="mb-2 text-xl font-bold text-gray-900 dark:text-gray-100">
          {t('auth_required_title')}
        </h2>
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          {t('auth_required_body')}
        </p>
        <div className="flex flex-col gap-3">
          <Link
            href="/login"
            className="rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white shadow-md transition hover:bg-blue-700"
          >
            {t('nav_login')}
          </Link>
          <Link
            href="/register"
            className="rounded-xl border border-gray-300 px-6 py-3 font-semibold text-gray-700 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            {t('nav_register')}
          </Link>
        </div>
      </div>
    </div>
  )
}
