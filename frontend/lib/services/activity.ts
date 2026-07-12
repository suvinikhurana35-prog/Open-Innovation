import type { PolicyView, SearchEntry, CompareEntry, ChatEntry, SourceType } from '@/lib/types/activity'

const KEYS = {
  ENABLED: 'janniti_activity_enabled',
  VIEWS: 'janniti_activity_views',
  SEARCHES: 'janniti_activity_searches',
  COMPARES: 'janniti_activity_compares',
  CHATS: 'janniti_activity_chats',
}

const MAX = 20

/* ─── Low-level helpers ─── */

function read<T>(key: string): T[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function write<T>(key: string, data: T[]): void {
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch {
    /* quota exceeded — silently fail */
  }
}

function prepend<T>(items: T[], newItem: T, dedupKey: (item: T) => string): T[] {
  const filtered = items.filter(i => dedupKey(i) !== dedupKey(newItem))
  return [newItem, ...filtered].slice(0, MAX)
}

/* ─── Migration helpers (backward compat with old localStorage data) ─── */

function migrateView(v: any): PolicyView {
  return {
    policyId: v.policyId,
    title: v.title,
    viewedAt: v.viewedAt,
    lastVisitedAt: v.lastVisitedAt || v.viewedAt,
    source: v.source || 'other',
    viewCount: v.viewCount ?? 1,
  }
}

function readViews(): PolicyView[] {
  return read<any>(KEYS.VIEWS).map(migrateView)
}

function migrateSearch(v: any): SearchEntry {
  return { query: v.query, timestamp: v.timestamp, source: v.source || undefined }
}

function readSearches(): SearchEntry[] {
  return read<any>(KEYS.SEARCHES).map(migrateSearch)
}

function migrateCompare(v: any): CompareEntry {
  return { ...v, source: v.source || undefined }
}

function readCompares(): CompareEntry[] {
  return read<any>(KEYS.COMPARES).map(migrateCompare)
}

function migrateChat(v: any): ChatEntry {
  return { ...v, source: v.source || undefined }
}

function readChats(): ChatEntry[] {
  return read<any>(KEYS.CHATS).map(migrateChat)
}

/* ─── Privacy toggle ─── */

export function isEnabled(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(KEYS.ENABLED) !== 'false'
}

export function setEnabled(enabled: boolean): void {
  localStorage.setItem(KEYS.ENABLED, String(enabled))
  if (!enabled) clearAll()
}

/* ─── Views ─── */

export function getViews(): PolicyView[] {
  return readViews()
}

export function trackView(policyId: string, title: string, source: SourceType = 'other'): void {
  if (!isEnabled()) return
  const items = readViews()
  const now = new Date().toISOString()
  const existing = items.find(i => i.policyId === policyId)
  const entry: PolicyView = {
    policyId,
    title,
    viewedAt: existing ? existing.viewedAt : now,
    lastVisitedAt: now,
    source,
    viewCount: existing ? existing.viewCount + 1 : 1,
  }
  write(KEYS.VIEWS, prepend(items, entry, i => i.policyId))
}

export function removeView(policyId: string): void {
  write(KEYS.VIEWS, readViews().filter(i => i.policyId !== policyId))
}

export function clearViews(): void {
  write(KEYS.VIEWS, [])
}

/* ─── Recommendation-ready helpers for views ─── */

export function getMostRecentViews(limit?: number): PolicyView[] {
  const items = readViews().sort((a, b) => new Date(b.lastVisitedAt).getTime() - new Date(a.lastVisitedAt).getTime())
  return limit ? items.slice(0, limit) : items
}

export function getMostFrequentViews(limit?: number): PolicyView[] {
  const items = readViews().sort((a, b) => b.viewCount - a.viewCount)
  return limit ? items.slice(0, limit) : items
}

export function getViewsBySource(source: SourceType): PolicyView[] {
  return readViews().filter(v => v.source === source)
}

export function getViewsBySources(sources: SourceType[]): PolicyView[] {
  return readViews().filter(v => sources.includes(v.source))
}

export function getTopViewedPolicies(limit: number = 5): { policyId: string; title: string; viewCount: number; lastVisitedAt: string }[] {
  return getMostFrequentViews(limit).map(v => ({
    policyId: v.policyId,
    title: v.title,
    viewCount: v.viewCount,
    lastVisitedAt: v.lastVisitedAt,
  }))
}

/* ─── Searches ─── */

export function getSearches(): SearchEntry[] {
  return readSearches()
}

export function trackSearch(query: string, source: SourceType = 'search'): void {
  if (!isEnabled() || !query.trim()) return
  const items = readSearches()
  const entry: SearchEntry = { query: query.trim(), timestamp: new Date().toISOString(), source }
  write(KEYS.SEARCHES, prepend(items, entry, i => i.query))
}

export function removeSearch(query: string): void {
  write(KEYS.SEARCHES, readSearches().filter(i => i.query !== query))
}

export function clearSearches(): void {
  write(KEYS.SEARCHES, [])
}

export function getRecentSearches(limit?: number): SearchEntry[] {
  const items = readSearches().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  return limit ? items.slice(0, limit) : items
}

/* ─── Compares ─── */

export function getCompares(): CompareEntry[] {
  return readCompares()
}

export function trackCompare(
  scheme1Id: string, scheme2Id: string,
  scheme1Title: string, scheme2Title: string,
  source: SourceType = 'compare',
): void {
  if (!isEnabled()) return
  const items = readCompares()
  const entry: CompareEntry = {
    scheme1Id, scheme2Id, scheme1Title, scheme2Title,
    timestamp: new Date().toISOString(), source,
  }
  write(KEYS.COMPARES, prepend(items, entry, i => `${i.scheme1Id}::${i.scheme2Id}`))
}

export function removeCompare(index: number): void {
  const items = readCompares()
  items.splice(index, 1)
  write(KEYS.COMPARES, items)
}

export function clearCompares(): void {
  write(KEYS.COMPARES, [])
}

export function getRecentCompares(limit?: number): CompareEntry[] {
  const items = readCompares().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  return limit ? items.slice(0, limit) : items
}

/* ─── Chats ─── */

export function getChats(): ChatEntry[] {
  return readChats()
}

export function trackChat(query: string, response: string, source: SourceType = 'chatbot'): void {
  if (!isEnabled() || !query.trim()) return
  const items = readChats()
  const entry: ChatEntry = { query: query.trim(), response, timestamp: new Date().toISOString(), source }
  write(KEYS.CHATS, prepend(items, entry, i => i.timestamp))
}

export function removeChat(timestamp: string): void {
  write(KEYS.CHATS, readChats().filter(i => i.timestamp !== timestamp))
}

export function clearChats(): void {
  write(KEYS.CHATS, [])
}

export function getRecentChats(limit?: number): ChatEntry[] {
  const items = readChats().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  return limit ? items.slice(0, limit) : items
}

/* ─── Clear all ─── */

export function clearAll(): void {
  write(KEYS.VIEWS, [])
  write(KEYS.SEARCHES, [])
  write(KEYS.COMPARES, [])
  write(KEYS.CHATS, [])
}
