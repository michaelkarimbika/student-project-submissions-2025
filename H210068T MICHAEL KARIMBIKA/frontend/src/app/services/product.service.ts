import { Injectable } from "@angular/core"
import { environment } from "../../environments/environment"
import { HttpClient, HttpErrorResponse, HttpParams } from "@angular/common/http"
import { catchError, map, Observable, of, tap } from "rxjs"
import { PaginatedResponse, Product } from "../models/product"
import { Category } from "../models/category"
import { AuthService } from "./auth.service"


@Injectable({
  providedIn: "root",
})
export class ProductService {
  private apiUrl = `${environment.apiUrl}`

  constructor(
    private http: HttpClient,
    private authService: AuthService,
  ) {}

  /**
   * Get the user's country from AuthService
   * @returns The user's country or null if not available
   */
  private getUserCountry(): string | null {
    const currentUser = this.authService.currentUserValue
    return currentUser?.country || null
  }

  /**
   * Add user's country to params if available
   * @param params Existing HttpParams or object
   * @returns HttpParams with user country added if available
   */
  private addUserCountryToParams(params?: any): HttpParams {
    let httpParams = new HttpParams()

    // Add existing params if provided
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key])
      })
    }

    // Add user country if available
    const userCountry = this.getUserCountry()
    if (userCountry) {
      httpParams = httpParams.set("user_country", userCountry)
    }

    return httpParams
  }

  getProducts(params?: any): Observable<PaginatedResponse<Product>> {
    const httpParams = this.addUserCountryToParams(params)
    return this.http.get<PaginatedResponse<Product>>(`${this.apiUrl}/products/`, { params: httpParams }).pipe(
      tap((response) => console.log("Products fetched with country prioritization:", this.getUserCountry())),
      catchError((error: HttpErrorResponse) => {
        console.error("Error fetching products:", error)
        throw error
      }),
    )
  }

  getProductById(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.apiUrl}/products/${id}/`).pipe(
      catchError((error: HttpErrorResponse) => {
        console.error(`Error fetching product with ID ${id}:`, error)
        throw error
      }),
    )
  }

  getProductBySlug(slug: string): Observable<Product> {
    return this.http.get<Product>(`${this.apiUrl}/products/${slug}/`).pipe(
      catchError((error: HttpErrorResponse) => {
        console.error(`Error fetching product with slug ${slug}:`, error)
        throw error
      }),
    )
  }

  getFeaturedProducts(): Observable<Product[]> {
    const params = this.addUserCountryToParams()
    return this.http.get<Product[]>(`${this.apiUrl}/products/featured/`, { params }).pipe(
      tap((products) => console.log("Featured products fetched with country prioritization:", this.getUserCountry())),
      catchError((error: HttpErrorResponse) => {
        console.error("Error fetching featured products:", error)
        throw error
      }),
    )
  }

  getRecommendedProducts(): Observable<Product[]> {
    const params = this.addUserCountryToParams()
    return this.http.get<Product[]>(`${this.apiUrl}/recommended-products/`, { params }).pipe(
      tap((products) =>
        console.log("Recommended products fetched with country prioritization:", this.getUserCountry()),
      ),
      catchError((error: HttpErrorResponse) => {
        console.error("Error fetching recommended products:", error)
        throw error
      }),
    )
  }

  getSimilarProducts(productId: number): Observable<Product[]> {
    const params = this.addUserCountryToParams()
    return this.http.get<Product[]>(`${this.apiUrl}/similar-products/${productId}/`, { params }).pipe(
      tap((products) =>
        console.log(
          `Similar products for product ${productId} fetched with country prioritization:`,
          this.getUserCountry(),
        ),
      ),
      catchError((error: HttpErrorResponse) => {
        console.error(`Error fetching similar products for product ${productId}:`, error)
        throw error
      }),
    )
  }

  searchProducts(query: string): Observable<PaginatedResponse<Product>> {
    let params = this.addUserCountryToParams()
    params = params.set("search", query)

    return this.http.get<PaginatedResponse<Product>>(`${this.apiUrl}/products/`, { params }).pipe(
      tap((response) =>
        console.log(`Search results for "${query}" with country prioritization:`, this.getUserCountry()),
      ),
      catchError((error: HttpErrorResponse) => {
        console.error(`Error searching products with query "${query}":`, error)
        throw error
      }),
    )
  }

  /**
   * Get products specifically from the user's country
   * @param params Additional query parameters
   * @returns Observable of paginated products from user's country
   */
  getLocalProducts(params?: any): Observable<PaginatedResponse<Product>> {
    const userCountry = this.getUserCountry()
    if (!userCountry) {
      console.warn("No user country available for local products")
      return this.getProducts(params)
    }

    let httpParams = this.addUserCountryToParams(params)
    httpParams = httpParams.set("country", userCountry)

    return this.http.get<PaginatedResponse<Product>>(`${this.apiUrl}/products/`, { params: httpParams }).pipe(
      tap((response) => console.log(`Local products from ${userCountry} fetched`)),
      catchError((error: HttpErrorResponse) => {
        console.error(`Error fetching local products from ${userCountry}:`, error)
        throw error
      }),
    )
  }
}