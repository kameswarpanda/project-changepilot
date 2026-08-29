import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private isDarkModeSubject = new BehaviorSubject<boolean>(true);
  public isDarkMode$: Observable<boolean> = this.isDarkModeSubject.asObservable();

  constructor() {
    const savedTheme = localStorage.getItem('cp_theme');
    if (savedTheme === 'light') {
      this.setTheme(false);
    } else {
      this.setTheme(true);
    }
  }

  get isDarkMode(): boolean {
    return this.isDarkModeSubject.value;
  }

  toggleTheme(): void {
    this.setTheme(!this.isDarkMode);
  }

  setTheme(isDark: boolean): void {
    this.isDarkModeSubject.next(isDark);
    if (isDark) {
      document.body.classList.remove('light-theme');
      localStorage.setItem('cp_theme', 'dark');
    } else {
      document.body.classList.add('light-theme');
      localStorage.setItem('cp_theme', 'light');
    }
  }
}
