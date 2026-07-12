'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { CheckCircle, AlertCircle, X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'info'

interface Toast {
  type: ToastType
  message: string
}

interface ToastContextValue {
  showToast: (type: ToastType, message: string) => void
}

const Ctx = createContext<ToastContextValue>({ showToast: () => {} })

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((type: ToastType, message: string) => {
    const id = Date.now()
    setToasts(prev => [...prev, { type, message }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.message !== message || t.type !== type))
    }, 3500)
  }, [])

  const dismiss = (type: ToastType, message: string) => {
    setToasts(prev => prev.filter(t => t.message !== message || t.type !== type))
  }

  return (
    <Ctx.Provider value={{ showToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed top-20 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast, i) => (
          <div
            key={`${toast.type}-${toast.message}-${i}`}
            className={`pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium animate-slide-up max-w-sm ${
              toast.type === 'success'
                ? 'bg-green-50 text-green-800 border-green-200 dark:bg-green-900/40 dark:text-green-400 dark:border-green-800'
                : toast.type === 'error'
                  ? 'bg-red-50 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-400 dark:border-red-800'
                  : 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-900/40 dark:text-blue-400 dark:border-blue-800'
            }`}
          >
            {toast.type === 'success' ? (
              <CheckCircle className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span className="flex-1">{toast.message}</span>
            <button onClick={() => dismiss(toast.type, toast.message)} className="shrink-0 hover:opacity-70">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  )
}

export function useToast() {
  return useContext(Ctx)
}
