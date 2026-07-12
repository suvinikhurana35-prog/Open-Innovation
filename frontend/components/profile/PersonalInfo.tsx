'use client'

import { Input } from '@/components/ui/Input'
import { UserProfile, Gender } from '@/lib/types/profile'

interface Props {
  profile: UserProfile
  onChange: (updated: UserProfile) => void
  errors: Partial<Record<keyof UserProfile, string>>
  t: (key: string) => string
}

const GENDERS: { value: Gender; label: string }[] = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
]

export function PersonalInfo({ profile, onChange, errors, t }: Props) {
  const set = (field: keyof UserProfile, value: any) => onChange({ ...profile, [field]: value })

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t('profile_personal_info')}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          id="fullName"
          label={t('profile_full_name')}
          value={profile.fullName}
          onChange={e => set('fullName', e.target.value)}
          error={errors.fullName}
          placeholder="Enter your full name"
        />
        <Input
          id="phone"
          label={`${t('profile_phone')} *`}
          type="tel"
          value={profile.phone}
          onChange={e => set('phone', e.target.value)}
          error={errors.phone}
          placeholder="Enter 10-digit phone number"
        />
        <Input
          id="email"
          label={t('profile_email')}
          type="email"
          value={profile.email}
          onChange={e => set('email', e.target.value)}
          error={errors.email}
          placeholder="email@example.com"
        />
        <Input
          id="age"
          label={t('profile_age')}
          type="number"
          min={1}
          max={150}
          value={profile.age ?? ''}
          onChange={e => set('age', e.target.value ? Number(e.target.value) : null)}
          error={errors.age}
          placeholder="Enter your age"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          {t('profile_gender')}
        </label>
        <div className="flex gap-3">
          {GENDERS.map(g => (
            <button
              key={g.value}
              type="button"
              onClick={() => set('gender', g.value)}
              className={`px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                profile.gender === g.value
                  ? 'bg-primary-50 border-primary-400 text-primary-700 dark:bg-primary-900/30 dark:border-primary-500 dark:text-primary-300'
                  : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 hover:border-gray-400'
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>
        {errors.gender && <p className="mt-1 text-sm text-red-600">{errors.gender}</p>}
      </div>
    </div>
  )
}
