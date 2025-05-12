import { Injectable } from "@angular/core"
import { BehaviorSubject, type Observable, throwError } from "rxjs"
import { catchError, map } from "rxjs/operators"
import  { Router } from "@angular/router"
import { environment } from "../../environments/environment"
import { HttpClient } from "@angular/common/http"


interface User {
  id: number
  name: string
  email: string
  token: string
  country?: string
  city?: string
  state?: string
}


@Injectable({
  providedIn: "root",
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>
  public currentUser: Observable<User | null>
  private isLoggedInSubject = new BehaviorSubject<boolean>(false)
  public isLoggedIn$ = this.isLoggedInSubject.asObservable()

  constructor(
    private http: HttpClient,
    private router: Router,
  ) {
    const storedUser = localStorage.getItem("currentUser")
    this.currentUserSubject = new BehaviorSubject<User | null>(storedUser ? JSON.parse(storedUser) : null)
    this.currentUser = this.currentUserSubject.asObservable()
    this.isLoggedInSubject.next(!!storedUser)
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value
  }

  login(email: string, password: string): Observable<User> {
    return this.http.post<any>(`${environment.apiUrl}/auth/login/`, { email, password }).pipe(
      map((response) => {
        console.log("Login response:", response)
        // store user details and jwt token in local storage to keep user logged in between page refreshes
        const user: User = {
          id: response.user.id,
          name: response.user.username || response.user.email,
          email: response.user.email,
          token: response.token,
          country:response.user.country,
          city:response.user.city,
          state:response.user.state
        }
        localStorage.setItem("currentUser", JSON.stringify(user))
        this.currentUserSubject.next(user)
        this.isLoggedInSubject.next(true)
        return user
      }),
      catchError((error) => {
        console.error("Login error:", error)
        return throwError(() => error)
      }),
    )
  }

  register(userData: any): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/auth/register/`, userData).pipe(
      catchError((error) => {
        return throwError(() => error)
      }),
    )
  }

  logout(): void {
    // remove user from local storage to log user out
    localStorage.removeItem("currentUser")
    this.currentUserSubject.next(null)
    this.isLoggedInSubject.next(false)
    this.router.navigate(["/login"])
  }

  public getToken(): string | null {
    const currentUser = this.currentUserValue
    if (!currentUser) {
      console.log("No current user found")
      return null
    }

    console.log("Token available:", !!currentUser.token)
    return currentUser.token
  }
}

