import { Component, OnInit } from '@angular/core';
import { CartItem } from '../../models/cart';
import {   Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CartService } from '../../services/cart.service';
import { OrderService } from '../../services/order.service';

@Component({
  selector: 'app-checkout',
  imports: [RouterLink,CommonModule,FormsModule],
  templateUrl: './checkout.component.html',
  styleUrl: './checkout.component.css'
})
export class CheckoutComponent implements OnInit {
  cartItems: CartItem[] = []
  loading = true
  processing = false
  subtotal = 0
  shipping = 5.99
  total = 0
  termsAccepted = false
  errorMessage = ""

  shippingInfo = {
    full_name: "",
    email: "",
    address: "",
    phone: "",
  }

  constructor(
    private cartService: CartService,
    private orderService: OrderService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.cartService.cartItems$.subscribe((items) => {
      this.cartItems = items
      this.calculateTotals()
      this.loading = false
    })
  }

 
  // Add a method to parse price
  getPrice(price: string | number): number {
    return typeof price === "string" ? Number.parseFloat(price) : price
  }

  // Update the calculateTotals method
  calculateTotals(): void {
    this.subtotal = this.cartItems.reduce((sum, item) => sum + this.getPrice(item.product.price) * item.quantity, 0)
    this.total = this.subtotal + this.shipping
  }



  isFormValid(): boolean {
    return (
      this.shippingInfo.full_name.trim() !== "" &&
      this.shippingInfo.email.trim() !== "" &&
      this.shippingInfo.address.trim() !== "" &&
      this.shippingInfo.phone.trim() !== "" &&
      this.termsAccepted
    )
  }

  placeOrder(): void {
    if (!this.isFormValid()) {
      this.errorMessage = "Please fill in all required fields and accept the terms."
      return
    }

    this.processing = true
    this.errorMessage = ""

    this.orderService
      .createOrder({
        
        ...this.shippingInfo,
        items: this.cartItems.map((item) => ({
          productId: item.product.id,
          quantity: item.quantity
        })),
      })
      .subscribe({
        next: (response) => {
          // Redirect to PesePay payment page
         // console.log("Order placed successfully:", response)
         
        window.location.href = response.payment_url
        },
        error: (error) => {
          alert("Error placing order: " + error.message)
          console.error("Error placing order:", error)
          this.errorMessage = "There was an error processing your order. Please try again."
          this.processing = false
        },
      })
  }
  
  
}

