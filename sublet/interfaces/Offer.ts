// interfaces/Offers.ts

export interface OfferInterface {
  id?: number;
  phone_number: string;
  email?: string;
  message?: string;
  created_date?: Date;
  user?: string;
  sublet: number;
}
