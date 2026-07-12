'use client'

import Link from 'next/link'
import { Card, CardContent, CardTitle } from '@/components/ui/Card'
import { useI18n } from '@/lib/i18n'
import IndianHero from '@/components/ui/IndianHero'
import { ArrowRight, FileText, Search, Shield, MessageCircle, GitCompare, BarChart3, Volume2, BookOpen, HeartHandshake } from 'lucide-react'

function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(' ')
}

export default function Home() {
  const { t } = useI18n()

  const FEATURES = [
    { icon: FileText, title: t('feat_explainer_title'), desc: t('feat_explainer_desc'), href: '/explainer', color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30' },
    { icon: Search, title: t('feat_hidden_title'), desc: t('feat_hidden_desc'), href: '/explainer', color: 'text-red-600 bg-red-100 dark:bg-red-900/30' },
    { icon: MessageCircle, title: t('feat_chatbot_title'), desc: t('feat_chatbot_desc'), href: '/chatbot', color: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30' },
    { icon: GitCompare, title: t('feat_compare_title'), desc: t('feat_compare_desc'), href: '/compare', color: 'text-green-600 bg-green-100 dark:bg-green-900/30' },
    { icon: Volume2, title: t('feat_voice_title'), desc: t('feat_voice_desc'), href: '/explainer', color: 'text-teal-600 bg-teal-100 dark:bg-teal-900/30' },
  ]

  const STATS = [
    { number: t('stat_schemes_num'), label: t('stat_schemes_label'), desc: t('stat_schemes_desc') },
    { number: t('stat_langs_num'), label: t('stat_langs_label'), desc: t('stat_langs_desc') },
    { number: t('stat_reading_num'), label: t('stat_reading_label'), desc: t('stat_reading_desc') },
    { number: t('stat_transparent_num'), label: t('stat_transparent_label'), desc: t('stat_transparent_desc') },
  ]

  return (
    <div className="space-y-0">
      {/* Indic animated hero (Ashoka Chakra + your animated posters) */}
      <IndianHero />

      {/* Stats strip with tricolor divider */}
      <section className="bg-white dark:bg-gray-900 border-y border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="tricolor-bar mx-auto mb-8 w-40" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {STATS.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-safron-600 dark:text-safron-400">{stat.number}</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 mt-1">{stat.label}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{stat.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">{t('features_heading')}</h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">{t('features_sub')}</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature, i) => {
            const Icon = feature.icon
            return (
              <Link key={i} href={feature.href}>
                <Card interactive className="h-full">
                  <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center mb-4', feature.color)}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <CardTitle className="text-lg mb-2">{feature.title}</CardTitle>
                  <CardContent>
                    <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
                  </CardContent>
                  <div className="mt-4 flex items-center text-sm font-medium text-safron-600 dark:text-safron-400">
                    {t('try_now')} <ArrowRight className="w-4 h-4 ml-1" />
                  </div>
                </Card>
              </Link>
            )
          })}
        </div>
      </section>

      {/* Trust */}
      <section className="bg-gradient-to-r from-safron-50 via-white to-green-50 dark:from-gray-800 dark:via-gray-800 dark:to-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="max-w-3xl mx-auto text-center">
            <Shield className="w-12 h-12 text-safron-600 mx-auto mb-4" />
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">{t('trust_heading')}</h2>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{t('trust_sub')}</p>
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
              <div className="bg-white dark:bg-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-green-600 font-semibold mb-1">
                  <HeartHandshake className="w-5 h-5" />{t('trust_trustworthy_title')}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('trust_trustworthy_desc')}</p>
              </div>
              <div className="bg-white dark:bg-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-ashoka font-semibold mb-1">
                  <BookOpen className="w-5 h-5" />{t('trust_simple_title')}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('trust_simple_desc')}</p>
              </div>
              <div className="bg-white dark:bg-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-safron-600 font-semibold mb-1">
                  <Shield className="w-5 h-5" />{t('trust_nomis_title')}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('trust_nomis_desc')}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
        <div className="tricolor-bar w-full" style={{ borderRadius: 0 }} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <Shield className="w-4 h-4 text-safron-600" />
              {t('footer_tagline')}
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>{t('footer_disclaimer')}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
