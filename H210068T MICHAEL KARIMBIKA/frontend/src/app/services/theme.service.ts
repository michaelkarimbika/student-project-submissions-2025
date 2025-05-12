import { Injectable } from "@angular/core"
import { BehaviorSubject } from "rxjs"

@Injectable({
  providedIn: "root",
})
export class ThemeService {
  private darkMode = new BehaviorSubject<boolean>(false)
  darkMode$ = this.darkMode.asObservable()

  constructor() {
    // Check for saved preference or system preference
    const savedTheme = localStorage.getItem("theme")
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches

    if (savedTheme === "dark" || (!savedTheme && systemPrefersDark)) {
      this.setDarkMode(true)
    }
  }

  setDarkMode(isDark: boolean): void {
    if (isDark) {
      document.documentElement.classList.add("dark")
      localStorage.setItem("theme", "dark")
    } else {
      document.documentElement.classList.remove("dark")
      localStorage.setItem("theme", "light")
    }
    this.darkMode.next(isDark)
  }

  toggleDarkMode(): void {
    this.setDarkMode(!this.darkMode.value)
  }
}

