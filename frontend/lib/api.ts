import { apiFetch } from './utils'

export interface PolicyQuery {
  query: string
  language?: string
  state?: string
}

export async function explainScheme(query: PolicyQuery) {
  return apiFetch('/api/explainer/explain', {
    method: 'POST',
    body: JSON.stringify(query),
  })
}

export async function detectConditions(query: PolicyQuery) {
  return apiFetch('/api/explainer/conditions', {
    method: 'POST',
    body: JSON.stringify(query),
  })
}

export async function getELI5(query: PolicyQuery) {
  return apiFetch('/api/explainer/eli5', {
    method: 'POST',
    body: JSON.stringify(query),
  })
}

export async function searchSchemes(q: string) {
  return apiFetch(`/api/explainer/search?q=${encodeURIComponent(q)}`)
}

export type ChatTurn = { role: 'user' | 'assistant'; content: string }

export async function translateTexts(texts: string[], language: string) {
  return apiFetch('/api/chat/translate', {
    method: 'POST',
    body: JSON.stringify({ texts, language }),
  })
}

export async function chatWithAI(
  message: string,
  language: string = 'en',
  conversationHistory: ChatTurn[] = [],
  conversationId?: string,
  profile?: Record<string, any>
) {
  return apiFetch('/api/chat/message', {
    method: 'POST',
    body: JSON.stringify({
      message,
      language,
      conversation_history: conversationHistory,
      conversation_id: conversationId,
      profile: profile || null,
    }),
  })
}

export async function compareSchemes(scheme1: string, scheme2: string, language: string = 'en') {
  return apiFetch('/api/compare/', {
    method: 'POST',
    body: JSON.stringify({ scheme1, scheme2, language }),
  })
}

export async function getDashboardStats() {
  return apiFetch('/api/dashboard/stats')
}

export async function recommendForProfile(scheme1: string, scheme2: string, profile: Record<string, string>, language: string = 'en') {
  return apiFetch('/api/compare/recommend', {
    method: 'POST',
    body: JSON.stringify({ scheme1, scheme2, profile, language }),
  })
}

// Latin -> Indic transliteration suggestions (proxied via backend to avoid CORS).
export async function transliterate(text: string, lang: string): Promise<string[]> {
  if (!text || lang === 'en') return []
  try {
    const res = await apiFetch(
      `/api/transliterate?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(lang)}`
    )
    return (res?.suggestions as string[]) || []
  } catch {
    return []
  }
}
