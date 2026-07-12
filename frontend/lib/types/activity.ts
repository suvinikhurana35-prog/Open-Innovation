export type SourceType = 'home' | 'search' | 'chatbot' | 'explainer' | 'compare' | 'recommendation' | 'profile' | 'other'

export interface PolicyView {
  policyId: string
  title: string
  viewedAt: string
  lastVisitedAt: string
  source: SourceType
  viewCount: number
}

export interface SearchEntry {
  query: string
  timestamp: string
  source?: SourceType
}

export interface CompareEntry {
  scheme1Id: string
  scheme2Id: string
  scheme1Title: string
  scheme2Title: string
  timestamp: string
  source?: SourceType
}

export interface ChatEntry {
  query: string
  response: string
  timestamp: string
  source?: SourceType
}
