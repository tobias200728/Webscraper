export interface Vehicle {
  id: string;
  source: string;
  title: string;
  brand: string | null;
  model: string | null;
  color: string | null;
  price: number | null;
  mileage: number | null;
  year: number | null;
  power_kw: number | null;
  fuel: string | null;
  location: string | null;
  image_urls: string[];
  listing_url: string;
  price_rating: "cheap" | "average" | "expensive" | null;
}

export interface SearchParams {
  brand: string;
  model: string;
  color?: string;
  max_mileage?: number;
  min_price?: number;
  max_price?: number;
  sources?: string[];
}

export type SortOption = "price_asc" | "price_desc" | "mileage_asc" | "year_desc" | "year_asc";
