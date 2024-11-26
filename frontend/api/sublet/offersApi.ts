// /api/offersApi.ts
import { CreateOfferRequest, OfferResponse } from '@/interfaces/sublet/Offer'
import { doApiRequest } from '@/utils/fetch'

const BASE_URL = 'api/sublet'

// Get all offers for a specific sublet
export const getOffers = async (subletId: string): Promise<OfferResponse[]> => {
  const response = await doApiRequest(`${BASE_URL}/listOffers/${subletId}`)
  if (!response.ok) {
    console.error('Failed to fetch offers')
    return []
  }
  return response.json()
}

// Create a new offer for a sublet
export const createOffer = async (
  subletId: string,
  data: CreateOfferRequest
): Promise<boolean> => {
  const response = await doApiRequest(`${BASE_URL}/createOffer/${subletId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    console.error('Failed to create offer')
    return false
  }
  return true
}

// Delete an offer by sublet ID (no request body required)
export const deleteOffer = async (subletId: string): Promise<boolean> => {
  const response = await doApiRequest(`${BASE_URL}/destroyOffer/${subletId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    console.error('Failed to delete offer')
    return false
  }
  return true
}
