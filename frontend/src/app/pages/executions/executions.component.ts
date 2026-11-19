import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Project, TestExecution } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-executions',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Execution History & Evidence</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Real execution telemetry, Playwright browser test traces, and failure triage.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <label class="text-xs font-bold text-slate-600 dark:text-slate-300">Project:</label>
          <select
            [(ngModel)]="selectedProjectId"
            (change)="loadExecutions()"
            class="px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 shadow-sm focus:border-blue-500 outline-none"
          >
            <option *ngFor="let p of projects" [value]="p.id">
              {{ p.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Executions Table -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-subtle overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200/80 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold text-[10px]">
              <tr>
                <th class="px-5 py-3">Run Key</th>
                <th class="px-5 py-3">Target URL</th>
                <th class="px-5 py-3">Runner</th>
                <th class="px-5 py-3">Status</th>
                <th class="px-5 py-3">Passed / Total</th>
                <th class="px-5 py-3">Duration</th>
                <th class="px-5 py-3">Executed At</th>
                <th class="px-5 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60" *ngIf="executions.length; else emptyTpl">
              <tr
                *ngFor="let ex of executions"
                class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                (click)="openDetail(ex)"
              >
                <td class="px-5 py-3.5 font-mono font-bold text-blue-600 dark:text-blue-400 whitespace-nowrap">
                  {{ ex.execution_key }}
                </td>
                <td class="px-5 py-3.5 font-mono text-[11px] text-slate-600 dark:text-slate-300 truncate max-w-xs">
                  {{ ex.base_url || 'http://localhost:4200' }}
                </td>
                <td class="px-5 py-3.5 text-slate-700 dark:text-slate-300 font-semibold capitalize whitespace-nowrap">
                  {{ ex.runner_type }} ({{ ex.browser }})
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span
                    class="px-2.5 py-0.5 rounded-full text-[10px] font-bold"
                    [ngClass]="{
                      'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800': ex.failed_tests === 0,
                      'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800': ex.failed_tests > 0
                    }"
                  >
                    {{ ex.failed_tests === 0 ? 'Passed' : 'Defects Found' }}
                  </span>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span class="font-bold text-emerald-600 dark:text-emerald-400">{{ ex.passed_tests }}</span>
                  <span class="text-slate-400"> / </span>
                  <span class="font-bold text-slate-800 dark:text-slate-200">{{ ex.total_tests }}</span>
                </td>
                <td class="px-5 py-3.5 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                  {{ ex.execution_duration_seconds | number:'1.1-2' }}s
                </td>
                <td class="px-5 py-3.5 text-slate-400 dark:text-slate-500 whitespace-nowrap text-[11px]">
                  {{ ex.created_at | date:'medium' }}
                </td>
                <td class="px-5 py-3.5 text-right whitespace-nowrap">
                  <button class="px-2.5 py-1 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/60 rounded-lg">
                    View Results →
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ng-template #emptyTpl>
          <div class="p-12 text-center text-slate-400 dark:text-slate-500 text-xs">
            No test execution history recorded for this project yet.
          </div>
        </ng-template>
      </div>

      <!-- Detail Modal -->
      <div
        *ngIf="selectedExecution"
        class="fixed inset-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      >
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[85vh] overflow-y-auto space-y-4">
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <span class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">{{ selectedExecution.execution_key }}</span>
              <h3 class="font-bold text-slate-900 dark:text-white text-sm mt-0.5">Execution Details</h3>
            </div>
            <button (click)="selectedExecution = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <app-icon name="x" size="18"></app-icon>
            </button>
          </div>

          <div class="grid grid-cols-3 gap-3 p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 text-center">
            <div>
              <div class="text-[10px] text-slate-400">Passed</div>
              <div class="text-lg font-bold text-emerald-600 dark:text-emerald-400">{{ selectedExecution.passed_tests }}</div>
            </div>
            <div>
              <div class="text-[10px] text-slate-400">Failed</div>
              <div class="text-lg font-bold text-rose-600 dark:text-rose-400">{{ selectedExecution.failed_tests }}</div>
            </div>
            <div>
              <div class="text-[10px] text-slate-400">Duration</div>
              <div class="text-lg font-bold text-slate-800 dark:text-slate-200">{{ selectedExecution.execution_duration_seconds | number:'1.1-2' }}s</div>
            </div>
          </div>

          <!-- Individual Results -->
          <div class="space-y-3" *ngIf="selectedExecution.results?.length; else noResTpl">
            <h4 class="font-bold text-xs text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px]">Test Suite Assertions</h4>
            <div
              *ngFor="let r of selectedExecution.results"
              class="p-3 rounded-xl border space-y-1.5"
              [ngClass]="r.status === 'Passed' ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20' : 'border-rose-200 dark:border-rose-800 bg-rose-50/40 dark:bg-rose-950/20'"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-xs text-slate-900 dark:text-white">{{ r.test_title }}</span>
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                  [ngClass]="r.status === 'Passed' ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-300' : 'bg-rose-100 dark:bg-rose-900 text-rose-800 dark:text-rose-300'"
                >
                  {{ r.status }}
                </span>
              </div>

              <div *ngIf="r.error_message" class="text-[11px] font-mono text-rose-700 dark:text-rose-300 bg-white dark:bg-slate-950 p-2.5 rounded-lg border border-rose-100 dark:border-rose-900/60 whitespace-pre-wrap">
                {{ r.error_message }}
              </div>

              <div *ngIf="r.suggested_fix" class="text-[11px] text-slate-600 dark:text-slate-400">
                <span class="font-semibold text-slate-700 dark:text-slate-300">AI Suggested Fix:</span> {{ r.suggested_fix }}
              </div>
            </div>
          </div>

          <ng-template #noResTpl>
            <div class="py-4 text-center text-xs text-slate-400">
              No granular assertion results logged.
            </div>
          </ng-template>
        </div>
      </div>
    </div>
  `,
})
export class ExecutionsComponent implements OnInit {
  private api = inject(ApiService);

  projects: Project[] = [];
  selectedProjectId = '';
  executions: TestExecution[] = [];
  selectedExecution: TestExecution | null = null;

  ngOnInit() {
    this.api.getProjects().subscribe({
      next: (res) => {
        this.projects = res;
        if (this.projects.length) {
          this.selectedProjectId = this.projects[0].id;
          this.loadExecutions();
        }
      },
    });
  }

  loadExecutions() {
    if (!this.selectedProjectId) return;
    this.api.getExecutions(this.selectedProjectId).subscribe({
      next: (res) => (this.executions = res),
    });
  }

  openDetail(ex: TestExecution) {
    this.api.getExecution(ex.id).subscribe({
      next: (full) => (this.selectedExecution = full),
      error: () => (this.selectedExecution = ex),
    });
  }
}
