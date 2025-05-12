import { Injectable } from "@angular/core"
import type { Observable } from "rxjs"
import { environment } from "../../environments/environment.development"
import { HttpClient } from "@angular/common/http"


interface OrderItem {
  productId: number
  quantity: number
}

interface OrderRequest {
  full_name: string
  email: string
  address: string
  phone: string
  items: OrderItem[]
}

interface OrderResponse {
  orderId: number
  payment_url: string
  reference_number: string
}

@Injectable({
  providedIn: "root",
})
export class OrderService {
  private apiUrl = `${environment.apiUrl}`

  constructor(private http: HttpClient) {}

  createOrder(orderData: OrderRequest): Observable<OrderResponse> {
    
    return this.http.post<OrderResponse>(`${this.apiUrl}/checkout/`, orderData)
  }

  getOrders(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/orders/`)
  }

  getOrderById(orderId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/orders/${orderId}/`)
  }
}

