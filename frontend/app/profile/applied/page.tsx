'use client'

import Link from 'next/link'
import { ClipboardCheck, ArrowLeft } from 'lucide-react'

export default function AppliedPoliciesPage() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mx-auto mb-4">
          <ClipboardCheck className="w-8 h-8 text-primary-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Applied Policies</h1>
        <p className="text-gray-500 dark:text-gray-400 mb-2">
          Track the government schemes and policies you&apos;ve applied for.
        </p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mb-6">This feature will be available soon.</p>
        <Link
          href="/profile"
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Profile
        </Link>
      </div>
    </div>
  )
}
