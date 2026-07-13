'use client'

import { useEffect, useState } from 'react'
import { usePersistent } from '@/lib/contexts/AppStateContext'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { SourceBadge } from '@/components/ui/SourceBadge'
import { explainScheme, detectConditions, getELI5 } from '@/lib/api'
import { useLang } from '@/lib/i18n'
import { SCHEMES, schemeLabel, findScheme } from '@/lib/schemes'
import { trackView } from '@/lib/services/activity'
import {
  Loader2, AlertTriangle, CheckCircle2, Info, ExternalLink,
  FileText, BookOpen, Lightbulb, Users, FileCheck,
  ClipboardList, CalendarClock, HelpCircle,
  Sparkles, Shield, AlertOctagon
} from 'lucide-react'

interface SchemeResult {
  title: string
  what_is: string
  why_introduced: string
  benefits: string[]
  eligibility: string[]
  documents: string[]
  how_to_apply: string
  deadlines: string | null
  misunderstood_clauses: string[]
  source: string
  ministry: string
  last_updated: string
  confidence: string
  disclaimer: string
}

interface Condition {
  text: string
  severity: 'green' | 'yellow' | 'red'
  explanation: string
}

interface ELI5Result {
  story: string
  simple_explanation: string
  everyday_example: string
  key_takeaway: string
}

function SeverityIcon({ severity }: { severity: string }) {
  switch (severity) {
    case 'red': return <AlertOctagon className="w-5 h-5 text-alert-red" />
    case 'yellow': return <AlertTriangle className="w-5 h-5 text-alert-yellow" />
    default: return <Info className="w-5 h-5 text-alert-green" />
  }
}

