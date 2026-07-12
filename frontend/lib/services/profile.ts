import { UserProfile, DEFAULT_PROFILE } from '@/lib/types/profile'

const STORAGE_KEY = 'janniti_profile'

function isBrowser(): boolean {
  return typeof window !== 'undefined'
}

function getStored(): UserProfile {
  if (!isBrowser()) return { ...DEFAULT_PROFILE }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...DEFAULT_PROFILE, ...JSON.parse(raw) } : { ...DEFAULT_PROFILE }
  } catch {
    return { ...DEFAULT_PROFILE }
  }
}

function saveToStorage(profile: UserProfile): void {
  if (!isBrowser()) return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
  } catch (e) {
    console.error('Profile save failed:', e)
  }
}

/**
 * Fetches the user profile from the local store.
 * When a backend API is available, replace the implementation with:
 *   return apiFetch('/api/profile', { method: 'GET' })
 */
export async function getUserProfile(): Promise<UserProfile> {
  // TODO: Replace with backend API call when available
  // return apiFetch('/api/profile', { method: 'GET' })
  return getStored()
}

/**
 * Persists the user profile.
 * When a backend API is available, replace the implementation with:
 *   return apiFetch('/api/profile', { method: 'PUT', body: JSON.stringify(profile) })
 */
export async function updateUserProfile(profile: UserProfile): Promise<UserProfile> {
  // TODO: Replace with backend API call when available
  // return apiFetch('/api/profile', { method: 'PUT', body: JSON.stringify(profile) })
  saveToStorage(profile)
  return profile
}

const COMPLETION_FIELDS: (keyof UserProfile)[] = [
  'fullName', 'phone', 'email', 'age', 'gender',
  'state', 'district', 'pincode', 'areaType',
  'occupation', 'annualIncome', 'familyType', 'familyMembers',
  'category', 'disability', 'isStudent', 'isFarmer',
]

const WEIGHT = 100 / COMPLETION_FIELDS.length

function isFieldComplete(profile: UserProfile, field: keyof UserProfile): boolean {
  const value = profile[field]
  if (value === null || value === '') return false
  if (typeof value === 'number' && value <= 0) return false
  if (typeof value === 'string' && value.trim() === '') return false
  // boolean `false` is a valid explicit answer (e.g. "No" for isStudent/isFarmer/disability)
  return true
}

/**
 * Calculates the profile completion percentage (0–100).
 * When a backend API is available, replace with:
 *   return apiFetch('/api/profile/completion', { method: 'GET' })
 */
export async function getProfileCompletion(profile?: UserProfile): Promise<number> {
  const p = profile || await getUserProfile()
  const completed = COMPLETION_FIELDS.filter(f => isFieldComplete(p, f)).length
  return Math.round(completed * WEIGHT)
}
