import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { User, AuthSessionResponse } from '../models';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000/api/auth';
  
  private initialToken = localStorage.getItem('cp_token');
  private tokenSubject = new BehaviorSubject<string | null>(this.initialToken);
  public token$: Observable<string | null> = this.tokenSubject.asObservable();

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$: Observable<User | null> = this.currentUserSubject.asObservable();

  private isAuthenticatedSubject = new BehaviorSubject<boolean>(!!this.initialToken);
  public isAuthenticated$: Observable<boolean> = this.isAuthenticatedSubject.asObservable();

  constructor(private http: HttpClient) {
    if (this.initialToken) {
      this.fetchProfile();
    }
  }

  get token(): string | null {
    return this.tokenSubject.value;
  }

  get isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  get currentUser(): User | null {
    return this.currentUserSubject.value;
  }

  fetchProfile(): void {
    const headers = { Authorization: `Bearer ${this.token}` };
    this.http.get<User>(`${this.apiUrl}/me`, { headers }).subscribe({
      next: (user) => {
        this.currentUserSubject.next(user);
        this.isAuthenticatedSubject.next(true);
      },
      error: () => {
        this.logout();
      }
    });
  }

  loginWithGoogle(emailOrToken: string = 'developer@google.com'): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${this.apiUrl}/login`, {
      provider: 'google',
      email: emailOrToken
    }).pipe(
      tap((res) => this.handleAuthSuccess(res))
    );
  }

  loginWithPassword(email: string, password: string): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${this.apiUrl}/login`, {
      provider: 'password',
      email: email,
      password: password
    }).pipe(
      tap((res) => this.handleAuthSuccess(res))
    );
  }

  register(email: string, password: string, displayName: string): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${this.apiUrl}/register`, {
      email: email,
      password: password,
      display_name: displayName
    }).pipe(
      tap((res) => this.handleAuthSuccess(res))
    );
  }

  loginDemo(username: string = 'kameswar'): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${this.apiUrl}/login`, {
      provider: 'local',
      demo_username: username
    }).pipe(
      tap((res) => this.handleAuthSuccess(res))
    );
  }

  private handleAuthSuccess(res: AuthSessionResponse): void {
    localStorage.setItem('cp_token', res.access_token);
    this.tokenSubject.next(res.access_token);
    this.currentUserSubject.next(res.user);
    this.isAuthenticatedSubject.next(true);
  }

  logout(): void {
    localStorage.removeItem('cp_token');
    this.tokenSubject.next(null);
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
  }
}
