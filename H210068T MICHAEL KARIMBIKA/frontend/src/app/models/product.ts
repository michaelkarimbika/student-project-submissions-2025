// Update the Product model to match the backend API response
export interface Product {
  id: number
  name: string
  slug: string
  description: string
  price: string | number
  discount_price: string | null | number
  category: number
  category_name: string
  stock: number
  featured: boolean
  created_at: string
  updated_at: string
  images: ProductImage[]
  primary_image: string
  rating: number
  review_count: number
  seasons: Season[]
  is_in_season: boolean
  is_location_specific: boolean
  available_countries: string
  available_regions: string | null
}

export interface ProductImage {
  id: number
  image: string
  alt_text: string
  is_primary: boolean
}

export interface Season {
  id: number
  name: string
  start_month: number
  end_month: number
  hemisphere: string
}

// Paginated response interface for handling API responses
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

