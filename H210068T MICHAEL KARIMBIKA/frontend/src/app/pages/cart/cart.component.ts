import { Component, OnInit } from '@angular/core';
import { CartItem } from '../../models/cart';
import { CartService } from '../../services/cart.service';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-cart',
  imports: [RouterLink,CommonModule],
  templateUrl: './cart.component.html',
  styleUrl: './cart.component.css'
})
export class CartComponent implements OnInit {
  cartItems: CartItem[] = []
  loading = true
  subtotal = 0
  shipping = 5.99
  total = 0

  constructor(private cartService: CartService) {}

  ngOnInit(): void {
    this.cartService.cartItems$.subscribe((items) => {
      this.cartItems = items
      this.calculateTotals()
      this.loading = false
    })
  }
  calculateTotals(): void {
    this.subtotal = this.cartItems.reduce((sum, item) => sum + this.getPrice(item.product.price) * item.quantity, 0)
    this.total = this.subtotal + this.shipping
  }
    // Add a method to parse price
    getPrice(price: string | number): number {
      return typeof price === "string" ? Number.parseFloat(price) : price
    }
  updateQuantity(item: CartItem, quantity: number): void {
    if (quantity < 1) return
    this.cartService.updateCartItem(item.id, quantity)
  }

  removeItem(item: CartItem): void {
    this.cartService.removeFromCart(item.id)
  }
}

