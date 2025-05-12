import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { OrderService } from '../../../services/order.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-payment-result',
  imports: [CommonModule,RouterModule],
  templateUrl: './payment-result.component.html',
  styleUrl: './payment-result.component.css'
})
export class PaymentResultComponent implements OnInit, OnDestroy {
    orderId: string | null = null
    orderDetails: any = null
    loading = true
    error = false
    errorMessage = ""
    countdown = 10
    private countdownInterval: any
  
    constructor(
      private route: ActivatedRoute,
      private router: Router,
      private orderService: OrderService,
    ) {}
  
    ngOnInit(): void {
      // Get order ID from query params
      this.route.queryParams.subscribe((params) => {
        console.log("Query params:", params)
        this.orderId = params["reference"] || params["orderId"] || null
  
        if (this.orderId) {
          this.loadOrderDetails()
        } else {
          this.error = true
          this.errorMessage = "No order reference found in the URL."
          this.loading = false
        }
      })
  
      // Start countdown for redirect
      this.startCountdown()
    }
  
    loadOrderDetails(): void {
      if (!this.orderId) {
        this.error = true
        this.errorMessage = "Order ID is missing."
        this.loading = false
        return
      }
  
      this.orderService.getOrderById(Number(this.orderId)).subscribe({
        next: (order) => {
          console.log("Order details:", order)
          this.orderDetails = order
          this.loading = false
        },
        error: (err) => {
          console.error("Error loading order details:", err)
          this.error = true
          this.errorMessage = "Could not load order details. Please contact customer support."
          this.loading = false
        },
      })
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
  
    redirectToOrderDetails(): void {
      if (this.orderId) {
        this.router.navigate(["/orders", this.orderId])
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
