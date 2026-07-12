'use client'
import { I18nProvider } from '@/lib/i18n'
import { AuthProvider } from '@/lib/contexts/AuthContext'
import { ToastProvider } from '@/lib/contexts/ToastContext'
import AccessibilityPanel from '@/components/ui/AccessibilityPanel'
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <I18nProvider>
        <AuthProvider>
          {children}
          <AccessibilityPanel />
        </AuthProvider>
      </I18nProvider>
    </ToastProvider>
  )
}
