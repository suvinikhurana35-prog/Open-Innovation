'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import * as ActivityService from '@/lib/services/activity'

export default function SettingsPage() {
  const [enabled, setEnabled] = useState(true)

  useEffect(() => {
    setEnabled(ActivityService.isEnabled())
  }, [])

  const handleToggle = () => {
    const next = !enabled
    setEnabled(next)
    ActivityService.setEnabled(next)
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <Link
        href="/profile"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Profile
      </Link>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Settings</h1>

      <div className="space-y-4">
        {/* Privacy toggle */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center shrink-0 mt-0.5">
                <Save className="w-4 h-4 text-primary-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Save my activity on this device</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Track recently viewed policies, searches, comparisons and chats to improve recommendations. Data stays on this device only.
                </p>
              </div>
            </div>
            <button
              onClick={handleToggle}
              className={`relative inline-flex h-6 w-11 items-center rounded-full shrink-0 transition-colors ${
                enabled ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
              }`}
              role="switch"
              aria-checked={enabled}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                enabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
          {!enabled && (
            <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                <Trash2 className="w-3.5 h-3.5" />
                Activity tracking is off. Existing data has been cleared.
              </div>
            </div>
          )}
        </div>

        {/* Future settings placeholder */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 opacity-50">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Notifications</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Coming soon</p>
        </div>
      </div>
    </div>
  )
}
