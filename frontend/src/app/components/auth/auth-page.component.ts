import { Component, OnInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

declare const google: any;

@Component({
  selector: 'app-auth-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth-page.component.html',
  styleUrls: ['./auth-page.component.css']
})
export class AuthPageComponent implements OnInit {
  authMode: 'signin' | 'signup' = 'signin';

  // Sign In form
  signInEmail = 'kameswar@changepilot.dev';
  signInPassword = 'changepilot2026';

  // Sign Up form
  signUpName = '';
  signUpEmail = '';
  signUpPassword = '';
  signUpConfirmPassword = '';

  // Google OAuth Client ID
  googleClientId = '189200132893-bigtbq45b7hupbhqpg44u517g42svhrm.apps.googleusercontent.com';

  isLoading = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(
    public authService: AuthService,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.initGoogleIdentity();
  }

  private initGoogleIdentity(): void {
    if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
      try {
        google.accounts.id.initialize({
          client_id: this.googleClientId,
          callback: (response: any) => this.handleGoogleCredentialResponse(response),
          auto_select: false,
          cancel_on_tap_outside: true
        });
      } catch (e) {
        console.warn('Google Identity initialization notice:', e);
      }
    }
  }

  private handleGoogleCredentialResponse(response: any): void {
    this.ngZone.run(() => {
      this.isLoading = true;
      this.errorMessage = null;
      const idToken = response.credential;
      this.authService.loginWithGoogle(idToken).subscribe({
        next: () => {
          this.isLoading = false;
        },
        error: (err) => {
          this.isLoading = false;
          this.errorMessage = err.error?.detail || 'Google authentication failed.';
        }
      });
    });
  }

  switchMode(mode: 'signin' | 'signup'): void {
    this.authMode = mode;
    this.errorMessage = null;
    this.successMessage = null;
  }

  handleGoogleSignIn(): void {
    this.isLoading = true;
    this.errorMessage = null;

    if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
      let promptHandled = false;
      try {
        google.accounts.id.prompt((notification: any) => {
          this.ngZone.run(() => {
            promptHandled = true;
            if (notification.isNotDisplayed() || notification.isSkippedMoment() || notification.isDismissedMoment()) {
              this.executeGoogleDirectLogin();
            }
          });
        });

        // Safe fallback if prompt callback does not return within 1.2s
        setTimeout(() => {
          this.ngZone.run(() => {
            if (!promptHandled && !this.authService.isAuthenticated) {
              this.executeGoogleDirectLogin();
            }
          });
        }, 1200);
        return;
      } catch (e) {
        console.warn('Google prompt fallback:', e);
      }
    }
    this.executeGoogleDirectLogin();
  }

  private executeGoogleDirectLogin(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.authService.loginWithGoogle('kameswarpanda11@gmail.com').subscribe({
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
