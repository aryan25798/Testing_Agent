import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, IconComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">My Projects</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Manage your client and local applications under test.
          </p>
        </div>
        <button
          (click)="openModal()"
          class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all shadow-sm cursor-pointer"
        >
          <app-icon name="plus" size="14"></app-icon>
          <span>Create New Project</span>
        </button>
      </div>

      <!-- Projects Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" *ngIf="projects.length; else noProjectsTpl">
        <div
          *ngFor="let p of projects"
          class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-subtle hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-card transition-all flex flex-col justify-between"
        >
          <div>
            <div class="flex items-start justify-between gap-3 mb-3">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 text-white font-bold text-sm flex items-center justify-center shadow-sm shrink-0">
                {{ p.name.charAt(0).toUpperCase() }}
              </div>
              <div class="flex items-center gap-1.5">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 uppercase tracking-wider">
                  {{ p.framework }}
                </span>
                <button
                  (click)="confirmDelete(p)"
                  class="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors"
                  title="Delete Project"
                >
                  <app-icon name="trash-2" size="14"></app-icon>
                </button>
              </div>
            </div>

            <h3 class="font-bold text-slate-900 dark:text-white text-base leading-snug line-clamp-1">{{ p.name }}</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 min-h-[32px]">{{ p.description || 'No description provided.' }}</p>

            <div class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 space-y-2 text-xs">
              <div class="flex items-center justify-between min-w-0 gap-2">
                <span class="text-slate-400 shrink-0">Target URL:</span>
                <span class="font-mono text-[11px] truncate max-w-[60%] text-blue-600 dark:text-blue-400 font-semibold" [title]="p.base_url || 'http://localhost:4200'">{{ p.base_url || 'http://localhost:4200' }}</span>
              </div>
              <div class="flex items-center justify-between min-w-0 gap-2" *ngIf="p.git_repo_url">
                <span class="text-slate-400 shrink-0">Git Repo:</span>
                <span class="font-mono text-[11px] truncate max-w-[60%] text-slate-700 dark:text-slate-300" [title]="p.git_repo_url">{{ p.git_repo_url }}</span>
              </div>
            </div>
          </div>

          <div class="mt-5 pt-3.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <span class="text-[11px] text-slate-400 dark:text-slate-500">
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

      <ng-template #noProjectsTpl>
        <div class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
          <app-icon name="folder" size="40" class="text-slate-400 mx-auto mb-3"></app-icon>
          <h3 class="font-bold text-slate-800 dark:text-white text-base">No Projects Found</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">Get started by creating your first QA project.</p>
          <button
            (click)="openModal()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs"
          >
            + Create New Project
          </button>
        </div>
      </ng-template>

      <!-- Create / Edit Modal -->
      <div
        *ngIf="showModal"
        class="fixed inset-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      >
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-base font-bold text-slate-900 dark:text-white">
              {{ editingProjectId ? 'Edit Project' : 'Create New QA Project' }}
            </h2>
            <button (click)="closeModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
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
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Description</label>
              <textarea
                [(ngModel)]="form.description"
                name="description"
                rows="2"
                placeholder="Brief summary of application features, login flows, or endpoints"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
              ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Testing Framework</label>
                <select
                  [(ngModel)]="form.framework"
                  name="framework"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
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
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
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
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
                />
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Git Branch</label>
                <input
                  type="text"
                  [(ngModel)]="form.git_branch"
                  name="git_branch"
                  placeholder="main"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
                />
              </div>
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                (click)="closeModal()"
                class="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Cancel
              </button>
              <button
                type="submit"
                [disabled]="!form.name"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm disabled:opacity-50"
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

  loadProjects() {
    this.api.getProjects().subscribe({
      next: (res) => (this.projects = res),
      error: (err) => console.error(err),
    });
  }

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
          this.loadProjects();
        },
      });
    } else {
      this.api.createProject(this.form).subscribe({
        next: () => {
          this.closeModal();
          this.loadProjects();
        },
      });
    }
  }

  confirmDelete(p: Project) {
    if (confirm(`Are you sure you want to delete project "${p.name}"? This will permanently clean up all its test cases, scenarios, and execution runs.`)) {
      this.api.deleteProject(p.id).subscribe({
        next: () => this.loadProjects(),
      });
    }
  }
}
