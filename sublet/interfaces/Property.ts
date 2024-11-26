// interfaces/Property.ts

export interface ImageInterface {
  id: number;
  image_url: string;
}

export interface PropertyInterface {
  id: number;
  subletter: string;
  amenities: string[];
  title: string;
  address?: string;
  beds?: number;
  baths?: number;
  description?: string;
  external_link: string;
  price: number;
  negotiable: boolean;
  start_date: string;
  end_date: string;
  expires_at?: string;
  images: ImageInterface[];
}
