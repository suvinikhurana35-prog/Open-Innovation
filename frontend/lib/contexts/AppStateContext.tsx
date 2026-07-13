'use client'

/**
 * AppStateContext — keeps per-feature UI state alive across route changes.
 *
 * In the Next.js app router, navigating between /explainer, /compare and
 * /chatbot unmounts each page, so any local useState is lost (the "switching
 * tabs wipes my results" bug). This provider lives in the root layout and never
 * unmounts, so state stored here via usePersistent(key, initial) survives tab
 * switches for the whole session.
 */
import { createContext, useContext, useRef, useState, useCallback, ReactNode } from 'react'

type Store = Record<string, unknown>

interface AppStateCtx {
  get: (key: string) => unknown
  has: (key: string) => boolean
  set: (key: string, value: unknown) => void
  clearAll: () => void
}

const Ctx = createContext<AppStateCtx | null>(null)

export function AppStateProvider({ children }: { children: ReactNode }) {
  const store = useRef<Store>({})
  const [, force] = useState(0)

  const get = useCallback((key: string) => store.current[key], [])
  const has = useCallback((key: string) => key in store.current, [])
  const set = useCallback((key: string, value: unknown) => {
    store.current[key] = value
    force((n) => n + 1)
  }, [])
  const clearAll = useCallback(() => {
    store.current = {}
    force((n) => n + 1)
  }, [])

  return <Ctx.Provider value={{ get, has, set, clearAll }}>{children}</Ctx.Provider>
}

/** Drop-in replacement for useState that persists across navigation. */
export function usePersistent<T>(key: string, initial: T): [T, (v: T | ((prev: T) => T)) => void] {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('usePersistent must be used within <AppStateProvider>')
  const current = (ctx.has(key) ? ctx.get(key) : initial) as T
  const setValue = useCallback((v: T | ((prev: T) => T)) => {
    const prev = (ctx.has(key) ? ctx.get(key) : initial) as T
    const next = typeof v === 'function' ? (v as (p: T) => T)(prev) : v
    ctx.set(key, next)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  return [current, setValue]
}

export function useAppState() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAppState must be used within <AppStateProvider>')
  return ctx
}
