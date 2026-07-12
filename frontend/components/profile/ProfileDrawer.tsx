'use client'

import { useEffect, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { useToast } from '@/lib/contexts/ToastContext'
import { useI18n } from '@/lib/i18n'
import { ProfileCompletion } from './ProfileCompletion'
import { getProfileCompletion } from '@/lib/services/profile'
import {
  X, User, FileText, BarChart3, Settings, LogOut, Shield, ChevronRight, Activity,
} from 'lucide-react'
import { useState } from 'react'

interface Props {
  isOpen: boolean
  onClose: () => void
}

export function ProfileDrawer({ isOpen, onClose }: Props) {
  const pathname = usePathname()
  const { user, isAuthenticated, logout } = useAuth()
  const { showToast } = useToast()
  const { t } = useI18n()
  const drawerRef = useRef<HTMLDivElement>(null)
  const [completion, setCompletion] = useState(0)

  useEffect(() => {
    if (user) {
      getProfileCompletion(user).then(setCompletion)
    }
  }, [user])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen, onClose])

  const handleLogout = () => {
    logout()
    onClose()
    showToast('info', 'Logged out successfully.')
  }

  const signInLink = `/login?redirect=${encodeURIComponent(pathname)}`
  const registerLink = `/register?redirect=${encodeURIComponent(pathname)}`

  const DRAWER_ITEMS = [
    { href: '/profile', key: t('drawer_my_profile') || 'My Profile', icon: User },
    { href: '/profile/recommended', key: t('drawer_recommended') || 'Recommended Policies', icon: FileText },
    { href: '/profile/applied', key: t('drawer_applied') || 'Applied Policies', icon: BarChart3 },
    { href: '/profile/activity', key: t('drawer_activity') || 'My Activity', icon: Activity },
    { href: '/profile/settings', key: t('drawer_settings') || 'Settings', icon: Settings },
  ]

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      <div
        ref={drawerRef}
        className={`fixed top-0 left-0 z-50 h-full w-80 max-w-[85vw] bg-white dark:bg-gray-900 shadow-2xl border-r border-gray-200 dark:border-gray-800 transform transition-transform duration-300 ease-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-safron-500" />
              <span className="font-bold text-gray-900 dark:text-gray-100">JanNiti</span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {isAuthenticated && user ? (
            <>
              {/* User Info */}
              <div className="px-5 py-5 border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center overflow-hidden flex-shrink-0">
                    {user.photoUrl ? (
                      <img src={user.photoUrl} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-6 h-6 text-primary-600" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-gray-900 dark:text-gray-100 truncate">
                      {user.fullName || 'User'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{user.phone}</p>
                  </div>
                </div>
                <div className="mt-3">
                  <ProfileCompletion percentage={completion} />
                </div>
              </div>

              {/* Navigation Items */}
              <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
                {DRAWER_ITEMS.map(item => {
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className="flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <span className="flex items-center gap-3">
                        <Icon className="w-4 h-4" />
                        {item.key}
                      </span>
                      <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
                    </Link>
                  )
                })}
              </nav>

              {/* Logout */}
              <div className="px-3 py-3 border-t border-gray-200 dark:border-gray-800">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  {t('drawer_logout') || 'Logout'}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Not logged in */}
              <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
                <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
                  <User className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-900 dark:text-gray-100 font-semibold mb-1">{t('drawer_welcome') || 'Welcome to JanNiti'}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{t('drawer_welcome_sub') || 'Sign in to access your profile and personalized recommendations'}</p>

                <Link
                  href={signInLink}
                  onClick={onClose}
                  className="w-full px-4 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors text-center mb-2"
                >
                  {t('drawer_sign_in') || 'Sign In'}
                </Link>
                <Link
                  href={registerLink}
                  onClick={onClose}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-center"
                >
                  {t('drawer_create_account') || 'Create Account'}
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}
