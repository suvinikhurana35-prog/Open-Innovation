export type Gender = 'male' | 'female' | 'other'

export type FamilyType = 'joint' | 'nuclear'

export type Category = 'general' | 'obc' | 'sc' | 'st' | 'other'

export type AreaType = 'rural' | 'urban'

export interface UserProfile {
  fullName: string
  phone: string
  email: string
  age: number | null
  gender: Gender | ''
  state: string
  district: string
  pincode: string
  areaType: AreaType | ''
  occupation: string
  annualIncome: number | null
  familyType: FamilyType | ''
  familyMembers: number | null
  category: Category | ''
  disability: boolean | null
  isStudent: boolean | null
  isFarmer: boolean | null
  photoUrl: string
}

export const DEFAULT_PROFILE: UserProfile = {
  fullName: '',
  phone: '',
  email: '',
  age: null,
  gender: '',
  state: '',
  district: '',
  pincode: '',
  areaType: '',
  occupation: '',
  annualIncome: null,
  familyType: '',
  familyMembers: null,
  category: '',
  disability: null,
  isStudent: null,
  isFarmer: null,
  photoUrl: '',
}

export const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
  'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry',
]

export const OCCUPATIONS = [
  'Government Employee', 'Private Employee', 'Self-Employed', 'Business Owner',
  'Daily Wage Worker', 'Homemaker', 'Retired', 'Unemployed', 'Other',
]

export const INCOME_SLABS = [
  { label: 'Up to ₹25,000', value: 25000 },
  { label: '₹25,001 - ₹50,000', value: 50000 },
  { label: '₹50,001 - ₹1,00,000', value: 100000 },
  { label: '₹1,00,001 - ₹2,50,000', value: 250000 },
  { label: '₹2,50,001 - ₹5,00,000', value: 500000 },
  { label: '₹5,00,001 - ₹10,00,000', value: 1000000 },
  { label: 'Above ₹10,00,000', value: 1000001 },
]
