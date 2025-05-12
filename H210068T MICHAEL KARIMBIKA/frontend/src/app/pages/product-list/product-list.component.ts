import { CommonModule } from "@angular/common"
import { Component, type OnInit } from "@angular/core"
import { FormsModule } from "@angular/forms"
import { RouterLink } from "@angular/router"
import { ProductCardComponent } from "../../components/product-card/product-card.component"
import { Product } from "../../models/product"
import { ProductService } from "../../services/product.service"
import { CartService } from "../../services/cart.service"
import { AuthService } from "../../services/auth.service"

interface Season {
  id: number
  name: string
  start_month: number
  end_month: number
  hemisphere: string
}

interface Country {
  code: string
  name: string
}

@Component({
  selector: "app-product-list",
  standalone: true,
  imports: [CommonModule, FormsModule, ProductCardComponent],
  templateUrl: "./product-list.component.html",
  styleUrls: ["./product-list.component.css"],
})
export class ProductListComponent implements OnInit {
  products: Product[] = []
  filteredProducts: Product[] = []
  loading = true
  totalCount = 0

  // Filters
  searchQuery = ""
  selectedCategories: string[] = []
  priceRange = { min: 0, max: 1000 }
  selectedRating: number | null = null
  sortOption = "featured"
  selectedCountry: string | null = null
  selectedSeason: number | null = null
  showLocalOnly = false

  // User's country
  userCountry: string | null = null

  // Pagination
  currentPage = 1
  itemsPerPage = 9
  totalPages = 1

  // Categories
  categories = [
    { id: 1, slug: "electronics", name: "Electronics" },
    { id: 2, slug: "clothing", name: "Clothing" },
    { id: 3, slug: "home-kitchen", name: "Home & Kitchen" },
    { id: 4, slug: "beauty-personal-care", name: "Beauty & Personal Care" },
    { id: 5, slug: "sports-outdoors", name: "Sports & Outdoors" },
  ]

  // Countries
  countries: Country[] = [
    { code: "US", name: "United States" },
    { code: "GB", name: "United Kingdom" },
    { code: "CA", name: "Canada" },
    { code: "AU", name: "Australia" },
    { code: "DE", name: "Germany" },
    { code: "FR", name: "France" },
    { code: "JP", name: "Japan" },
    { code: "CN", name: "China" },
    { code: "IN", name: "India" },
    { code: "BR", name: "Brazil" },
    { code: "ZA", name: "South Africa" },
    { code: "NG", name: "Nigeria" },
    { code: "KE", name: "Kenya" },
    { code: "ZW", name: "Zimbabwe" },
  ]

  // Seasons
  seasons: Season[] = [
    { id: 1, name: "Spring", start_month: 3, end_month: 5, hemisphere: "N" },
    { id: 2, name: "Summer", start_month: 6, end_month: 8, hemisphere: "N" },
    { id: 3, name: "Fall", start_month: 9, end_month: 11, hemisphere: "N" },
    { id: 4, name: "Winter", start_month: 12, end_month: 2, hemisphere: "N" },
    { id: 5, name: "Spring", start_month: 9, end_month: 11, hemisphere: "S" },
    { id: 6, name: "Summer", start_month: 12, end_month: 2, hemisphere: "S" },
    { id: 7, name: "Fall", start_month: 3, end_month: 5, hemisphere: "S" },
    { id: 8, name: "Winter", start_month: 6, end_month: 8, hemisphere: "S" },
  ]

  // Current season
  currentSeason: Season | null = null
  currentHemisphere = "N" // Default to Northern hemisphere

  // Make Math available to the template
  Math = Math

  constructor(
    private productService: ProductService,
    private cartService: CartService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    // Get user's country if logged in
    if (this.authService.currentUserValue?.country) {
      this.userCountry = this.authService.currentUserValue.country
      console.log("User country:", this.userCountry)
    }

    // Determine current season based on month
    this.determineCurrentSeason()

    this.loadProducts()
  }

  determineCurrentSeason(): void {
    const currentMonth = new Date().getMonth() + 1 // JavaScript months are 0-indexed

    // Determine hemisphere based on user country if available
    if (this.userCountry) {
      const northernCountries = ["US", "CA", "GB", "DE", "FR", "IT", "ES", "JP", "CN"]
      const southernCountries = ["AU", "NZ", "AR", "BR", "CL", "ZA","ZW"]

      if (southernCountries.includes(this.userCountry)) {
        this.currentHemisphere = "S"
      } else {
        this.currentHemisphere = "S"
      }
    }

    // Find current season based on month and hemisphere
    this.currentSeason =
      this.seasons.find(
        (season) =>
          season.hemisphere === this.currentHemisphere &&
          ((season.start_month <= season.end_month &&
            currentMonth >= season.start_month &&
            currentMonth <= season.end_month) ||
            (season.start_month > season.end_month &&
              (currentMonth >= season.start_month || currentMonth <= season.end_month))),
      ) || null

    console.log("Current season:", this.currentSeason?.name, "Hemisphere:", this.currentHemisphere)
  }

