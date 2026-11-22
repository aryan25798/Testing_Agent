import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Project, AutomationScript } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-automation',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Test Automation Scripts</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Generated Playwright and Selenium Python test automation scripts.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <label class="text-xs font-bold text-slate-600 dark:text-slate-300">Project:</label>
          <select
            [(ngModel)]="selectedProjectId"
            (change)="loadScripts()"
            class="px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 shadow-sm focus:border-blue-500 outline-none"
          >
            <option *ngFor="let p of projects" [value]="p.id">
              {{ p.name }}
            </option>
          </select>

          <a
            *ngIf="scripts.length"
            [href]="api.downloadAutomationZipUrl(selectedProjectId)"
            class="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs shadow-sm transition-all"
            download
          >
            <app-icon name="download" size="14"></app-icon>
            <span>Download ZIP</span>
          </a>
        </div>
      </div>

      <!-- Scripts Content Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6" *ngIf="scripts.length; else emptyTpl">
        <!-- Scripts List (Left 4 cols) -->
        <div class="lg:col-span-4 space-y-2">
          <div
            *ngFor="let s of scripts"
            (click)="selectedScript = s"
            class="p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between"
            [ngClass]="{
              'border-blue-500 bg-blue-50/50 dark:bg-blue-950/40 shadow-sm': selectedScript?.id === s.id,
              'border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700': selectedScript?.id !== s.id
            }"
          >
            <div class="flex items-center justify-between mb-2 min-w-0 gap-2">
              <span class="font-bold text-slate-900 dark:text-white text-xs font-mono truncate min-w-0 flex-1">
                {{ s.script_name }}
              </span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase shrink-0">
                {{ s.framework }}
              </span>
            </div>
            <div class="text-[11px] text-slate-400 dark:text-slate-500 font-mono truncate">
              {{ s.file_path }}
            </div>
          </div>
        </div>

        <!-- Script Viewer (Right 8 cols) -->
        <div class="lg:col-span-8 bg-slate-950 rounded-2xl p-5 border border-slate-800 shadow-xl text-slate-100 flex flex-col justify-between" *ngIf="selectedScript">
          <div>
            <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div class="flex items-center gap-2">
                <span class="text-blue-400 font-mono text-xs font-bold">{{ selectedScript.script_name }}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
                  Syntax Valid
                </span>
              </div>
              <button
                (click)="copyCode()"
                class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <app-icon [name]="copied ? 'check' : 'copy'" size="13"></app-icon>
                <span>{{ copied ? 'Copied!' : 'Copy Code' }}</span>
              </button>
            </div>

            <pre class="font-mono text-xs text-blue-200/90 overflow-x-auto p-4 bg-slate-900 rounded-xl border border-slate-800/80 leading-relaxed max-h-[500px]"><code>{{ selectedScript.code_content }}</code></pre>
          </div>
        </div>
      </div>

      <ng-template #emptyTpl>
        <div class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
          <app-icon name="cog" size="40" class="text-slate-400 mx-auto mb-3"></app-icon>
          <h3 class="font-bold text-slate-800 dark:text-white text-base">No Automation Scripts Generated</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Run the autonomous testing workflow to generate Playwright/Selenium scripts.</p>
        </div>
      </ng-template>
    </div>
  `,
})
export class AutomationComponent implements OnInit {
  api = inject(ApiService);

  projects: Project[] = [];
  selectedProjectId = '';
  scripts: AutomationScript[] = [];
  selectedScript: AutomationScript | null = null;
  copied = false;

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
        this.selectedScript = this.scripts.length ? this.scripts[0] : null;
      },
    });
  }

  copyCode() {
    if (!this.selectedScript) return;
    navigator.clipboard.writeText(this.selectedScript.code_content).then(() => {
      this.copied = true;
      setTimeout(() => (this.copied = false), 2000);
    });
  }
}
