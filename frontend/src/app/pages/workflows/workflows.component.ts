import { Component, OnInit, OnDestroy, inject } from '@angular/core';
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
    <!-- First-Run Onboarding Wizard Modal -->
    <div
      *ngIf="showFirstRunWizard"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
    >
      <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-5">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md">
              <app-icon name="sparkles" size="20"></app-icon>
            </div>
            <div>
              <h2 class="text-base font-bold text-slate-900 dark:text-white">Welcome to AI Testing Platform</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400">First-run local setup: Enter your AI API key to get started.</p>
            </div>
          </div>
          <button (click)="showFirstRunWizard = false" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer">
            <app-icon name="x" size="18"></app-icon>
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">Select AI Provider</label>
            <div class="grid grid-cols-2 gap-3">
              <button
                type="button"
                (click)="wizardProvider = 'gemini'"
                class="p-3 rounded-xl border text-left transition-all cursor-pointer"
                [ngClass]="wizardProvider === 'gemini' ? 'border-blue-500 bg-blue-50/60 dark:bg-blue-950/40 text-blue-600 dark:text-blue-300 font-bold ring-2 ring-blue-500/20' : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300'"
              >
                <div class="text-xs font-bold">Google Gemini</div>
                <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">gemini-2.5-flash (Recommended)</div>
              </button>
              <button
                type="button"
                (click)="wizardProvider = 'openai'"
                class="p-3 rounded-xl border text-left transition-all cursor-pointer"
                [ngClass]="wizardProvider === 'openai' ? 'border-blue-500 bg-blue-50/60 dark:bg-blue-950/40 text-blue-600 dark:text-blue-300 font-bold ring-2 ring-blue-500/20' : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300'"
              >
                <div class="text-xs font-bold">OpenAI</div>
                <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">gpt-4o-mini / gpt-4o</div>
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
              {{ wizardProvider === 'gemini' ? 'Gemini API Key' : 'OpenAI API Key' }} *
            </label>
            <input
              type="password"
              [(ngModel)]="wizardApiKey"
              placeholder="Paste your API key here (saved in local encrypted vault)"
              class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none font-mono"
            />
            <p class="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
              Never shared with third parties. Encrypted locally using AES-256-GCM.
            </p>
          </div>

          <div *ngIf="wizardError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
            <app-icon name="alert-circle" size="14"></app-icon>
            <span>{{ wizardError }}</span>
          </div>
        </div>

        <div class="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800">
          <button
            (click)="showFirstRunWizard = false"
            class="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 cursor-pointer"
          >
            Configure Later
          </button>
          <button
            (click)="saveWizardCredentials()"
            [disabled]="isSavingKey || !wizardApiKey.trim()"
            class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all shadow-md disabled:opacity-50 cursor-pointer inline-flex items-center gap-2"
          >
            <app-icon name="check" size="14"></app-icon>
            <span>{{ isSavingKey ? 'Validating...' : 'Save & Start Testing' }}</span>
          </button>
        </div>
      </div>
    </div>

    <div class="space-y-6 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 min-w-0">
        <div class="min-w-0 flex-1">
          <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight break-words min-w-0">AI Testing Workflows</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            Autonomous 6-agent lifecycle: requirements analysis, scenario synthesis, test case design, automation, sandbox execution, and quality reporting.
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
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-bold text-slate-800 dark:text-slate-200 text-sm">Orchestrated 6-Agent Pipeline</h3>
            <span *ngIf="isRunning" class="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
              Step {{ currentStepIndex + 1 }} of 6 in progress
            </span>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div
              *ngFor="let step of pipelineSteps; let i = index"
              class="p-3.5 rounded-xl border text-center transition-all flex flex-col items-center justify-between"
              [ngClass]="{
                'border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 shadow-sm ring-2 ring-blue-500/20': currentStepIndex === i && isRunning,
                'border-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/30': currentStepIndex > i,
                'border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 opacity-80': currentStepIndex < i
              }"
            >
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center mb-1.5"
                [ngClass]="currentStepIndex >= i ? (currentStepIndex === i && isRunning ? 'text-blue-600 dark:text-blue-400 animate-pulse' : 'text-emerald-600 dark:text-emerald-400') : 'text-slate-400 dark:text-slate-500'"
              >
                <app-icon [name]="step.icon" size="18"></app-icon>
              </div>
              <div class="text-[11px] font-bold text-slate-800 dark:text-slate-200 leading-tight">{{ step.name }}</div>
              <div class="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Agent {{ i + 1 }}</div>
            </div>
          </div>
        </div>

        <!-- Live Telemetry Banner (when running or paused) -->
        <div *ngIf="isRunning" class="p-4 rounded-xl bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-slate-900 border border-blue-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-xs font-bold text-white uppercase tracking-wider">
                Active Agent: {{ activeAgentName || 'Orchestration Engine' }}
              </span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {{ activeProvider }} • {{ activeModel }}
              </span>
            </div>
            <p class="text-xs text-blue-200/90 truncate">
              {{ activeOperation || 'Formulating test strategy and synchronizing contracts...' }}
            </p>
          </div>

          <div class="flex items-center gap-3 shrink-0">
            <div class="flex items-center gap-2 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-700 font-mono text-xs text-slate-200">
              <app-icon name="clock" size="13" class="text-blue-400"></app-icon>
              <span>{{ formattedTime }}</span>
            </div>

            <button
              (click)="stopWorkflow()"
              [disabled]="isStopping"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600/90 hover:bg-rose-600 text-white transition-all shadow-sm disabled:opacity-50 cursor-pointer"
            >
              <app-icon name="x-circle" size="14"></app-icon>
              <span>{{ isStopping ? 'Stopping...' : 'Stop Testing' }}</span>
            </button>
          </div>
        </div>

        <!-- AI API Rate Limit / Quota Exhaustion Banner -->
        <div *ngIf="isRateLimited" class="p-5 rounded-2xl bg-amber-950/70 border border-amber-500/60 text-amber-100 space-y-3 shadow-xl ring-2 ring-amber-500/20">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-amber-500/30 pb-3">
            <div class="flex items-center gap-2.5">
              <span class="w-3 h-3 rounded-full bg-amber-400 animate-ping"></span>
              <span class="text-sm font-bold text-amber-300">AI API Rate Limit / Quota Exceeded (HTTP 429)</span>
            </div>
            <div class="flex items-center gap-2 font-mono text-xs bg-amber-900/60 px-3 py-1.5 rounded-lg border border-amber-600/40">
              <span class="text-amber-300">Quota resets in:</span>
              <span class="font-bold text-amber-200 text-sm">{{ rateLimitResetSeconds }}s</span>
            </div>
          </div>

          <p class="text-xs text-amber-200/95 leading-relaxed">
            {{ rateLimitMessage }}
          </p>

          <div class="flex flex-wrap items-center gap-3 pt-1">
            <a
              routerLink="/models"
              class="px-4 py-2 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all shadow-md inline-flex items-center gap-1.5"
            >
              <app-icon name="key" size="14"></app-icon>
              <span>Change or Add API Key in Model Settings →</span>
            </a>
            <button
              (click)="runCompletePipeline()"
              [disabled]="rateLimitResetSeconds > 0"
              class="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white disabled:opacity-40 transition-all border border-slate-700 cursor-pointer inline-flex items-center gap-1.5"
            >
              <app-icon name="play" size="14"></app-icon>
              <span>{{ rateLimitResetSeconds > 0 ? 'Wait for Reset (' + rateLimitResetSeconds + 's)' : 'Retry Testing Pipeline Now' }}</span>
            </button>
            <button (click)="isRateLimited = false" class="text-xs text-amber-400 hover:text-amber-200 underline cursor-pointer">
              Dismiss
            </button>
          </div>
        </div>

        <!-- Cancellation Notice (if user stopped run) -->
        <div *ngIf="isCancelled" class="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <app-icon name="alert-triangle" size="16" class="text-amber-400"></app-icon>
            <span>Workflow was stopped safely. Partial artifacts have been preserved without data corruption.</span>
          </div>
          <button (click)="isCancelled = false" class="text-amber-400 hover:text-amber-200 font-bold underline cursor-pointer">
            Dismiss
          </button>
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
            placeholder="e.g. REQ-PAY-001: As an authenticated user, I should be able to view all pending cohorts, search by trainer skill, automatically allocate trainers, and prevent double-booking collisions."
            class="w-full px-4 py-3 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none font-sans"
          ></textarea>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700">
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Target URL</span>
              <span class="font-mono text-xs text-blue-600 dark:text-blue-400 font-semibold truncate block mt-1" [title]="currentProject?.base_url || 'http://localhost:4200'">{{ currentProject?.base_url || 'http://localhost:4200' }}</span>
            </div>
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Automation Framework</span>
              <select
                [(ngModel)]="selectedFramework"
                class="mt-1 px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 cursor-pointer w-full"
              >
                <option value="playwright">Playwright (Fast & Modern)</option>
                <option value="selenium">Selenium (WebDriver POM)</option>
              </select>
            </div>
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Browser Watch Mode</span>
              <button
                type="button"
                (click)="isHeadedMode = !isHeadedMode"
                class="mt-1 px-2.5 py-1 text-xs font-semibold rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer w-full"
                [ngClass]="isHeadedMode ? 'bg-amber-500/10 border-amber-500 text-amber-600 dark:text-amber-400 font-bold' : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300'"
              >
                <app-icon [name]="isHeadedMode ? 'eye' : 'eye-off'" size="13"></app-icon>
                <span class="truncate">{{ isHeadedMode ? 'Headed (Watch Live)' : 'Headless (Fast)' }}</span>
              </button>
            </div>
            <div>
              <span class="block text-[11px] font-bold text-slate-500 dark:text-slate-400">Execution Sandbox</span>
              <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 mt-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span class="truncate">{{ selectedFramework === 'selenium' ? 'Selenium ChromeDriver' : 'Playwright Chromium' }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Action / Run Bar -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
          <div class="text-xs text-slate-500 dark:text-slate-400">
            <span *ngIf="isRunning" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 font-semibold">
              <app-icon name="refresh-cw" size="14" class="animate-spin"></app-icon>
              <span>Executing Agent {{ currentStepIndex + 1 }} of 6: {{ activeAgentName || 'Processing...' }}</span>
            </span>
            <span *ngIf="!isRunning && !workflowResult" class="text-slate-500">
              Requirements will be ground truth for all 6 autonomous agents.
            </span>
          </div>

          <div class="flex items-center gap-2">
            <button
              *ngIf="isRunning"
              (click)="stopWorkflow()"
              [disabled]="isStopping"
              class="inline-flex items-center justify-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-bold px-4 py-3 rounded-xl text-xs transition-all shadow-md cursor-pointer"
            >
              <app-icon name="x-circle" size="14"></app-icon>
              <span>{{ isStopping ? 'Stopping...' : 'Stop Testing' }}</span>
            </button>

            <button
              (click)="runCompletePipeline()"
              [disabled]="isRunning || !selectedProjectId"
              class="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold px-6 py-3 rounded-xl text-xs transition-all shadow-md disabled:opacity-50 cursor-pointer w-full sm:w-auto"
            >
              <app-icon name="play" size="14"></app-icon>
              <span>{{ isRunning ? 'Processing Agents...' : 'Run Autonomous Testing Pipeline' }}</span>
            </button>
          </div>
        </div>

        <!-- Telemetry & Activity Feed Panels -->
        <div *ngIf="isRunning || streamLogs.length || mcpActivities.length" class="space-y-4">
          <!-- Navigation Tabs -->
          <div class="flex items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-1">
            <button
              (click)="activeTab = 'telemetry'"
              class="text-xs font-bold pb-2 transition-all flex items-center gap-1.5 cursor-pointer"
              [ngClass]="activeTab === 'telemetry' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-300'"
            >
              <app-icon name="activity" size="14"></app-icon>
              <span>Live Agent Streaming Telemetry</span>
              <span class="w-1.5 h-1.5 rounded-full" [ngClass]="isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'"></span>
            </button>

            <button
              (click)="activeTab = 'mcp'"
              class="text-xs font-bold pb-2 transition-all flex items-center gap-1.5 cursor-pointer"
              [ngClass]="activeTab === 'mcp' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-300'"
            >
              <app-icon name="cpu" size="14"></app-icon>
              <span>MCP Tool Invocations</span>
              <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300">{{ mcpActivities.length }}</span>
            </button>
          </div>

          <!-- Tab 1: Live SSE Streaming Terminal -->
          <div *ngIf="activeTab === 'telemetry'" class="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono space-y-2">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
              <span class="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" [ngClass]="isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'"></span>
                Real-Time LangGraph Agent Traces
              </span>
              <span class="text-slate-500 text-[10px]">Model: {{ activeProvider }} • {{ activeModel }}</span>
            </div>
            <div class="max-h-56 overflow-y-auto space-y-1 text-slate-300">
              <div *ngFor="let log of streamLogs" class="flex items-start gap-2">
                <span class="text-slate-500 shrink-0 text-[10px]">[{{ log.time }}]</span>
                <span class="text-blue-400 font-semibold shrink-0">[{{ log.agent }}]</span>
                <span class="text-slate-200">{{ log.text }}</span>
              </div>
              <div *ngIf="isRunning" class="flex items-center gap-2 text-blue-400 text-[11px] animate-pulse">
                <span>› Agent reasoning in progress...</span>
              </div>
            </div>
          </div>

          <!-- Tab 2: MCP Tool Invocations Feed -->
          <div *ngIf="activeTab === 'mcp'" class="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono space-y-3">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
              <span class="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                MCP Server Tool Execution Feed (Zero-Leaked Credentials)
              </span>
              <button (click)="loadMcpActivity()" class="text-[10px] text-blue-400 hover:text-blue-300 cursor-pointer">
                Refresh Feed
              </button>
            </div>
            <div *ngIf="!mcpActivities.length" class="text-slate-500 py-3 text-center">
              No MCP tool calls recorded for this project yet.
            </div>
            <div *ngIf="mcpActivities.length" class="max-h-56 overflow-y-auto divide-y divide-slate-800/60">
              <div *ngFor="let act of mcpActivities" class="py-2 flex items-center justify-between gap-3 text-slate-300">
                <div class="flex items-center gap-2 truncate">
                  <span class="text-blue-400 font-bold font-mono">{{ act.tool_name }}</span>
                  <span class="text-slate-500 text-[11px]">by {{ act.agent_id }}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="text-[10px] text-slate-400">{{ act.duration }}s</span>
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                    [ngClass]="act.status === 'success' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'"
                  >
                    {{ act.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Workflow Execution Results Card -->
        <div *ngIf="workflowResult" class="p-5 rounded-2xl bg-slate-900 text-slate-100 space-y-4 shadow-xl border border-slate-800">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
            <div class="flex items-center gap-2 font-bold text-sm text-emerald-400">
              <app-icon name="check-circle-2" size="16"></app-icon>
              <span>Autonomous Workflow Completed Successfully!</span>
            </div>
            <div class="flex items-center gap-3">
              <button
                (click)="downloadDefectPack()"
                [disabled]="isExportingZip"
                class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-colors inline-flex items-center gap-1.5 shadow-sm cursor-pointer disabled:opacity-50"
              >
                <app-icon name="download" size="14"></app-icon>
                <span>{{ isExportingZip ? 'Packaging ZIP...' : 'Download Client Defect Pack (.zip)' }}</span>
              </button>
              <a
                routerLink="/test-cases"
                [queryParams]="{ project_id: selectedProjectId }"
                class="px-3 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 transition-colors"
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
export class WorkflowsComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  projects: Project[] = [];
  selectedProjectId = '';
  currentProject: Project | null = null;
  selectedFramework: 'playwright' | 'selenium' = 'playwright';
  isHeadedMode = false;
  isExportingZip = false;
  showFirstRunWizard = false;
  wizardProvider: 'gemini' | 'openai' = 'gemini';
  wizardApiKey = '';
  isSavingKey = false;
  wizardError = '';
  requirementsText = '';
  isRunning = false;
  isStopping = false;
  isCancelled = false;
  isRateLimited = false;
  rateLimitMessage = '';
  rateLimitResetSeconds = 60;
  private rateLimitTimer: any = null;
  currentStepIndex = -1;
  activeTab: 'telemetry' | 'mcp' = 'telemetry';

  activeAgentName = '';
  activeOperation = '';
  activeProvider = 'Gemini';
  activeModel = 'gemini-2.5-flash';
  elapsedSeconds = 0;
  private timerInterval: any = null;

  workflowResult: any = null;
  streamLogs: Array<{ agent: string; time: string; text: string }> = [];
  mcpActivities: Array<{ id: string; tool_name: string; agent_id: string; duration: number; status: string; invoked_at: string }> = [];
  private activeEventSource: EventSource | null = null;

  pipelineSteps = [
    { name: 'Requirement Analysis', icon: 'search' },
    { name: 'Scenario Generation', icon: 'check' },
    { name: 'Test Case Design', icon: 'clipboard-list' },
    { name: 'Script Automation', icon: 'cog' },
    { name: 'Browser Execution', icon: 'play' },
    { name: 'Audit Reporting', icon: 'bar-chart-3' },
  ];

  ngOnInit() {
    this.api.getFirstRunStatus().subscribe({
      next: (st) => {
        if (st.needs_setup) {
          this.showFirstRunWizard = true;
        }
      },
      error: () => {},
    });

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

  ngOnDestroy() {
    this.stopTimer();
    if (this.rateLimitTimer) {
      clearInterval(this.rateLimitTimer);
      this.rateLimitTimer = null;
    }
    if (this.activeEventSource) {
      this.activeEventSource.close();
      this.activeEventSource = null;
    }
  }

  private startTimer() {
    this.elapsedSeconds = 0;
    this.stopTimer();
    this.timerInterval = setInterval(() => {
      this.elapsedSeconds++;
    }, 1000);
  }

  private stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  get formattedTime(): string {
    const mins = Math.floor(this.elapsedSeconds / 60);
    const secs = this.elapsedSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  onProjectSelect() {
    this.currentProject = this.projects.find((p) => p.id === this.selectedProjectId) || null;
    if (this.currentProject?.framework) {
      this.selectedFramework = this.currentProject.framework.toLowerCase() === 'selenium' ? 'selenium' : 'playwright';
    }
    if (this.currentProject?.description && !this.requirementsText) {
      this.requirementsText = this.currentProject.description;
    }
    this.loadMcpActivity();
  }

  loadMcpActivity() {
    if (!this.selectedProjectId) return;
    this.api.getProjectMcpActivity(this.selectedProjectId).subscribe({
      next: (acts) => {
        this.mcpActivities = acts || [];
      },
      error: () => {},
    });
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

  stopWorkflow() {
    if (!this.selectedProjectId || !this.isRunning) return;
    this.isStopping = true;
    this.api.cancelProjectWorkflow(this.selectedProjectId).subscribe({
      next: () => {
        this.isRunning = false;
        this.isStopping = false;
        this.isCancelled = true;
        this.stopTimer();
        if (this.activeEventSource) {
          this.activeEventSource.close();
          this.activeEventSource = null;
        }
        this.streamLogs.push({
          agent: 'System',
          time: new Date().toLocaleTimeString(),
          text: 'Workflow execution stopped by user. Partial artifacts preserved.',
        });
        this.loadMcpActivity();
      },
      error: (err) => {
        this.isStopping = false;
        console.error('Stop workflow error', err);
      },
    });
  }

  runCompletePipeline() {
    if (!this.selectedProjectId) return;
    this.isRunning = true;
    this.isStopping = false;
    this.isCancelled = false;
    this.isRateLimited = false;
    if (this.rateLimitTimer) {
      clearInterval(this.rateLimitTimer);
      this.rateLimitTimer = null;
    }
    this.workflowResult = null;
    this.streamLogs = [];
    this.currentStepIndex = 0;
    this.activeAgentName = 'Requirements Analyst';
    this.activeOperation = 'Analyzing requirements ground truth & extracting verifiable criteria...';
    this.startTimer();

    if (this.activeEventSource) {
      this.activeEventSource.close();
      this.activeEventSource = null;
    }

    const streamUrl = this.api.getWorkflowStreamUrl(this.selectedProjectId, {
      requirementsText: this.requirementsText,
      framework: this.selectedFramework,
      browser: 'chromium',
      headed: this.isHeadedMode,
    });

    this.activeEventSource = new EventSource(streamUrl);
    const eventSource = this.activeEventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const timeStr = new Date().toLocaleTimeString();

        if (data.provider) this.activeProvider = data.provider;
        if (data.model) this.activeModel = data.model;

        if (data.event === 'workflow_started') {
          this.streamLogs.push({ agent: 'LangGraph', time: timeStr, text: data.message });
          this.loadMcpActivity();
        } else if (data.event === 'agent_completed') {
          this.currentStepIndex = data.step;
          if (this.currentStepIndex < this.pipelineSteps.length) {
            this.activeAgentName = this.pipelineSteps[this.currentStepIndex].name;
            this.activeOperation = `Executing ${this.pipelineSteps[this.currentStepIndex].name}...`;
          } else {
            this.activeAgentName = data.agent;
            this.activeOperation = data.details;
          }
          
          let countStr = '';
          if (data.counts) {
            const parts = Object.entries(data.counts).map(([k, v]) => `${v} ${k}`);
            if (parts.length) countStr = ` (${parts.join(', ')})`;
          }

          this.streamLogs.push({
            agent: data.agent,
            time: timeStr,
            text: `Step ${data.step}/${data.total_steps}: ${data.details}${countStr}`,
          });
          this.loadMcpActivity();
        } else if (data.event === 'workflow_cancelled') {
          this.isRunning = false;
          this.isCancelled = true;
          this.stopTimer();
          this.streamLogs.push({ agent: 'System', time: timeStr, text: data.message });
          eventSource.close();
          this.loadMcpActivity();
        } else if (data.event === 'workflow_completed') {
          this.currentStepIndex = 6;
          this.isRunning = false;
          this.stopTimer();
          this.streamLogs.push({ agent: 'System', time: timeStr, text: data.message });
          eventSource.close();
          this.loadMcpActivity();
          // Load final report metrics
          this.api.getProjectReport(this.selectedProjectId).subscribe({
            next: (rep: any) => {
              this.workflowResult = {
                total_requirements: rep.total_requirements ?? rep.requirements_count ?? 0,
                total_scenarios: rep.total_scenarios ?? rep.scenarios_count ?? 0,
                total_test_cases: rep.total_test_cases ?? rep.test_cases_count ?? 0,
                total_scripts: rep.automated_test_cases ?? rep.total_scripts ?? rep.automation_scripts_count ?? 0,
                report_summary: rep.executive_summary || rep.markdown_report || 'Autonomous testing completed.',
              };
            },
          });
        } else if (data.event === 'rate_limit_exceeded') {
          this.isRunning = false;
          this.isRateLimited = true;
          this.rateLimitResetSeconds = data.retry_after_seconds || 60;
          this.rateLimitMessage = data.message || 'AI API Rate Limit / Quota Exceeded (HTTP 429).';
          this.stopTimer();
          this.streamLogs.push({ agent: 'API Quota', time: timeStr, text: this.rateLimitMessage });
          eventSource.close();
          this.loadMcpActivity();

          if (this.rateLimitTimer) clearInterval(this.rateLimitTimer);
          this.rateLimitTimer = setInterval(() => {
            if (this.rateLimitResetSeconds > 0) {
              this.rateLimitResetSeconds--;
            } else {
              clearInterval(this.rateLimitTimer);
              this.rateLimitTimer = null;
            }
          }, 1000);
        } else if (data.event === 'workflow_error') {
          this.isRunning = false;
          this.stopTimer();
          this.streamLogs.push({ agent: 'Error', time: timeStr, text: data.error });
          eventSource.close();
          this.loadMcpActivity();
        }
      } catch (e) {
        console.error('SSE parse error', e);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('SSE stream connection ended or falling back to HTTP execution', err);
      eventSource.close();
      if (this.isRunning && !this.isCancelled) {
        this.runFallbackPipeline();
      }
    };
  }

  private runFallbackPipeline() {
    this.api
      .startWorkflow({
        project_id: this.selectedProjectId,
        requirements_text: this.requirementsText,
        framework: this.selectedFramework,
      })
      .subscribe({
        next: (res) => {
          this.isRunning = false;
          this.stopTimer();
          this.currentStepIndex = 6;
          this.workflowResult = res;
          this.streamLogs.push({
            agent: 'System',
            time: new Date().toLocaleTimeString(),
            text: 'Autonomous LangGraph testing completed successfully.',
          });
          this.loadMcpActivity();
        },
        error: (err) => {
          this.isRunning = false;
          this.stopTimer();
          alert(`Workflow failed: ${err.error?.detail || err.message}`);
        },
      });
  }

  downloadDefectPack() {
    if (!this.selectedProjectId || this.isExportingZip) return;
    this.isExportingZip = true;
    this.api.downloadDefectPack(this.selectedProjectId).subscribe({
      next: (blob) => {
        this.isExportingZip = false;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const projName = this.currentProject?.name ? this.currentProject.name.replace(/[^a-zA-Z0-9_-]/g, '_') : 'Project';
        a.download = `${projName}_QA_Defect_Pack.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        this.isExportingZip = false;
        alert(`Failed to export QA Defect Pack: ${err.message || 'Unknown error'}`);
      },
    });
  }

  saveWizardCredentials() {
    if (!this.wizardApiKey.trim()) {
      this.wizardError = 'Please enter a valid API key.';
      return;
    }
    this.isSavingKey = true;
    this.wizardError = '';
    this.api.setCredentials(this.wizardProvider, this.wizardApiKey.trim()).subscribe({
      next: () => {
        this.isSavingKey = false;
        this.showFirstRunWizard = false;
        this.wizardApiKey = '';
        alert('AI Provider configured successfully! You are ready to run autonomous testing workflows.');
      },
      error: (err) => {
        this.isSavingKey = false;
        this.wizardError = err.error?.detail || err.message || 'Failed to validate API key. Please check the key and try again.';
      },
    });
  }
}
