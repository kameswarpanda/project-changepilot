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
  private currentUserSubject = new BehaviorSubject<User>({
    id: 'usr-kameswar-01',
    identity_provider_id: 'gh-kameswar-2026',
    username: 'kameswar',
    display_name: 'Kameswar',
    email: 'kameswar@changepilot.dev',
    avatar_url: 'https://avatars.githubusercontent.com/u/583231',
    provider: 'github',
    roles: ['admin', 'developer']
  });

  public currentUser$: Observable<User> = this.currentUserSubject.asObservable();
  private tokenSubject = new BehaviorSubject<string | null>(localStorage.getItem('cp_token'));
  public token$: Observable<string | null> = this.tokenSubject.asObservable();

  constructor(private http: HttpClient) {
    // If token exists, fetch profile from backend
    if (this.tokenSubject.value) {
      this.fetchProfile();
    } else {
      // Auto-authenticate as default developer for zero-friction local mode
      this.loginDemo('kameswar').subscribe();
    }
  }

  get token(): string | null {
    return this.tokenSubject.value;
  }

  get currentUser(): User {
    return this.currentUserSubject.value;
  }

  fetchProfile(): void {
    const headers = { Authorization: `Bearer ${this.token}` };
    this.http.get<User>(`${this.apiUrl}/me`, { headers }).subscribe({
      next: (user) => this.currentUserSubject.next(user),
      error: () => this.loginDemo('kameswar').subscribe()
    });
  }

  loginDemo(username: string = 'kameswar'): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${this.apiUrl}/login`, {
      provider: 'local',
      demo_username: username
    }).pipe(
      tap((res) => {
        localStorage.setItem('cp_token', res.access_token);
        this.tokenSubject.next(res.access_token);
        this.currentUserSubject.next(res.user);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('cp_token');
    this.tokenSubject.next(null);
    this.currentUserSubject.next({
      id: 'usr-guest',
      identity_provider_id: 'guest',
      username: 'guest',
      display_name: 'Guest User',
      email: 'guest@changepilot.local',
      provider: 'local',
      roles: ['viewer']
    });
  }
}
