export interface Review {
  id: number
  product: number
  user: number
  user_name: string
  userAvatar?: string
  rating: number
  comment: string
  created_at: string
  updated_at: string
  helpfulCount: number
  datePosted: string
}
