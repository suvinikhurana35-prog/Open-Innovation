'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Mic, MicOff, Loader2 } from 'lucide-react'

type VoiceState = 'idle' | 'listening' | 'processing'

/**
 * Priority-ordered BCP 47 language codes for SpeechRecognition.
 * Chrome may not support every India-specific locale (e.g. bn-IN, ta-IN),
 * so we fall back through a chain of broader codes.
 */
const LANG_PRIORITY: Record<string, string[]> = {
  en: ['en-IN', 'en'],
  hi: ['hi-IN', 'hi'],
  bn: ['bn-IN', 'bn-BD', 'bn'],
  ta: ['ta-IN', 'ta-LK', 'ta'],
}

const DEFAULT_LANG = 'en-IN'

interface VoiceButtonProps {
  onTranscript: (text: string) => void
  onSubmit?: (text: string) => void
  onStateChange?: (state: VoiceState) => void
  language?: string
  className?: string
}

export function VoiceButton({ onTranscript, onSubmit, onStateChange, language = 'en', className }: VoiceButtonProps) {
  const [state, setState] = useState<VoiceState>('idle')
  const [unsupported, setUnsupported] = useState(false)
  const [langIndex, setLangIndex] = useState(0)
  const recognitionRef = useRef<any>(null)
  const finalTranscriptRef = useRef('')
  const shouldSubmitRef = useRef(false)
  const onTranscriptRef = useRef(onTranscript)
  const onSubmitRef = useRef(onSubmit)
  const onStateChangeRef = useRef(onStateChange)
  const langIndexRef = useRef(0)

  onTranscriptRef.current = onTranscript
  onSubmitRef.current = onSubmit
  onStateChangeRef.current = onStateChange

  const codes = LANG_PRIORITY[language] || [DEFAULT_LANG]
  const currentCode = codes[langIndex] || codes[0]

  const updateState = useCallback((newState: VoiceState) => {
    setState(newState)
    onStateChangeRef.current?.(newState)
  }, [])

  useEffect(() => {
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognitionAPI) {
      setUnsupported(true)
      return
    }

    const recognition = new SpeechRecognitionAPI()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event: any) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      const text = final || interim
      if (text) {
        onTranscriptRef.current(text)
      }
      if (final) {
        finalTranscriptRef.current = final
      }
    }

    recognition.onerror = (event: any) => {
      const error = event.error || 'unknown'
      if (shouldSubmitRef.current && codes.length > 1 && langIndexRef.current < codes.length - 1) {
        const nextIdx = langIndexRef.current + 1
        langIndexRef.current = nextIdx
        setLangIndex(nextIdx)
        recognition.lang = codes[nextIdx]
        try { recognition.start() } catch {}
      } else {
        shouldSubmitRef.current = false
        updateState('idle')
      }
    }

    recognition.onend = () => {
      const text = finalTranscriptRef.current
      finalTranscriptRef.current = ''
      if (text && shouldSubmitRef.current && onSubmitRef.current) {
        updateState('processing')
        onSubmitRef.current(text)
        setTimeout(() => updateState('idle'), 400)
      } else {
        updateState('idle')
      }
      shouldSubmitRef.current = false
    }

    recognitionRef.current = recognition

    return () => {
      recognition.abort()
    }
  }, [language, updateState, codes])

  const toggleListening = useCallback(() => {
    const recognition = recognitionRef.current
    if (!recognition || state === 'processing') return

    if (state === 'listening') {
      shouldSubmitRef.current = false
      recognition.stop()
      setLangIndex(0)
      langIndexRef.current = 0
      updateState('idle')
    } else {
      finalTranscriptRef.current = ''
      shouldSubmitRef.current = true
      langIndexRef.current = 0
      setLangIndex(0)
      recognition.lang = codes[0]
      try { recognition.start() } catch {}
      updateState('listening')
    }
  }, [state, codes, updateState])

  if (unsupported) return null

  return (
    <button
      onClick={toggleListening}
      disabled={state === 'processing'}
      className={cn(
        'flex items-center justify-center w-14 h-14 rounded-full transition-all duration-200 shrink-0',
        state === 'listening'
          ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30'
          : 'bg-primary-600 text-white hover:bg-primary-700 shadow-md',
        state === 'processing' && 'opacity-50 cursor-not-allowed',
        className
      )}
      aria-label={state === 'listening' ? 'Stop listening' : 'Start voice input'}
      title={
        state === 'listening'
          ? 'Listening...'
          : state === 'processing'
            ? 'Processing...'
            : 'Tap to speak'
      }
    >
      {state === 'processing' ? (
        <Loader2 className="w-6 h-6 animate-spin" />
      ) : state === 'listening' ? (
        <MicOff className="w-6 h-6" />
      ) : (
        <Mic className="w-6 h-6" />
      )}
    </button>
  )
}
