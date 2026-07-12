'use client'

import { useState, useRef, FormEvent, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/contexts/AuthContext'
import { useToast } from '@/lib/contexts/ToastContext'
import { useI18n } from '@/lib/i18n'
import { UserProfile, DEFAULT_PROFILE } from '@/lib/types/profile'
import { PersonalInfo } from '@/components/profile/PersonalInfo'
import { LocationInfo } from '@/components/profile/LocationInfo'
import { SocioEconomicInfo } from '@/components/profile/SocioEconomicInfo'
import {
  Shield, Lock, Camera, User, ArrowLeft, CheckCircle,
} from 'lucide-react'

const STEPS = ['personal', 'location', 'socioeconomic', 'review'] as const
type Step = (typeof STEPS)[number]

function RegisterForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { register, isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const { t } = useI18n()
  const [profile, setProfile] = useState<UserProfile>({ ...DEFAULT_PROFILE })
  const [errors, setErrors] = useState<Partial<Record<keyof UserProfile, string>>>({})
  const [password, setPassword] = useState('')
  const [step, setStep] = useState<Step>('personal')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const [photoPreview, setPhotoPreview] = useState('')

  const redirectTo = searchParams.get('redirect') || '/'

  if (isAuthenticated) {
    router.replace(redirectTo)
    return null
  }

  const handleProfileChange = (updated: UserProfile) => {
    setProfile(updated)
  }

  const handlePhoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 2 * 1024 * 1024) {
      setError('Photo must be under 2MB')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      setPhotoPreview(dataUrl)
      setProfile(prev => ({ ...prev, photoUrl: dataUrl }))
      setError('')
    }
    reader.readAsDataURL(file)
  }

  const removePhoto = () => {
    setPhotoPreview('')
    setProfile(prev => ({ ...prev, photoUrl: '' }))
  }

  const isStepValid = (): boolean => {
    const e: Partial<Record<keyof UserProfile, string>> = {}
    if (step === 'personal') {
      if (!profile.fullName.trim()) e.fullName = 'Name is required'
      if (!profile.phone || !/^\d{10}$/.test(profile.phone)) e.phone = 'Enter a valid 10-digit phone number'
      if (profile.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) e.email = 'Enter a valid email'
      if (!password || password.length < 4) setError('Password must be at least 4 characters')
      else setError('')
    }
    if (step === 'location') {
      if (profile.pincode && !/^\d{6}$/.test(profile.pincode)) e.pincode = 'Enter a valid 6-digit pincode'
    }
    setErrors(e)
    return Object.keys(e).length === 0 && (step !== 'personal' || password.length >= 4)
  }

  const nextStep = () => {
    if (!isStepValid()) return
    const idx = STEPS.indexOf(step)
    if (idx < STEPS.length - 1) setStep(STEPS[idx + 1])
  }

  const prevStep = () => {
    const idx = STEPS.indexOf(step)
    if (idx > 0) setStep(STEPS[idx - 1])
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    const digits = profile.phone.replace(/\D/g, '')
    if (digits.length !== 10) { setError('Enter a valid 10-digit phone number'); return }
    if (!password || password.length < 4) { setError('Password must be at least 4 characters'); return }

    setLoading(true)
    try {
      await register(digits, password, { ...profile, phone: digits })
      showToast('success', 'Registration Successful!')
      setTimeout(() => router.replace(redirectTo), 500)
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const renderPhotoUpload = () => (
    <div className="flex items-center gap-4">
      <div className="relative">
        <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden border-2 border-dashed border-gray-300 dark:border-gray-600">
          {photoPreview ? (
            <img src={photoPreview} alt="Preview" className="w-full h-full object-cover" />
          ) : (
            <User className="w-8 h-8 text-gray-400" />
          )}
        </div>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-primary-600 text-white flex items-center justify-center hover:bg-primary-700 transition-colors shadow-sm"
        >
          <Camera className="w-3.5 h-3.5" />
        </button>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Profile Photo</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">Optional. Max 2MB.</p>
        {photoPreview && (
          <button type="button" onClick={removePhoto} className="mt-1 text-xs text-red-600 hover:text-red-700 dark:text-red-400">
            Remove photo
          </button>
        )}
      </div>
      <input ref={fileRef} type="file" accept="image/*" onChange={handlePhoto} className="hidden" />
    </div>
  )

  const stepLabels: Record<Step, string> = {
    personal: t('reg_step_personal'),
    location: t('reg_step_location'),
    socioeconomic: t('reg_step_socioeconomic'),
    review: t('reg_step_review'),
  }

  const renderStepIndicator = () => (
    <div className="flex items-center gap-2 mb-8">
      {STEPS.map((s, i) => {
        const isCurrent = s === step
        const isDone = STEPS.indexOf(step) > i
        return (
          <div key={s} className="flex items-center gap-2 flex-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
              isDone
                ? 'bg-green-500 text-white'
                : isCurrent
                  ? 'bg-primary-600 text-white ring-2 ring-primary-200 dark:ring-primary-800'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
            }`}>
              {isDone ? <CheckCircle className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`text-xs font-medium hidden sm:block ${isCurrent ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'}`}>
              {stepLabels[s]}
            </span>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-px mx-1 ${isDone ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'}`} />
            )}
          </div>
        )
      })}
    </div>
  )

  return (
    <div className="min-h-[calc(100vh-4rem)] px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <button
          onClick={() => router.push('/')}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </button>

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm p-6 md:p-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Create Your Account</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">Fill in your details to get personalized scheme recommendations</p>
            </div>
          </div>

          {renderStepIndicator()}

          <form onSubmit={handleSubmit}>
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-400">
                {error}
              </div>
            )}

            {step === 'personal' && (
              <div className="space-y-6">
                {renderPhotoUpload()}
                <PersonalInfo profile={profile} onChange={handleProfileChange} errors={errors} t={t} />
                <div>
                  <label htmlFor="reg-password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      id="reg-password"
                      type="password"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder="Create a password (min 4 characters)"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all text-base"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 'location' && (
              <LocationInfo profile={profile} onChange={handleProfileChange} errors={errors} t={t} />
            )}

            {step === 'socioeconomic' && (
              <SocioEconomicInfo profile={profile} onChange={handleProfileChange} errors={errors} t={t} />
            )}

            {step === 'review' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Review Your Information</h3>
                <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
                  <div><span className="text-xs text-gray-500">Name</span><p className="text-sm font-medium">{profile.fullName}</p></div>
                  <div><span className="text-xs text-gray-500">Phone</span><p className="text-sm font-medium">{profile.phone}</p></div>
                  <div><span className="text-xs text-gray-500">Email</span><p className="text-sm font-medium">{profile.email || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Age</span><p className="text-sm font-medium">{profile.age ?? '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Gender</span><p className="text-sm font-medium">{profile.gender || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">State</span><p className="text-sm font-medium">{profile.state || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">District</span><p className="text-sm font-medium">{profile.district || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Pincode</span><p className="text-sm font-medium">{profile.pincode || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Area Type</span><p className="text-sm font-medium">{profile.areaType || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Occupation</span><p className="text-sm font-medium">{profile.occupation || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Family Income</span><p className="text-sm font-medium">{profile.annualIncome ? `₹${profile.annualIncome.toLocaleString()}` : '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Family Type</span><p className="text-sm font-medium">{profile.familyType || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Family Members</span><p className="text-sm font-medium">{profile.familyMembers ?? '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Category</span><p className="text-sm font-medium">{profile.category || '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Disability</span><p className="text-sm font-medium">{profile.disability === true ? 'Yes' : profile.disability === false ? 'No' : '-'}</p></div>
                  <div><span className="text-xs text-gray-500">Student</span><p className="text-sm font-medium">{profile.isStudent === true ? 'Yes' : profile.isStudent === false ? 'No' : '-'}</p></div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={prevStep}
                disabled={step === 'personal'}
                className="px-4 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>

              {step !== 'review' ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="px-6 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-all"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="px-8 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Creating Account...
                    </span>
                  ) : (
                    'Create Account'
                  )}
                </button>
              )}
            </div>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
            Already have an account?{' '}
            <Link href="/login" className="text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-[calc(100vh-4rem)] flex items-center justify-center"><div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" /></div>}>
      <RegisterForm />
    </Suspense>
  )
}
