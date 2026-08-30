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

    const applyClasses = () => {
      if (isDark) {
        document.documentElement.classList.remove('light');
        document.documentElement.classList.add('dark');
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        localStorage.setItem('cp_theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        localStorage.setItem('cp_theme', 'light');
      }
    };

    if (typeof document !== 'undefined' && 'startViewTransition' in document) {
      (document as any).startViewTransition(() => {
        applyClasses();
      });
    } else {
      applyClasses();
    }
  }
}
