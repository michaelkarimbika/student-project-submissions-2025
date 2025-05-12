import { Component, OnInit } from '@angular/core';
import { CartService } from '../../services/cart.service';
import { ProductService } from '../../services/product.service';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Product } from '../../models/product';
import { CommonModule } from '@angular/common';
import { SimilarProductsComponent } from '../../components/similar-products/similar-products.component';
import { ProductReviewsComponent } from '../../components/product-reviews/product-reviews.component';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-product-detail',
  imports: [CommonModule,SimilarProductsComponent,ProductReviewsComponent],
  templateUrl: './product-detail.component.html',
  styleUrl: './product-detail.component.css'
})
export class ProductDetailComponent implements OnInit {
  productId = 0
  productSlug = ""
  product: Product | null = null
  loading = true
  quantity = 1
  activeTab = "description"

  constructor(
    private route: ActivatedRoute,
    private productService: ProductService,
    private cartService: CartService,
  ) {}

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      if (params["id"]) {
        this.productId = +params["id"]
        this.loadProductById()
      } else if (params["slug"]) {
        this.productSlug = params["slug"]
        this.loadProductBySlug()
      }
    })
  }

  loadProductById(): void {
    this.loading = true
    this.productService.getProductById(this.productId).subscribe({
      next: (product) => {
        this.product = product
        console.log("Product loaded by ID:", product)
        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching product details by ID:", error)
        this.loading = false
      },
    })
  }

  loadProductBySlug(): void {
    this.loading = true
    this.productService.getProductBySlug(this.productSlug).subscribe({
      next: (product) => {
        this.product = product
        this.productId = product.id // Set the ID for similar products
        console.log("Product loaded by slug:", product)
        this.loading = false
      },
      error: (error) => {
        console.error("Error fetching product details by slug:", error)
        this.loading = false
      },
    })
  }

  getImageUrl(path: string): string {
    // Handle relative URLs from the backend
    if (path && path.startsWith("/")) {
      return `${environment.apiUrl1}${path}`
    }
    return path || "/assets/placeholder.jpg"
  }

  increaseQuantity(): void {
    if (this.product && this.quantity < this.product.stock) {
      this.quantity++
    }
  }

  decreaseQuantity(): void {
    if (this.quantity > 1) {
      this.quantity--
    }
  }

  addToCart(): void {
    if (this.product) {
      this.cartService.addToCart(this.productId, this.quantity).subscribe({
        next: () => {
          console.log(`Added ${this.quantity} of ${this.product?.name} to cart`)
        },
        error: (error) => {
          console.error("Error adding to cart:", error)
        },
      })
    }
  }

  getPrice(price: string | number): number {
    return typeof price === "string" ? Number.parseFloat(price) : price
  }
}

