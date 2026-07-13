'use client'
import { I18nProvider } from '@/lib/i18n'
import { AuthProvider } from '@/lib/contexts/AuthContext'
import { ToastProvider } from '@/lib/contexts/ToastContext'
import { AppStateProvider } from '@/lib/contexts/AppStateContext'
import { AuthGate } from '@/components/AuthGate'
import AccessibilityPanel from '@/components/ui/AccessibilityPanel'
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <I18nProvider>
        <AuthProvider>
          <AppStateProvider>
            <AuthGate>{children}</AuthGate>
            <AccessibilityPanel />
          </AppStateProvider>
        </AuthProvider>
      </I18nProvider>
    </ToastProvider>
  )
}
