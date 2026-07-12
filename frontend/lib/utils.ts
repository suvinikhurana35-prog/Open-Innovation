import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
]

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiFetch(endpoint: string, options?: RequestInit) {
  const mergedHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: options?.method,
    headers: mergedHeaders,
    body: options?.body,
    signal: options?.signal,
  })

  const body = await res.json().catch(() => ({}))

  if (!res.ok) {
    const errMsg = body?.error || body?.detail || `Request failed with status ${res.status}`
    console.error(`API Error [${res.status}] ${endpoint}:`, errMsg)
    throw new Error(errMsg)
  }

  // Unwrap standardized { success, data, error } format
  if (body && typeof body === 'object' && 'success' in body) {
    if (!body.success) {
      throw new Error(body.error || 'Request failed')
    }
    return body.data
  }

  // Fallback: return body as-is for non-wrapped responses
  return body
}

export function getConfidenceColor(confidence: string): string {
  switch (confidence?.toLowerCase()) {
    case 'high': return 'text-green-600 dark:text-green-400'
    case 'medium': return 'text-yellow-600 dark:text-yellow-400'
    case 'low': return 'text-red-600 dark:text-red-400'
    default: return 'text-gray-500'
  }
}
