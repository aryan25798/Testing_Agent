import { Injectable, signal, effect } from '@angular/core';

export type AppTheme = 'light' | 'dark' | 'system';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  private readonly THEME_KEY = 'ai_testing_assistant_theme';
  theme = signal<AppTheme>('system');
  isDark = signal<boolean>(false);

  private mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  constructor() {
    // 1. Load saved theme or default to system
    const saved = localStorage.getItem(this.THEME_KEY) as AppTheme | null;
    if (saved && ['light', 'dark', 'system'].includes(saved)) {
      this.theme.set(saved);
    } else {
      this.theme.set('system');
    }

    // 2. Compute dark state
    this.updateComputedDark();

    // 3. Listen to system preference changes
    this.mediaQuery.addEventListener('change', () => {
      if (this.theme() === 'system') {
        this.updateComputedDark();
      }
    });

    // 4. Reactively apply class to document root
    effect(() => {
      const dark = this.isDark();
      if (dark) {
        document.documentElement.classList.add('dark');
        document.body.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
        document.body.classList.remove('dark');
      }
    });
  }

  setTheme(newTheme: AppTheme) {
    this.theme.set(newTheme);
    localStorage.setItem(this.THEME_KEY, newTheme);
    this.updateComputedDark();
  }

  cycleTheme() {
    const current = this.theme();
    if (current === 'light') this.setTheme('dark');
    else if (current === 'dark') this.setTheme('system');
    else this.setTheme('light');
  }

  private updateComputedDark() {
    const current = this.theme();
    if (current === 'dark') {
      this.isDark.set(true);
    } else if (current === 'light') {
      this.isDark.set(false);
    } else {
      this.isDark.set(this.mediaQuery.matches);
    }
  }
}
