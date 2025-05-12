import { Injectable } from "@angular/core"
import type { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpErrorResponse } from "@angular/common/http"
import { type Observable, throwError } from "rxjs"
import { catchError, finalize } from "rxjs/operators"
import { AuthService } from "../services/auth.service"
import { LoadingService } from "../services/loading.service"
import { Router } from "@angular/router"

interface User {
  id: number
  name: string
  email: string
  token: string
}
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(
    private authService: AuthService,
    private router: Router,
    private loadingService: LoadingService,
  ) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Show loading indicator
    this.loadingService.setLoading(true)

    // Get the auth token
    const token = this.authService.getToken()

    // Clone the request and add the authorization header if token exists
    if (token) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      })
    }

    // Handle the request and catch any errors
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          // Unauthorized - token might be expired
          this.authService.logout()
          this.router.navigate(["/login"], {
            queryParams: { returnUrl: this.router.url },
          })
        } else if (error.status === 403) {
          // Forbidden - user doesn't have permission
          this.router.navigate(["/forbidden"])
        } else if (error.status === 404) {
          // Not found
          this.router.navigate(["/not-found"])
        } else if (error.status >= 500) {
          // Server error
          console.error("Server error occurred:", error)
          // Optionally navigate to an error page
          // this.router.navigate(['/server-error']);
        }

        return throwError(() => error)
      }),
      finalize(() => {
        // Hide loading indicator when request is complete
        this.loadingService.setLoading(false)
      }),
    )
  }
}

