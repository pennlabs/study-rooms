// SubletListing.ts

export interface Sublet {
  id: number
  subletter: string // Name or ID of the subletter
  amenities: string[] // Array of amenities as strings
  title: string // Required, max length 255 characters
  address?: string | null // Optional, max length 255 characters
  beds?: number | null // Optional, integer
  baths?: string | null // Optional, can be a decimal, e.g., "1.5"
  description?: string | null // Optional description
  external_link?: string | null // Optional external URL, must match a valid URL pattern
  price: number // Required, integer value
  negotiable: boolean // Indicates if the price is negotiable
  start_date: string // Required, ISO 8601 date string
  end_date: string // Required, ISO 8601 date string
  expires_at: string // Required, ISO 8601 datetime string
}

// /interfaces/SubletResponse.ts
export interface SubletResponse {
  id: number
  subletter: string // Subletter’s name or ID
  amenities: string[] // List of amenities
  title: string
  address?: string | null // Optional or nullable
  beds?: number | null // Optional number of beds
  baths?: string | null // Optional, can be a decimal
  description?: string | null // Optional description
  external_link?: string | null // Optional external URL
  price: number
  negotiable: boolean // Is price negotiable?
  start_date: string // ISO date string
  end_date: string // ISO date string
  expires_at: string // ISO datetime string
}

// /interfaces/CreateSubletRequest.ts
export interface CreateSubletRequest {
  amenities: string[]
  title: string
  address?: string | null
  beds?: number | null
  baths?: string | null
  description?: string | null
  external_link?: string | null
  price: number
  negotiable: boolean
  start_date: string
  end_date: string
  expires_at: string
}

// /interfaces/UpdateSubletRequest.ts
export interface UpdateSubletRequest {
  amenities: string[]
  title: string
  address?: string | null
  beds?: number | null
  baths?: string | null
  description?: string | null
  external_link?: string | null
  price: number
  negotiable: boolean
  start_date: string
  end_date: string
  expires_at: string
}

// /interfaces/CreateSubletImageRequest.ts
export interface CreateSubletImageRequest {
  sublet: number // Sublet ID
  image: File | null // Binary image file
}