export default function ExplainerPage() {
  const { lang, t } = useLang()
  const [query, setQuery] = usePersistent<string>('explainer:query', '')
  const [loading, setLoading] = useState(false)
  const [showELI5, setShowELI5] = useState(false)
  const [showConditions, setShowConditions] = useState(false)
  const [activeTab, setActiveTab] = usePersistent<'explain' | 'eli5' | 'conditions'>('explainer:tab', 'explain')

  const [result, setResult] = usePersistent<SchemeResult | null>('explainer:result', null)
  const [eli5, setEli5] = usePersistent<ELI5Result | null>('explainer:eli5', null)
  const [conditions, setConditions] = usePersistent<{ conditions: Condition[], summary: string } | null>('explainer:conditions', null)
  const [error, setError] = useState('')

  const handleSearch = async (override?: string) => {
    const q = (override ?? query).trim()
    if (!q) return
    setLoading(true)
    setError('')
    setResult(null)
    setEli5(null)
    setConditions(null)
    setActiveTab('explain')

    try {
      // Only the explanation loads on search -> fast. Other tabs load on demand.
      const explainResult = await explainScheme({ query: q, language: lang })
      setResult(explainResult)
      const scheme = findScheme(q)
      if (scheme) {
        trackView(scheme.id, explainResult.title, 'explainer')
      }
    } catch (err) {
      console.error('Explainer API error:', err)
      setError('Failed to fetch explanation. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // LANGUAGE SWITCH FIX: when the user changes language after content has
  // loaded, re-fetch everything that is on screen in the new language —
  // no new search or refresh needed. (Previously only UI headings changed.)
  useEffect(() => {
    if (!result || !query.trim()) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const q = query.trim()
        const [explainRes, eli5Res, condRes] = await Promise.all([
          explainScheme({ query: q, language: lang }),
          eli5 ? getELI5({ query: q, language: lang }) : Promise.resolve(null),
          conditions ? detectConditions({ query: q, language: lang }) : Promise.resolve(null),
        ])
        if (cancelled) return
        setResult(explainRes)
        if (eli5Res) setEli5(eli5Res)
        if (condRes) setConditions(condRes)
      } catch (err) {
        console.error('Language re-fetch error:', err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  // Lazy-load the Simple Story only when its tab is opened
  const loadEli5 = async () => {
    if (eli5 || !query.trim()) return
    try {
      setEli5(await getELI5({ query: query.trim(), language: lang }))
    } catch (err) { console.error('ELI5 error:', err) }
  }

  // Lazy-load Hidden Conditions only when its tab is opened
  const loadConditions = async () => {
    if (conditions || !query.trim()) return
    try {
      setConditions(await detectConditions({ query: query.trim(), language: lang }))
    } catch (err) { console.error('Conditions error:', err) }
  }




  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">
          {t('page_title')}
        </h1>
        <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">
          {t('page_sub')}
        </p>
      </div>

      {/* Scheme picker (one-click, in the selected language) */}
      <div className="mb-8">
        <p className="text-center text-gray-600 dark:text-gray-400 mb-3">{t('explainer_pick')}</p>
        <div className="max-w-xl mx-auto">
          <select
            value={query}
            onChange={(e) => { const id = e.target.value; setQuery(id); if (id) handleSearch(id) }}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-base focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label={t('choose_scheme')}
          >
            <option value="">{t('choose_scheme')}</option>
            {SCHEMES.map((sc) => (
              <option key={sc.id} value={sc.id}>{schemeLabel(sc, lang)}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-16">
          <Loader2 className="w-10 h-10 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">{t('analyzing')}</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6 animate-fade-in">
          {/* Title */}
          <div className="bg-gradient-to-r from-primary-50 to-safron-50 dark:from-gray-800 dark:to-gray-800 rounded-2xl p-6 md:p-8 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-4">
              <Shield className="w-8 h-8 text-primary-600 mt-1 shrink-0" />
              <div>
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">{result.title}</h2>
                <SourceBadge
                  source={result.source}
                  ministry={result.ministry}
                  lastUpdated={result.last_updated}
                  confidence={result.confidence}
                  officialUrl={findScheme(query)?.official}
                />
              </div>
            </div>
          </div>

          {/* Apply Now -> official government portal (new tab) */}
          {findScheme(query) && (
            <a
              href={findScheme(query)!.apply}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between gap-4 bg-green-600 hover:bg-green-700 text-white rounded-2xl px-6 py-5 transition-colors shadow-sm"
            >
              <div>
                <div className="text-lg md:text-xl font-bold flex items-center gap-2">
                  <ExternalLink className="w-5 h-5" /> {t('apply_now')}
                </div>
                <div className="text-sm text-green-100 mt-0.5">{t('apply_sub')}</div>
              </div>
              <span className="hidden sm:inline text-sm font-mono bg-green-700/60 rounded-lg px-3 py-1.5 truncate max-w-[16rem]">
                {findScheme(query)!.apply.replace('https://', '')}
              </span>
            </a>
          )}

          {/* Application mode note: offline-only / hybrid schemes get honest guidance */}
          {findScheme(query) && findScheme(query)!.mode !== 'online' && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 text-sm text-blue-800 dark:text-blue-200">
              {findScheme(query)!.mode === 'offline' ? t('apply_offline_note') : t('apply_hybrid_note')}
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-2">
            {[
              { id: 'explain', label: t('tab_explanation'), icon: FileText },
              { id: 'eli5', label: t('tab_story'), icon: BookOpen },
              { id: 'conditions', label: t('tab_hidden'), icon: AlertTriangle },
            ].map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id as any)
                    if (tab.id === 'eli5') loadEli5()
                    if (tab.id === 'conditions') loadConditions()
                  }}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* Explanation Tab */}
          {activeTab === 'explain' && (
            <div className="space-y-6">
              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <Info className="w-5 h-5 text-primary-600" />
                  {t('q_what_is')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-base">{result.what_is}</p>
                </CardContent>
              </Card>

              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-safron-600" />
                  {t('q_why')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{result.why_introduced}</p>
                </CardContent>
              </Card>

              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  {t('q_benefits')}
                </CardTitle>
                <CardContent>
                  <ul className="space-y-2">
                    {result.benefits.map((b, i) => (
                      <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                        <CheckCircle2 className="w-4 h-4 text-green-500 mt-1 shrink-0" />
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <Users className="w-5 h-5 text-blue-600" />
                  {t('q_eligible')}
                </CardTitle>
                <CardContent>
                  <ul className="space-y-2">
                    {result.eligibility.map((e, i) => (
                      <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                        <Users className="w-4 h-4 text-blue-400 mt-1 shrink-0" />
                        <span>{e}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <FileCheck className="w-5 h-5 text-purple-600" />
                  {t('q_documents')}
                </CardTitle>
                <CardContent>
                  <ul className="space-y-2">
                    {result.documents
                      .filter((d) => !/^\s*note\s*:/i.test(d))
                      .map((d, i) => (
                      <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                        <FileCheck className="w-4 h-4 text-purple-400 mt-1 shrink-0" />
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                  {result.documents.filter((d) => /^\s*note\s*:/i.test(d)).map((d, i) => (
                    <div key={`note-${i}`}
                      className="mt-4 flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2.5 text-sm text-red-600 dark:text-red-300">
                      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                      <span>{d.replace(/^\s*note\s*:\s*/i, '')}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <ClipboardList className="w-5 h-5 text-teal-600" />
                  {t('q_how_apply')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{result.how_to_apply}</p>
                </CardContent>
              </Card>

              {result.deadlines && (
                <Card>
                  <CardTitle className="flex items-center gap-2 mb-3">
                    <CalendarClock className="w-5 h-5 text-orange-600" />
                    {t('q_deadlines')}
                  </CardTitle>
                  <CardContent>
                    <p className="text-gray-700 dark:text-gray-300">{result.deadlines}</p>
                  </CardContent>
                </Card>
              )}

              {result.misunderstood_clauses.length > 0 && (
                <Card>
                  <CardTitle className="flex items-center gap-2 mb-3">
                    <HelpCircle className="w-5 h-5 text-red-600" />
                    {t('q_clauses')}
                  </CardTitle>
                  <CardContent>
                    <ul className="space-y-2">
                      {result.misunderstood_clauses.map((m, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300 bg-red-50 dark:bg-red-900/10 rounded-lg p-3">
                          <AlertTriangle className="w-4 h-4 text-red-500 mt-1 shrink-0" />
                          <span>{m}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 text-sm text-amber-800 dark:text-amber-200">
                {result.disclaimer}
              </div>
            </div>
          )}

          {/* ELI5 Tab */}
          {activeTab === 'eli5' && eli5 && (
            <div className="space-y-6 animate-fade-in">
              <Card className="bg-gradient-to-br from-green-50 to-teal-50 dark:from-gray-800 dark:to-gray-800 border-green-200 dark:border-green-800">
                <CardTitle className="flex items-center gap-2 mb-3 text-green-700 dark:text-green-400">
                  <BookOpen className="w-5 h-5" />
                  {t('story_title')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed italic">
                    &ldquo;{eli5.story}&rdquo;
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardTitle className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-5 h-5 text-yellow-600" />
                  {t('story_simple')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                    {eli5.simple_explanation}
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-blue-50 dark:bg-blue-900/10">
                <CardTitle className="flex items-center gap-2 mb-3 text-blue-700 dark:text-blue-400">
                  <Sparkles className="w-5 h-5" />
                  {t('story_example')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                    {eli5.everyday_example}
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
                <CardTitle className="flex items-center gap-2 mb-3 text-primary-700 dark:text-primary-400">
                  <CheckCircle2 className="w-5 h-5" />
                  {t('story_takeaway')}
                </CardTitle>
                <CardContent>
                  <p className="text-gray-800 dark:text-gray-200 text-xl font-semibold">
                    {eli5.key_takeaway}
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Conditions Tab */}
          {activeTab === 'conditions' && conditions && (
            <div className="space-y-6 animate-fade-in">
              {conditions.summary && (
                <Card className="bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
                  <CardTitle className="flex items-center gap-2 mb-3 text-amber-700 dark:text-amber-400">
                    <AlertTriangle className="w-5 h-5" />
                    {t('cond_summary')}
                  </CardTitle>
                  <CardContent>
                    <p className="text-gray-700 dark:text-gray-300">{conditions.summary}</p>
                  </CardContent>
                </Card>
              )}

              <div className="space-y-3">
                {conditions.conditions?.map((cond, i) => {
                  const severityColors = {
                    green: 'border-l-green-500 bg-green-50 dark:bg-green-900/10',
                    yellow: 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10',
                    red: 'border-l-red-500 bg-red-50 dark:bg-red-900/10',
                  }
                  const severityLabels = {
                    green: t('cond_general'),
                    yellow: t('cond_read'),
                    red: t('cond_alert'),
                  }
                  return (
                    <div
                      key={i}
                      className={`border-l-4 rounded-lg p-4 ${severityColors[cond.severity] || severityColors.green}`}
                    >
                      <div className="flex items-start gap-3">
                        <SeverityIcon severity={cond.severity} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant={cond.severity as any}>
                              {severityLabels[cond.severity]}
                            </Badge>
                          </div>
                          <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">{cond.text}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{cond.explanation}</p>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              {(!conditions.conditions || conditions.conditions.length === 0) && (
                <Card>
                  <CardContent>
                    <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                      {t('cond_none')}
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
