import { Component, OnInit, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { IconComponent } from '../../shared/components/icon.component';
import { Project, TestCase } from '../../core/models/types';

interface SearchResult {
  category: 'Pages' | 'Projects' | 'Agents' | 'Test Cases';
  title: string;
  subtitle: string;
  route: string[];
  queryParams?: Record<string, string>;
  icon: string;
}

@Component({
  selector: 'app-global-search',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <!-- Trigger Button in Header -->
    <button
      (click)="openSearch()"
      class="w-full flex items-center justify-between px-3.5 py-2 text-xs bg-slate-100 hover:bg-slate-200/70 dark:bg-slate-800 dark:hover:bg-slate-700/80 text-slate-500 dark:text-slate-400 rounded-xl border border-transparent focus:border-blue-500 focus:outline-none transition-all cursor-pointer"
    >
      <div class="flex items-center gap-2.5">
        <app-icon name="search" size="14" class="text-slate-400 dark:text-slate-500"></app-icon>
        <span class="truncate">Search projects, agents, test cases...</span>
      </div>
      <kbd class="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 text-[10px] font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-500 dark:text-slate-400 shadow-2xs">
        <span class="text-xs">⌘</span>K
      </kbd>
    </button>

    <!-- Search Modal Backdrop -->
    <div
      *ngIf="isOpen()"
      (click)="closeSearch()"
      class="fixed inset-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-start justify-center pt-16 sm:pt-24 px-4"
    >
      <!-- Search Dialog Window -->
      <div
        (click)="$event.stopPropagation()"
        class="bg-white dark:bg-slate-900 w-full max-w-xl rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col max-h-[75vh]"
      >
        <!-- Search Input Bar -->
        <div class="px-4 py-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center gap-3">
          <app-icon name="search" size="18" class="text-slate-400 dark:text-slate-500"></app-icon>
          <input
            #searchInput
            type="text"
            [(ngModel)]="query"
            (input)="onQueryChange()"
            (keydown)="onKeyDown($event)"
            placeholder="Type to search anything (Projects, Agents, Test Cases, Pages)..."
            class="flex-1 bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 outline-none"
            autofocus
          />
          <button
            *ngIf="query"
            (click)="query = ''; onQueryChange()"
            class="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded"
          >
            <app-icon name="x" size="14"></app-icon>
          </button>
          <span class="text-[10px] font-mono text-slate-400 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded">
            ESC
          </span>
        </div>

        <!-- Results List -->
        <div class="overflow-y-auto p-2 divide-y divide-slate-100 dark:divide-slate-800/60">
          <div *ngIf="results.length > 0; else noResultsTpl" class="space-y-1">
            <div
              *ngFor="let item of results; let i = index"
              (click)="selectResult(item)"
              [class.bg-blue-50]="selectedIndex === i"
              [class.dark:bg-slate-800]="selectedIndex === i"
              class="px-3 py-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors flex items-center justify-between cursor-pointer group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300 shrink-0">
                  <app-icon [name]="item.icon" size="16"></app-icon>
                </div>
                <div class="min-w-0">
                  <div class="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {{ item.title }}
                  </div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                    {{ item.subtitle }}
                  </div>
                </div>
              </div>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 shrink-0 uppercase tracking-wider">
                {{ item.category }}
              </span>
            </div>
          </div>

          <ng-template #noResultsTpl>
            <div class="py-12 text-center text-xs text-slate-400 dark:text-slate-500">
              <span *ngIf="query">No matching results found for "{{ query }}".</span>
              <span *ngIf="!query">Type to search projects, agents, test cases, or routes.</span>
            </div>
          </ng-template>
        </div>

        <!-- Footer -->
        <div class="px-4 py-2.5 bg-slate-50 dark:bg-slate-900/90 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 dark:text-slate-500 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span>↑↓ to navigate</span>
            <span>↵ to select</span>
            <span>ESC to close</span>
          </div>
          <span>AI Testing Workspace</span>
        </div>
      </div>
    </div>
  `,
})
export class GlobalSearchComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);

  isOpen = signal<boolean>(false);
  query = '';
  results: SearchResult[] = [];
  selectedIndex = 0;

  private allProjects: Project[] = [];
  private staticPages: SearchResult[] = [
    { category: 'Pages', title: 'Dashboard', subtitle: 'Main testing analytics and metrics', route: ['/dashboard'], icon: 'home' },
    { category: 'Pages', title: 'My Projects', subtitle: 'Manage client testing applications', route: ['/projects'], icon: 'folder' },
    { category: 'Pages', title: 'My Agents', subtitle: 'Predefined and custom testing agents', route: ['/agents'], icon: 'users' },
    { category: 'Pages', title: 'Workflows', subtitle: 'Execute 6-agent autonomous pipeline', route: ['/workflows'], icon: 'workflow' },
    { category: 'Pages', title: 'Test Cases', subtitle: 'Step-by-step test cases and assertions', route: ['/test-cases'], icon: 'clipboard-list' },
    { category: 'Pages', title: 'Automation', subtitle: 'Playwright and Selenium scripts', route: ['/automation'], icon: 'cog' },
    { category: 'Pages', title: 'Execution History', subtitle: 'Test runs and triage results', route: ['/executions'], icon: 'clock' },
    { category: 'Pages', title: 'Reports', subtitle: 'Executive summary, PDF and CSV exports', route: ['/reports'], icon: 'bar-chart-3' },
    { category: 'Pages', title: 'AI Model Settings', subtitle: 'Gemini and OpenAI API keys and routing', route: ['/models'], icon: 'bot' },
    { category: 'Pages', title: 'Settings', subtitle: 'Jira and GitHub integrations', route: ['/settings'], icon: 'settings' },
  ];

  @HostListener('window:keydown', ['$event'])
  handleGlobalShortcut(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      this.openSearch();
    }
  }

  ngOnInit() {
    this.api.getProjects().subscribe({
      next: (res) => (this.allProjects = res),
    });
  }

  openSearch() {
    this.isOpen.set(true);
    this.query = '';
    this.results = [...this.staticPages];
    this.selectedIndex = 0;
  }

  closeSearch() {
    this.isOpen.set(false);
  }

  onQueryChange() {
    const q = this.query.trim().toLowerCase();
    if (!q) {
      this.results = [...this.staticPages];
      this.selectedIndex = 0;
      return;
    }

    const matchedPages = this.staticPages.filter(
      (p) => p.title.toLowerCase().includes(q) || p.subtitle.toLowerCase().includes(q)
    );

    const matchedProjects: SearchResult[] = this.allProjects
      .filter((p) => p.name.toLowerCase().includes(q) || (p.description && p.description.toLowerCase().includes(q)))
      .map((p) => ({
        category: 'Projects',
        title: p.name,
        subtitle: `Framework: ${p.framework} | Base URL: ${p.base_url || 'http://localhost:4200'}`,
        route: ['/projects'],
        queryParams: { id: p.id },
        icon: 'folder',
      }));

    this.results = [...matchedProjects, ...matchedPages];
    this.selectedIndex = 0;
  }

  onKeyDown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex + 1) % (this.results.length || 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex - 1 + this.results.length) % (this.results.length || 1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (this.results[this.selectedIndex]) {
        this.selectResult(this.results[this.selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      this.closeSearch();
    }
  }

  selectResult(item: SearchResult) {
    this.closeSearch();
    this.router.navigate(item.route, { queryParams: item.queryParams });
  }
}