  loadProducts(): void {
    this.loading = true

    // Create params object for API request
    const params: any = {
      page: this.currentPage,
      page_size: this.itemsPerPage,
    }

    // Add filters to params if they exist
    if (this.searchQuery) {
      params.search = this.searchQuery
    }

    if (this.selectedCategories.length > 0) {
      params.category = this.selectedCategories.join(",")
    }

    if (this.priceRange.min > 0) {
      params.min_price = this.priceRange.min
    }

    if (this.priceRange.max < 1000) {
      params.max_price = this.priceRange.max
    }

    if (this.selectedRating) {
      params.min_rating = this.selectedRating
    }

    // Add country filter
    if (this.selectedCountry) {
      params.country = this.selectedCountry
    } else if (this.showLocalOnly && this.userCountry) {
      params.country = this.userCountry
    }

    // Add season filter
    if (this.selectedSeason !== null) {
      const season = this.seasons.find((s) => s.id === this.selectedSeason)
      if (season) {
        params.season = season.id
        params.hemisphere = season.hemisphere
      }
    }

    // Add sorting
    if (this.sortOption) {
      switch (this.sortOption) {
        case "price-low":
          params.ordering = "price"
          break
        case "price-high":
          params.ordering = "-price"
          break
        case "rating":
          params.ordering = "-rating"
          break
        case "newest":
          params.ordering = "-created_at"
          break
        case "featured":
          params.featured = true
          break
      }
    }

    // Always send user country for prioritization if available
    if (this.userCountry) {
      params.user_country = this.userCountry
    }

    this.productService.getProducts(params).subscribe({
      next: (response) => {
        // Process products to add is_in_season flag
        this.products = response.results.map((product) => {
          return {
            ...product,
            is_in_season: this.isProductInSeason(product),
          }
        })

        this.filteredProducts = this.products
        this.totalCount = response.count
        this.totalPages = Math.ceil(response.count / this.itemsPerPage)
        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching products:", error)
        this.loading = false
      },
    })
  }

  onSearch(): void {
    this.currentPage = 1
    this.loadProducts()
  }

  onCategoryChange(categorySlug: string, event: any): void {
    const checked = event.target.checked

    if (checked) {
      this.selectedCategories.push(categorySlug)
    } else {
      this.selectedCategories = this.selectedCategories.filter((slug) => slug !== categorySlug)
    }

    this.currentPage = 1
    this.loadProducts()
  }

  onPriceChange(): void {
    this.currentPage = 1
    this.loadProducts()
  }

  onRatingChange(): void {
    this.currentPage = 1
    this.loadProducts()
  }

  onCountryChange(): void {
    // If a specific country is selected, disable "local only" option
    if (this.selectedCountry) {
      this.showLocalOnly = false
    }
    this.currentPage = 1
    this.loadProducts()
  }

  onSeasonChange(): void {
    this.currentPage = 1
    this.loadProducts()
  }

  onLocalOnlyChange(): void {
    // If "local only" is checked, clear selected country
    if (this.showLocalOnly) {
      this.selectedCountry = null
    }
    this.currentPage = 1
    this.loadProducts()
  }

  loadCurrentSeasonProducts(): void {
    if (this.currentSeason) {
      this.selectedSeason = this.currentSeason.id
      this.currentPage = 1
      this.loadProducts()
    }
  }

  onSortChange(): void {
    this.loadProducts()
  }

  clearFilters(): void {
    this.searchQuery = ""
    this.selectedCategories = []
    this.priceRange = { min: 0, max: 1000 }
    this.selectedRating = null
    this.sortOption = "featured"
    this.selectedCountry = null
    this.selectedSeason = null
    this.showLocalOnly = false
    this.currentPage = 1
    this.loadProducts()
  }

  goToPage(page: string | number): void {
    if (typeof page === "number" && page >= 1 && page <= this.totalPages) {
      this.currentPage = page
      this.loadProducts()
      // Scroll to top of products
      window.scrollTo({ top: 0, behavior: "smooth" })
    }
  }

  getPageNumbers(): (number | string)[] {
    const pages: (number | string)[] = []

    if (this.totalPages <= 7) {
      for (let i = 1; i <= this.totalPages; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1)

      if (this.currentPage > 3) {
        pages.push("...")
      }

      const start = Math.max(2, this.currentPage - 1)
      const end = Math.min(this.totalPages - 1, this.currentPage + 1)

      for (let i = start; i <= end; i++) {
        pages.push(i)
      }

      if (this.currentPage < this.totalPages - 2) {
        pages.push("...")
      }

      pages.push(this.totalPages)
    }

    return pages
  }

  handleAddToCart(product: Product): void {
    this.cartService.addToCart(product.id, 1).subscribe({
      next: () => {
        console.log(`Added ${product.name} to cart`)
      },
      error: (error) => {
        console.error("Error adding to cart:", error)
      },
    })
  }

  // Helper method to get country name from code
  getCountryName(countryCode: string): string {
    const country = this.countries.find((c) => c.code === countryCode)
    return country ? country.name : countryCode
  }

  // Check if a product is from the user's country
  isLocalProduct(product: Product): boolean {
    if (!this.userCountry || !product.available_countries) return false
    return product.available_countries.includes(this.userCountry)
  }

  // Check if a product is in season
  isProductInSeason(product: Product): boolean {
    if (!product.seasons || product.seasons.length === 0) return true // Always in season if no seasons specified
    if (!this.currentSeason) return true

    return product.seasons.some(
      (season) => season.id === this.currentSeason?.id || season.hemisphere === "B", // Both hemispheres
    )
  }
}
