import { Component, OnInit } from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import {  Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-register',
  imports: [RouterLink,CommonModule,FormsModule,ReactiveFormsModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})
export class RegisterComponent implements OnInit {
  registerForm!: FormGroup
  loading = false
  submitted = false
  errorMessage = ""

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.registerForm = this.formBuilder.group(
      {
        email: ["", [Validators.required, Validators.email]],
        username: ["", Validators.required],
        first_name: [""],
        last_name: [""],
        country: [null],
        city: [null],
        state: [null],
        postal_code: [null],
        password: ["", [Validators.required, Validators.minLength(6)]],
        confirmPassword: ["", Validators.required],
        terms: [false, Validators.requiredTrue],
      },
      {
        validator: this.mustMatch("password", "confirmPassword"),
      },
    )
  }

  get f() {
    return this.registerForm.controls
  }

  mustMatch(controlName: string, matchingControlName: string) {
    return (formGroup: FormGroup) => {
      const control = formGroup.controls[controlName]
      const matchingControl = formGroup.controls[matchingControlName]

      if (matchingControl.errors && !matchingControl.errors["mustMatch"]) {
        return
      }

      if (control.value !== matchingControl.value) {
        matchingControl.setErrors({ mustMatch: true })
      } else {
        matchingControl.setErrors(null)
      }
    }
  }

  onSubmit(): void {
    this.submitted = true
    this.errorMessage = ""

    if (this.registerForm.invalid) {
      return
    }

    this.loading = true

    // Extract the required fields for the API
    const userData = {
      email: this.f["email"].value,
      username: this.f["username"].value,
      first_name: this.f["first_name"].value,
      last_name: this.f["last_name"].value,
      country: this.f["country"].value,
      city: this.f["city"].value,
      state: this.f["state"].value,
      postal_code: this.f["postal_code"].value,
      password: this.f["password"].value,
      password2: this.f["confirmPassword"].value,
     // terms: this.f["terms"].value,
    }

    this.authService.register(userData).subscribe({
      next: () => {
        this.router.navigate(["/login"], { queryParams: { registered: true } })
      },
      error: (error) => {
        this.errorMessage = error.error?.message || "Registration failed. Please try again."
        this.loading = false
      },
    })
  }
}

