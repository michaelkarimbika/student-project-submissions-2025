import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { HomeComponent } from './pages/home/home.component';
import { ProductListComponent } from './pages/product-list/product-list.component';
import { ProductDetailComponent } from './pages/product-detail/product-detail.component';
import { CartComponent } from './pages/cart/cart.component';
import { CheckoutComponent } from './pages/checkout/checkout.component';
import { AuthGuard } from './guards/auth.guard';
import { PaymentReturnComponent } from './Pesepay/pages/payment-return/payment-return.component';
import { PaymentResultComponent } from './Pesepay/pages/payment-result/payment-result.component';

export const routes: Routes = [
    { 
        path: '',
         redirectTo: '', 
         pathMatch: 'full' 
    },
    { path: 'payment/result', component: PaymentResultComponent },
  { path: 'payment/return', component: PaymentReturnComponent },
     { path: "", 
        component: HomeComponent ,
        canActivate: [AuthGuard]
    },
    {
        path: "products",
         component: ProductListComponent,canActivate:[AuthGuard]
    },
    
      { path: "products/:id",
         component: ProductDetailComponent,
         canActivate: [AuthGuard] },
         { path: 'products/slug/:slug', component: ProductDetailComponent },
     { path: "cart",
         component: CartComponent, 
         canActivate: [AuthGuard]
         },
     { path: "checkout", 
        component: CheckoutComponent, 
        canActivate: [AuthGuard] 
    },
     { path: "login", 
        component: LoginComponent 
    },
     { path: "register", 
        component: RegisterComponent 
    }
     
    ];
   