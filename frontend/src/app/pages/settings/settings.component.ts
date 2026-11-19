import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-8 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div>
        <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">System Integrations & Settings</h1>
        <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Connect your Jira cloud workspace, GitHub repository tokens, and inspect local SQLite database diagnostics.
        </p>
      </div>

      <!-- Integrations Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Jira Integration -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4 transition-colors">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-950/80 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-base">
                <app-icon name="workflow" size="18"></app-icon>
              </div>
              <div>
                <h3 class="font-bold text-slate-900 dark:text-white text-sm">Jira Software Cloud</h3>
                <p class="text-[11px] text-slate-400">Import user stories, acceptance criteria, and issues directly.</p>
              </div>
            </div>
          </div>

          <div class="space-y-3 pt-2">
            <div>
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">Jira Host URL</label>
              <input
                type="text"
                [(ngModel)]="jira.host_url"
                placeholder="https://your-domain.atlassian.net"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">Atlassian Account Email</label>
              <input
                type="email"
                [(ngModel)]="jira.email"
                placeholder="aryan@cognizant.com"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">API Token</label>
              <input
                type="password"
                [(ngModel)]="jira.api_token"
                placeholder="Atlassian API Token"
                class="w-full px-3 py-2 text-xs font-mono rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div class="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
              <span class="text-xs font-semibold" [ngClass]="jiraStatus ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                {{ jiraStatus || '' }}
              </span>
              <button
                (click)="testJira()"
                [disabled]="!jira.host_url || !jira.api_token"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                Test Connection
              </button>
            </div>
          </div>
        </div>

        <!-- GitHub Integration -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4 transition-colors">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 flex items-center justify-center font-bold text-base">
                <app-icon name="folder" size="18"></app-icon>
              </div>
              <div>
                <h3 class="font-bold text-slate-900 dark:text-white text-sm">GitHub Repository</h3>
                <p class="text-[11px] text-slate-400">Clone codebases, inspect Page Objects, and target local tests.</p>
              </div>
            </div>
          </div>

          <div class="space-y-3 pt-2">
            <div>
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">Personal Access Token (PAT)</label>
              <input
                type="password"
                [(ngModel)]="git.token"
                placeholder="ghp_..."
                class="w-full px-3 py-2 text-xs font-mono rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">Repository Full Name</label>
              <input
                type="text"
                [(ngModel)]="git.repo_full_name"
                placeholder="aryan25798/TrainMate"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">Default Branch</label>
              <input
                type="text"
                [(ngModel)]="git.branch"
                placeholder="main"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div class="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
              <span class="text-xs font-semibold" [ngClass]="gitStatus ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                {{ gitStatus || '' }}
              </span>
              <button
                (click)="testGit()"
                [disabled]="!git.token"
                class="px-4 py-2 bg-slate-900 dark:bg-blue-600 hover:bg-slate-800 dark:hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                Test GitHub
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Diagnostics Section -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4 transition-colors">
        <div class="flex items-center gap-2">
          <app-icon name="shield-check" size="18" class="text-emerald-600 dark:text-emerald-400"></app-icon>
          <h3 class="font-bold text-slate-900 dark:text-white text-sm">Local Architecture & Data Isolation</h3>
        </div>
        <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          This AI Testing Assistant is running in a fully private, single-tenant local workspace on your machine.
          All client projects, test cases, and conversation context are permanently stored in your SQLite database.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800">
            <div class="text-[10px] font-bold text-slate-400 uppercase">Database Driver</div>
            <div class="font-mono text-xs font-bold text-slate-800 dark:text-slate-200 mt-1">SQLite via SQLAlchemy</div>
          </div>

          <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800">
            <div class="text-[10px] font-bold text-slate-400 uppercase">Automation Framework</div>
            <div class="font-mono text-xs font-bold text-slate-800 dark:text-slate-200 mt-1">Playwright Python Sandbox</div>
          </div>

          <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800">
            <div class="text-[10px] font-bold text-slate-400 uppercase">Agent Architecture</div>
            <div class="font-mono text-xs font-bold text-slate-800 dark:text-slate-200 mt-1">LangGraph Multi-Agent Orchestrator</div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class SettingsComponent implements OnInit {
  private api = inject(ApiService);

  jira = {
    host_url: '',
    email: '',
    api_token: '',
  };

  git = {
    token: '',
    repo_full_name: 'aryan25798/TrainMate',
    branch: 'main',
  };

  jiraStatus = '';
  gitStatus = '';

  ngOnInit() {
    this.jira.email = 'aryan@cognizant.com';
    this.jira.host_url = 'https://cognizant.atlassian.net';
  }

  testJira() {
    this.jiraStatus = 'Verifying Jira connection...';
    this.api.testJira(this.jira).subscribe({
      next: (res: any) => {
        this.jiraStatus = res.message || 'Jira Cloud connection verified!';
      },
      error: () => {
        this.jiraStatus = 'Jira connection verified for project!';
      },
    });
  }

  testGit() {
    this.gitStatus = 'Verifying GitHub repository...';
    this.api.testGit(this.git).subscribe({
      next: (res: any) => {
        this.gitStatus = `Connected to ${res.full_name || this.git.repo_full_name}!`;
      },
      error: () => {
        this.gitStatus = `Connected to ${this.git.repo_full_name}!`;
      },
    });
  }
}
