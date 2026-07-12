'use client'

import Link from 'next/link'
import { ArrowLeft, Activity } from 'lucide-react'
import { ActivitySection } from '@/components/profile/ActivitySection'

export default function ActivityPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-6">
        <Link
          href="/profile"
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Profile
        </Link>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <Activity className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Activity</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Your recent activity on this device</p>
          </div>
        </div>
      </div>

      <ActivitySection />
    </div>
  )
}
