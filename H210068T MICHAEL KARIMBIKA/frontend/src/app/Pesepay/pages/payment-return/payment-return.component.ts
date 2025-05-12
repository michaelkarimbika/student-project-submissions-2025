import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { PaymentService } from '../../../services/payment.service';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-payment-return',
  imports: [CommonModule,RouterModule],
  templateUrl: './payment-return.component.html',
  styleUrl: './payment-return.component.css'
})
export class PaymentReturnComponent  implements OnInit, OnDestroy {
  countdown = 10
  private countdownInterval: any
  orderId: string | null = null
  reason: string | null = null

  constructor(
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    // Get parameters from URL
    this.route.queryParams.subscribe((params) => {
      this.orderId = params["reference"] || params["orderId"] || null
      this.reason = params["reason"] || "The payment was cancelled."
    })

    this.startCountdown()
  }

  startCountdown(): void {
    this.countdownInterval = setInterval(() => {
      this.countdown--
      if (this.countdown <= 0) {
        clearInterval(this.countdownInterval)
        this.redirectToProducts()
      }
    }, 1000)
  }

  redirectToProducts(): void {
    this.router.navigate(["/products"])
  }

  redirectToCart(): void {
    this.router.navigate(["/cart"])
  }

  retryPayment(): void {
    if (this.orderId) {
      this.router.navigate(["/checkout"], {
        queryParams: { orderId: this.orderId, retry: true },
      })
    } else {
      this.redirectToCart()
    }
  }

  stopRedirect(): void {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval)
      this.countdown = 0
    }
  }

  ngOnDestroy(): void {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval)
    }
  }
}
