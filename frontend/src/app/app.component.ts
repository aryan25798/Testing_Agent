import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './layout/sidebar/sidebar.component';
import { HeaderComponent } from './layout/header/header.component';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, HeaderComponent],
  template: `
    <div class="flex h-screen overflow-hidden bg-[#f4f7fc] dark:bg-slate-950 text-slate-800 dark:text-slate-100 transition-colors">
      <!-- Fixed / Collapsible / Mobile Drawer Sidebar -->
      <app-sidebar></app-sidebar>

      <!-- Main App Content Area (expands automatically when sidebar collapses) -->
      <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <!-- Top Sticky Header -->
        <app-header></app-header>

        <!-- Routed Views Viewport -->
        <main class="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
})
export class AppComponent {
  title = 'AI Testing Assistant';
  themeService = inject(ThemeService); // Initializes theme listener and local storage on startup
}
