import type { HttpInterceptorFn, HttpErrorResponse } from "@angular/common/http"
import { inject } from "@angular/core"
import { Router } from "@angular/router"
import { catchError, finalize, throwError } from "rxjs"
import { AuthService } from "../services/auth.service"
import { LoadingService } from "../services/loading.service"

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService)
  const router = inject(Router)
  const loadingService = inject(LoadingService)

  // Show loading indicator
  loadingService.setLoading(true)

  // Get the auth token
  const token = authService.getToken()

  // Clone the request and add the authorization header if token exists
  let authReq = req
  console.log(token)
  if (token) {
    console.log("Adding auth token to request:", req.url)
    authReq = req.clone({
    
      setHeaders: {
        Authorization: `Bearer ${token}`,
        
      },
    })
  } else {
    console.log("No auth token available for request:", req.url)
  }

  // Handle the request and catch any errors
  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      console.error("HTTP error:", error.status, error.message, req.url)

      if (error.status === 401) {
        // Unauthorized - token might be expired
        console.log("401 Unauthorized - redirecting to login")
        authService.logout()
        router.navigate(["/login"], {
          queryParams: { returnUrl: router.url },
        })
      } else if (error.status === 403) {
        // Forbidden - user doesn't have permission
        router.navigate(["/forbidden"])
      } else if (error.status === 404) {
        // Not found
        router.navigate(["/not-found"])
      } else if (error.status >= 500) {
        // Server error
        console.error("Server error occurred:", error)
      }

      return throwError(() => error)
    }),
    finalize(() => {
      // Hide loading indicator when request is complete
      loadingService.setLoading(false)
    }),
  )
}

