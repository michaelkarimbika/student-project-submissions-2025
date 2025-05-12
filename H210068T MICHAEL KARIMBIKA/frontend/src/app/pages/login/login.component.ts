import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import {  Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-login',
  imports: [RouterLink,CommonModule,FormsModule,ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent implements OnInit {
  loginForm!: FormGroup
  loading = false
  submitted = false
  errorMessage = ""

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.loginForm = this.formBuilder.group({
      email: ["", [Validators.required, Validators.email]],
      password: ["", [Validators.required, Validators.minLength(6)]],
      rememberMe: [false],
    })
  }

  get f() {
    return this.loginForm.controls
  }

  onSubmit(): void {
    this.submitted = true
    this.errorMessage = ""

    if (this.loginForm.invalid) {
      return
    }

    this.loading = true

    this.authService.login(this.f["email"].value, this.f["password"].value).subscribe({
      next: () => {
        this.router.navigate(["/products"])
      },
      error: (error) => {
        this.errorMessage = error.error?.message || "Invalid email or password"
        this.loading = false
      },
    })
  }
}

