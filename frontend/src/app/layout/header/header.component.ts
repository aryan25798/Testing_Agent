import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarService } from '../../core/services/sidebar.service';
import { GlobalSearchComponent } from './global-search.component';
import { ThemeToggleComponent } from './theme-toggle.component';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, GlobalSearchComponent, ThemeToggleComponent, IconComponent],
  template: `
    <header class="h-16 shrink-0 bg-white dark:bg-[#070e1e] border-b border-slate-200/80 dark:border-slate-800/80 px-4 sm:px-6 flex items-center justify-between gap-4 transition-colors sticky top-0 z-30">
      <!-- Left: Sidebar Toggle + Global Search -->
      <div class="flex items-center gap-2 sm:gap-4 flex-1 max-w-xl min-w-0">
        <!-- Desktop Sidebar Collapse Toggle -->
        <button
          (click)="sidebarService.toggleCollapse()"
          class="hidden lg:flex p-2 rounded-xl text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0"
          title="Toggle sidebar width"
          aria-label="Toggle sidebar width"
        >
          <app-icon name="menu" size="18"></app-icon>
        </button>

        <!-- Mobile Drawer Hamburger Toggle -->
        <button
          (click)="sidebarService.toggleMobile()"
          class="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0"
          title="Open navigation"
          aria-label="Open mobile drawer"
        >
          <app-icon name="menu" size="20"></app-icon>
        </button>

        <!-- Global Search Dialog Trigger -->
        <div class="w-full min-w-0">
          <app-global-search></app-global-search>
        </div>
      </div>

      <!-- Right: Theme Switcher & User Profile (Clean, Unified Height) -->
      <div class="flex items-center gap-2 sm:gap-4 shrink-0">
        <!-- Theme Dropdown Switcher -->
        <app-theme-toggle></app-theme-toggle>

        <!-- Vertical Divider -->
        <div class="h-5 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>

        <!-- User Profile Avatar Pill -->
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-500 text-white font-bold text-xs flex items-center justify-center shadow-sm shrink-0">
            A
          </div>
          <div class="hidden md:block text-left">
            <div class="text-xs font-bold text-slate-800 dark:text-slate-100 leading-tight">Aryan</div>
            <div class="text-[10px] font-medium text-slate-500 dark:text-slate-400">Personal QA Workspace</div>
          </div>
        </div>
      </div>
    </header>
  `,
})
export class HeaderComponent {
  sidebarService = inject(SidebarService);
}
