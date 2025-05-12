import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Product } from '../../models/product';
import { ProductService } from '../../services/product.service';
import { CartService } from '../../services/cart.service';
import { ProductCardComponent } from '../product-card/product-card.component';

@Component({
  selector: 'app-featured-products',
  imports: [RouterLink,CommonModule,ProductCardComponent],
  templateUrl: './featured-products.component.html',
  styleUrl: './featured-products.component.css'
})
export class FeaturedProductsComponent {
  products: Product[] = []
  loading = true

  constructor(
    private productService: ProductService,
    private cartService: CartService,
  ) {}

  ngOnInit(): void {
    this.productService.getFeaturedProducts().subscribe({
      next: (products) => {
        this.products = products
        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching featured products:", error)
        this.loading = false
      },
    })
  }

  addToCart(product: Product): void {
    this.cartService.addToCart(product.id, 1)
  }
}
