'use client'

import { useState, useRef, useCallback } from 'react'
import { Input } from '@/components/ui/Input'
import { UserProfile, INDIAN_STATES, AreaType } from '@/lib/types/profile'
import { fetchLocationByPincode } from '@/lib/services/location'
import { Loader2 } from 'lucide-react'

interface Props {
  profile: UserProfile
  onChange: (updated: UserProfile) => void
  errors: Partial<Record<keyof UserProfile, string>>
  t: (key: string) => string
}

const AREA_TYPES: { value: AreaType; label: string }[] = [
  { value: 'rural', label: 'Rural' },
  { value: 'urban', label: 'Urban' },
]

const DEBOUNCE_MS = 500

export function LocationInfo({ profile, onChange, errors, t }: Props) {
  const [pincodeLoading, setPincodeLoading] = useState(false)
  const [pincodeError, setPincodeError] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastLookupRef = useRef('')

  const set = (field: keyof UserProfile, value: any) => {
    onChange({ ...profile, [field]: value })
  }

  const doLookup = useCallback(async (pincode: string) => {
    const clean = pincode.replace(/\D/g, '')
    if (clean.length !== 6) return

    setPincodeLoading(true)
    setPincodeError('')
    lastLookupRef.current = clean

    try {
      const result = await fetchLocationByPincode(clean)
      // Only apply results if the pincode hasn't changed since we started
      if (lastLookupRef.current !== clean) return

      const updated = { ...profile }
      let changed = false

      if (result.state && result.state !== updated.state) {
        updated.state = result.state
        changed = true
      }
      if (result.district && result.district !== updated.district) {
        updated.district = result.district
        changed = true
      }

      if (changed) onChange(updated)
    } catch (err: any) {
      if (lastLookupRef.current !== clean) return
      setPincodeError(err.message || 'Failed to look up PIN code')
    } finally {
      if (lastLookupRef.current === clean) {
        setPincodeLoading(false)
      }
    }
  }, [profile, onChange])

  const handlePincodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    // Only allow digits up to 6 characters
    const digits = raw.replace(/\D/g, '').slice(0, 6)
    set('pincode', digits)

    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (digits.length === 6) {
      debounceRef.current = setTimeout(() => doLookup(digits), DEBOUNCE_MS)
    } else {
      setPincodeError('')
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t('profile_location')}</h3>

      {/* Pincode — first field, auto-fills state and district */}
      <div className="relative">
        <label htmlFor="pincode" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          {t('profile_pincode')}
        </label>
        <div className="relative">
          <input
            id="pincode"
            type="text"
            inputMode="numeric"
            value={profile.pincode}
            onChange={handlePincodeChange}
            placeholder="Enter 6-digit pincode"
            maxLength={6}
            className={`w-full px-4 py-3 rounded-xl border bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:border-transparent transition-all duration-200 text-base pr-10 ${
              pincodeError || errors.pincode
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
            }`}
          />
          {pincodeLoading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
            </div>
          )}
        </div>
        {(pincodeError || errors.pincode) && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400">
            {pincodeError || errors.pincode}
          </p>
        )}
      </div>

      {/* State & District — auto-filled from pincode, still editable */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="state" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            {t('profile_state')}
          </label>
          <select
            id="state"
            value={profile.state}
            onChange={e => set('state', e.target.value)}
            className={`w-full px-4 py-3 rounded-xl border bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 transition-all text-base ${
              errors.state
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
            }`}
          >
            <option value="">Select state</option>
            {INDIAN_STATES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          {errors.state && <p className="mt-1 text-sm text-red-600">{errors.state}</p>}
        </div>

        <Input
          id="district"
          label={t('profile_district')}
          value={profile.district}
          onChange={e => set('district', e.target.value)}
          error={errors.district}
          placeholder="Enter your district"
        />
      </div>

      {/* Rural / Urban */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          {t('profile_area_type')}
        </label>
        <div className="flex gap-3">
          {AREA_TYPES.map(at => (
            <button
              key={at.value}
              type="button"
              onClick={() => set('areaType', at.value)}
              className={`px-4 py-2 rounded-xl border text-sm font-medium transition-all ${
                profile.areaType === at.value
                  ? 'bg-primary-50 border-primary-400 text-primary-700 dark:bg-primary-900/30 dark:border-primary-500 dark:text-primary-300'
                  : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 hover:border-gray-400'
              }`}
            >
              {at.label}
            </button>
          ))}
        </div>
        {errors.areaType && <p className="mt-1 text-sm text-red-600">{errors.areaType}</p>}
      </div>
    </div>
  )
}
