import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Project, AutomationScript } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';
import { PaginationComponent } from '../../shared/components/pagination.component';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';

@Component({
  selector: 'app-automation',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, PaginationComponent, EmptyStateComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-16">
      <!-- 1. Header Banner -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 min-w-0">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2.5">
            <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight break-words min-w-0">
              Test Automation Scripts
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              {{ filteredScripts.length }} Scripts
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            Executable Playwright and Selenium Python test automation scripts with explicit waits and POM architecture.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2.5 sm:gap-3 shrink-0">
          <div class="flex items-center gap-2">
            <label class="text-xs font-bold text-slate-600 dark:text-slate-300">Project:</label>
            <select
              [(ngModel)]="selectedProjectId"
              (change)="onProjectChange()"
              class="px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 shadow-sm focus:border-blue-500 outline-none cursor-pointer"
            >
              <option *ngFor="let p of projects" [value]="p.id">
                {{ p.name }}
              </option>
            </select>
          </div>

          <a
            *ngIf="scripts.length"
            [href]="api.downloadAutomationZipUrl(selectedProjectId)"
            class="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs shadow-sm transition-all cursor-pointer"
            download
          >
            <app-icon name="download" size="14"></app-icon>
            <span>Download All (ZIP)</span>
          </a>
        </div>
      </div>

      <!-- 2. Search & Filter Bar -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3" *ngIf="scripts.length">
        <div class="relative flex-1 max-w-md">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <app-icon name="search" size="14"></app-icon>
          </span>
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (ngModelChange)="applyFilters()"
            placeholder="Search scripts by filename or code content..."
            class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        <div class="flex items-center gap-2">
          <select
            [(ngModel)]="selectedFramework"
            (change)="applyFilters()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Frameworks</option>
            <option value="playwright">Playwright</option>
            <option value="selenium">Selenium</option>
          </select>
        </div>
      </div>

      <!-- 3. Scripts Content Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6" *ngIf="filteredScripts.length; else emptyTpl">
        <!-- Scripts List (Left 4 cols) -->
        <div class="lg:col-span-4 space-y-2">
          <div
            *ngFor="let s of paginatedScripts"
            (click)="selectedScript = s"
            class="p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between"
            [ngClass]="{
              'border-blue-500 bg-blue-50/50 dark:bg-blue-950/40 shadow-sm ring-1 ring-blue-500/30': selectedScript?.id === s.id,
              'border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700': selectedScript?.id !== s.id
            }"
          >
            <div class="flex items-center justify-between mb-2 min-w-0 gap-2">
              <span class="font-bold text-slate-900 dark:text-white text-xs font-mono truncate min-w-0 flex-1" [title]="s.script_name">
                {{ s.script_name }}
              </span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase shrink-0">
                {{ s.framework }}
              </span>
            </div>
            <div class="text-[11px] text-slate-400 dark:text-slate-500 font-mono truncate" [title]="s.file_path">
              {{ s.file_path }}
            </div>
          </div>

          <!-- Script List Pagination -->
          <div class="pt-2" *ngIf="filteredScripts.length > pageSize">
            <app-pagination
              [currentPage]="currentPage"
              [pageSize]="pageSize"
              [totalItems]="filteredScripts.length"
              [pageSizeOptions]="[5, 10, 20]"
              (pageChange)="onPageChange($event)"
              (pageSizeChange)="onPageSizeChange($event)"
            ></app-pagination>
          </div>
        </div>

        <!-- Script Viewer (Right 8 cols) -->
        <div class="lg:col-span-8 bg-slate-950 rounded-2xl p-5 border border-slate-800 shadow-xl text-slate-100 flex flex-col justify-between" *ngIf="selectedScript">
          <div>
            <div class="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 mb-4 gap-2">
              <div class="flex items-center gap-2">
                <span class="text-blue-400 font-mono text-xs font-bold">{{ selectedScript.script_name }}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
                  Syntax Valid
                </span>
                <span class="text-slate-500 text-[11px] font-mono">{{ selectedScript.framework }}</span>
              </div>
              <button
                (click)="copyCode()"
                class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <app-icon [name]="copied ? 'check' : 'copy'" size="13"></app-icon>
                <span>{{ copied ? 'Copied!' : 'Copy Code' }}</span>
              </button>
            </div>

            <pre class="font-mono text-xs text-blue-200/90 overflow-x-auto p-4 bg-slate-900 rounded-xl border border-slate-800/80 leading-relaxed max-h-[520px]"><code>{{ selectedScript.code_content }}</code></pre>
          </div>
        </div>
      </div>

      <ng-template #emptyTpl>
        <app-empty-state
          icon="cog"
          [title]="searchQuery || selectedFramework ? 'No Matching Automation Scripts' : 'No Automation Scripts Generated'"
          [description]="searchQuery || selectedFramework ? 'Try resetting your search or framework filter.' : 'Run the 6-agent autonomous workflow to automatically generate test scripts.'"
        ></app-empty-state>
      </ng-template>
    </div>
  `,
})
export class AutomationComponent implements OnInit {
  api = inject(ApiService);

  projects: Project[] = [];
  selectedProjectId = '';
  scripts: AutomationScript[] = [];
  filteredScripts: AutomationScript[] = [];
  selectedScript: AutomationScript | null = null;
  copied = false;

  searchQuery = '';
  selectedFramework = '';
  currentPage = 1;
  pageSize = 5;

  ngOnInit() {
    this.api.getProjects().subscribe({
      next: (res) => {
        this.projects = res;
        if (this.projects.length) {
          this.selectedProjectId = this.projects[0].id;
          this.loadScripts();
        }
      },
    });
  }

  loadScripts() {
    if (!this.selectedProjectId) return;
    this.api.getAutomationScripts(this.selectedProjectId).subscribe({
      next: (res) => {
        this.scripts = res;
        this.applyFilters();
      },
    });
  }

  onProjectChange() {
    this.currentPage = 1;
    this.loadScripts();
  }

  applyFilters() {
    this.filteredScripts = this.scripts.filter((s) => {
      const matchSearch =
        !this.searchQuery ||
        s.script_name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        s.code_content.toLowerCase().includes(this.searchQuery.toLowerCase());
      const matchFw = !this.selectedFramework || s.framework.toLowerCase() === this.selectedFramework.toLowerCase();
      return matchSearch && matchFw;
    });

    this.selectedScript = this.filteredScripts.length ? this.filteredScripts[0] : null;
    this.currentPage = 1;
  }

  get paginatedScripts(): AutomationScript[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filteredScripts.slice(start, start + this.pageSize);
  }

  onPageChange(page: number) {
    this.currentPage = page;
  }

  onPageSizeChange(size: number) {
    this.pageSize = size;
    this.currentPage = 1;
  }

  copyCode() {
    if (!this.selectedScript) return;
    navigator.clipboard.writeText(this.selectedScript.code_content).then(() => {
      this.copied = true;
      setTimeout(() => (this.copied = false), 2000);
    });
  }
}
