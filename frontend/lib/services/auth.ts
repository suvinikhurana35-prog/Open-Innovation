import { UserProfile, DEFAULT_PROFILE } from '@/lib/types/profile'

const AUTH_KEY = 'janniti_auth_users'
const SESSION_KEY = 'janniti_auth_session'
const PHOTOS_KEY = 'janniti_photos'

interface StoredUser {
  phone: string
  passwordHash: string
}

function isBrowser(): boolean {
  return typeof window !== 'undefined'
}

function getStoredUsers(): StoredUser[] {
  if (!isBrowser()) return []
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveUsers(users: StoredUser[]): void {
  if (!isBrowser()) return
  localStorage.setItem(AUTH_KEY, JSON.stringify(users))
}

async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('')
}

export interface AuthSession {
  phone: string
  loginTime: number
}

function getStoredSession(): AuthSession | null {
  if (!isBrowser()) return null
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveSession(session: AuthSession): void {
  if (!isBrowser()) return
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

function clearStoredSession(): void {
  if (!isBrowser()) return
  localStorage.removeItem(SESSION_KEY)
}

export function getProfileKey(phone: string): string {
  return `janniti_profile_${phone}`
}

function getStoredProfile(phone: string): UserProfile {
  if (!isBrowser()) return { ...DEFAULT_PROFILE }
  try {
    const raw = localStorage.getItem(getProfileKey(phone))
    return raw ? { ...DEFAULT_PROFILE, ...JSON.parse(raw) } : { ...DEFAULT_PROFILE }
  } catch {
    return { ...DEFAULT_PROFILE }
  }
}

function saveProfile(phone: string, profile: UserProfile): void {
  if (!isBrowser()) return
  localStorage.setItem(getProfileKey(phone), JSON.stringify(profile))
}

function getStoredPhotos(): Record<string, string> {
  if (!isBrowser()) return {}
  try {
    const raw = localStorage.getItem(PHOTOS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function savePhoto(phone: string, dataUrl: string): void {
  if (!isBrowser()) return
  const photos = getStoredPhotos()
  photos[phone] = dataUrl
  localStorage.setItem(PHOTOS_KEY, JSON.stringify(photos))
}

export function getPhoto(phone: string): string {
  const photos = getStoredPhotos()
  return photos[phone] || ''
}

export function deletePhoto(phone: string): void {
  const photos = getStoredPhotos()
  delete photos[phone]
  localStorage.setItem(PHOTOS_KEY, JSON.stringify(photos))
}

export async function isPhoneRegistered(phone: string): Promise<boolean> {
  return getStoredUsers().some(u => u.phone === phone)
}

export async function registerUser(
  phone: string,
  password: string,
  profile: UserProfile,
): Promise<void> {
  const users = getStoredUsers()
  if (users.some(u => u.phone === phone)) {
    throw new Error('This phone number is already registered')
  }
  const passwordHash = await hashPassword(password)
  users.push({ phone, passwordHash })
  saveUsers(users)
  saveProfile(phone, profile)
  saveSession({ phone, loginTime: Date.now() })
}

export async function loginUser(
  phone: string,
  password: string,
): Promise<UserProfile> {
  const users = getStoredUsers()
  const entry = users.find(u => u.phone === phone)
  if (!entry) {
    throw new Error('No account found with this phone number')
  }
  const passwordHash = await hashPassword(password)
  if (passwordHash !== entry.passwordHash) {
    throw new Error('Incorrect password')
  }
  saveSession({ phone, loginTime: Date.now() })
  const profile = getStoredProfile(phone)
  const photo = getPhoto(phone)
  if (photo) profile.photoUrl = photo
  return profile
}

export function logoutUser(): void {
  clearStoredSession()
}

export function getCurrentSession(): AuthSession | null {
  return getStoredSession()
}

export function getProfileForPhone(phone: string): UserProfile {
  const profile = getStoredProfile(phone)
  const photo = getPhoto(phone)
  if (photo) profile.photoUrl = photo
  return profile
}

export function updateProfileForPhone(phone: string, profile: UserProfile): void {
  saveProfile(phone, profile)
}

export function saveProfilePhoto(phone: string, dataUrl: string): void {
  savePhoto(phone, dataUrl)
}

export function ensurePhoneDirectory(phone: string): void {
}
