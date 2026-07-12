'use client'

import { useState, useEffect, useCallback } from 'react'
import { Eye, Search, ArrowRightLeft, MessageSquare, Trash2, ChevronDown, ChevronUp, Clock, FileText, Home, MessageCircle, GitCompare, User, Sparkles } from 'lucide-react'
import * as ActivityService from '@/lib/services/activity'
import type { PolicyView, SearchEntry, CompareEntry, ChatEntry, SourceType } from '@/lib/types/activity'

const SOURCE_LABELS: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  home: { label: 'Home', icon: <Home className="w-3 h-3" />, color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
  search: { label: 'Search', icon: <Search className="w-3 h-3" />, color: 'bg-safron-100 text-safron-700 dark:bg-amber-900/30 dark:text-amber-300' },
  chatbot: { label: 'Chat', icon: <MessageCircle className="w-3 h-3" />, color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
  explainer: { label: 'Explainer', icon: <FileText className="w-3 h-3" />, color: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' },
  compare: { label: 'Compare', icon: <GitCompare className="w-3 h-3" />, color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
  recommendation: { label: 'Recommended', icon: <Sparkles className="w-3 h-3" />, color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' },
  profile: { label: 'Profile', icon: <User className="w-3 h-3" />, color: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300' },
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} hr ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

interface SectionProps<T> {
  icon: React.ReactNode
  title: string
  items: T[]
  emptyLabel: string
  renderItem: (item: T, index: number) => React.ReactNode
  onClear: () => void
}

function CollapsibleSection<T>({ icon, title, items, emptyLabel, renderItem, onClear }: SectionProps<T>) {
  const [open, setOpen] = useState(true)
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
          {icon}
          {title}
          {items.length > 0 && (
            <span className="text-xs text-gray-400 font-normal">({items.length})</span>
          )}
        </span>
        <div className="flex items-center gap-2">
          {items.length > 0 && (
            <button
              onClick={(e) => { e.stopPropagation(); onClear() }}
              className="text-xs text-red-500 hover:text-red-600 dark:text-red-400 px-2 py-0.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Clear
            </button>
          )}
          {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>
      {open && (
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {items.length === 0 ? (
            <p className="px-4 py-6 text-sm text-gray-400 text-center">{emptyLabel}</p>
          ) : (
            items.map((item, i) => (
              <div key={i} className="px-4 py-2.5">
                {renderItem(item, i)}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export function ActivitySection() {
  const [views, setViews] = useState<PolicyView[]>([])
  const [searches, setSearches] = useState<SearchEntry[]>([])
  const [compares, setCompares] = useState<CompareEntry[]>([])
  const [chats, setChats] = useState<ChatEntry[]>([])

  const load = useCallback(() => {
    setViews(ActivityService.getViews())
    setSearches(ActivityService.getSearches())
    setCompares(ActivityService.getCompares())
    setChats(ActivityService.getChats())
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="space-y-4">
      {/* Views */}
      <CollapsibleSection
        icon={<Eye className="w-4 h-4 text-primary-500" />}
        title="Recently Viewed"
        items={views}
        emptyLabel="No policies viewed yet"
        onClear={() => { ActivityService.clearViews(); load() }}
        renderItem={(item, _i) => {
          const src = SOURCE_LABELS[item.source]
          return (
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <FileText className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                <div className="min-w-0 flex-1">
                  <span className="text-sm text-gray-700 dark:text-gray-300 truncate block">{item.title}</span>
                  {src && (
                    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium mt-0.5 ${src.color}`}>
                      {src.icon}{src.label}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-gray-400">{timeAgo(item.lastVisitedAt || item.viewedAt)}</span>
                <span className="text-[10px] text-gray-300 dark:text-gray-600">×{item.viewCount}</span>
                <button
                  onClick={() => { ActivityService.removeView(item.policyId); load() }}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )
        }}
      />

      {/* Searches */}
      <CollapsibleSection
        icon={<Search className="w-4 h-4 text-safron-500" />}
        title="Recent Searches"
        items={searches}
        emptyLabel="No searches yet"
        onClear={() => { ActivityService.clearSearches(); load() }}
        renderItem={(item, _i) => (
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm text-gray-700 dark:text-gray-300 truncate min-w-0 flex-1">{item.query}</span>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-gray-400">{timeAgo(item.timestamp)}</span>
              <button
                onClick={() => { ActivityService.removeSearch(item.query); load() }}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      />

      {/* Compares */}
      <CollapsibleSection
        icon={<ArrowRightLeft className="w-4 h-4 text-blue-500" />}
        title="Recent Comparisons"
        items={compares}
        emptyLabel="No comparisons yet"
        onClear={() => { ActivityService.clearCompares(); load() }}
        renderItem={(item, i) => (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-300 min-w-0 flex-1 truncate">
              <span className="truncate">{item.scheme1Title}</span>
              <span className="text-gray-400 text-xs shrink-0">vs</span>
              <span className="truncate">{item.scheme2Title}</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-gray-400">{timeAgo(item.timestamp)}</span>
              <button
                onClick={() => { ActivityService.removeCompare(i); load() }}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      />

      {/* Chats */}
      <CollapsibleSection
        icon={<MessageSquare className="w-4 h-4 text-green-500" />}
        title="Recent Chats"
        items={chats}
        emptyLabel="No chats yet"
        onClear={() => { ActivityService.clearChats(); load() }}
        renderItem={(item, _i) => (
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-700 dark:text-gray-300 truncate font-medium">{item.query}</p>
              <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{item.response}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0 mt-0.5">
              <span className="text-xs text-gray-400">{timeAgo(item.timestamp)}</span>
              <button
                onClick={() => { ActivityService.removeChat(item.timestamp); load() }}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      />

      {/* Clear all */}
      {[views, searches, compares, chats].some(arr => arr.length > 0) && (
        <div className="flex justify-center pt-2">
          <button
            onClick={() => { ActivityService.clearAll(); load() }}
            className="px-4 py-2 rounded-xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            Clear All Activity
          </button>
        </div>
      )}
    </div>
  )
}
