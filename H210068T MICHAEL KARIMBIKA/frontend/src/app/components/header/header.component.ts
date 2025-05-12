import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { CartService } from '../../services/cart.service';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-header',
  imports: [RouterLink,RouterLinkActive,CommonModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css'
})
export class HeaderComponent {
  isLoggedIn = false
  showDropdown = false
  cartItemCount = 0
  isDarkMode = false
  userCountry: string | null = null
  userName: string | null = null

  constructor(
    private authService: AuthService,
    private cartService: CartService,
    private themeService: ThemeService,
  ) {
    this.authService.isLoggedIn$.subscribe((status) => {
      this.isLoggedIn = status
    })

    this.cartService.cartItems$.subscribe((items) => {
      this.cartItemCount = items.reduce((count, item) => count + item.quantity, 0)
    })

    this.themeService.darkMode$.subscribe((isDark) => {
      this.isDarkMode = isDark
    })

    this.authService.currentUser.subscribe((user) => {
      if (user) {
        this.userCountry = user.country || null
        this.userName = user.name
       // alert(this.userCountry)
      } else {
        this.userCountry = null
        this.userName = null
      }
    })
  }

  toggleDropdown() {
    this.showDropdown = !this.showDropdown
  }

  logout() {
    this.authService.logout()
    this.showDropdown = false
  }

  toggleDarkMode() {
    this.themeService.toggleDarkMode()
  }
}
