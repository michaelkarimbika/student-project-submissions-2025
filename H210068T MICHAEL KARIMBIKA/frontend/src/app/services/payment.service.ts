import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
export interface PaymentResponse {
  success: boolean
  paymentUrl?: string
  paymentReference?: string
  error?: string
}
interface PaymentStatusResponse {
  status: string;
  reference_number: string;
}
@Injectable({
  providedIn: 'root'
})
export class PaymentService {
  private apiUrl = `${environment.apiUrl}`

  constructor(private http: HttpClient) {}

  /**
   * Process payment for an order
   * @param orderId The ID of the order to process payment for
   */
  processPayment(orderId: number): Observable<PaymentResponse> {
    return this.http.post<any>(`${this.apiUrl}/payments/process/`, { orderId }).pipe(
      map((response) => {
        console.log("Payment process response:", response)
        return {
          success: true,
          paymentUrl: response.paymentUrl,
          paymentReference: response.paymentReference,
        }
      }),
      catchError((error) => {
        console.error("Payment process error:", error)
        return throwError(() => ({
          success: false,
          error: error.error?.message || "Failed to process payment",
        }))
      }),
    )
  }

  /**
   * Verify payment status
   * @param reference Payment reference to verify
   */
  verifyPayment(reference: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/payments/verify/${reference}/`).pipe(
      catchError((error) => {
        console.error("Payment verification error:", error)
        return throwError(() => error)
      }),
    )
  }

  /**
   * Get payment methods available for the user
   */
  getPaymentMethods(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/payments/methods/`).pipe(
      catchError((error) => {
        console.error("Get payment methods error:", error)
        return throwError(() => error)
      }),
    )
  }
}