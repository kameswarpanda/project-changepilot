import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-auth-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth-page.component.html',
  styleUrls: ['./auth-page.component.css']
})
export class AuthPageComponent {
  authMode: 'signin' | 'signup' = 'signin';

  // Sign In form
  signInEmail = 'kameswar@changepilot.dev';
  signInPassword = 'changepilot2026';

  // Sign Up form
  signUpName = '';
  signUpEmail = '';
  signUpPassword = '';
  signUpConfirmPassword = '';

  // Google email input modal / prompt (if desired)
  googleEmail = 'developer@google.com';

  isLoading = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(public authService: AuthService) {}

  switchMode(mode: 'signin' | 'signup'): void {
    this.authMode = mode;
    this.errorMessage = null;
    this.successMessage = null;
  }

  handleGoogleSignIn(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.authService.loginWithGoogle(this.googleEmail).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Google sign-in encountered an issue. Please try again.';
      }
    });
  }

  handlePasswordSignIn(): void {
    if (!this.signInEmail.trim() || !this.signInPassword.trim()) {
      this.errorMessage = 'Please provide both email and password.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    this.authService.loginWithPassword(this.signInEmail.trim(), this.signInPassword).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Invalid email or password.';
      }
    });
  }

  handleSignUp(): void {
    if (!this.signUpName.trim() || !this.signUpEmail.trim() || !this.signUpPassword) {
      this.errorMessage = 'Please complete all required fields.';
      return;
    }

    if (this.signUpPassword.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters.';
      return;
    }

    if (this.signUpPassword !== this.signUpConfirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    this.authService.register(
      this.signUpEmail.trim(),
      this.signUpPassword,
      this.signUpName.trim()
    ).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Registration failed. Email may already be in use.';
      }
    });
  }

  handleDemoLogin(username: string): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.authService.loginDemo(username).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Demo login failed.';
      }
    });
  }
}
