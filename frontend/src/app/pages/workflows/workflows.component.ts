import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-workflows',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, IconComponent],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 min-w-0">
        <div class="min-w-0 flex-1">
          <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight break-words min-w-0">AI Testing Workflows</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            End-to-end autonomous test design, Playwright script generation, and browser validation.
          </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <label class="text-xs font-bold text-slate-600 dark:text-slate-300">Active Project:</label>
          <select
            [(ngModel)]="selectedProjectId"
            (change)="onProjectSelect()"
            class="px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 shadow-sm focus:border-blue-500 outline-none"
          >
            <option *ngFor="let p of projects" [value]="p.id">
              {{ p.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Main Workflow Execution Card -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-6">
        <!-- Pipeline Steps Visualizer -->
        <div>
          <h3 class="font-bold text-slate-800 dark:text-slate-200 text-sm mb-3">Orchestrated 6-Agent Pipeline</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div
              *ngFor="let step of pipelineSteps; let i = index"
              class="p-3.5 rounded-xl border text-center transition-all flex flex-col items-center justify-between"
              [ngClass]="{
                'border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 shadow-sm': currentStepIndex === i,
                'border-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/30': currentStepIndex > i,
                'border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 opacity-80': currentStepIndex < i
              }"
            >
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center mb-1.5"
                [ngClass]="currentStepIndex >= i ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'"
              >
                <app-icon [name]="step.icon" size="18"></app-icon>
              </div>
              <div class="text-[11px] font-bold text-slate-800 dark:text-slate-200 leading-tight">{{ step.name }}</div>
              <div class="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Agent {{ i + 1 }}</div>
            </div>
          </div>
        </div>

        <div class="h-px bg-slate-100 dark:bg-slate-800"></div>

        <!-- Input Section -->
        <div class="space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
            <label class="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Requirements, User Stories, or Acceptance Criteria *
            </label>
            <div class="flex items-center gap-2 shrink-0">
              <label class="cursor-pointer text-xs font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
                <app-icon name="download" size="13"></app-icon>
                <span>Upload Requirement File</span>
                <input type="file" (change)="onFileUpload($event)" class="hidden" accept=".pdf,.docx,.xlsx,.csv,.txt" />
              </label>
            </div>
          </div>

          <textarea
            [(ngModel)]="requirementsText"
            rows="5"
            placeholder="e.g. As an authenticated user, I should be able to view all pending cohorts, search by trainer skill, automatically allocate trainers, and prevent double-booking collisions."
            class="w-full px-4 py-3 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none font-sans"
          ></textarea>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700">
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Target URL</span>
              <span class="font-mono text-xs text-blue-600 dark:text-blue-400 font-semibold">{{ currentProject?.base_url || 'http://localhost:4200' }}</span>
            </div>
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Automation Framework</span>
              <span class="text-xs font-semibold text-slate-800 dark:text-slate-200 capitalize">{{ currentProject?.framework || 'playwright' }}</span>
            </div>
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Execution Sandbox</span>
              <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400">Isolated Playwright Chromium</span>
            </div>
          </div>
        </div>

        <!-- Action / Run -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
          <div class="text-xs text-slate-500 dark:text-slate-400">
            <span *ngIf="isRunning" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 font-semibold">
              <app-icon name="refresh-cw" size="14" class="animate-spin"></app-icon>
              <span>Running autonomous LangGraph workflow... please wait.</span>
            </span>
          </div>

          <button
            (click)="runCompletePipeline()"
            [disabled]="isRunning || !selectedProjectId"
            class="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold px-6 py-3 rounded-xl text-xs transition-all shadow-md disabled:opacity-50 cursor-pointer w-full sm:w-auto"
          >
            <app-icon name="play" size="14"></app-icon>
            <span>{{ isRunning ? 'Processing Agents...' : 'Run Autonomous Testing Pipeline' }}</span>
          </button>
        </div>

        <!-- Workflow Execution Results Card -->
        <div *ngIf="workflowResult" class="p-5 rounded-2xl bg-slate-900 text-slate-100 space-y-4 shadow-xl border border-slate-800">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
            <div class="flex items-center gap-2 font-bold text-sm text-emerald-400">
              <app-icon name="check-circle-2" size="16"></app-icon>
              <span>Autonomous Workflow Completed Successfully!</span>
            </div>
            <div class="flex items-center gap-3">
              <a
                routerLink="/test-cases"
                [queryParams]="{ project_id: selectedProjectId }"
                class="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 transition-colors"
              >
                View Generated Test Cases →
              </a>
            </div>
          </div>

          <!-- Summary Metric Counters -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="bg-slate-800/80 p-3 rounded-xl border border-slate-700/60">
              <div class="text-[11px] text-slate-400">Requirements Extracted</div>
              <div class="text-xl font-bold text-white mt-1">{{ workflowResult.total_requirements }}</div>
            </div>
            <div class="bg-slate-800/80 p-3 rounded-xl border border-slate-700/60">
              <div class="text-[11px] text-slate-400">Scenarios Generated</div>
              <div class="text-xl font-bold text-white mt-1">{{ workflowResult.total_scenarios }}</div>
            </div>
            <div class="bg-slate-800/80 p-3 rounded-xl border border-slate-700/60">
              <div class="text-[11px] text-slate-400">Test Cases Designed</div>
              <div class="text-xl font-bold text-white mt-1">{{ workflowResult.total_test_cases }}</div>
            </div>
            <div class="bg-slate-800/80 p-3 rounded-xl border border-slate-700/60">
              <div class="text-[11px] text-slate-400">Automation Scripts</div>
              <div class="text-xl font-bold text-white mt-1">{{ workflowResult.total_scripts }}</div>
            </div>
          </div>

          <!-- Report Preview -->
          <div *ngIf="workflowResult.report_summary" class="bg-slate-950 p-4 rounded-xl border border-slate-800/80 text-xs font-mono text-slate-300 max-h-60 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {{ workflowResult.report_summary }}
          </div>
        </div>
      </div>
    </div>
  `,
})
export class WorkflowsComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  projects: Project[] = [];
  selectedProjectId = '';
  currentProject: Project | null = null;
  requirementsText = '';
  isRunning = false;
  currentStepIndex = -1;
  workflowResult: any = null;

  pipelineSteps = [
    { name: 'Requirement Analysis', icon: 'search' },
    { name: 'Scenario Generation', icon: 'check' },
    { name: 'Test Case Design', icon: 'clipboard-list' },
    { name: 'Script Automation', icon: 'cog' },
    { name: 'Browser Execution', icon: 'play' },
    { name: 'Audit Reporting', icon: 'bar-chart-3' },
  ];

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
          this.onProjectSelect();
        });
      },
    });
  }

  onProjectSelect() {
    this.currentProject = this.projects.find((p) => p.id === this.selectedProjectId) || null;
    if (this.currentProject?.description && !this.requirementsText) {
      this.requirementsText = this.currentProject.description;
    }
  }

  onFileUpload(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.api.uploadRequirementFile(file).subscribe({
        next: (res) => {
          this.requirementsText = res.extracted_text;
          alert(`Successfully extracted requirements from ${file.name} (${res.character_count} chars)!`);
        },
        error: (err) => alert(`File upload failed: ${err.message}`),
      });
    }
  }

  runCompletePipeline() {
    if (!this.selectedProjectId) return;
    this.isRunning = true;
    this.workflowResult = null;
    this.currentStepIndex = 0;

    const stepInterval = setInterval(() => {
      if (this.currentStepIndex < 5 && this.isRunning) {
        this.currentStepIndex++;
      }
    }, 2500);

    this.api
      .startWorkflow({
        project_id: this.selectedProjectId,
        requirements_text: this.requirementsText,
        framework: this.currentProject?.framework || 'playwright',
      })
      .subscribe({
        next: (res) => {
          clearInterval(stepInterval);
          this.isRunning = false;
          this.currentStepIndex = 6;
          this.workflowResult = res;
        },
        error: (err) => {
          clearInterval(stepInterval);
          this.isRunning = false;
          alert(`Workflow failed: ${err.error?.detail || err.message}`);
        },
      });
  }
}
