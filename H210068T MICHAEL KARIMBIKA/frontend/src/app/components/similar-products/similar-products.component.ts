import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ProductService } from '../../services/product.service';
import { CartService } from '../../services/cart.service';
import { Product } from '../../models/product';
import { ProductCardComponent } from '../product-card/product-card.component';

@Component({
  selector: 'app-similar-products',
  imports: [CommonModule,ProductCardComponent],
  templateUrl: './similar-products.component.html',
  styleUrl: './similar-products.component.css'
})
export class SimilarProductsComponent implements OnInit {
addToCart(arg0: Product[]) {
throw new Error('Method not implemented.');
}
  @Input() productId!: number
  similarProducts: Product[] = []
  loading = true

  constructor(private productService: ProductService) {}

  ngOnInit(): void {
    this.loadSimilarProducts()
  }

  loadSimilarProducts(): void {
    this.productService.getSimilarProducts(this.productId).subscribe({
      next: (products) => {
        this.similarProducts = products
        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching similar products:", error)
        this.loading = false
      },
    })
  }
}

