'use client'

import { useState, useRef, useEffect } from 'react'
import { UserProfile } from '@/lib/types/profile'
import { PersonalInfo } from './PersonalInfo'
import { LocationInfo } from './LocationInfo'
import { SocioEconomicInfo } from './SocioEconomicInfo'
import { useI18n } from '@/lib/i18n'
import { X, Camera, User, Save, Trash2 } from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  profile: UserProfile
  onSave: (profile: UserProfile) => void
  onPhotoUpdate: (dataUrl: string) => void
}

export function EditProfileModal({ isOpen, onClose, profile, onSave, onPhotoUpdate }: Props) {
  const { t } = useI18n()
  const [edited, setEdited] = useState<UserProfile>({ ...profile })
  const [errors, setErrors] = useState<Partial<Record<keyof UserProfile, string>>>({})
  const [saving, setSaving] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const [photoPreview, setPhotoPreview] = useState(profile.photoUrl)

  useEffect(() => {
    setEdited({ ...profile })
    setPhotoPreview(profile.photoUrl)
  }, [profile, isOpen])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  const handlePhoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 2 * 1024 * 1024) return
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      setPhotoPreview(dataUrl)
      onPhotoUpdate(dataUrl)
    }
    reader.readAsDataURL(file)
  }

  const handleRemovePhoto = () => {
    setPhotoPreview('')
    onPhotoUpdate('')
  }

  const handleChange = (updated: UserProfile) => {
    setEdited(updated)
    const e: Partial<Record<keyof UserProfile, string>> = {}
    if (updated.phone && !/^\d{10}$/.test(updated.phone)) e.phone = 'Enter a valid 10-digit phone number'
    if (updated.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(updated.email)) e.email = 'Enter a valid email address'
    if (updated.pincode && !/^\d{6}$/.test(updated.pincode)) e.pincode = 'Enter a valid 6-digit pincode'
    setErrors(e)
  }

  const handleSave = () => {
    const e: Partial<Record<keyof UserProfile, string>> = {}
    if (edited.phone && !/^\d{10}$/.test(edited.phone)) e.phone = 'Enter a valid 10-digit phone number'
    if (edited.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(edited.email)) e.email = 'Enter a valid email address'
    if (edited.pincode && !/^\d{6}$/.test(edited.pincode)) e.pincode = 'Enter a valid 6-digit pincode'
    setErrors(e)
    if (Object.keys(e).length > 0) return

    setSaving(true)
    const final = { ...edited, photoUrl: photoPreview }
    onSave(final)
    setTimeout(() => { setSaving(false); onClose() }, 300)
  }

  if (!isOpen) return null

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto py-8 px-4">
        <div
          className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-xl my-auto"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Edit Profile</h2>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Photo */}
          <div className="px-6 pt-5 pb-2">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden border-2 border-gray-200 dark:border-gray-600">
                  {photoPreview ? (
                    <img src={photoPreview} alt="" className="w-full h-full object-cover" />
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
                <p className="text-xs text-gray-500 dark:text-gray-400">Max 2MB</p>
                {photoPreview && (
                  <button type="button" onClick={handleRemovePhoto} className="mt-1 flex items-center gap-1 text-xs text-red-600 hover:text-red-700 dark:text-red-400">
                    <Trash2 className="w-3 h-3" /> Remove photo
                  </button>
                )}
              </div>
              <input ref={fileRef} type="file" accept="image/*" onChange={handlePhoto} className="hidden" />
            </div>
          </div>

          {/* Form */}
          <div className="px-6 pb-4 space-y-6 overflow-y-auto max-h-[60vh]">
            <PersonalInfo profile={edited} onChange={handleChange} errors={errors} t={t} />
            <hr className="border-gray-200 dark:border-gray-700" />
            <LocationInfo profile={edited} onChange={handleChange} errors={errors} t={t} />
            <hr className="border-gray-200 dark:border-gray-700" />
            <SocioEconomicInfo profile={edited} onChange={handleChange} errors={errors} t={t} />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              className="px-4 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
