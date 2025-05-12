// Updated Category model to match Django backend
export interface Category {
    id: number
    name: string
    slug: string
    description: string | null
    image: string | null
    parent: number | null
    children?: Category[]
  }
  
  