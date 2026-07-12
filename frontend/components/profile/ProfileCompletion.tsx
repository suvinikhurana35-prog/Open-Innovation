'use client'

import { cn } from '@/lib/utils'

interface Props {
  percentage: number
  className?: string
}

export function ProfileCompletion({ percentage, className }: Props) {
  const color =
    percentage >= 80 ? 'bg-green-500' :
    percentage >= 50 ? 'bg-yellow-500' :
    percentage >= 25 ? 'bg-orange-500' :
    'bg-red-500'

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700 dark:text-gray-300">Profile Completion</span>
        <span className="font-semibold text-gray-900 dark:text-gray-100">{percentage}%</span>
      </div>
      <div className="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500 ease-out', color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        {percentage === 100
          ? 'Your profile is complete!'
          : percentage >= 80
            ? 'Almost there — fill the remaining fields for a complete profile.'
            : percentage >= 50
              ? 'Halfway done — keep adding details.'
              : percentage >= 25
                ? 'Good start — add more information to improve your profile.'
                : 'Start filling in your details to complete your profile.'}
      </p>
    </div>
  )
}
