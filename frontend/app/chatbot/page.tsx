'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { TransliterateInput } from '@/components/ui/TransliterateInput'
import { VoiceButton } from '@/components/ui/VoiceButton'
import { chatWithAI } from '@/lib/api'
import { useI18n } from '@/lib/i18n'
import { useAuth } from '@/lib/contexts/AuthContext'
import { trackChat } from '@/lib/services/activity'
import { Send, Loader2, Bot, User, Shield, AlertTriangle, Volume2 } from 'lucide-react'
import { cn, getConfidenceColor } from '@/lib/utils'

const LANG_MAP: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  bn: 'bn-IN',
  ta: 'ta-IN',
}

/** Language names for broader TTS voice fallback matching */
const LANG_NAMES: Record<string, string[]> = {
  en: ['en', 'english'],
  hi: ['hi', 'hindi'],
  bn: ['bn', 'bengali', 'bangla'],
  ta: ['ta', 'tamil'],
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  confidence?: string
}

export default function ChatbotPage() {
  const { lang, t } = useI18n()
  const { user } = useAuth()

  // Greet by first name only when we have a signed-in profile.
  const firstName = (user?.fullName || '').trim().split(/\s+/)[0] || ''
  const greeting = firstName
    ? `${t('chat_greeting_hi')} ${firstName}! ${t('chat_greeting_body')}`
    : t('chat_greeting')

  // Compact profile sent to the backend so the bot personalises answers
  // instead of asking questions.
  const profilePayload = user ? {
    fullName: user.fullName,
    age: user.age,
    gender: user.gender,
    state: user.state,
    district: user.district,
    occupation: user.occupation,
    annualIncome: user.annualIncome,
    category: user.category,
    isFarmer: user.isFarmer,
    isStudent: user.isStudent,
    disability: user.disability,
  } : undefined

  const SUGGESTED_QUESTIONS = [
    t('chat_q1'), t('chat_q2'), t('chat_q3'), t('chat_q4'), t('chat_q5'), t('chat_q6'),
  ]
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: greeting },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null)
  const [voiceStatus, setVoiceStatus] = useState<'idle' | 'listening' | 'processing'>('idle')
  const [ttsVoices, setTtsVoices] = useState<SpeechSynthesisVoice[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
    const load = () => {
      const v = window.speechSynthesis.getVoices()
      setTtsVoices([...v])
      if (v.length > 0) {
        Object.entries(LANG_MAP).forEach(([code, bcp]) => {
          const match = v.find(voice => voice.lang === bcp)
          console.log(`[JanNiti TTS] ${code} (${bcp}): ${match ? match.name : 'NO MATCH'}`)
        })
      }
    }
    load()
    window.speechSynthesis.onvoiceschanged = load
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // refresh the greeting when the user switches language or signs in (before any chat starts)
  useEffect(() => {
    setMessages((m) => (m.length === 1 && m[0].role === 'assistant'
      ? [{ role: 'assistant', content: greeting }] : m))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang, firstName])

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText || input).trim()
    if (!text || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await chatWithAI(text, lang, [], undefined, profilePayload)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.reply,
        sources: res.sources,
        confidence: res.confidence,
      }])
      trackChat(text, res.reply)
    } catch (err) {
      console.error('Chatbot API error:', err)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        confidence: 'Low',
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleVoiceTranscript = (text: string) => {
    setInput(text)
  }

  const findVoice = (): SpeechSynthesisVoice | null => {
    const available = ttsVoices.length > 0 ? ttsVoices : window.speechSynthesis.getVoices()
    if (available.length === 0) return null

    const bcpTag = LANG_MAP[lang] || 'en-IN'

    // 1) Exact BCP 47 match
    const exact = available.find(v => v.lang === bcpTag)
    if (exact) return exact

    // 2) Language-only prefix match (e.g. 'bn' matches 'bn-BD', 'bn-IN')
    const langRoot = bcpTag.split('-')[0]
    const prefix = available.find(v => v.lang.startsWith(langRoot))
    if (prefix) return prefix

    // 3) Name-based fuzzy match (e.g. voice name contains "Bengali")
    const names = LANG_NAMES[lang] || []
    if (names.length > 0) {
      const lower = names.map(n => n.toLowerCase())
      const fuzzy = available.find(v =>
        lower.some(l => v.name.toLowerCase().includes(l) || v.lang.toLowerCase().includes(l))
      )
      if (fuzzy) return fuzzy
    }

    return null
  }

  const speakMessage = (text: string, index: number) => {
    window.speechSynthesis.cancel()
    setSpeakingIndex(index)

    const utterance = new SpeechSynthesisUtterance(text)
    const bcpTag = LANG_MAP[lang] || 'en-IN'
    utterance.lang = bcpTag

    const voice = findVoice()
    if (voice) utterance.voice = voice

    utterance.onend = () => setSpeakingIndex(null)
    utterance.onerror = () => setSpeakingIndex(null)

    window.speechSynthesis.speak(utterance)
  }

  const stopSpeaking = () => {
    window.speechSynthesis.cancel()
    setSpeakingIndex(null)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">
          {t('chatbot_title')}
        </h1>
        <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">
          {t('chatbot_sub')}
        </p>
      </div>

      {/* Chat Container */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        {/* Messages */}
        <div className="h-[500px] overflow-y-auto p-4 md:p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-primary-600" />
                </div>
              )}
              <div className={cn(
                'max-w-[80%] rounded-2xl px-4 py-3',
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-md'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-md'
              )}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                    <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                      <Shield className="w-3 h-3" />
                      {t('chat_sources')}: {msg.sources.join(', ')}
                    </div>
                  </div>
                )}
                {msg.confidence && (
                  <div className="mt-1 flex items-center gap-2">
                    <span className={cn('text-xs font-medium', getConfidenceColor(msg.confidence))}>
                      {t('chat_confidence')}: {msg.confidence}
                    </span>
                    {msg.role === 'assistant' && typeof window !== 'undefined' && 'speechSynthesis' in window && (
                      <button
                        onClick={() => speakingIndex === i ? stopSpeaking() : speakMessage(msg.content, i)}
                        className="p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                        title={speakingIndex === i ? 'Stop' : 'Read aloud'}
                      >
                        <Volume2 className={cn('w-3.5 h-3.5', speakingIndex === i ? 'text-primary-600' : 'text-gray-400')} />
                      </button>
                    )}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center shrink-0 mt-1">
                  <User className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-primary-600" />
              </div>
              <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
                <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="flex flex-col gap-2">
            {voiceStatus !== 'idle' && (
              <div className="text-xs text-center text-gray-500 dark:text-gray-400 animate-pulse">
                {voiceStatus === 'listening' ? 'Listening...' : 'Processing...'}
              </div>
            )}
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <TransliterateInput
                  value={input}
                  onChange={(v) => setInput(v)}
                  onSubmit={() => { handleSend() }}
                  placeholder={t('chat_input_placeholder')}
                />
              </div>
              <VoiceButton
                onTranscript={handleVoiceTranscript}
                onSubmit={(text) => { setInput(text); handleSend(text) }}
                onStateChange={setVoiceStatus}
                language={lang}
              />
              <Button onClick={() => { handleSend() }} disabled={loading || !input.trim()} className="h-14 px-6">
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Suggested Questions */}
      <div className="mt-8">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
          {t('chat_try_asking')}
        </h3>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => { setInput(q) }}
              className="px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400 hover:bg-primary-50 hover:text-primary-600 dark:hover:bg-primary-900/20 dark:hover:text-primary-400 transition-colors border border-gray-200 dark:border-gray-700"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 text-sm text-amber-800 dark:text-amber-200">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{t('chat_disclaimer')}</span>
        </div>
      </div>
    </div>
  )
}
