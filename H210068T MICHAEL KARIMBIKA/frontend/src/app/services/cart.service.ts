import { Injectable } from "@angular/core"
import { Product } from "../models/product"
import { environment } from "../../environments/environment"
import { BehaviorSubject, Observable, tap } from "rxjs"
import { HttpClient } from "@angular/common/http"
import { AuthService } from "./auth.service"

export interface CartItem {
  id: number
  product: Product
  quantity: number
  added_at: string
}

export interface Cart {
  id: number
  items: CartItem[]
  total_price: number
  item_count: number
  created_at: string
  updated_at: string
}

@Injectable({
  providedIn: "root",
})
export class CartService {
  private apiUrl = `${environment.apiUrl}/cart`
  private cartItemsSubject = new BehaviorSubject<CartItem[]>([])
  cartItems$ = this.cartItemsSubject.asObservable()

  constructor(
    private http: HttpClient,
    private authService: AuthService,
  ) {
    this.loadCart()

    // Reload cart when user logs in or out
    this.authService.isLoggedIn$.subscribe((isLoggedIn) => {
      if (isLoggedIn) {
        this.loadCart()
      } else {
        this.cartItemsSubject.next([])
      }
    })
  }

  private loadCart(): void {
    if (this.authService.currentUserValue?.token) {
      this.getCart().subscribe({
        next: (cart) => {
          this.cartItemsSubject.next(cart.items)
        },
        error: (error) => {
          console.error("Error loading cart:", error)
        },
      })
    }
  }

  getCart(): Observable<Cart> {
    return this.http.get<Cart>(`${this.apiUrl}/`)
  }

  addToCart(productId: number, quantity: number): Observable<Cart> {
    return this.http.post<Cart>(`${this.apiUrl}/`, { product_id: productId, quantity }).pipe(
      tap({
        next: (cart) => {
          this.cartItemsSubject.next(cart.items)
        },
        error: (error) => {
          console.error("Error adding to cart:", error)
        },
      }),
    )
  }

  updateCartItem(itemId: number, quantity: number): Observable<Cart> {
    return this.http.put<Cart>(`${this.apiUrl}/${itemId}/`, { quantity }).pipe(
      tap({
        next: (cart) => {
          this.cartItemsSubject.next(cart.items)
        },
        error: (error) => {
          console.error("Error updating cart item:", error)
        },
      }),
    )
  }

  removeFromCart(itemId: number): Observable<Cart> {
    return this.http.delete<Cart>(`${this.apiUrl}/${itemId}/`).pipe(
      tap({
        next: (cart) => {
          this.cartItemsSubject.next(cart.items)
        },
        error: (error) => {
          console.error("Error removing from cart:", error)
        },
      }),
    )
  }
}

