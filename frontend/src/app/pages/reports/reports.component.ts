import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Project } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Consolidated QA Reports</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Audit-ready test execution reports, coverage metrics, and executive summaries.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2">
            <label class="text-xs font-bold text-slate-600 dark:text-slate-300">Project:</label>
            <select
              [(ngModel)]="selectedProjectId"
              (change)="loadReport()"
              class="px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-sm focus:border-blue-500 outline-none"
            >
              <option *ngFor="let p of projects" [value]="p.id">
                {{ p.name }}
              </option>
            </select>
          </div>

          <!-- Export Buttons -->
          <a
            [href]="api.getPdfReportUrl(selectedProjectId)"
            target="_blank"
            class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl text-xs shadow-sm transition-all"
          >
            <app-icon name="file-text" size="14" class="text-white"></app-icon>
            <span>Download PDF</span>
          </a>

          <a
            [href]="api.getCsvReportUrl(selectedProjectId)"
            class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs shadow-sm transition-all"
            download
          >
            <app-icon name="download" size="14" class="text-white"></app-icon>
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      <!-- Report Card -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-6 transition-colors" *ngIf="reportData; else noReportTpl">
        <!-- KPI Row -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
            <div class="text-xs text-slate-500 dark:text-slate-400">Total Requirements</div>
            <div class="text-2xl font-black text-slate-900 dark:text-white mt-1">{{ reportData.total_requirements || 0 }}</div>
          </div>
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
            <div class="text-xs text-slate-500 dark:text-slate-400">Test Cases Designed</div>
            <div class="text-2xl font-black text-slate-900 dark:text-white mt-1">{{ reportData.total_test_cases || 0 }}</div>
          </div>
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
            <div class="text-xs text-slate-500 dark:text-slate-400">Tests Evaluated</div>
            <div class="text-2xl font-black text-slate-900 dark:text-white mt-1">{{ reportData.total_tests_evaluated || 0 }}</div>
          </div>
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
            <div class="text-xs text-slate-500 dark:text-slate-400">Pass Rate</div>
            <div class="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{{ reportData.pass_rate_percentage || 0 }}%</div>
          </div>
        </div>

        <!-- Markdown Executive Report -->
        <div class="border-t border-slate-100 dark:border-slate-800 pt-5">
          <div class="flex items-center gap-2 mb-3">
            <app-icon name="file-text" size="16" class="text-blue-600 dark:text-blue-400"></app-icon>
            <h3 class="font-bold text-slate-900 dark:text-white text-sm">Executive Summary & Audit Findings</h3>
          </div>
          <div class="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 font-sans text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
            {{ reportData.markdown_report }}
          </div>
        </div>
      </div>

      <ng-template #noReportTpl>
        <div class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 transition-colors">
          <app-icon name="bar-chart-3" size="40" class="text-slate-400 mx-auto mb-3"></app-icon>
          <h3 class="font-bold text-slate-800 dark:text-slate-200 text-base">No Report Available</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Select a project with test runs to generate an executive report.</p>
        </div>
      </ng-template>
    </div>
  `,
})
export class ReportsComponent implements OnInit {
  api = inject(ApiService);

  projects: Project[] = [];
  selectedProjectId = '';
  reportData: any = null;

  ngOnInit() {
    this.api.getProjects().subscribe({
      next: (res) => {
        this.projects = res;
        if (this.projects.length) {
          this.selectedProjectId = this.projects[0].id;
          this.loadReport();
        }
      },
    });
  }

  loadReport() {
    if (!this.selectedProjectId) return;
    this.api.getProjectReport(this.selectedProjectId).subscribe({
      next: (res) => (this.reportData = res),
      error: () => (this.reportData = null),
    });
  }
}
