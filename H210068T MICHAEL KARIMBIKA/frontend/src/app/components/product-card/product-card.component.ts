import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Product } from '../../models/product';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-product-card',
  imports: [CommonModule,RouterLink],
  templateUrl: './product-card.component.html',
  styleUrl: './product-card.component.css'
})
export class ProductCardComponent {
  @Input() product!: Product
  @Input() userCountry: string | null = null
  @Output() addToCartEvent = new EventEmitter<Product>()

  getImageUrl(path: string): string {
    // Handle relative URLs from the backend
    if (path && path.startsWith("/")) {
      return `${environment.imageUrl}${path}`
    }
    return path || "/assets/placeholder.jpeg"
  }

  getPrice(price: string | number): number {
    return typeof price === "string" ? Number.parseFloat(price) : price
  }

  addToCart(): void {
    this.addToCartEvent.emit(this.product)
  }

  // Check if a product is from the user's country
  get isLocalProduct(): boolean {
    if (!this.userCountry || !this.product.available_countries) return false
    return this.product.available_countries.includes(this.userCountry)
  }

  // Check if a product is in season
  get isInSeason(): boolean {
    if (!this.product.seasons || this.product.seasons.length === 0) return true // Always in season if no seasons specified

    // This is a simplified check - in a real app, you'd check against the current season
    // For now, we'll use a flag that would be set by the backend or parent component
    return this.product.is_in_season === true
  }

  // Get the first country code from available countries
  get countryCode(): string {
    if (!this.product.available_countries) return ""
    return this.product.available_countries.split(",")[0]
  }

  // Get the season name if available
  get seasonName(): string {
    if (!this.product.seasons || this.product.seasons.length === 0) return ""
    return this.product.seasons[0].name
  }
}
