import { Component, OnInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';

declare const google: any;

@Component({
  selector: 'app-auth-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth-page.component.html',
  styleUrls: ['./auth-page.component.css']
})
export class AuthPageComponent implements OnInit {
  authMode: 'signin' | 'signup' | 'forgot' = 'signin';

  // Sign In form (initial empty fields to avoid autofill pre-population)
  signInEmail = '';
  signInPassword = '';

  // Sign Up form (with 2-Step OTP Verification Gate)
  signUpStep: 'form' | 'verify' = 'form';
  signUpName = '';
  signUpEmail = '';
  signUpPassword = '';
  signUpConfirmPassword = '';
  signUpOtp = '';

  // Forgot Password 3-Step Flow
  forgotStep: 'request' | 'verify' | 'reset' = 'request';
  forgotEmail = '';
  forgotOtp = '';
  forgotNewPassword = '';
  forgotConfirmPassword = '';

  // Google OAuth Client ID
  googleClientId = '189200132893-bigtbq45b7hupbhqpg44u517g42svhrm.apps.googleusercontent.com';

  isLoading = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;
  devHintMessage: string | null = null;

  constructor(
    public authService: AuthService,
    public themeService: ThemeService,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.initGoogleIdentity();
  }

  // Password validation helpers
  isMinLength(pwd: string): boolean {
    return pwd.length >= 8;
  }

  hasUpper(pwd: string): boolean {
    return /[A-Z]/.test(pwd);
  }

  hasLower(pwd: string): boolean {
    return /[a-z]/.test(pwd);
  }

  hasNumber(pwd: string): boolean {
    return /[0-9]/.test(pwd);
  }

  hasSpecial(pwd: string): boolean {
    return /[!@#$%^&*(),.?":{}|<>]/.test(pwd);
  }

  isPasswordStrong(pwd: string): boolean {
    return this.isMinLength(pwd) && this.hasUpper(pwd) && this.hasLower(pwd) && this.hasNumber(pwd) && this.hasSpecial(pwd);
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

  switchMode(mode: 'signin' | 'signup' | 'forgot'): void {
    this.authMode = mode;
    this.errorMessage = null;
    this.successMessage = null;
    this.devHintMessage = null;
    if (mode === 'signup') {
      this.signUpStep = 'form';
      this.signUpOtp = '';
    }
    if (mode === 'forgot') {
      this.forgotStep = 'request';
      this.forgotOtp = '';
      this.forgotNewPassword = '';
      this.forgotConfirmPassword = '';
    }
  }

  private isProcessingGoogle = false;

  handleGoogleSignIn(): void {
    if (this.isLoading || this.isProcessingGoogle) {
      return;
    }
    this.errorMessage = null;

    // 1. Try Google Identity Services OAuth 2.0 Token Client (Popup)
    if (typeof google !== 'undefined' && google.accounts && google.accounts.oauth2) {
      try {
        const client = google.accounts.oauth2.initTokenClient({
          client_id: this.googleClientId,
          scope: 'openid email profile',
          callback: (tokenResponse: any) => {
            this.ngZone.run(() => {
              if (tokenResponse && tokenResponse.access_token) {
                this.isLoading = true;
                this.authService.loginWithGoogle(tokenResponse.access_token).subscribe({
                  next: () => {
                    this.isLoading = false;
                  },
                  error: (err) => {
                    this.isLoading = false;
                    this.errorMessage = err.error?.detail || 'Google sign-in failed. Please check credentials.';
                  }
                });
              } else if (tokenResponse && tokenResponse.error) {
                this.errorMessage = 'Google sign-in was cancelled or encountered an error.';
              }
            });
          },
          error_callback: (err: any) => {
            this.ngZone.run(() => {
              this.errorMessage = 'Google authentication popup could not be initialized.';
            });
          }
        });
        client.requestAccessToken({ prompt: 'select_account' });
        return;
      } catch (e) {
        console.warn('Google Identity Token Client notice:', e);
      }
    }

    // 2. Fallback Google Identity prompt
    if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
      try {
        google.accounts.id.prompt();
        return;
      } catch (e) {
        console.warn('Google One Tap notice:', e);
      }
    }

    // 3. Fallback direct Google OAuth 2.0 popup
    const redirectUri = window.location.origin + '/auth';
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${this.googleClientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=token&scope=openid%20email%20profile&prompt=select_account`;
    const popup = window.open(authUrl, 'google_oauth_popup', 'width=520,height=620,top=100,left=100');
    if (!popup) {
      window.location.href = authUrl;
    }
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
    this.handleRequestSignUpOtp();
  }

  handleRequestSignUpOtp(): void {
    if (!this.signUpName.trim() || !this.signUpEmail.trim() || !this.signUpPassword) {
      this.errorMessage = 'Please complete all required fields.';
      return;
    }

    if (!this.isPasswordStrong(this.signUpPassword)) {
      this.errorMessage = 'Please ensure your password meets all complexity requirements below.';
      return;
    }

    if (this.signUpPassword !== this.signUpConfirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.authService.requestSignupOtp(
      this.signUpEmail.trim(),
      this.signUpPassword,
      this.signUpName.trim()
    ).subscribe({
      next: (res: any) => {
        this.isLoading = false;
        this.signUpStep = 'verify';
        this.signUpOtp = '';
        this.successMessage = res.message || `Verification code sent to ${this.signUpEmail}. Please enter the 6-digit code.`;
        this.devHintMessage = res.dev_hint || null;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Failed to send verification code. Email may already be in use.';
      }
    });
  }

  handleVerifySignUpOtp(): void {
    if (!this.signUpOtp.trim() || this.signUpOtp.trim().length !== 6) {
      this.errorMessage = 'Please enter the valid 6-digit verification code sent to your email.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.authService.verifySignupOtp(this.signUpEmail.trim(), this.signUpOtp.trim()).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Account created and verified successfully! Redirecting...';
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Invalid or expired verification code.';
      }
    });
  }

  // --- Forgot Password Handlers ---
  handleSendResetOtp(): void {
    if (!this.forgotEmail.trim()) {
      this.errorMessage = 'Please enter your work email to receive a verification code.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.authService.requestPasswordResetOtp(this.forgotEmail.trim()).subscribe({
      next: (res: any) => {
        this.isLoading = false;
        this.forgotStep = 'verify';
        this.forgotOtp = ''; // User must manually enter the 6-digit code received via email
        this.successMessage = res.message || 'Verification code sent! Please check your email.';
        this.devHintMessage = res.dev_hint || null;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Failed to send verification code. Please verify your email.';
      }
    });
  }

  handleVerifyResetOtp(): void {
    if (!this.forgotOtp.trim() || this.forgotOtp.trim().length !== 6) {
      this.errorMessage = 'Please enter the valid 6-digit verification code.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.authService.verifyPasswordResetOtp(this.forgotEmail.trim(), this.forgotOtp.trim()).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.forgotStep = 'reset';
        this.successMessage = res.message || 'Code verified! Now choose a new password.';
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Invalid verification code. Please check and retry.';
      }
    });
  }

  handleResetPassword(): void {
    if (!this.forgotNewPassword) {
      this.errorMessage = 'Please enter your new password.';
      return;
    }

    if (!this.isPasswordStrong(this.forgotNewPassword)) {
      this.errorMessage = 'New password does not meet security criteria.';
      return;
    }

    if (this.forgotNewPassword !== this.forgotConfirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    this.authService.resetPasswordWithOtp(
      this.forgotEmail.trim(),
      this.forgotOtp.trim(),
      this.forgotNewPassword
    ).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.successMessage = res.message || 'Password successfully reset!';
        setTimeout(() => {
          this.signInEmail = this.forgotEmail;
          this.switchMode('signin');
        }, 1500);
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Password reset failed. Please retry.';
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
