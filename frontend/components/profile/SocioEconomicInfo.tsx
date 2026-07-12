'use client'

import { Input } from '@/components/ui/Input'
import {
  UserProfile, OCCUPATIONS, INCOME_SLABS, FamilyType, Category,
} from '@/lib/types/profile'

interface Props {
  profile: UserProfile
  onChange: (updated: UserProfile) => void
  errors: Partial<Record<keyof UserProfile, string>>
  t: (key: string) => string
}

const FAMILY_TYPES: { value: FamilyType; label: string }[] = [
  { value: 'joint', label: 'Joint' },
  { value: 'nuclear', label: 'Nuclear' },
]

const CATEGORIES: { value: Category; label: string }[] = [
  { value: 'general', label: 'General' },
  { value: 'obc', label: 'OBC' },
  { value: 'sc', label: 'SC' },
  { value: 'st', label: 'ST' },
  { value: 'other', label: 'Other' },
]

export function SocioEconomicInfo({ profile, onChange, errors, t }: Props) {
  const set = (field: keyof UserProfile, value: any) => onChange({ ...profile, [field]: value })

  const toggleBool = (field: keyof UserProfile, current: boolean | null) => {
    set(field, current === true ? false : current === false ? null : true)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t('profile_socioeconomic')}</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="occupation" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            {t('profile_occupation')}
          </label>
          <select
            id="occupation"
            value={profile.occupation}
            onChange={e => set('occupation', e.target.value)}
            className={`w-full px-4 py-3 rounded-xl border bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 transition-all text-base ${
              errors.occupation
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
            }`}
          >
            <option value="">Select occupation</option>
            {OCCUPATIONS.map(o => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
          {errors.occupation && <p className="mt-1 text-sm text-red-600">{errors.occupation}</p>}
        </div>

        <div>
          <label htmlFor="annualIncome" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            {t('profile_annual_income')}
          </label>
          <select
            id="annualIncome"
            value={profile.annualIncome ?? ''}
            onChange={e => set('annualIncome', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all text-base"
          >
            <option value="">Select income range</option>
            {INCOME_SLABS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            {t('profile_family_type')}
          </label>
          <div className="flex gap-3">
            {FAMILY_TYPES.map(ft => (
              <button
                key={ft.value}
                type="button"
                onClick={() => set('familyType', ft.value)}
                className={`px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                  profile.familyType === ft.value
                    ? 'bg-primary-50 border-primary-400 text-primary-700 dark:bg-primary-900/30 dark:border-primary-500 dark:text-primary-300'
                    : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 hover:border-gray-400'
                }`}
              >
                {ft.label}
              </button>
            ))}
          </div>
          {errors.familyType && <p className="mt-1 text-sm text-red-600">{errors.familyType}</p>}
        </div>

        <Input
          id="familyMembers"
          label={t('profile_family_members')}
          type="number"
          min={1}
          max={50}
          value={profile.familyMembers ?? ''}
          onChange={e => set('familyMembers', e.target.value ? Number(e.target.value) : null)}
          error={errors.familyMembers}
          placeholder="Number of family members"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          {t('profile_category')}
        </label>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(c => (
            <button
              key={c.value}
              type="button"
              onClick={() => set('category', c.value)}
              className={`px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                profile.category === c.value
                  ? 'bg-primary-50 border-primary-400 text-primary-700 dark:bg-primary-900/30 dark:border-primary-500 dark:text-primary-300'
                  : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 hover:border-gray-400'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
        {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category}</p>}
      </div>

      {/* Yes/No toggles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {([
          { field: 'disability' as const, label: t('profile_disability') },
          { field: 'isStudent' as const, label: t('profile_student') },
          { field: 'isFarmer' as const, label: t('profile_farmer') },
        ]).map(({ field, label }) => (
          <div key={field}>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{label}</label>
            <div className="flex gap-2">
              {(['Yes', 'No'] as const).map(answer => {
                const boolVal = answer === 'Yes'
                const isActive = profile[field] === boolVal
                return (
                  <button
                    key={answer}
                    type="button"
                    onClick={() => set(field, isActive ? null : boolVal)}
                    className={`px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-primary-50 border-primary-400 text-primary-700 dark:bg-primary-900/30 dark:border-primary-500 dark:text-primary-300'
                        : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 hover:border-gray-400'
                    }`}
                  >
                    {answer}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
