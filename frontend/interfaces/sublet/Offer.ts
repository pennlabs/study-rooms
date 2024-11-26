// /interfaces/CreateOfferRequest.ts
export interface CreateOfferRequest {
  phone_number: string // Required phone number
  email?: string | null // Optional email, max length 255 characters
  message: string // Message, max length 255 characters
  sublet: number // Sublet ID
}

// /interfaces/OfferResponse.ts
export interface OfferResponse {
  id: number // Offer ID
  phone_number: string // Phone number of the user making the offer
  email?: string | null // Optional email
  message: string // Message content
  created_date: string // ISO datetime string
  user: string // User ID or name
  sublet: number // Sublet ID associated with the offer
}
