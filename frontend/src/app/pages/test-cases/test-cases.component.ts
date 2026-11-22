import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project, TestCase, PaginatedResponse } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';
import { PaginationComponent } from '../../shared/components/pagination.component';
import { ConfirmationModalComponent } from '../../shared/components/confirmation-modal.component';
import { BulkToolbarComponent } from '../../shared/components/bulk-toolbar.component';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';
import { LoadingSkeletonComponent } from '../../shared/components/loading-skeleton.component';

@Component({
  selector: 'app-test-cases',
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
              Test Cases Explorer
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              {{ totalCases }} Total
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            Review, approve, bulk-manage, and inspect autonomous step-by-step test cases.
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
            placeholder="Search test case key, title, or objective..."
            class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        <!-- Filter Dropdowns -->
        <div class="flex items-center gap-2.5 flex-wrap">
          <select
            [(ngModel)]="selectedPriority"
            (change)="onFilterChange()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <select
            [(ngModel)]="selectedType"
            (change)="onFilterChange()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Types</option>
            <option value="Functional">Functional</option>
            <option value="Boundary">Boundary</option>
            <option value="Security">Security</option>
            <option value="Negative">Negative</option>
          </select>

          <select
            [(ngModel)]="selectedApprovalStatus"
            (change)="onFilterChange()"
            class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="approved">Approved</option>
            <option value="draft">Draft (Unapproved)</option>
          </select>
        </div>
      </div>

      <!-- Loading State Skeleton -->
      <app-loading-skeleton *ngIf="isLoading" type="table" [count]="6"></app-loading-skeleton>

      <!-- 3. Test Cases Table -->
      <div *ngIf="!isLoading">
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-subtle overflow-hidden" *ngIf="testCases.length; else emptyTpl">
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
                  <th class="px-5 py-3">Key</th>
                  <th class="px-5 py-3">Title & Objective</th>
                  <th class="px-5 py-3">Type</th>
                  <th class="px-5 py-3">Priority</th>
                  <th class="px-5 py-3">Automated</th>
                  <th class="px-5 py-3">Status</th>
                  <th class="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60">
                <tr
                  *ngFor="let tc of testCases"
                  class="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                  [ngClass]="{
                    'bg-blue-50/20 dark:bg-blue-950/20': isSelected(tc.id)
                  }"
                  (click)="openDetail(tc)"
                >
                  <td class="px-4 py-3.5 text-center" (click)="$event.stopPropagation()">
                    <input
                      type="checkbox"
                      [checked]="isSelected(tc.id)"
                      (change)="toggleSelect(tc.id)"
                      class="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer"
                    />
                  </td>
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
                        class="px-2.5 py-1 text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 rounded-lg transition-colors cursor-pointer"
                        title="Approve test case"
                      >
                        Approve
                      </button>
                      <button
                        (click)="promptDeleteCase(tc)"
                        class="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
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
        </div>

        <!-- Empty State -->
        <ng-template #emptyTpl>
          <app-empty-state
            icon="clipboard"
            [title]="searchQuery || selectedPriority || selectedType ? 'No Matching Test Cases' : 'No Test Cases Found'"
            [description]="searchQuery || selectedPriority || selectedType ? 'Try clearing your filters or search keywords.' : 'Run a 6-agent workflow to autonomously generate test cases for this project.'"
            [secondaryActionText]="searchQuery || selectedPriority || selectedType ? 'Reset Filters' : undefined"
            (secondaryAction)="resetFilters()"
          ></app-empty-state>
        </ng-template>

        <!-- 4. Global Server-Side Pagination Bar -->
        <div class="mt-6">
          <app-pagination
            [currentPage]="currentPage"
            [pageSize]="pageSize"
            [totalItems]="totalCases"
            [pageSizeOptions]="[10, 25, 50, 100]"
            [isLoading]="isLoading"
            (pageChange)="onPageChange($event)"
            (pageSizeChange)="onPageSizeChange($event)"
          ></app-pagination>
        </div>
      </div>

      <!-- 5. Floating Bulk Selection Toolbar -->
      <app-bulk-toolbar
        [selectedCount]="selectedIds.size"
        [totalCount]="testCases.length"
        [isAllSelected]="isCurrentPageAllSelected"
        [itemLabel]="'test case'"
        [showApprove]="true"
        [showExport]="true"
        [showDelete]="true"
        [isLoading]="isBulkProcessing"
        (selectAll)="toggleSelectAll()"
        (clearSelection)="clearSelection()"
        (approveSelected)="executeBulkApprove()"
        (exportSelected)="exportSelectedToCsv()"
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

      <!-- 7. Detail Slide-over Drawer -->
      <div
        *ngIf="selectedCase"
        class="fixed inset-0 !m-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex justify-end transition-opacity"
        (click)="selectedCase = null"
      >
        <div
          class="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl p-4 sm:p-6 overflow-y-auto space-y-5 border-l border-slate-200 dark:border-slate-800"
          (click)="$event.stopPropagation()"
        >
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <span class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">{{ selectedCase.test_case_key }}</span>
              <h2 class="text-base font-bold text-slate-900 dark:text-white leading-tight mt-0.5">{{ selectedCase.title }}</h2>
            </div>
            <button (click)="selectedCase = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
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
  totalCases = 0;
  currentPage = 1;
  pageSize = 10;
  isLoading = false;

  // Search & Filter State
  searchQuery = '';
  selectedPriority = '';
  selectedType = '';
  selectedApprovalStatus = '';

  // Selection & Bulk State
  selectedIds = new Set<string>();
  isBulkProcessing = false;
  selectedCase: TestCase | null = null;

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
          this.loadTestCases();
        });
      },
      error: (err) => console.error(err),
    });
  }

  get isCurrentPageAllSelected(): boolean {
    if (this.testCases.length === 0) return false;
    return this.testCases.every((tc) => this.selectedIds.has(tc.id));
  }

  loadTestCases() {
    if (!this.selectedProjectId) return;
    this.isLoading = true;

    let isApprovedParam: boolean | undefined = undefined;
    if (this.selectedApprovalStatus === 'approved') isApprovedParam = true;
    else if (this.selectedApprovalStatus === 'draft') isApprovedParam = false;

    this.api
      .getTestCasesPaginated(this.selectedProjectId, {
        priority: this.selectedPriority || undefined,
        test_type: this.selectedType || undefined,
        is_approved: isApprovedParam,
        search: this.searchQuery || undefined,
        page: this.currentPage,
        page_size: this.pageSize,
        sort_by: 'created_at',
        sort_order: 'asc',
      })
      .subscribe({
        next: (res: PaginatedResponse<TestCase>) => {
          this.testCases = res.items || [];
          this.totalCases = res.total || 0;
          this.isLoading = false;

          if (this.currentPage > res.total_pages && res.total_pages > 0) {
            this.currentPage = res.total_pages;
            this.loadTestCases();
          }
        },
        error: (err) => {
          console.error(err);
          this.isLoading = false;
          this.showToast('Failed to load test cases.', 'error');
        },
      });
  }

  onProjectChange() {
    this.currentPage = 1;
    this.selectedIds.clear();
    this.loadTestCases();
  }

  onFilterChange() {
    this.currentPage = 1;
    this.loadTestCases();
  }

  resetFilters() {
    this.searchQuery = '';
    this.selectedPriority = '';
    this.selectedType = '';
    this.selectedApprovalStatus = '';
    this.currentPage = 1;
    this.loadTestCases();
  }

  onPageChange(page: number) {
    this.currentPage = page;
    this.loadTestCases();
  }

  onPageSizeChange(size: number) {
    this.pageSize = size;
    this.currentPage = 1;
    this.loadTestCases();
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
      this.testCases.forEach((tc) => this.selectedIds.delete(tc.id));
    } else {
      this.testCases.forEach((tc) => this.selectedIds.add(tc.id));
    }
  }

  clearSelection() {
    this.selectedIds.clear();
  }

  openDetail(tc: TestCase) {
    this.selectedCase = tc;
  }

  // --- Single & Bulk Approve ---
  approve(tc: TestCase) {
    this.api.approveTestCase(tc.id).subscribe({
      next: () => {
        tc.is_approved = true;
        tc.status = 'Approved';
        this.showToast(`Test case ${tc.test_case_key} approved.`, 'success');
      },
      error: () => this.showToast('Approval failed.', 'error'),
    });
  }

  executeBulkApprove() {
    if (this.selectedIds.size === 0) return;
    this.isBulkProcessing = true;
    const ids = Array.from(this.selectedIds);

    this.api.bulkApproveTestCases(ids).subscribe({
      next: (res) => {
        this.isBulkProcessing = false;
        this.clearSelection();
        this.showToast(res.message, 'success');
        this.loadTestCases();
      },
      error: () => {
        this.isBulkProcessing = false;
        this.showToast('Bulk approval failed.', 'error');
      },
    });
  }

  // --- Export to CSV ---
  exportSelectedToCsv() {
    if (this.selectedIds.size === 0) return;
    const selected = this.testCases.filter((tc) => this.selectedIds.has(tc.id));
    if (selected.length === 0) return;

    const headers = ['Key', 'Title', 'Objective', 'Type', 'Priority', 'Status', 'Preconditions', 'Expected Results'];
    const rows = selected.map((tc) => [
      `"${tc.test_case_key}"`,
      `"${(tc.title || '').replace(/"/g, '""')}"`,
      `"${(tc.objective || '').replace(/"/g, '""')}"`,
      `"${tc.test_type}"`,
      `"${tc.priority}"`,
      `"${tc.is_approved ? 'Approved' : 'Draft'}"`,
      `"${(tc.preconditions || '').replace(/"/g, '""')}"`,
      `"${(tc.expected_results || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `test-cases-export-${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    this.showToast(`Exported ${selected.length} test cases to CSV.`, 'success');
  }

  // --- Single & Bulk Delete ---
  promptDeleteCase(tc: TestCase) {
    this.pendingDeleteIds = [tc.id];
    this.modalTitle = `Delete Test Case "${tc.test_case_key}"?`;
    this.modalMessage = `Are you sure you want to delete test case ${tc.title}?`;
    this.modalWarning = `This action cannot be undone.`;
    this.modalItemNames = [tc.test_case_key];
    this.showDeleteModal = true;
  }

  promptBulkDelete() {
    if (this.selectedIds.size === 0) return;
    this.pendingDeleteIds = Array.from(this.selectedIds);
    const count = this.pendingDeleteIds.length;
    const keys = this.testCases.filter((tc) => this.selectedIds.has(tc.id)).map((tc) => tc.test_case_key);

    this.modalTitle = `Delete ${count} Selected Test Case${count > 1 ? 's' : ''}?`;
    this.modalMessage = `Are you sure you want to delete ${count} test case${count > 1 ? 's' : ''}?`;
    this.modalWarning = `Permanently removes selected test cases from this project.`;
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

    this.api.bulkDeleteTestCases(this.pendingDeleteIds).subscribe({
      next: (res) => {
        this.isBulkProcessing = false;
        this.closeDeleteModal();
        this.clearSelection();
        this.showToast(res.message, 'success');
        this.loadTestCases();
      },
      error: () => {
        this.isBulkProcessing = false;
        this.closeDeleteModal();
        this.showToast('Failed to delete test cases.', 'error');
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
