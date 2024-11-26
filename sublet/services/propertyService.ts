import { PropertyInterface } from '../interfaces/Property';
import { OfferInterface } from '@/interfaces/Offer';
import apiRequest from '../utils/fetch';

//listSublets
export const fetchProperties = async (): Promise<PropertyInterface[]> => {
  const properties: PropertyInterface[] = await apiRequest("properties", "GET");
  return properties;
};

//createSublet
export const createProperty = async (property: any): Promise<any> => {
  const newProperty: PropertyInterface = await apiRequest("properties", "POST", property);
  return newProperty
};

//retrieveSubletSerializerRead
export const fetchProperty = async (id: string): Promise<any> => {
  const property: PropertyInterface = await apiRequest(`properties/${id}`, "GET");
  return property
};

//updateSublet
export const updateProperty = async (id: string, property: any): Promise<any> => {
  const updatedProperty: PropertyInterface = await apiRequest(`properties/${id}`, "PUT", property);
  return updatedProperty
};

//partialUpdateSublet
export const partialUpdateProperty = async (id: string, property: any): Promise<any> => {
  const updatedProperty: PropertyInterface = await apiRequest(`properties/${id}`, "PATCH", property);
  return updatedProperty
};

//destroySublet
export const deleteProperty = async (id: string): Promise<void> => {
  await apiRequest(`properties/${id}`, "DELETE");
};

//listAmenitys
export const fetchAmenities = async (): Promise<string[]> => {
  const amenities: string[] = await apiRequest("amenities", "GET");
  return amenities;
};

//listSubletSerializerSimples
export const fetchFavorites = async (): Promise<PropertyInterface[]> => {
  const properties: PropertyInterface[] = await apiRequest("favorites", "GET");
  return properties;
};

//listOffers
export const fetchOffers = async (): Promise<OfferInterface[]> => {
  const properties: OfferInterface[] = await apiRequest("offers", "GET");
  return properties;
};

//listOffers (property)
export const fetchPropertyOffers = async (sublet_id: string): Promise<OfferInterface[]> => {
  const properties: OfferInterface[] = await apiRequest(`properties/${sublet_id}/offers`, "GET");
  return properties;
};

//createOffer
export const createOffer = async (sublet_id: string, offer: OfferInterface): Promise<any> => {
  const newOffer: OfferInterface = await apiRequest(`properties/${sublet_id}/offers`, "POST", offer);
  return newOffer
};

//destroyOffer
export const deleteOffer = async (sublet_id: string): Promise<void> => {
  await apiRequest(`properties/${sublet_id}/offers`, "DELETE");
};

//createSubletImage
export const createPropertyImage = async (sublet_id: string, image: File): Promise<any> => {
  // Create FormData object to hold the image data
  const formData = new FormData();
  formData.append('sublet', sublet_id); // The 'sublet' field must be an integer
  formData.append('images', image); // 'image' should be the File object

  return await apiRequest(`properties/${sublet_id}/images`, 'POST', formData)
};