'use client'

/**
 * AccessibilityPanel — MyScheme-style accessibility options (JanNiti v2.0).
 *
 * Drop-in component: render it ONCE, e.g. in app/layout.tsx or providers.tsx:
 *
 *     import AccessibilityPanel from '@/components/ui/AccessibilityPanel'
 *     ...
 *     <AccessibilityPanel />
 *
 * Features (parity with myscheme.gov.in): Bigger/Smaller Text, Text Spacing,
 * Line Height, Dyslexia Friendly, ADHD Mode (reading focus band), High
 * Saturation, Invert Colors, Highlight Links, Big Cursor, Pause Animations,
 * Hide Images, Reset All. Keyboard shortcut: Ctrl + F2. Preferences persist
 * in localStorage. WCAG: focus-visible outlines, aria labels, Esc to close.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

type Prefs = {
  fontScale: number        // 1 = 100%
  textSpacing: boolean
  lineHeight: boolean
  dyslexia: boolean
  adhd: boolean
  saturation: boolean
  invert: boolean
  highlightLinks: boolean
  bigCursor: boolean
  pauseAnim: boolean
  hideImages: boolean
}

const DEFAULTS: Prefs = {
  fontScale: 1, textSpacing: false, lineHeight: false, dyslexia: false,
  adhd: false, saturation: false, invert: false, highlightLinks: false,
  bigCursor: false, pauseAnim: false, hideImages: false,
}

const STORAGE_KEY = 'janniti_a11y'
const STYLE_ID = 'janniti-a11y-style'

const GLOBAL_CSS = `
html.a11y-text-spacing body { letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }
html.a11y-line-height body * { line-height: 1.9 !important; }
html.a11y-dyslexia body, html.a11y-dyslexia body * { font-family: 'Comic Sans MS', 'Trebuchet MS', Verdana, sans-serif !important; }
html.a11y-saturation body { filter: saturate(2.2); }
html.a11y-invert body { filter: invert(1) hue-rotate(180deg); }
html.a11y-invert body img, html.a11y-invert body video { filter: invert(1) hue-rotate(180deg); }
html.a11y-saturation.a11y-invert body { filter: invert(1) hue-rotate(180deg) saturate(2.2); }
html.a11y-links a { text-decoration: underline !important; outline: 2px solid #f59e0b !important; outline-offset: 2px; background: rgba(245,158,11,.15) !important; }
html.a11y-cursor, html.a11y-cursor * { cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24'><path d='M4 2l16 11h-7l4 8-3 1.5-4-8-6 5z' fill='black' stroke='white' stroke-width='1.5'/></svg>") 4 2, auto !important; }
html.a11y-pause *, html.a11y-pause *::before, html.a11y-pause *::after { animation-play-state: paused !important; transition: none !important; scroll-behavior: auto !important; }
html.a11y-noimg body img, html.a11y-noimg body svg:not(.a11y-keep), html.a11y-noimg body video { visibility: hidden !important; }
.a11y-adhd-mask { position: fixed; left: 0; right: 0; background: rgba(0,0,0,.55); z-index: 99990; pointer-events: none; }
`

function applyPrefs(p: Prefs) {
  const html = document.documentElement
  html.style.fontSize = p.fontScale === 1 ? '' : `${p.fontScale * 100}%`
  const cls: Array<[string, boolean]> = [
    ['a11y-text-spacing', p.textSpacing], ['a11y-line-height', p.lineHeight],
    ['a11y-dyslexia', p.dyslexia], ['a11y-saturation', p.saturation],
    ['a11y-invert', p.invert], ['a11y-links', p.highlightLinks],
    ['a11y-cursor', p.bigCursor], ['a11y-pause', p.pauseAnim],
    ['a11y-noimg', p.hideImages],
  ]
  cls.forEach(([c, on]) => html.classList.toggle(c, on))
}

export default function AccessibilityPanel() {
  const [open, setOpen] = useState(false)
  const [prefs, setPrefs] = useState<Prefs>(DEFAULTS)
  const maskTop = useRef<HTMLDivElement | null>(null)
  const maskBottom = useRef<HTMLDivElement | null>(null)

  // inject global CSS once
  useEffect(() => {
    if (!document.getElementById(STYLE_ID)) {
      const s = document.createElement('style')
      s.id = STYLE_ID
      s.textContent = GLOBAL_CSS
      document.head.appendChild(s)
    }
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const p = { ...DEFAULTS, ...JSON.parse(saved) } as Prefs
        setPrefs(p); applyPrefs(p)
      }
    } catch { /* corrupted prefs -> defaults */ }
  }, [])

  // persist + apply on change
  useEffect(() => {
    applyPrefs(prefs)
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs)) } catch { /* ignore */ }
  }, [prefs])

  // Ctrl+F2 toggle, Esc close
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'F2') { e.preventDefault(); setOpen(o => !o) }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // ADHD reading focus band follows the mouse
  useEffect(() => {
    if (!prefs.adhd) {
      maskTop.current?.remove(); maskBottom.current?.remove()
      maskTop.current = maskBottom.current = null
      return
    }
    const top = document.createElement('div'); top.className = 'a11y-adhd-mask'
    const bottom = document.createElement('div'); bottom.className = 'a11y-adhd-mask'
    document.body.append(top, bottom)
    maskTop.current = top; maskBottom.current = bottom
    const BAND = 140
    const move = (e: MouseEvent) => {
      const y = e.clientY
      top.style.top = '0'; top.style.height = `${Math.max(0, y - BAND / 2)}px`
      bottom.style.top = `${y + BAND / 2}px`; bottom.style.bottom = '0'; bottom.style.height = ''
    }
    move({ clientY: window.innerHeight / 2 } as MouseEvent)
    window.addEventListener('mousemove', move)
    return () => { window.removeEventListener('mousemove', move); top.remove(); bottom.remove() }
  }, [prefs.adhd])

  const set = useCallback(<K extends keyof Prefs>(k: K, v: Prefs[K]) => {
    setPrefs(p => ({ ...p, [k]: v }))
  }, [])

  const toggle = (k: keyof Prefs) => set(k, !prefs[k] as never)

  const Tile = ({ label, active, onClick, children, disabled }: {
    label: string; active?: boolean; onClick: () => void; children: React.ReactNode; disabled?: boolean
  }) => (
    <button
      type="button" onClick={onClick} aria-pressed={!!active} disabled={disabled}
      className={`flex flex-col items-center justify-center gap-2 rounded-xl border p-4 text-sm font-medium transition
        ${active ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300' : 'border-slate-600/60 bg-slate-800/60 text-slate-200 hover:border-slate-400'}
        ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
    >
      <span aria-hidden className="text-xl leading-none">{children}</span>
      <span className="text-center leading-tight">{label}</span>
    </button>
  )

  return (
    <>
      {/* floating opener */}
      <button
        type="button"
        aria-label="Accessibility options (Ctrl+F2)"
        title="Accessibility options (Ctrl+F2)"
        onClick={() => setOpen(o => !o)}
        className="fixed right-3 top-1/3 z-[99995] flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-300"
      >
        <svg className="a11y-keep" width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
          <circle cx="12" cy="4.5" r="2.2" />
          <path d="M12 8c-3 0-5.5-.6-7.5-1.2l-.5 1.9C6 9.4 8 9.9 10 10v3l-2.3 7.2 1.9.7L12 14.6l2.4 6.3 1.9-.7L14 13v-3c2-.1 4-.6 6-1.3l-.5-1.9C17.5 7.4 15 8 12 8z" />
        </svg>
      </button>

      {open && (
        <div
          role="dialog" aria-modal="true" aria-label="Accessibility options"
          className="fixed right-3 top-16 z-[99996] w-[min(26rem,calc(100vw-1.5rem))] rounded-2xl border border-slate-600/60 bg-slate-900/95 p-4 shadow-2xl backdrop-blur"
        >
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-white">Accessibility options</h2>
              <kbd className="rounded bg-indigo-600/30 px-2 py-0.5 text-xs text-indigo-200">Ctrl+F2</kbd>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close"
              className="rounded p-1 text-slate-300 hover:bg-slate-700 hover:text-white">✕</button>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <Tile label="Bigger Text" onClick={() => set('fontScale', Math.min(1.4, +(prefs.fontScale + 0.1).toFixed(2)))}
              active={prefs.fontScale > 1} disabled={prefs.fontScale >= 1.4}>T↑</Tile>
            <Tile label="Smaller Text" onClick={() => set('fontScale', Math.max(0.8, +(prefs.fontScale - 0.1).toFixed(2)))}
              active={prefs.fontScale < 1} disabled={prefs.fontScale <= 0.8}>T↓</Tile>
            <Tile label="Text Spacing" active={prefs.textSpacing} onClick={() => toggle('textSpacing')}>A·B</Tile>
            <Tile label="Line Height" active={prefs.lineHeight} onClick={() => toggle('lineHeight')}>≡</Tile>
            <Tile label="Dyslexia Friendly" active={prefs.dyslexia} onClick={() => toggle('dyslexia')}>Df</Tile>
            <Tile label="ADHD Mode" active={prefs.adhd} onClick={() => toggle('adhd')}>◫</Tile>
            <Tile label="High Saturation" active={prefs.saturation} onClick={() => toggle('saturation')}>◐</Tile>
            <Tile label="Invert Colors" active={prefs.invert} onClick={() => toggle('invert')}>◑</Tile>
            <Tile label="Highlight Links" active={prefs.highlightLinks} onClick={() => toggle('highlightLinks')}>🔗</Tile>
            <Tile label="Big Cursor" active={prefs.bigCursor} onClick={() => toggle('bigCursor')}>↖</Tile>
            <Tile label="Pause Animation" active={prefs.pauseAnim} onClick={() => toggle('pauseAnim')}>⏸</Tile>
            <Tile label="Hide Images" active={prefs.hideImages} onClick={() => toggle('hideImages')}>🖼</Tile>
          </div>

          <button
            type="button"
            onClick={() => setPrefs(DEFAULTS)}
            className="mt-3 w-full rounded-xl border border-slate-600/60 bg-slate-800/60 py-2 text-sm font-medium text-slate-200 hover:border-slate-400"
          >
            ⟲ Reset All Settings
          </button>
        </div>
      )}
    </>
  )
}
