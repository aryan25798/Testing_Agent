import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project, PaginatedResponse } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';
import { PaginationComponent } from '../../shared/components/pagination.component';
import { ConfirmationModalComponent } from '../../shared/components/confirmation-modal.component';
import { BulkToolbarComponent } from '../../shared/components/bulk-toolbar.component';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';
import { LoadingSkeletonComponent } from '../../shared/components/loading-skeleton.component';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
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
              My Projects
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              {{ totalProjects }} Total
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            Manage your client and local applications under test, execution frameworks, and repository mappings.
          </p>
        </div>

        <button
          (click)="openModal()"
          class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all shadow-sm cursor-pointer shrink-0 self-start sm:self-auto hover:shadow-glow-blue"
        >
          <app-icon name="plus" size="14"></app-icon>
          <span>Create New Project</span>
        </button>
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

      <!-- 2. Search, Filter & Bulk Controls Toolbar -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-3">
        <!-- Search Input -->
        <div class="relative flex-1 max-w-md">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <app-icon name="search" size="14"></app-icon>
          </span>
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (ngModelChange)="onSearchChange()"
            placeholder="Search projects by name, description, or target URL..."
            class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        <!-- Filter & Sort Controls -->
        <div class="flex items-center gap-2.5 flex-wrap">
          <!-- Framework Filter -->
          <div class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span>Framework:</span>
            <select
              [(ngModel)]="selectedFramework"
              (change)="onFilterChange()"
              class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 outline-none cursor-pointer"
            >
              <option value="">All Frameworks</option>
              <option value="playwright">Playwright</option>
              <option value="selenium">Selenium</option>
            </select>
          </div>

          <!-- Sort Order -->
          <div class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span>Sort:</span>
            <select
              [(ngModel)]="sortBy"
              (change)="onSortChange()"
              class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 outline-none cursor-pointer"
            >
              <option value="created_at_desc">Newest First</option>
              <option value="created_at_asc">Oldest First</option>
              <option value="name_asc">Name (A-Z)</option>
              <option value="name_desc">Name (Z-A)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Loading State Skeleton -->
      <app-loading-skeleton *ngIf="isLoading" type="cards" [count]="6"></app-loading-skeleton>

      <!-- 3. Projects Grid -->
      <div *ngIf="!isLoading">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" *ngIf="projects.length; else noProjectsTpl">
          <div
            *ngFor="let p of projects"
            class="bg-white dark:bg-slate-900 rounded-2xl p-5 border shadow-subtle hover:shadow-card transition-all flex flex-col justify-between relative group"
            [ngClass]="{
              'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/15 dark:bg-blue-950/20': isSelected(p.id),
              'border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700': !isSelected(p.id)
            }"
          >
            <div>
              <!-- Card Top Row: Checkbox + Avatar + Framework Badge + Trash -->
              <div class="flex items-start justify-between gap-3 mb-3">
                <div class="flex items-center gap-3">
                  <!-- Project Selection Checkbox -->
                  <label class="relative flex items-center cursor-pointer p-0.5" (click)="$event.stopPropagation()">
                    <input
                      type="checkbox"
                      [checked]="isSelected(p.id)"
                      (change)="toggleSelect(p.id)"
                      class="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 dark:focus:ring-blue-600 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer transition-colors"
                      [attr.aria-label]="'Select project ' + p.name"
                    />
                  </label>

                  <!-- Project Avatar Icon -->
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 text-white font-bold text-sm flex items-center justify-center shadow-sm shrink-0">
                    {{ p.name.charAt(0).toUpperCase() }}
                  </div>
                </div>

                <div class="flex items-center gap-1.5">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 uppercase tracking-wider">
                    {{ p.framework }}
                  </span>
                  <button
                    (click)="promptDeleteProject(p)"
                    class="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors cursor-pointer"
                    title="Delete Project"
                  >
                    <app-icon name="trash-2" size="14"></app-icon>
                  </button>
                </div>
              </div>

              <!-- Project Name & Description -->
              <h3 class="font-bold text-slate-900 dark:text-white text-base leading-snug line-clamp-1" [title]="p.name">
                {{ p.name }}
              </h3>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 min-h-[32px]">
                {{ p.description || 'No description provided.' }}
              </p>

              <!-- Target URL & Git Repo Metadata -->
              <div class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 space-y-2 text-xs">
                <div class="flex items-center justify-between min-w-0 gap-2">
                  <span class="text-slate-400 shrink-0 font-medium">Target URL:</span>
                  <span
                    class="font-mono text-[11px] truncate max-w-[60%] text-blue-600 dark:text-blue-400 font-semibold"
                    [title]="p.base_url || 'http://localhost:4200'"
                  >
                    {{ p.base_url || 'http://localhost:4200' }}
                  </span>
                </div>
                <div class="flex items-center justify-between min-w-0 gap-2" *ngIf="p.git_repo_url">
                  <span class="text-slate-400 shrink-0 font-medium">Git Repo:</span>
                  <span
                    class="font-mono text-[11px] truncate max-w-[60%] text-slate-700 dark:text-slate-300"
                    [title]="p.git_repo_url"
                  >
                    {{ p.git_repo_url }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Card Footer: Created Date + Actions -->
            <div class="mt-5 pt-3.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <span class="text-[11px] text-slate-400 dark:text-slate-500 font-medium">
                {{ p.created_at | date:'shortDate' }}
              </span>
              <div class="flex items-center gap-2">
                <button
                  (click)="editProject(p)"
                  class="px-2.5 py-1 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Edit
                </button>
                <a
                  routerLink="/workflows"
                  [queryParams]="{ project_id: p.id }"
                  class="px-3 py-1 bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/60 rounded-lg text-xs font-bold transition-colors flex items-center gap-1"
                >
                  <span>Run Tests</span>
                  <app-icon name="arrow-right" size="12"></app-icon>
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State Component -->
        <ng-template #noProjectsTpl>
          <app-empty-state
            icon="folder"
            [title]="searchQuery || selectedFramework ? 'No Matching Projects' : 'No Projects Found'"
            [description]="searchQuery || selectedFramework ? 'Try modifying your search or framework filter to find projects.' : 'Get started by creating your first QA project under test.'"
            [actionText]="'+ Create New Project'"
            [secondaryActionText]="searchQuery || selectedFramework ? 'Reset Filters' : undefined"
            (action)="openModal()"
            (secondaryAction)="resetFilters()"
          ></app-empty-state>
        </ng-template>

        <!-- 4. Global Server-Side Pagination Bar -->
        <div class="mt-6">
          <app-pagination
            [currentPage]="currentPage"
            [pageSize]="pageSize"
            [totalItems]="totalProjects"
            [pageSizeOptions]="[6, 12, 24, 48]"
            [isLoading]="isLoading"
            (pageChange)="onPageChange($event)"
            (pageSizeChange)="onPageSizeChange($event)"
          ></app-pagination>
        </div>
      </div>

      <!-- 5. Floating Bulk Selection Toolbar -->
      <app-bulk-toolbar
        [selectedCount]="selectedIds.size"
        [totalCount]="projects.length"
        [isAllSelected]="isCurrentPageAllSelected"
        [itemLabel]="'project'"
        [showDelete]="true"
        [isLoading]="isBulkDeleting"
        (selectAll)="toggleSelectAll()"
        (clearSelection)="clearSelection()"
        (deleteSelected)="promptBulkDelete()"
      ></app-bulk-toolbar>

      <!-- 6. Professional Confirmation Modal for Single & Bulk Deletions -->
      <app-confirmation-modal
        [isOpen]="showDeleteModal"
        [title]="modalTitle"
        [message]="modalMessage"
        [warningText]="modalWarning"
        [itemsList]="modalItemNames"
        [confirmText]="'Confirm Delete'"
        [isDestructive]="true"
        [isLoading]="isBulkDeleting"
        (confirm)="executeConfirmedDelete()"
        (cancel)="closeDeleteModal()"
      ></app-confirmation-modal>

      <!-- 7. Create / Edit Project Modal -->
      <div
        *ngIf="showModal"
        class="fixed inset-0 !m-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4"
      >
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-5 sm:p-6 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-base font-bold text-slate-900 dark:text-white">
              {{ editingProjectId ? 'Edit Project' : 'Create New QA Project' }}
            </h2>
            <button (click)="closeModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
              <app-icon name="x" size="18"></app-icon>
            </button>
          </div>

          <form (ngSubmit)="saveProject()" class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Project Name *</label>
              <input
                type="text"
                [(ngModel)]="form.name"
                name="name"
                required
                placeholder="e.g. TrainMate Allocation System"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Description</label>
              <textarea
                [(ngModel)]="form.description"
                name="description"
                rows="2"
                placeholder="Brief summary of application features, login flows, or endpoints"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              ></textarea>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Testing Framework</label>
                <select
                  [(ngModel)]="form.framework"
                  name="framework"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                >
                  <option value="playwright">Playwright (Chromium)</option>
                  <option value="selenium">Selenium (WebDriver)</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Live Base URL *</label>
                <input
                  type="text"
                  [(ngModel)]="form.base_url"
                  name="base_url"
                  placeholder="e.g. http://localhost:4200"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">GitHub Repo URL</label>
                <input
                  type="text"
                  [(ngModel)]="form.git_repo_url"
                  name="git_repo_url"
                  placeholder="https://github.com/..."
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                />
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Git Branch</label>
                <input
                  type="text"
                  [(ngModel)]="form.git_branch"
                  name="git_branch"
                  placeholder="main"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                />
              </div>
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                (click)="closeModal()"
                class="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                [disabled]="!form.name"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm disabled:opacity-50 cursor-pointer"
              >
                {{ editingProjectId ? 'Save Changes' : 'Create Project' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
})
export class ProjectsComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  projects: Project[] = [];
  totalProjects = 0;
  currentPage = 1;
  pageSize = 6;
  isLoading = false;

  // Search & Filter State
  searchQuery = '';
  selectedFramework = '';
  sortBy = 'created_at_desc';

  // Selection & Bulk State
  selectedIds = new Set<string>();
  isBulkDeleting = false;

  // Confirmation Modal State
  showDeleteModal = false;
  modalTitle = '';
  modalMessage = '';
  modalWarning = '';
  modalItemNames: string[] = [];
  pendingDeleteIds: string[] = [];

  // Toast State
  toastMessage: string | null = null;
  toastType: 'success' | 'error' = 'success';

  // Create / Edit Modal State
  showModal = false;
  editingProjectId: string | null = null;
  form: Partial<Project> = {
    name: '',
    description: '',
    framework: 'playwright',
    base_url: 'http://localhost:4200',
    git_repo_url: '',
    git_branch: 'main',
  };

  ngOnInit() {
    this.loadProjects();
    this.route.queryParams.subscribe((params) => {
      if (params['action'] === 'new') {
        this.openModal();
      }
    });
  }

  get isCurrentPageAllSelected(): boolean {
    if (this.projects.length === 0) return false;
    return this.projects.every((p) => this.selectedIds.has(p.id));
  }

  loadProjects() {
    this.isLoading = true;
    const [sortCol, sortOrder] = this.sortBy.split('_');

    this.api
      .getProjectsPaginated({
        page: this.currentPage,
        page_size: this.pageSize,
        search: this.searchQuery,
        framework: this.selectedFramework,
        sort_by: sortCol === 'name' ? 'name' : 'created_at',
        sort_order: sortOrder || 'desc',
      })
      .subscribe({
        next: (res: PaginatedResponse<Project>) => {
          this.projects = res.items || [];
          this.totalProjects = res.total || 0;
          this.isLoading = false;

          // If current page is beyond total pages after deletion, adjust
          if (this.currentPage > res.total_pages && res.total_pages > 0) {
            this.currentPage = res.total_pages;
            this.loadProjects();
          }
        },
        error: (err) => {
          console.error(err);
          this.isLoading = false;
          this.showToast('Failed to load projects from server.', 'error');
        },
      });
  }

  onSearchChange() {
    this.currentPage = 1;
    this.loadProjects();
  }

  onFilterChange() {
    this.currentPage = 1;
    this.loadProjects();
  }

  onSortChange() {
    this.currentPage = 1;
    this.loadProjects();
  }

  resetFilters() {
    this.searchQuery = '';
    this.selectedFramework = '';
    this.sortBy = 'created_at_desc';
    this.currentPage = 1;
    this.loadProjects();
  }

  onPageChange(page: number) {
    this.currentPage = page;
    this.loadProjects();
  }

  onPageSizeChange(size: number) {
    this.pageSize = size;
    this.currentPage = 1;
    this.loadProjects();
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
      // Deselect all on current page
      this.projects.forEach((p) => this.selectedIds.delete(p.id));
    } else {
      // Select all on current page
      this.projects.forEach((p) => this.selectedIds.add(p.id));
    }
  }

  clearSelection() {
    this.selectedIds.clear();
  }

  // --- Deletion Flow (Single & Bulk) ---
  promptDeleteProject(p: Project) {
    this.pendingDeleteIds = [p.id];
    this.modalTitle = `Delete Project "${p.name}"?`;
    this.modalMessage = `Are you sure you want to delete this project?`;
    this.modalWarning = `Deleting will permanently remove all associated requirements, test scenarios, test cases, automation scripts, execution history, and generated reports.`;
    this.modalItemNames = [p.name];
    this.showDeleteModal = true;
  }

  promptBulkDelete() {
    if (this.selectedIds.size === 0) return;
    this.pendingDeleteIds = Array.from(this.selectedIds);
    const count = this.pendingDeleteIds.length;
    const names = this.projects.filter((p) => this.selectedIds.has(p.id)).map((p) => p.name);

    this.modalTitle = `Delete ${count} Selected Project${count > 1 ? 's' : ''}?`;
    this.modalMessage = `You are about to permanently delete ${count} project${count > 1 ? 's' : ''}.`;
    this.modalWarning = `This operation will also cascade and permanently remove all associated test cases, scenarios, execution runs, and reports. This action cannot be undone.`;
    this.modalItemNames = names.length ? names : this.pendingDeleteIds;
    this.showDeleteModal = true;
  }

  closeDeleteModal() {
    this.showDeleteModal = false;
    this.pendingDeleteIds = [];
  }

  executeConfirmedDelete() {
    if (this.pendingDeleteIds.length === 0) return;
    this.isBulkDeleting = true;

    this.api.bulkDeleteProjects(this.pendingDeleteIds).subscribe({
      next: (res) => {
        this.isBulkDeleting = false;
        this.closeDeleteModal();
        this.selectedIds.clear();
        if (res.failed_ids && res.failed_ids.length > 0) {
          this.showToast(res.message, 'error');
        } else {
          this.showToast(res.message || `Successfully deleted projects.`, 'success');
        }
        this.loadProjects();
      },
      error: (err) => {
        this.isBulkDeleting = false;
        this.closeDeleteModal();
        const detail = err?.error?.detail || err?.message || 'Failed to delete selected projects.';
        this.showToast(detail, 'error');
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

  // --- Create / Edit Modal Logic ---
  openModal() {
    this.editingProjectId = null;
    this.form = {
      name: '',
      description: '',
      framework: 'playwright',
      base_url: 'http://localhost:4200',
      git_repo_url: '',
      git_branch: 'main',
    };
    this.showModal = true;
  }

  editProject(p: Project) {
    this.editingProjectId = p.id;
    this.form = { ...p };
    this.showModal = true;
  }

  closeModal() {
    this.showModal = false;
  }

  saveProject() {
    if (this.editingProjectId) {
      this.api.updateProject(this.editingProjectId, this.form).subscribe({
        next: () => {
          this.closeModal();
          this.showToast('Project updated successfully.', 'success');
          this.loadProjects();
        },
        error: (err) => this.showToast(err?.error?.detail || 'Failed to update project.', 'error'),
      });
    } else {
      this.api.createProject(this.form).subscribe({
        next: () => {
          this.closeModal();
          this.showToast('Project created successfully.', 'success');
          this.loadProjects();
        },
        error: (err) => this.showToast(err?.error?.detail || 'Failed to create project.', 'error'),
      });
    }
  }
}
