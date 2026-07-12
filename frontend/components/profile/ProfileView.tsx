'use client'

import { useState, useEffect } from 'react'
import { UserProfile } from '@/lib/types/profile'
import { ProfileCompletion } from './ProfileCompletion'
import { EditProfileModal } from './EditProfileModal'
import { getProfileCompletion } from '@/lib/services/profile'
import {
  User, Mail, Phone, MapPin, Briefcase, Camera, Pencil, LogOut,
} from 'lucide-react'
import { useAuth } from '@/lib/contexts/AuthContext'

export function ProfileView() {
  const { user, updateProfile, updatePhoto, logout } = useAuth()
  const [completion, setCompletion] = useState(0)
  const [editOpen, setEditOpen] = useState(false)

  useEffect(() => {
    if (user) getProfileCompletion(user).then(setCompletion)
  }, [user])

  if (!user) return null

  const InfoRow = ({ icon: Icon, label, value }: { icon: any; label: string; value: string }) => (
    <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-900/50">
      <div className="w-9 h-9 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0">
        <Icon className="w-4 h-4 text-primary-600" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{value}</p>
      </div>
    </div>
  )

  return (
    <>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        {/* Profile Header Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          {/* Photo Banner */}
          <div className="h-32 bg-gradient-to-r from-primary-500 to-primary-700 relative">
            <div className="absolute -bottom-12 left-8">
              <div className="w-24 h-24 rounded-full border-4 border-white dark:border-gray-800 bg-gray-200 dark:bg-gray-700 flex items-center justify-center overflow-hidden shadow-md">
                {user.photoUrl ? (
                  <img src={user.photoUrl} alt="" className="w-full h-full object-cover" />
                ) : (
                  <User className="w-10 h-10 text-gray-400" />
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 px-6 pt-3">
            <button
              onClick={() => setEditOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-sm font-medium hover:bg-primary-100 dark:hover:bg-primary-900/50 transition-colors"
            >
              <Pencil className="w-3.5 h-3.5" />
              Edit Profile
            </button>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Logout
            </button>
          </div>

          {/* User Info Summary */}
          <div className="px-6 pb-2 mt-14">
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{user.fullName || 'User'}</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{user.occupation || 'No occupation set'}</p>
            <ProfileCompletion percentage={completion} />
          </div>

          {/* Details Grid */}
          <div className="px-6 pb-6 space-y-3 mt-4">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Contact</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <InfoRow icon={Phone} label="Phone" value={user.phone} />
              <InfoRow icon={Mail} label="Email" value={user.email || 'Not provided'} />
            </div>

            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mt-4">Location</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <InfoRow icon={MapPin} label="State" value={user.state || 'Not set'} />
              <InfoRow icon={MapPin} label="District" value={user.district || 'Not set'} />
            </div>

            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mt-4">Demographics</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <InfoRow icon={User} label="Age" value={user.age ? String(user.age) : 'Not set'} />
              <InfoRow icon={User} label="Gender" value={user.gender || 'Not set'} />
              <InfoRow icon={Briefcase} label="Occupation" value={user.occupation || 'Not set'} />
              <InfoRow icon={Briefcase} label="Annual Income" value={user.annualIncome ? `₹${user.annualIncome.toLocaleString()}` : 'Not set'} />
              <InfoRow icon={User} label="Category" value={user.category || 'Not set'} />
              <InfoRow icon={User} label="Family Type" value={user.familyType || 'Not set'} />
            </div>
          </div>
        </div>
      </div>

      <EditProfileModal
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        profile={user}
        onSave={updateProfile}
        onPhotoUpdate={updatePhoto}
      />
    </>
  )
}
