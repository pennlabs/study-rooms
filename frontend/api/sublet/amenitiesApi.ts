// /api/amenitiesApi.ts

import { doApiRequest } from '@/utils/fetch'

const BASE_URL = 'api/sublet'

export const getAmenities = async (): Promise<string[]> => {
  const response = await doApiRequest(`${BASE_URL}/listAmenities`)
  if (!response.ok) {
    console.error('Failed to fetch amenities')
    return []
  }
  return response.json()
}
