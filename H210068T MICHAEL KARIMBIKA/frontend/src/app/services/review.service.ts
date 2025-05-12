import { Injectable } from "@angular/core"
import { type Observable, catchError, tap, throwError } from "rxjs"
import { environment } from "../../environments/environment"
import { HttpClient, HttpErrorResponse } from "@angular/common/http"
import { AuthService } from "./auth.service"
import { Review } from "../models/review"


interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

@Injectable({
  providedIn: "root",
})
export class ReviewService {
  private apiUrl = `${environment.apiUrl}`

 
  constructor(
    private http: HttpClient,
    private authService: AuthService,
  ) {}

  getProductReviews(productId: number): Observable<PaginatedResponse<Review>> {
    console.log(`Fetching reviews for product ${productId}`)

    return this.http
      .get<PaginatedResponse<Review>>(`${this.apiUrl}/reviews/`, {
        params: { product: productId.toString() },
      })
      .pipe(
        tap((response) => {
          console.log(`Received ${response.count} reviews for product ${productId}:`, response)
        }),
        catchError(this.handleError),
      )
  }

  addReview(productId: number, rating: number, comment: string): Observable<Review> {
    // Check if user is logged in
    if (!this.authService.currentUserValue) {
      return throwError(() => new Error("You must be logged in to add a review"))
    }

    console.log(`Adding review for product ${productId}: rating=${rating}, comment=${comment}`)

    return this.http
      .post<Review>(`${this.apiUrl}/reviews/`, {
        product: productId,
        rating,
        comment,
      })
      .pipe(
        tap((review) => console.log("Added review:", review)),
        catchError(this.handleError),
      )
  }

  markReviewHelpful(reviewId: number): Observable<Review> {
    // Check if user is logged in
    if (!this.authService.currentUserValue) {
      return throwError(() => new Error("You must be logged in to mark a review as helpful"))
    }

    return this.http.post<Review>(`${this.apiUrl}/reviews/${reviewId}/helpful/`, {}).pipe(
      tap((response) => console.log("Marked review as helpful:", response)),
      catchError(this.handleError),
    )
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = "An unknown error occurred"

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`
    } else {
      // Server-side error
      if (error.status === 401) {
        errorMessage = "You must be logged in to perform this action"
      } else if (error.error && error.error.detail) {
        errorMessage = error.error.detail
      } else {
        errorMessage = `Error Code: ${error.status}, Message: ${error.message}`
      }
    }

    console.error("Review service error:", errorMessage)
    return throwError(() => new Error(errorMessage))
  }
}
