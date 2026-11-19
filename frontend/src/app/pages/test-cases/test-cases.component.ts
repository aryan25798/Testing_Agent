import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project, TestCase } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-test-cases',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Test Cases Explorer</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Review, approve, and inspect autonomous step-by-step test cases.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <label class="text-xs font-bold text-slate-600 dark:text-slate-300">Project:</label>
          <select
            [(ngModel)]="selectedProjectId"
            (change)="loadTestCases()"
            class="px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 shadow-sm focus:border-blue-500 outline-none"
          >
            <option *ngFor="let p of projects" [value]="p.id">
              {{ p.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Filters & Search Toolbar -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div class="relative flex-1 max-w-md">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <app-icon name="search" size="14"></app-icon>
          </span>
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (input)="applyFilters()"
            placeholder="Search test case key, title, or objective..."
            class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 outline-none"
          />
        </div>

        <div class="flex items-center gap-2.5 flex-wrap">
          <select
            [(ngModel)]="selectedPriority"
            (change)="applyFilters()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <select
            [(ngModel)]="selectedType"
            (change)="applyFilters()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
          >
            <option value="">All Types</option>
            <option value="Functional">Functional</option>
            <option value="Boundary">Boundary</option>
            <option value="Security">Security</option>
            <option value="Negative">Negative</option>
          </select>
        </div>
      </div>

      <!-- Test Cases Table -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-subtle overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200/80 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold text-[10px]">
              <tr>
                <th class="px-5 py-3">Key</th>
                <th class="px-5 py-3">Title & Objective</th>
                <th class="px-5 py-3">Type</th>
                <th class="px-5 py-3">Priority</th>
                <th class="px-5 py-3">Automated</th>
                <th class="px-5 py-3">Status</th>
                <th class="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60" *ngIf="filteredTestCases.length; else emptyTpl">
              <tr
                *ngFor="let tc of filteredTestCases"
                class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                (click)="openDetail(tc)"
              >
                <td class="px-5 py-3.5 font-mono font-bold text-blue-600 dark:text-blue-400 whitespace-nowrap">
                  {{ tc.test_case_key }}
                </td>
                <td class="px-5 py-3.5 max-w-sm">
                  <div class="font-bold text-slate-900 dark:text-white leading-snug">{{ tc.title }}</div>
                  <div class="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1 mt-0.5">{{ tc.objective }}</div>
                </td>
                <td class="px-5 py-3.5 text-slate-600 dark:text-slate-300 whitespace-nowrap">
                  {{ tc.test_type }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                    [ngClass]="{
                      'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800': tc.priority === 'Critical',
                      'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800': tc.priority === 'High',
                      'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800': tc.priority === 'Medium',
                      'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400': tc.priority === 'Low'
                    }"
                  >
                    {{ tc.priority }}
                  </span>
                </td>
                <td class="px-5 py-3.5 text-slate-600 dark:text-slate-300 whitespace-nowrap">
                  <span class="inline-flex items-center gap-1 font-semibold text-emerald-600 dark:text-emerald-400" *ngIf="tc.automation_suitability === 'Yes'">
                    <app-icon name="check-circle-2" size="13"></app-icon> Playwright
                  </span>
                  <span class="text-slate-400" *ngIf="tc.automation_suitability !== 'Yes'">
                    Manual
                  </span>
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                    [ngClass]="tc.is_approved ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'"
                  >
                    {{ tc.is_approved ? 'Approved' : 'Draft' }}
                  </span>
                </td>
                <td class="px-5 py-3.5 text-right whitespace-nowrap" (click)="$event.stopPropagation()">
                  <div class="flex items-center justify-end gap-1.5">
                    <button
                      *ngIf="!tc.is_approved"
                      (click)="approve(tc)"
                      class="px-2.5 py-1 text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 rounded-lg transition-colors"
                      title="Approve test case"
                    >
                      Approve
                    </button>
                    <button
                      (click)="deleteCase(tc)"
                      class="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                      title="Delete test case"
                    >
                      <app-icon name="trash-2" size="14"></app-icon>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ng-template #emptyTpl>
          <div class="p-12 text-center text-slate-400 dark:text-slate-500 text-xs">
            No test cases found for this project matching your criteria.
          </div>
        </ng-template>
      </div>

      <!-- Detail Slide-over Drawer -->
      <div
        *ngIf="selectedCase"
        class="fixed inset-0 z-50 bg-slate-900/50 dark:bg-slate-950/70 backdrop-blur-sm flex justify-end transition-opacity"
        (click)="selectedCase = null"
      >
        <div
          class="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl p-6 overflow-y-auto space-y-5 border-l border-slate-200 dark:border-slate-800"
          (click)="$event.stopPropagation()"
        >
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <span class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">{{ selectedCase.test_case_key }}</span>
              <h2 class="text-base font-bold text-slate-900 dark:text-white leading-tight mt-0.5">{{ selectedCase.title }}</h2>
            </div>
            <button (click)="selectedCase = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <app-icon name="x" size="18"></app-icon>
            </button>
          </div>

          <div class="space-y-4 text-xs">
            <div>
              <h4 class="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px]">Objective</h4>
              <p class="text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">{{ selectedCase.objective }}</p>
            </div>

            <div *ngIf="selectedCase.preconditions">
              <h4 class="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px]">Preconditions</h4>
              <p class="text-slate-600 dark:text-slate-400 mt-1 font-mono bg-slate-50 dark:bg-slate-800 p-2.5 rounded-xl border border-slate-100 dark:border-slate-700">{{ selectedCase.preconditions }}</p>
            </div>

            <!-- Execution Steps -->
            <div *ngIf="selectedCase.execution_steps?.length">
              <h4 class="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px] mb-2">Step-by-Step Actions</h4>
              <div class="space-y-2">
                <div
                  *ngFor="let s of selectedCase.execution_steps"
                  class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700"
                >
                  <div class="font-bold text-slate-800 dark:text-slate-200">Step {{ s.step_number }}: {{ s.action }}</div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Expected: {{ s.expected }}</div>
                </div>
              </div>
            </div>

            <div>
              <h4 class="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px]">Expected Results</h4>
              <p class="mt-1 bg-emerald-50/60 dark:bg-emerald-950/40 p-2.5 rounded-xl border border-emerald-100 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 font-medium">
                {{ selectedCase.expected_results }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class TestCasesComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  projects: Project[] = [];
  selectedProjectId = '';
  testCases: TestCase[] = [];
  filteredTestCases: TestCase[] = [];
  selectedCase: TestCase | null = null;

  searchQuery = '';
  selectedPriority = '';
  selectedType = '';

  ngOnInit() {
    this.api.getProjects().subscribe({
      next: (res) => {
        this.projects = res;
        this.route.queryParams.subscribe((params) => {
          if (params['project_id']) {
            this.selectedProjectId = params['project_id'];
          } else if (this.projects.length) {
            this.selectedProjectId = this.projects[0].id;
          }
          this.loadTestCases();
        });
      },
    });
  }

  loadTestCases() {
    if (!this.selectedProjectId) return;
    this.api.getTestCases(this.selectedProjectId).subscribe({
      next: (res) => {
        this.testCases = res;
        this.applyFilters();
      },
    });
  }

  applyFilters() {
    this.filteredTestCases = this.testCases.filter((tc) => {
      const matchSearch =
        !this.searchQuery ||
        tc.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        tc.test_case_key.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        tc.objective.toLowerCase().includes(this.searchQuery.toLowerCase());

      const matchPriority = !this.selectedPriority || tc.priority === this.selectedPriority;
      const matchType = !this.selectedType || tc.test_type === this.selectedType;

      return matchSearch && matchPriority && matchType;
    });
  }

  openDetail(tc: TestCase) {
    this.selectedCase = tc;
  }

  approve(tc: TestCase) {
    this.api.approveTestCase(tc.id).subscribe({
      next: () => {
        tc.is_approved = true;
        tc.status = 'Approved';
      },
    });
  }

  deleteCase(tc: TestCase) {
    if (confirm(`Delete test case ${tc.test_case_key}?`)) {
      this.api.deleteTestCase(tc.id).subscribe({
        next: () => this.loadTestCases(),
      });
    }
  }
}
