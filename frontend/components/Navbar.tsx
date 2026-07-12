'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { LANGUAGES } from '@/lib/utils'
import { useI18n, LangCode } from '@/lib/i18n'
import { useAuth } from '@/lib/contexts/AuthContext'
import { ProfileDrawer } from '@/components/profile/ProfileDrawer'
import {
  Menu, X, Sun, Moon, Globe, ChevronDown, Home,
  FileText, GitCompare, BarChart3, MessageCircle, Shield, User,
} from 'lucide-react'

const NAV_ITEMS = [
  { href: '/', key: 'nav_home', icon: Home },
  { href: '/explainer', key: 'nav_explainer', icon: FileText },
  { href: '/compare', key: 'nav_compare', icon: GitCompare },
  { href: '/chatbot', key: 'nav_chat', icon: MessageCircle },
]

/** Shows /public/logo.png ONLY after it successfully loads; otherwise a clean
 *  tricolor "JanNiti" wordmark. No broken-image icon ever. */
function LogoMark() {
  const [logoOk, setLogoOk] = useState(false)
  useEffect(() => {
    const img = new window.Image()
    img.onload = () => setLogoOk(true)
    img.onerror = () => setLogoOk(false)
    img.src = '/logo.png'
  }, [])
  if (logoOk) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src="/logo.png" alt="JanNiti" className="h-16 md:h-[4.5rem] w-auto max-w-[340px] object-contain" />
  }
  return (
    <span className="inline-flex items-center gap-2">
      <Shield className="w-7 h-7 text-safron-500" />
      <span>Jan<span className="text-green-600 dark:text-green-400">Niti</span></span>
    </span>
  )
}

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const [isDark, setIsDark] = useState(false)
  const [showLang, setShowLang] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const { lang, setLang, t } = useI18n()
  const { user, isAuthenticated } = useAuth()
  const currentLang = LANGUAGES.find(l => l.code === lang) || LANGUAGES[0]
  const pathname = usePathname()

  useEffect(() => {
    const dark = localStorage.getItem('theme') === 'dark' ||
      (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    setIsDark(dark)
    if (dark) document.documentElement.classList.add('dark')
  }, [])

  const toggleDark = () => {
    const newDark = !isDark
    setIsDark(newDark)
    document.documentElement.classList.toggle('dark')
    localStorage.setItem('theme', newDark ? 'dark' : 'light')
  }

  return (
    <>
      <nav className="sticky top-0 z-30 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md border-b border-gray-200 dark:border-gray-800" role="navigation" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-1">
              <Link href="/" className="flex items-center gap-2 text-xl font-bold text-primary-700 dark:text-primary-400" aria-label="JanNiti Home">
                {/* Save your logo at frontend/public/logo.png to show it.
                    Until then, a clean tricolor wordmark shows (no broken icon). */}
                <LogoMark />
              </Link>
              {/* Profile icon — left side, next to logo */}
              <button
                onClick={() => setDrawerOpen(true)}
                className="btn-ghost p-1.5 relative ml-1"
                aria-label="Profile"
              >
                {isAuthenticated && user?.photoUrl ? (
                  <div className="w-7 h-7 rounded-full overflow-hidden border-2 border-primary-200 dark:border-primary-800">
                    <img src={user.photoUrl} alt="" className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                    <User className="w-4 h-4 text-primary-600" />
                  </div>
                )}
              </button>
            </div>

            <div className="hidden md:flex items-center gap-1">
              {NAV_ITEMS.map(item => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-800'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="w-4 h-4" />
                    {t(item.key)}
                  </Link>
                )
              })}
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <button
                  onClick={() => setShowLang(!showLang)}
                  className="btn-ghost flex items-center gap-1 text-sm"
                  aria-label="Select language"
                  aria-expanded={showLang}
                >
                  <Globe className="w-4 h-4" />
                  <span className="hidden sm:inline">{currentLang.nativeName}</span>
                  <ChevronDown className="w-3 h-3" />
                </button>
                {showLang && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 z-20 max-h-72 overflow-y-auto">
                      {LANGUAGES.map(lang => (
                        <button
                          key={lang.code}
                          onClick={() => { setLang(lang.code as LangCode); setShowLang(false) }}
                          className={cn(
                            'w-full text-left px-4 py-2.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                            currentLang.code === lang.code ? 'text-primary-600 font-semibold' : 'text-gray-700 dark:text-gray-300'
                          )}
                        >
                          <span className="block">{lang.nativeName}</span>
                          <span className="block text-xs text-gray-400">{lang.name}</span>
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>

              <button
                onClick={toggleDark}
                className="btn-ghost p-2"
                aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              <button
                onClick={() => setIsOpen(!isOpen)}
                className="md:hidden btn-ghost p-2"
                aria-label="Toggle menu"
                aria-expanded={isOpen}
              >
                {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {isOpen && (
          <div className="md:hidden border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 animate-fade-in">
            <div className="px-4 py-3 space-y-1">
              {NAV_ITEMS.map(item => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      'flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    {t(item.key)}
                  </Link>
                )
              })}
              {/* Profile in mobile menu */}
              <button
                onClick={() => { setIsOpen(false); setDrawerOpen(true) }}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 w-full text-left"
              >
                <User className="w-5 h-5" />
                Profile
              </button>
            </div>
          </div>
        )}
      </nav>

      <ProfileDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  )
}
