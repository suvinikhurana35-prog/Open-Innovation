/**
 * Location service — PIN code lookup via the free India Post API.
 *
 * API docs: https://api.postalpincode.in/
 * Endpoint: https://api.postalpincode.in/pincode/{PINCODE}
 */

export interface PincodeResult {
  state: string
  district: string
}

interface PostOffice {
  Name: string
  District: string
  State: string
  Pincode: string
}

interface PostalResponse {
  Message: string
  Status: 'Success' | 'Error'
  PostOffice: PostOffice[] | null
}

/**
 * Fetches state and district for a given 6-digit Indian PIN code.
 * Throws a user-friendly error message on failure.
 */
export async function fetchLocationByPincode(pincode: string): Promise<PincodeResult> {
  const clean = pincode.replace(/\D/g, '')
  if (clean.length !== 6) {
    throw new Error('Please enter a valid 6-digit PIN code')
  }

  let data: PostalResponse[]
  try {
    const res = await fetch(`https://api.postalpincode.in/pincode/${clean}`)
    if (!res.ok) {
      throw new Error(`Server responded with ${res.status}`)
    }
    data = await res.json()
  } catch (err) {
    if (err instanceof TypeError && err.message === 'Failed to fetch') {
      throw new Error('Network error — please check your internet connection and try again')
    }
    throw new Error('Unable to verify PIN code. Please try again later.')
  }

  if (!Array.isArray(data) || data.length === 0) {
    throw new Error('No location data found for this PIN code')
  }

  const entry = data[0]
  if (entry.Status !== 'Success' || !entry.PostOffice || entry.PostOffice.length === 0) {
    throw new Error('PIN code not found in the postal database')
  }

  // All post offices under a PIN share the same district/state; use the first
  const po = entry.PostOffice[0]
  return {
    state: po.State,
    district: po.District,
  }
}
