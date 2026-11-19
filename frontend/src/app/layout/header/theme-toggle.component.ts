import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeService, AppTheme } from '../../core/services/theme.service';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="relative">
      <!-- Toggle Trigger -->
      <button
        (click)="isOpen.set(!isOpen())"
        class="w-9 h-9 rounded-xl flex items-center justify-center text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        [title]="'Current theme: ' + themeService.theme()"
        aria-label="Toggle theme"
      >
        <app-icon
          *ngIf="themeService.theme() === 'light'"
          name="sun"
          size="17"
          class="text-amber-500"
        ></app-icon>
        <app-icon
          *ngIf="themeService.theme() === 'dark'"
          name="moon"
          size="17"
          class="text-blue-400"
        ></app-icon>
        <app-icon
          *ngIf="themeService.theme() === 'system'"
          name="monitor"
          size="17"
          class="text-slate-500 dark:text-slate-400"
        ></app-icon>
      </button>

      <!-- Dropdown Menu -->
      <div
        *ngIf="isOpen()"
        (click)="isOpen.set(false)"
        class="fixed inset-0 z-40"
      ></div>

      <div
        *ngIf="isOpen()"
        class="absolute right-0 mt-2 w-36 py-1.5 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 z-50 text-xs text-slate-700 dark:text-slate-200 divide-y divide-slate-100 dark:divide-slate-700/60"
      >
        <button
          (click)="selectTheme('light')"
          class="w-full px-3 py-2 flex items-center gap-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors text-left"
          [class.font-bold]="themeService.theme() === 'light'"
          [class.text-blue-600]="themeService.theme() === 'light'"
          [class.dark:text-blue-400]="themeService.theme() === 'light'"
        >
          <app-icon name="sun" size="14" class="text-amber-500"></app-icon>
          <span>Light Mode</span>
        </button>

        <button
          (click)="selectTheme('dark')"
          class="w-full px-3 py-2 flex items-center gap-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors text-left"
          [class.font-bold]="themeService.theme() === 'dark'"
          [class.text-blue-600]="themeService.theme() === 'dark'"
          [class.dark:text-blue-400]="themeService.theme() === 'dark'"
        >
          <app-icon name="moon" size="14" class="text-blue-400"></app-icon>
          <span>Dark Mode</span>
        </button>

        <button
          (click)="selectTheme('system')"
          class="w-full px-3 py-2 flex items-center gap-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors text-left"
          [class.font-bold]="themeService.theme() === 'system'"
          [class.text-blue-600]="themeService.theme() === 'system'"
          [class.dark:text-blue-400]="themeService.theme() === 'system'"
        >
          <app-icon name="monitor" size="14" class="text-slate-500 dark:text-slate-400"></app-icon>
          <span>System Default</span>
        </button>
      </div>
    </div>
  `,
})
export class ThemeToggleComponent {
  themeService = inject(ThemeService);
  isOpen = signal<boolean>(false);

  selectTheme(theme: AppTheme) {
    this.themeService.setTheme(theme);
    this.isOpen.set(false);
  }
}
