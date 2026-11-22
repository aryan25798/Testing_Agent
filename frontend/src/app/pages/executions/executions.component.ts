import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project, TestExecution, PaginatedResponse } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';
import { PaginationComponent } from '../../shared/components/pagination.component';
import { ConfirmationModalComponent } from '../../shared/components/confirmation-modal.component';
import { BulkToolbarComponent } from '../../shared/components/bulk-toolbar.component';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';
import { LoadingSkeletonComponent } from '../../shared/components/loading-skeleton.component';

@Component({
  selector: 'app-executions',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IconComponent,
    PaginationComponent,
    ConfirmationModalComponent,
    BulkToolbarComponent,
    EmptyStateComponent,
    LoadingSkeletonComponent,
  ],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-16">
      <!-- 1. Header Banner -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 min-w-0">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2.5">
            <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight break-words min-w-0">
              Execution History & Evidence
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              {{ totalExecutions }} Runs
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            Real execution telemetry, Playwright browser test traces, failure triage, and CI/CD JUnit exports.
          </p>
        </div>

        <!-- Project Selector Dropdown -->
        <div class="flex items-center gap-2 sm:gap-3 shrink-0">
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
      </div>

      <!-- Feedback Toast Notification -->
      <div
        *ngIf="toastMessage"
        class="p-4 rounded-xl text-xs font-medium flex items-center justify-between shadow-lg transition-all animate-fadeIn"
        [ngClass]="toastType === 'success' ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400' : 'bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400'"
      >
        <div class="flex items-center gap-2.5">
          <app-icon [name]="toastType === 'success' ? 'check-circle-2' : 'alert-circle'" size="16"></app-icon>
          <span>{{ toastMessage }}</span>
        </div>
        <button (click)="toastMessage = null" class="p-1 hover:opacity-75">
          <app-icon name="x" size="14"></app-icon>
        </button>
      </div>

      <!-- 2. Search & Filters Toolbar -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-3">
        <!-- Search Input -->
        <div class="relative flex-1 max-w-md">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <app-icon name="search" size="14"></app-icon>
          </span>
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (ngModelChange)="onFilterChange()"
            placeholder="Search run key or target URL..."
            class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        <!-- Filter Dropdowns -->
        <div class="flex items-center gap-2.5 flex-wrap">
          <select
            [(ngModel)]="statusFilter"
            (change)="onFilterChange()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Outcomes</option>
            <option value="passed">Passed (0 Defects)</option>
            <option value="failed">Defects Found</option>
          </select>

          <select
            [(ngModel)]="runnerFilter"
            (change)="onFilterChange()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Runners</option>
            <option value="playwright">Playwright</option>
            <option value="selenium">Selenium</option>
          </select>
        </div>
      </div>

      <!-- Loading State Skeleton -->
      <app-loading-skeleton *ngIf="isLoading" type="table" [count]="6"></app-loading-skeleton>

      <!-- 3. Executions Table -->
      <div *ngIf="!isLoading">
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-subtle overflow-hidden" *ngIf="executions.length; else emptyTpl">
          <div class="overflow-x-auto w-full max-w-full">
            <table class="w-full text-left text-xs min-w-[760px]">
              <thead class="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200/80 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold text-[10px]">
                <tr>
                  <th class="px-4 py-3 w-10 text-center">
                    <input
                      type="checkbox"
                      [checked]="isCurrentPageAllSelected"
                      (change)="toggleSelectAll()"
                      class="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer"
                      title="Select all on current page"
                    />
                  </th>
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
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60">
                <tr
                  *ngFor="let ex of executions"
                  class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                  [ngClass]="{
                    'bg-blue-50/20 dark:bg-blue-950/20': isSelected(ex.id)
                  }"
                  (click)="openDetail(ex)"
                >
                  <td class="px-4 py-3.5 text-center" (click)="$event.stopPropagation()">
                    <input
                      type="checkbox"
                      [checked]="isSelected(ex.id)"
                      (change)="toggleSelect(ex.id)"
                      class="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer"
                    />
                  </td>
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
        </div>

        <!-- Empty State -->
        <ng-template #emptyTpl>
          <app-empty-state
            icon="play"
            [title]="searchQuery || statusFilter || runnerFilter ? 'No Matching Executions' : 'No Execution History'"
            [description]="searchQuery || statusFilter || runnerFilter ? 'Try clearing your filters or search keywords.' : 'Run a 6-agent workflow from the Workflows tab to execute browser test suites.'"
            [secondaryActionText]="searchQuery || statusFilter || runnerFilter ? 'Reset Filters' : undefined"
            (secondaryAction)="resetFilters()"
          ></app-empty-state>
        </ng-template>

        <!-- 4. Global Server-Side Pagination Bar -->
        <div class="mt-6">
          <app-pagination
            [currentPage]="currentPage"
            [pageSize]="pageSize"
            [totalItems]="totalExecutions"
            [pageSizeOptions]="[10, 20, 50, 100]"
            [isLoading]="isLoading"
            (pageChange)="onPageChange($event)"
            (pageSizeChange)="onPageSizeChange($event)"
          ></app-pagination>
        </div>
      </div>

      <!-- 5. Floating Bulk Selection Toolbar -->
      <app-bulk-toolbar
        [selectedCount]="selectedIds.size"
        [totalCount]="executions.length"
        [isAllSelected]="isCurrentPageAllSelected"
        [itemLabel]="'run'"
        [showDelete]="true"
        [isLoading]="isBulkProcessing"
        (selectAll)="toggleSelectAll()"
        (clearSelection)="clearSelection()"
        (deleteSelected)="promptBulkDelete()"
      ></app-bulk-toolbar>

      <!-- 6. Confirmation Modal -->
      <app-confirmation-modal
        [isOpen]="showDeleteModal"
        [title]="modalTitle"
        [message]="modalMessage"
        [warningText]="modalWarning"
        [itemsList]="modalItemNames"
        [confirmText]="'Confirm Delete'"
        [isDestructive]="true"
        [isLoading]="isBulkProcessing"
        (confirm)="executeConfirmedDelete()"
        (cancel)="closeDeleteModal()"
      ></app-confirmation-modal>

      <!-- 7. Execution Detail Modal -->
      <div
        *ngIf="selectedExecution"
        class="fixed inset-0 !m-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4"
      >
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full p-4 sm:p-6 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[85vh] overflow-y-auto space-y-4">
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <span class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">{{ selectedExecution.execution_key }}</span>
              <h3 class="font-bold text-slate-900 dark:text-white text-sm mt-0.5">Execution Details</h3>
            </div>
            <div class="flex items-center gap-2">
              <a
                [href]="downloadJunitXmlUrl(selectedExecution.id)"
                class="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors"
                download
              >
                <app-icon name="download" size="13"></app-icon>
                <span>Export JUnit XML</span>
              </a>
              <button (click)="selectedExecution = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
                <app-icon name="x" size="18"></app-icon>
              </button>
            </div>
          </div>

          <!-- Summary Badges -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <span class="text-slate-400 block text-[10px] uppercase font-bold">Total Tests</span>
              <span class="text-base font-bold text-slate-900 dark:text-white">{{ selectedExecution.total_tests }}</span>
            </div>
            <div class="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/40 border border-emerald-100 dark:border-emerald-800">
              <span class="text-emerald-600 dark:text-emerald-400 block text-[10px] uppercase font-bold">Passed</span>
              <span class="text-base font-bold text-emerald-700 dark:text-emerald-300">{{ selectedExecution.passed_tests }}</span>
            </div>
            <div class="p-3 rounded-xl bg-rose-50/50 dark:bg-rose-950/40 border border-rose-100 dark:border-rose-800">
              <span class="text-rose-600 dark:text-rose-400 block text-[10px] uppercase font-bold">Failed</span>
              <span class="text-base font-bold text-rose-700 dark:text-rose-300">{{ selectedExecution.failed_tests }}</span>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <span class="text-slate-400 block text-[10px] uppercase font-bold">Duration</span>
              <span class="text-base font-bold text-slate-900 dark:text-white">{{ selectedExecution.execution_duration_seconds | number:'1.1-2' }}s</span>
            </div>
          </div>

          <!-- Raw Execution Log Output -->
          <div *ngIf="selectedExecution.raw_log_output" class="space-y-1.5">
            <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Execution Console Log:</div>
            <pre class="p-3 bg-slate-950 text-emerald-400 font-mono text-[11px] rounded-xl overflow-x-auto max-h-60 border border-slate-800 whitespace-pre-wrap leading-relaxed">{{ selectedExecution.raw_log_output }}</pre>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class ExecutionsComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  projects: Project[] = [];
  selectedProjectId = '';
  executions: TestExecution[] = [];
  totalExecutions = 0;
  currentPage = 1;
  pageSize = 10;
  isLoading = false;

  // Search & Filter State
  searchQuery = '';
  statusFilter = '';
  runnerFilter = '';

  // Selection & Bulk State
  selectedIds = new Set<string>();
  isBulkProcessing = false;
  selectedExecution: TestExecution | null = null;

  // Confirmation Modal State
  showDeleteModal = false;
  modalTitle = '';
  modalMessage = '';
  modalWarning = '';
  modalItemNames: string[] = [];
  pendingDeleteIds: string[] = [];

  // Toast Notification State
  toastMessage: string | null = null;
  toastType: 'success' | 'error' = 'success';

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
          this.loadExecutions();
        });
      },
      error: (err) => console.error(err),
    });
  }

  get isCurrentPageAllSelected(): boolean {
    if (this.executions.length === 0) return false;
    return this.executions.every((ex) => this.selectedIds.has(ex.id));
  }

  loadExecutions() {
    if (!this.selectedProjectId) return;
    this.isLoading = true;

    this.api
      .getExecutionsPaginated(this.selectedProjectId, {
        page: this.currentPage,
        page_size: this.pageSize,
        search: this.searchQuery || undefined,
        runner_type: this.runnerFilter || undefined,
        status_filter: this.statusFilter || undefined,
      })
      .subscribe({
        next: (res: PaginatedResponse<TestExecution>) => {
          this.executions = res.items || [];
          this.totalExecutions = res.total || 0;
          this.isLoading = false;

          if (this.currentPage > res.total_pages && res.total_pages > 0) {
            this.currentPage = res.total_pages;
            this.loadExecutions();
          }
        },
        error: (err) => {
          console.error(err);
          this.isLoading = false;
          this.showToast('Failed to load execution history.', 'error');
        },
      });
  }

  onProjectChange() {
    this.currentPage = 1;
    this.selectedIds.clear();
    this.loadExecutions();
  }

  onFilterChange() {
    this.currentPage = 1;
    this.loadExecutions();
  }

  resetFilters() {
    this.searchQuery = '';
    this.statusFilter = '';
    this.runnerFilter = '';
    this.currentPage = 1;
    this.loadExecutions();
  }

  onPageChange(page: number) {
    this.currentPage = page;
    this.loadExecutions();
  }

  onPageSizeChange(size: number) {
    this.pageSize = size;
    this.currentPage = 1;
    this.loadExecutions();
  }

  // --- Selection Logic ---
  isSelected(id: string): boolean {
    return this.selectedIds.has(id);
  }

  toggleSelect(id: string) {
    if (this.selectedIds.has(id)) {
      this.selectedIds.delete(id);
    } else {
      this.selectedIds.add(id);
    }
  }

  toggleSelectAll() {
    if (this.isCurrentPageAllSelected) {
      this.executions.forEach((ex) => this.selectedIds.delete(ex.id));
    } else {
      this.executions.forEach((ex) => this.selectedIds.add(ex.id));
    }
  }

  clearSelection() {
    this.selectedIds.clear();
  }

  openDetail(ex: TestExecution) {
    this.selectedExecution = ex;
  }

  downloadJunitXmlUrl(executionId: string): string {
    return this.api.downloadJunitXmlUrl(executionId);
  }

  // --- Bulk Deletion ---
  promptBulkDelete() {
    if (this.selectedIds.size === 0) return;
    this.pendingDeleteIds = Array.from(this.selectedIds);
    const count = this.pendingDeleteIds.length;
    const keys = this.executions.filter((ex) => this.selectedIds.has(ex.id)).map((ex) => ex.execution_key);

    this.modalTitle = `Delete ${count} Selected Execution Run${count > 1 ? 's' : ''}?`;
    this.modalMessage = `Are you sure you want to permanently delete ${count} test execution record${count > 1 ? 's' : ''}?`;
    this.modalWarning = `Deleting runs removes telemetry, browser traces, and historical pass/fail records. This action cannot be reversed.`;
    this.modalItemNames = keys;
    this.showDeleteModal = true;
  }

  closeDeleteModal() {
    this.showDeleteModal = false;
    this.pendingDeleteIds = [];
  }

  executeConfirmedDelete() {
    if (this.pendingDeleteIds.length === 0) return;
    this.isBulkProcessing = true;

    this.api.bulkDeleteExecutions(this.pendingDeleteIds).subscribe({
      next: (res) => {
        this.isBulkProcessing = false;
        this.closeDeleteModal();
        this.clearSelection();
        this.showToast(res.message, 'success');
        this.loadExecutions();
      },
      error: () => {
        this.isBulkProcessing = false;
        this.closeDeleteModal();
        this.showToast('Failed to delete execution records.', 'error');
      },
    });
  }

  showToast(message: string, type: 'success' | 'error') {
    this.toastMessage = message;
    this.toastType = type;
    setTimeout(() => {
      if (this.toastMessage === message) {
        this.toastMessage = null;
      }
    }, 4500);
  }
}
