'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardTitle } from '@/components/ui/Card'
import { compareSchemes, recommendForProfile } from '@/lib/api'
import { useLang } from '@/lib/i18n'
import { SCHEMES, schemeLabel, findScheme } from '@/lib/schemes'
import { trackView, trackCompare } from '@/lib/services/activity'
import { Loader2, ArrowRightLeft, CheckCircle2, Info, Sparkles } from 'lucide-react'

export default function ComparePage() {
  const { lang, t } = useLang()
  const [scheme1, setScheme1] = useState('')
  const [scheme2, setScheme2] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState<Record<string, string>>({})
  const [recLoading, setRecLoading] = useState(false)
  const [rec, setRec] = useState<any>(null)

  const handleRecommend = async () => {
    if (!result) return
    setRecLoading(true)
    setRec(null)
    try {
      const res = await recommendForProfile(result.scheme1_name || scheme1, result.scheme2_name || scheme2, profile, lang)
      setRec(res)
    } catch (err) {
      console.error('Recommend API error:', err)
      setRec({ reasoning: 'Could not generate a suggestion right now. Please try again.' })
    } finally {
      setRecLoading(false)
    }
  }
  const setP = (k: string, v: string) => setProfile(prev => ({ ...prev, [k]: v }))

  // Auto re-run the comparison when the LANGUAGE changes (only if a comparison
  // is already showing), so the user never has to click "Compare" again.
  const didMount = useRef(false)
  useEffect(() => {
    if (!didMount.current) { didMount.current = true; return }
    if (result && scheme1.trim() && scheme2.trim()) {
      handleCompare()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  const handleCompare = async () => {
    if (!scheme1.trim() || !scheme2.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    setRec(null)

    try {
      const res = await compareSchemes(scheme1.trim(), scheme2.trim(), lang)
      setResult(res)
      const s1 = findScheme(scheme1.trim())
      const s2 = findScheme(scheme2.trim())
      if (s1 && s2) {
        trackView(s1.id, schemeLabel(s1, 'en'), 'compare')
        trackView(s2.id, schemeLabel(s2, 'en'), 'compare')
        trackCompare(s1.id, s2.id, schemeLabel(s1, 'en'), schemeLabel(s2, 'en'), 'compare')
      }
    } catch (err) {
      console.error('Compare API error:', err)
      setError('Failed to compare schemes. Please try again.')
    } finally {
      setLoading(false)
    }
  }



  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">
          {t('compare_title')}
        </h1>
        <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">
          {t('compare_sub')}
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{t('compare_scheme1')}</label>
          <select
            value={scheme1}
            onChange={(e) => setScheme1(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-base focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">{t('choose_scheme')}</option>
            {SCHEMES.map((sc) => (
              <option key={sc.id} value={sc.id}>{schemeLabel(sc, lang)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{t('compare_scheme2')}</label>
          <select
            value={scheme2}
            onChange={(e) => setScheme2(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-base focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">{t('choose_scheme')}</option>
            {SCHEMES.map((sc) => (
              <option key={sc.id} value={sc.id}>{schemeLabel(sc, lang)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex justify-center mb-8">
        <Button onClick={handleCompare} disabled={loading || !scheme1.trim() || !scheme2.trim()} size="lg" className="px-10">
          {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <ArrowRightLeft className="w-5 h-5 mr-2" />}
          {loading ? t('compare_loading') : t('compare_btn')}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-16">
          <Loader2 className="w-10 h-10 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">Analyzing and comparing schemes...</p>
        </div>
      )}

      {result && !loading && (() => {
        // LANGUAGE FIX (compare): the backend keeps the scheme *names* in
        // English even when the comparison body is translated. Show the
        // localized label from our scheme list instead, so the titles change
        // with the selected language. Falls back to the backend name.
        const s1opt = findScheme(scheme1)
        const s2opt = findScheme(scheme2)
        const name1 = s1opt ? schemeLabel(s1opt, lang) : (result.scheme1_name || scheme1)
        const name2 = s2opt ? schemeLabel(s2opt, lang) : (result.scheme2_name || scheme2)
        return (
        <div className="space-y-6 animate-fade-in">
          {/* Header */}
          <div className="bg-gradient-to-r from-primary-50 to-safron-50 dark:from-gray-800 dark:to-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center gap-4 text-center">
              <div className="flex-1 font-bold text-lg text-gray-900 dark:text-gray-100">{name1}</div>
              <div className="flex items-center gap-2 text-primary-600">
                <ArrowRightLeft className="w-6 h-6" />
                <span className="text-sm font-medium">VS</span>
              </div>
              <div className="flex-1 font-bold text-lg text-gray-900 dark:text-gray-100">{name2}</div>
            </div>
          </div>

          {/* Comparison Table */}
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left px-4 py-3 font-semibold text-gray-700 dark:text-gray-300 w-1/4">Aspect</th>
                    <th className="text-left px-4 py-3 font-semibold text-primary-700 dark:text-primary-400 w-[37.5%]">{name1}</th>
                    <th className="text-left px-4 py-3 font-semibold text-safron-700 dark:text-safron-400 w-[37.5%]">{name2}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.comparisons?.map((comp: any, i: number) => (
                    <tr key={i} className="border-b border-gray-100 dark:border-gray-700 last:border-0">
                      <td className="px-4 py-4 text-sm font-medium text-gray-600 dark:text-gray-400 align-top">
                        <div className="flex items-center gap-2">
                          <Info className="w-4 h-4 text-primary-500 shrink-0" />
                          {comp.aspect}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-800 dark:text-gray-200">{comp.scheme1_value}</td>
                      <td className="px-4 py-4 text-sm text-gray-800 dark:text-gray-200">{comp.scheme2_value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Recommendation */}
          {result.recommendation && (
            <Card className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-gray-800 dark:to-gray-800 border-green-200 dark:border-green-800">
              <CardTitle className="flex items-center gap-2 mb-3 text-green-700 dark:text-green-400">
                <CheckCircle2 className="w-5 h-5" />
                Recommendation
              </CardTitle>
              <CardContent>
                <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">{result.recommendation}</p>
              </CardContent>
            </Card>
          )}

          {/* Profile-based recommendation */}
          <Card className="border-primary-200 dark:border-primary-800">
            <CardTitle className="flex items-center gap-2 mb-1 text-primary-700 dark:text-primary-400">
              <Sparkles className="w-5 h-5" />
              {t('rec_heading')}
            </CardTitle>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{t('rec_sub')}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                <Input placeholder={t('rec_age')} value={profile.age || ''} onChange={(e) => setP('age', e.target.value)} />
                <Input placeholder={t('rec_state')} value={profile.state || ''} onChange={(e) => setP('state', e.target.value)} />
                <Input placeholder={t('rec_gender')} value={profile.gender || ''} onChange={(e) => setP('gender', e.target.value)} />
                <Input placeholder={t('rec_occupation')} value={profile.occupation || ''} onChange={(e) => setP('occupation', e.target.value)} />
                <Input placeholder={t('rec_income')} value={profile.income || ''} onChange={(e) => setP('income', e.target.value)} />
                <Input placeholder={t('rec_category')} value={profile.category || ''} onChange={(e) => setP('category', e.target.value)} />
              </div>
              <Button onClick={handleRecommend} disabled={recLoading}>
                {recLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                {recLoading ? t('rec_loading') : t('rec_btn')}
              </Button>

              {rec && !recLoading && (
                <div className="mt-5 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                  <div className="flex items-center gap-2 mb-2 text-green-700 dark:text-green-400 font-semibold">
                    <CheckCircle2 className="w-5 h-5" />
                    {t('rec_result_title')}
                    {rec.recommended_scheme ? <span>: {rec.recommended_scheme}</span> : null}
                  </div>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{rec.reasoning}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {(!result.comparisons || result.comparisons.length === 0) && (
            <Card>
              <CardContent>
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                  Could not generate comparison. Please try different scheme names.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
        )
      })()}
    </div>
  )
}
