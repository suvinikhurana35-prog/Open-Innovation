'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { PersonalInfo } from './PersonalInfo'
import { LocationInfo } from './LocationInfo'
import { SocioEconomicInfo } from './SocioEconomicInfo'
import { ProfileCompletion } from './ProfileCompletion'
import { UserProfile, DEFAULT_PROFILE } from '@/lib/types/profile'
import { getUserProfile, updateUserProfile, getProfileCompletion } from '@/lib/services/profile'
import { CheckCircle, AlertCircle, Save } from 'lucide-react'

interface Props {
  t: (key: string) => string
}

type Toast = { type: 'success' | 'error'; message: string } | null

const REQUIRED: (keyof UserProfile)[] = ['phone']

function validate(profile: UserProfile): Partial<Record<keyof UserProfile, string>> {
  const errors: Partial<Record<keyof UserProfile, string>> = {}

  if (!profile.phone || !/^\d{10}$/.test(profile.phone)) {
    errors.phone = 'Enter a valid 10-digit phone number'
  }
  if (profile.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) {
    errors.email = 'Enter a valid email address'
  }
  if (profile.pincode && !/^\d{6}$/.test(profile.pincode)) {
    errors.pincode = 'Enter a valid 6-digit pincode'
  }

  return errors
}

export function ProfileForm({ t }: Props) {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE)
  const [completion, setCompletion] = useState(0)
  const [errors, setErrors] = useState<Partial<Record<keyof UserProfile, string>>>({})
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<Toast>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    getUserProfile().then(p => {
      setProfile(p)
      getProfileCompletion(p).then(setCompletion)
      setLoaded(true)
    })
  }, [])

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3000)
  }

  const handleChange = (updated: UserProfile) => {
    setProfile(updated)
    const v = validate(updated)
    setErrors(v)
    if (Object.keys(v).length === 0) {
      getProfileCompletion(updated).then(setCompletion)
    }
  }

  const handleSave = async () => {
    const v = validate(profile)
    setErrors(v)
    if (Object.keys(v).length > 0) {
      showToast('error', 'Please fix the errors before saving.')
      return
    }

    setSaving(true)
    try {
      await updateUserProfile(profile)
      await getProfileCompletion(profile).then(setCompletion)
      showToast('success', 'Profile saved successfully!')
    } catch {
      showToast('error', 'Failed to save profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (!loaded) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-20 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all animate-slide-up ${
            toast.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800'
              : 'bg-red-50 text-red-800 border border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800'
          }`}
        >
          {toast.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {toast.message}
        </div>
      )}

      <ProfileCompletion percentage={completion} />

      <PersonalInfo profile={profile} onChange={handleChange} errors={errors} t={t} />

      <hr className="border-gray-200 dark:border-gray-700" />

      <LocationInfo profile={profile} onChange={handleChange} errors={errors} t={t} />

      <hr className="border-gray-200 dark:border-gray-700" />

      <SocioEconomicInfo profile={profile} onChange={handleChange} errors={errors} t={t} />

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} disabled={saving} size="lg">
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Profile'}
        </Button>
      </div>
    </div>
  )
}
