import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Review } from '../../models/review';
import { ReviewService } from '../../services/review.service';
import { AuthService } from '../../services/auth.service';


interface PaginatedReviews {
  count: number
  next: string | null
  previous: string | null
  results: Review[]
}
@Component({
  selector: 'app-product-reviews',
  imports: [RouterLink,CommonModule,FormsModule,ReactiveFormsModule],
  templateUrl: './product-reviews.component.html',
  styleUrl: './product-reviews.component.css'
})
export class ProductReviewsComponent {
  @Input() productId = 0
  reviews: Review[] = []
  loading = true
  isLoggedIn = false
  newReview = ""
  newRating = 5
  errorMessage = ""
  successMessage = ""
  submitting = false
  currentUrl = ""
  totalReviews = 0

  constructor(
    private reviewService: ReviewService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    console.log("ProductReviewsComponent initialized with productId:", this.productId)

    // Get current URL for return after login
    this.currentUrl = window.location.pathname

    // Check if user is logged in
    this.authService.isLoggedIn$.subscribe((status) => {
      this.isLoggedIn = status
    })

    // Load reviews
    this.loadReviews()
  }

  loadReviews(): void {
    console.log("Loading reviews for product:", this.productId)
    this.loading = true

    this.reviewService.getProductReviews(this.productId).subscribe({
      next: (response: PaginatedReviews) => {
        console.log("Reviews loaded successfully:", response)

        // Extract the results array from the paginated response
        if (response && response.results) {
          this.reviews = response.results
          this.totalReviews = response.count
        } else {
          console.error("Unexpected response format:", response)
          this.reviews = []
          this.totalReviews = 0
        }

        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching reviews:", error)
        this.reviews = []
        this.loading = false
      },
      complete: () => {
        console.log("Review loading complete")
        this.loading = false
      },
    })
  }

  submitReview(): void {
    // Reset messages
    this.errorMessage = ""
    this.successMessage = ""

    // Validate input
    if (!this.newReview.trim()) {
      this.errorMessage = "Please enter a review comment"
      return
    }

    this.submitting = true

    this.reviewService.addReview(this.productId, this.newRating, this.newReview).subscribe({
      next: () => {
        this.successMessage = "Your review has been submitted successfully!"
        this.newReview = ""
        this.newRating = 5
        this.submitting = false

        // Reload reviews to show the new one
        this.loadReviews()
      },
      error: (error) => {
        this.errorMessage = error.message || "Error submitting review. Please try again."
        this.submitting = false
        console.error("Error submitting review:", error)
      },
    })
  }

  markHelpful(reviewId: number): void {
    if (!this.isLoggedIn) {
      this.errorMessage = "You must be logged in to mark a review as helpful"
      return
    }

    this.reviewService.markReviewHelpful(reviewId).subscribe({
      next: () => {
        // Update the review in the local array
        this.reviews = this.reviews.map((review) =>
          review.id === reviewId ? { ...review, helpfulCount: review.helpfulCount + 1 } : review,
        )
      },
      error: (error) => {
        this.errorMessage = error.message || "Error marking review as helpful"
        console.error("Error marking review as helpful:", error)
      },
    })
  }
}
