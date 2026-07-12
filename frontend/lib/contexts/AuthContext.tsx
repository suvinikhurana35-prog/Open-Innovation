'use client'

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { UserProfile } from '@/lib/types/profile'
import {
  isPhoneRegistered,
  registerUser,
  loginUser,
  logoutUser,
  getCurrentSession,
  getProfileForPhone,
  updateProfileForPhone,
  saveProfilePhoto,
  getPhoto,
} from '@/lib/services/auth'

interface AuthContextValue {
  user: UserProfile | null
  isAuthenticated: boolean
  isLoading: boolean
  isRegistered: boolean
  checkRegistration: (phone: string) => Promise<boolean>
  register: (phone: string, password: string, profile: UserProfile) => Promise<void>
  login: (phone: string, password: string) => Promise<void>
  logout: () => void
  updateProfile: (profile: UserProfile) => void
  updatePhoto: (dataUrl: string) => void
}

const Ctx = createContext<AuthContextValue>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isRegistered: false,
  checkRegistration: async () => false,
  register: async () => {},
  login: async () => {},
  logout: () => {},
  updateProfile: () => {},
  updatePhoto: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const session = getCurrentSession()
    if (session) {
      const profile = getProfileForPhone(session.phone)
      setUser(profile)
    }
    setIsLoading(false)
  }, [])

  const checkRegistration = useCallback(async (phone: string): Promise<boolean> => {
    return isPhoneRegistered(phone)
  }, [])

  const register = useCallback(async (phone: string, password: string, profile: UserProfile) => {
    await registerUser(phone, password, profile)
    const photo = getPhoto(phone)
    if (photo) profile.photoUrl = photo
    setUser({ ...profile })
  }, [])

  const login = useCallback(async (phone: string, password: string) => {
    const profile = await loginUser(phone, password)
    setUser(profile)
  }, [])

  const logout = useCallback(() => {
    logoutUser()
    setUser(null)
  }, [])

  const updateProfile = useCallback((profile: UserProfile) => {
    if (!user?.phone) return
    updateProfileForPhone(user.phone, profile)
    setUser(profile)
  }, [user])

  const updatePhoto = useCallback((dataUrl: string) => {
    if (!user?.phone) return
    saveProfilePhoto(user.phone, dataUrl)
    setUser(prev => prev ? { ...prev, photoUrl: dataUrl } : null)
  }, [user])

  return (
    <Ctx.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        isRegistered: false,
        checkRegistration,
        register,
        login,
        logout,
        updateProfile,
        updatePhoto,
      }}
    >
      {children}
    </Ctx.Provider>
  )
}

export function useAuth() {
  return useContext(Ctx)
}
