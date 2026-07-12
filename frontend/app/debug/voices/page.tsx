'use client'

import { useState, useEffect } from 'react'

const APP_LANGUAGES = ['en', 'hi', 'bn', 'ta']

const LANG_MAP: Record<string, string> = {
  en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN',
}

const LANG_NAMES: Record<string, string[]> = {
  en: ['en', 'english'],
  hi: ['hi', 'hindi'],
  bn: ['bn', 'bengali', 'bangla'],
  ta: ['ta', 'tamil'],
}

const LANG_PRIORITY: Record<string, string[]> = {
  en: ['en-IN', 'en'],
  hi: ['hi-IN', 'hi'],
  bn: ['bn-IN', 'bn-BD', 'bn'],
  ta: ['ta-IN', 'ta-LK', 'ta'],
}

function findVoice(voices: SpeechSynthesisVoice[], lang: string): { strategy: string; voice: SpeechSynthesisVoice | null } {
  const bcpTag = LANG_MAP[lang] || 'en-IN'

  // 1) Exact BCP 47 match
  const exact = voices.find(v => v.lang === bcpTag)
  if (exact) return { strategy: `exact (${bcpTag})`, voice: exact }

  // 2) Lang root prefix match
  const langRoot = bcpTag.split('-')[0]
  const prefix = voices.find(v => v.lang.startsWith(langRoot))
  if (prefix) return { strategy: `prefix (${langRoot})`, voice: prefix }

  // 3) Name-based fuzzy match
  const names = LANG_NAMES[lang] || []
  if (names.length > 0) {
    const lower = names.map(n => n.toLowerCase())
    const fuzzy = voices.find(v =>
      lower.some(l => v.name.toLowerCase().includes(l) || v.lang.toLowerCase().includes(l))
    )
    if (fuzzy) return { strategy: `fuzzy name (${names.join(', ')})`, voice: fuzzy }
  }

  return { strategy: 'default voice (none matched)', voice: null }
}

export default function DebugVoicesPage() {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const [srResults, setSrResults] = useState<Record<string, string>>({})
  const [log, setLog] = useState<string[]>([])

  const addLog = (msg: string) => setLog(prev => [...prev, msg])

  useEffect(() => {
    if (typeof window === 'undefined') return

    // --- SpeechSynthesis voices ---
    if ('speechSynthesis' in window) {
      const loadVoices = () => {
        const v = window.speechSynthesis.getVoices()
        setVoices(v)
        addLog(`SpeechSynthesis: ${v.length} voices loaded`)
        v.forEach(vv => addLog(`  [${vv.lang}] ${vv.name} (${vv.voiceURI}) local=${vv.localService}`))
      }
      loadVoices()
      window.speechSynthesis.onvoiceschanged = loadVoices
    } else {
      addLog('SpeechSynthesis: NOT AVAILABLE')
    }

    // --- SpeechRecognition support ---
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognitionAPI) {
      addLog('SpeechRecognition: AVAILABLE')
      // Test all codes in the priority chain
      Object.entries(LANG_PRIORITY).forEach(([appLang, codes]) => {
        codes.forEach(code => {
          try {
            const rec = new SpeechRecognitionAPI()
            rec.lang = code
            setSrResults(prev => ({ ...prev, [code]: 'OK' }))
            addLog(`  SR ${code} (from ${appLang}): lang property accepted`)
          } catch (e: any) {
            setSrResults(prev => ({ ...prev, [code]: `ERROR: ${e.message}` }))
            addLog(`  SR ${code} (from ${appLang}): ERROR setting lang — ${e.message}`)
          }
        })
      })
    } else {
      addLog('SpeechRecognition: NOT AVAILABLE')
    }
  }, [])

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-8">
      <h1 className="text-2xl font-bold">Voice Diagnostics</h1>
      <p className="text-gray-600 text-sm">
        Vist this page in your browser, then open the browser console (F12) for full logs.
        Navigate to <strong>/chatbot</strong> and check the console for TTS voice matching logs.
      </p>

      {/* TTS Voice Fallback Resolution */}
      <section>
        <h2 className="text-lg font-semibold mb-2">TTS Voice Resolution (fallback chain)</h2>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2 text-left">App Lang</th>
              <th className="border p-2 text-left">Target BCP</th>
              <th className="border p-2 text-left">Available Voices for Lang</th>
              <th className="border p-2 text-left">Resolved Voice</th>
              <th className="border p-2 text-left">Fallback Strategy</th>
            </tr>
          </thead>
          <tbody>
            {APP_LANGUAGES.map(lang => {
              const { strategy, voice } = findVoice(voices, lang)
              const matchingVoices = voices.filter(v => v.lang.startsWith(LANG_MAP[lang].split('-')[0]))
              return (
                <tr key={lang} className={voice ? 'bg-green-50' : 'bg-yellow-50'}>
                  <td className="border p-2 font-mono">{lang}</td>
                  <td className="border p-2 font-mono">{LANG_MAP[lang]}</td>
                  <td className="border p-2">
                    {matchingVoices.length > 0
                      ? matchingVoices.map(v => `${v.name} [${v.lang}]`).join(', ')
                      : <span className="text-red-500">NONE</span>
                    }
                  </td>
                  <td className="border p-2">
                    {voice ? `${voice.name} [${voice.lang}]` : <span className="text-red-500">NONE (will use default)</span>}
                  </td>
                  <td className="border p-2 text-xs">{strategy}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>

      {/* STT Language Priority Chains */}
      <section>
        <h2 className="text-lg font-semibold mb-2">STT Language Priority Chains</h2>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2 text-left">App Lang</th>
              <th className="border p-2 text-left">Codes (priority order)</th>
              <th className="border p-2 text-left">Each Accepted?</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(LANG_PRIORITY).map(([appLang, codes]) => (
              <tr key={appLang}>
                <td className="border p-2 font-mono">{appLang}</td>
                <td className="border p-2 font-mono">{codes.join(' → ')}</td>
                <td className="border p-2">
                  {codes.map(code => (
                    <span key={code} className={srResults[code] === 'OK' ? 'text-green-600' : 'text-red-600'}>
                      {code}: {srResults[code] || 'pending...'}{' '}
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* All available voices */}
      <section>
        <h2 className="text-lg font-semibold mb-2">All Available SpeechSynthesis Voices ({voices.length})</h2>
        {voices.length === 0 ? (
          <p className="text-gray-500">Loading voices... (reload if empty)</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border p-2 text-left">Lang</th>
                  <th className="border p-2 text-left">Name</th>
                  <th className="border p-2 text-left">URI</th>
                  <th className="border p-2 text-left">Local</th>
                </tr>
              </thead>
              <tbody>
                {[...voices]
                  .sort((a, b) => a.lang.localeCompare(b.lang))
                  .map((v, i) => (
                    <tr key={i} className={
                      v.lang.startsWith('bn') || v.lang.startsWith('ta')
                        ? 'bg-yellow-100'
                        : v.lang.startsWith('hi') || v.lang.startsWith('en')
                          ? 'bg-green-50'
                          : ''
                    }>
                      <td className="border p-2 font-mono">{v.lang}</td>
                      <td className="border p-2">{v.name}</td>
                      <td className="border p-2 text-xs">{v.voiceURI}</td>
                      <td className="border p-2">{v.localService ? 'YES' : 'remote'}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Diagnostic log */}
      <section>
        <h2 className="text-lg font-semibold mb-2">Diagnostic Log</h2>
        <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-auto max-h-96 whitespace-pre-wrap">
          {log.map((line, i) => <div key={i}>{line}</div>)}
        </pre>
      </section>
    </div>
  )
}
