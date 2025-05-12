import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Product } from '../../models/product';
import { ProductService } from '../../services/product.service';
import { AuthService } from '../../services/auth.service';
import { CartService } from '../../services/cart.service';
import { ProductCardComponent } from '../product-card/product-card.component';

@Component({
  selector: 'app-recommended-products',
  imports: [RouterLink,CommonModule,ProductCardComponent],
  templateUrl: './recommended-products.component.html',
  styleUrl: './recommended-products.component.css'
})
export class RecommendedProductsComponent {

  products: Product[] = []
  loading = true
  isLoggedIn = false

  constructor(
    private productService: ProductService,
    private cartService: CartService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.authService.isLoggedIn$.subscribe((status) => {
      this.isLoggedIn = status

      if (status) {
        this.loadRecommendations()
      } else {
        this.loading = false
      }
    })
  }

  loadRecommendations(): void {
    this.productService.getRecommendedProducts().subscribe({
      next: (products) => {
        this.products = products
        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching recommended products:", error)
        this.loading = false
      },
    })
  }

  addToCart(product: Product): void {
    this.cartService.addToCart(product.id, 1)
  }
}


