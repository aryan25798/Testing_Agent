import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { SidebarService } from '../../core/services/sidebar.service';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, IconComponent],
  template: `
    <!-- Mobile Backdrop Overlay -->
    <div
      *ngIf="sidebarService.isMobileOpen()"
      (click)="sidebarService.closeMobile()"
      class="fixed inset-0 bg-slate-950/70 z-40 lg:hidden backdrop-blur-sm transition-opacity"
    ></div>

    <!-- Sidebar Container (Fixed h-full with flex-col: Header -> Scrollable Nav -> Pinned Footer) -->
    <aside
      [class.translate-x-0]="sidebarService.isMobileOpen()"
      [class.-translate-x-full]="!sidebarService.isMobileOpen()"
      [class.lg:w-64]="!sidebarService.isCollapsed()"
      [class.lg:w-20]="sidebarService.isCollapsed()"
      class="fixed top-0 bottom-0 left-0 z-50 h-[100dvh] lg:h-full w-64 sidebar-bg text-slate-300 flex flex-col justify-between transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:z-auto border-r border-slate-800/80 shadow-2xl lg:shadow-none overflow-hidden"
    >
      <!-- 1. Brand Header (Pinned at Top, Exact h-16 to align seamlessly with Top Navbar) -->
      <div
        class="h-16 shrink-0 border-b border-slate-800/80 flex items-center transition-all duration-300"
        [class.px-5]="!sidebarService.isCollapsed()"
        [class.px-3]="sidebarService.isCollapsed()"
        [class.justify-between]="!sidebarService.isCollapsed()"
        [class.justify-center]="sidebarService.isCollapsed()"
      >
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center font-black text-white text-lg shadow-glow-blue tracking-tight shrink-0">
            A
          </div>
          <div *ngIf="!sidebarService.isCollapsed()" class="truncate transition-opacity duration-200">
            <div class="font-bold text-white text-sm leading-tight tracking-tight">AI Testing</div>
            <div class="font-bold text-blue-400 text-xs leading-tight tracking-tight">Assistant</div>
          </div>
        </div>

        <!-- Close button on Mobile Drawer -->
        <button
          (click)="sidebarService.closeMobile()"
          class="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          aria-label="Close navigation"
        >
          <app-icon name="x" size="18"></app-icon>
        </button>
      </div>

      <!-- 2. Scrollable Navigation Menu (Takes available height; scrolls cleanly if screen is short) -->
      <nav
        class="flex-1 overflow-y-auto overflow-x-hidden py-3 space-y-1 transition-all duration-300"
        [class.px-3]="!sidebarService.isCollapsed()"
        [class.px-2]="sidebarService.isCollapsed()"
      >
        <a
          routerLink="/dashboard"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          [routerLinkActiveOptions]="{ exact: true }"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Home' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="home" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Home</span>
        </a>

        <a
          routerLink="/projects"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'My Projects' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="folder" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">My Projects</span>
        </a>

        <a
          routerLink="/agents"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'My Agents' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="users" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">My Agents</span>
        </a>

        <a
          routerLink="/workflows"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Workflows' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="workflow" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Workflows</span>
        </a>

        <a
          routerLink="/test-cases"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Test Cases' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="clipboard-list" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Test Cases</span>
        </a>

        <a
          routerLink="/automation"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Automation' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="rocket" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Automation</span>
        </a>

        <a
          routerLink="/executions"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Execution History' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="clock" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Execution History</span>
        </a>

        <a
          routerLink="/reports"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Reports' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="bar-chart-3" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Reports</span>
        </a>

        <a
          routerLink="/models"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'AI Model Settings' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="bot" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">AI Model Settings</span>
        </a>

        <a
          routerLink="/settings"
          routerLinkActive="bg-blue-600 text-white font-semibold shadow-glow-blue"
          (click)="onNavigate()"
          [title]="sidebarService.isCollapsed() ? 'Settings' : ''"
          class="flex items-center rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition-all text-xs group"
          [class.gap-3.5]="!sidebarService.isCollapsed()"
          [class.px-3.5]="!sidebarService.isCollapsed()"
          [class.py-2.5]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [class.p-3]="sidebarService.isCollapsed()"
        >
          <app-icon name="settings" size="18" class="shrink-0"></app-icon>
          <span *ngIf="!sidebarService.isCollapsed()" class="truncate font-medium">Settings</span>
        </a>
      </nav>

      <!-- 3. Bottom Pinned Section (ALWAYS 100% VISIBLE: shrink-0 with border-t) -->
      <div
        class="shrink-0 py-2.5 border-t border-slate-800/80 bg-[#070e1e]/90 space-y-1.5 transition-all duration-300"
        [class.px-3]="!sidebarService.isCollapsed()"
        [class.px-2]="sidebarService.isCollapsed()"
      >
        <!-- System Online Status Pill -->
        <div
          class="rounded-xl bg-slate-900/90 border border-slate-800/80 flex items-center"
          [class.p-2]="!sidebarService.isCollapsed()"
          [class.p-1.5]="sidebarService.isCollapsed()"
          [class.justify-between]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [title]="sidebarService.isCollapsed() ? 'System Online (All systems operational)' : ''"
        >
          <div class="flex items-center gap-2 min-w-0">
            <span class="relative flex h-2 w-2 shrink-0">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <div *ngIf="!sidebarService.isCollapsed()" class="truncate">
              <div class="text-[11px] font-bold text-white leading-none">System Online</div>
              <div class="text-[9px] text-emerald-400 font-medium mt-0.5">All systems operational</div>
            </div>
          </div>
          <span *ngIf="!sidebarService.isCollapsed()" class="text-emerald-400 text-xs font-mono shrink-0">∿</span>
        </div>

        <!-- User Profile Pill (matching target design, always visible at bottom) -->
        <div
          class="rounded-xl bg-slate-900/60 border border-slate-800/60 hover:bg-slate-800/60 transition-colors flex items-center cursor-pointer"
          [class.p-2]="!sidebarService.isCollapsed()"
          [class.p-1.5]="sidebarService.isCollapsed()"
          [class.justify-between]="!sidebarService.isCollapsed()"
          [class.justify-center]="sidebarService.isCollapsed()"
          [title]="sidebarService.isCollapsed() ? 'Aryan (Personal QA Workspace)' : ''"
        >
          <div class="flex items-center gap-2 min-w-0">
            <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-sm">
              A
            </div>
            <div *ngIf="!sidebarService.isCollapsed()" class="truncate">
              <div class="text-[11px] font-bold text-white leading-tight">Aryan</div>
              <div class="text-[9px] text-slate-400 leading-tight">Personal Workspace</div>
            </div>
          </div>
          <app-icon *ngIf="!sidebarService.isCollapsed()" name="chevron-down" size="12" class="text-slate-400 shrink-0"></app-icon>
        </div>
      </div>
    </aside>
  `,
})
export class SidebarComponent {
  sidebarService = inject(SidebarService);

  onNavigate() {
    if (this.sidebarService.isMobileOpen()) {
      this.sidebarService.closeMobile();
    }
  }
}
