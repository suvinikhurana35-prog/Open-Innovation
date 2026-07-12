'use client'

/**
 * IndianHero — single static hero banner (JanNiti v3.0).
 *
 * The old animated hero (Ashoka-Chakra spin, floating scheme icons, and the
 * poster carousel) has been removed. The hero is now ONE uploaded banner image
 * shown edge-to-edge at the top of the site, with the two primary call-to-action
 * buttons beneath it. No floating/animated images.
 *
 * The banner lives at /public/hero-banner.jpg. To swap it, replace that file.
 */

import Link from 'next/link'
import { useI18n } from '@/lib/i18n'

export default function IndianHero() {
  const { t } = useI18n()

  return (
    <section className="relative w-full" aria-label="JanNiti">
      {/* Full-width hero banner image */}
      <div className="w-full bg-white dark:bg-gray-900">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/hero-banner.jpg"
          alt="JanNiti — India's Schemes, Simplified for You. Your trusted guide to Government Schemes."
          className="block w-full h-auto"
          draggable={false}
        />
      </div>

      {/* Primary call-to-action buttons */}
      <div className="bg-white dark:bg-gray-900">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-4 px-4 py-6">
          <Link
            href="/explainer"
            className="rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-7 py-3.5 font-semibold text-white shadow-lg transition hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300"
          >
            🔍 {t('btn_search_scheme')}
          </Link>
          <Link
            href="/chatbot"
            className="rounded-xl border border-green-600/40 bg-green-50 px-7 py-3.5 font-semibold text-green-700 transition hover:bg-green-100 dark:border-green-500/40 dark:bg-green-500/10 dark:text-green-300 dark:hover:bg-green-500/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-400"
          >
            💬 {t('btn_ask_ai')}
          </Link>
        </div>
      </div>
    </section>
  )
}
