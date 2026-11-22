import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ModelInfo } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-model-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-8 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">AI Model Engine & Provider Configuration</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Connect your Gemini and OpenAI credentials, discover available live models, and assign independent models per testing agent.
          </p>
        </div>

        <button
          (click)="refreshModels()"
          [disabled]="isRefreshing"
          class="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all self-start sm:self-auto disabled:opacity-50"
        >
          <app-icon name="refresh-cw" size="14" [class]="isRefreshing ? 'animate-spin' : ''"></app-icon>
          <span>{{ isRefreshing ? 'Discovering Models...' : 'Refresh Discovered Models' }}</span>
        </button>
      </div>

      <!-- Provider API Key Management -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Google Gemini Card -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col justify-between space-y-4 transition-colors">
          <div>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/70 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-base shadow-2xs border border-blue-200/60 dark:border-blue-900/60">
                  <app-icon name="google" size="20"></app-icon>
                </div>
                <div>
                  <h3 class="font-bold text-slate-900 dark:text-white text-sm">Google Gemini Engine</h3>
                  <p class="text-[11px] text-slate-400">Native multimodal testing models with 1M+ context window.</p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <span
                  *ngIf="credentialStatuses['gemini']?.masked"
                  class="font-mono text-[10px] text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700"
                >
                  {{ credentialStatuses['gemini']?.masked }}
                </span>
                <span
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-bold"
                  [ngClass]="providerStatus['gemini'] ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'"
                >
                  {{ providerStatus['gemini'] ? 'Connected' : 'Not Configured' }}
                </span>
              </div>
            </div>

            <div class="space-y-1.5 pt-2">
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300">Gemini API Key</label>
              <div class="relative">
                <input
                  [type]="showGeminiKey ? 'text' : 'password'"
                  [(ngModel)]="geminiKey"
                  placeholder="Paste new key to update..."
                  class="w-full pl-3.5 pr-10 py-2.5 text-xs font-mono rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                />
                <button
                  type="button"
                  (click)="showGeminiKey = !showGeminiKey"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs"
                >
                  {{ showGeminiKey ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
            <span class="text-xs text-slate-500 dark:text-slate-400">
              {{ getModelsForProvider('gemini').length }} Gemini models ready
            </span>
            <div class="flex items-center gap-2">
              <button
                *ngIf="credentialStatuses['gemini']?.is_configured"
                (click)="deleteCredentials('gemini')"
                type="button"
                class="px-3 py-2 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 font-bold rounded-xl text-xs transition-colors border border-rose-200 dark:border-rose-900/60"
              >
                Revoke Key
              </button>
              <button
                (click)="saveCredentials('gemini', geminiKey)"
                [disabled]="!geminiKey"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                {{ credentialStatuses['gemini']?.is_configured ? 'Update Key' : 'Verify & Save Key' }}
              </button>
            </div>
          </div>
        </div>

        <!-- OpenAI Card -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col justify-between space-y-4 transition-colors">
          <div>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-base shadow-2xs border border-emerald-200/60 dark:border-emerald-900/60">
                  <app-icon name="openai" size="20"></app-icon>
                </div>
                <div>
                  <h3 class="font-bold text-slate-900 dark:text-white text-sm">OpenAI Engine</h3>
                  <p class="text-[11px] text-slate-400">Reasoning and code generation models (GPT-4o, o1, o3-mini).</p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <span
                  *ngIf="credentialStatuses['openai']?.masked"
                  class="font-mono text-[10px] text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700"
                >
                  {{ credentialStatuses['openai']?.masked }}
                </span>
                <span
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-bold"
                  [ngClass]="providerStatus['openai'] ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'"
                >
                  {{ providerStatus['openai'] ? 'Connected' : 'Not Configured' }}
                </span>
              </div>
            </div>

            <div class="space-y-1.5 pt-2">
              <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300">OpenAI API Key</label>
              <div class="relative">
                <input
                  [type]="showOpenaiKey ? 'text' : 'password'"
                  [(ngModel)]="openaiKey"
                  placeholder="Paste new key to update..."
                  class="w-full pl-3.5 pr-10 py-2.5 text-xs font-mono rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                />
                <button
                  type="button"
                  (click)="showOpenaiKey = !showOpenaiKey"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs"
                >
                  {{ showOpenaiKey ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
            <span class="text-xs text-slate-500 dark:text-slate-400">
              {{ getModelsForProvider('openai').length }} OpenAI models ready
            </span>
            <div class="flex items-center gap-2">
              <button
                *ngIf="credentialStatuses['openai']?.is_configured"
                (click)="deleteCredentials('openai')"
                type="button"
                class="px-3 py-2 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 font-bold rounded-xl text-xs transition-colors border border-rose-200 dark:border-rose-900/60"
              >
                Revoke Key
              </button>
              <button
                (click)="saveCredentials('openai', openaiKey)"
                [disabled]="!openaiKey"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                {{ credentialStatuses['openai']?.is_configured ? 'Update Key' : 'Verify & Save Key' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Discovered Models Banner (matching reference) -->
      <div class="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
            <app-icon name="check-circle-2" size="18"></app-icon>
          </div>
          <div>
            <div class="font-bold text-emerald-900 dark:text-emerald-200 text-sm">
              Discovered {{ availableModels.length }} Available Models across Connected Providers
            </div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 mt-0.5">
              Live models are inspected dynamically from your configured API providers without hardcoded limitations.
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 self-end sm:self-auto">
          <span class="px-3 py-1 rounded-lg bg-white dark:bg-slate-900 text-emerald-800 dark:text-emerald-300 font-bold text-xs border border-emerald-200 dark:border-emerald-800 shadow-2xs">
            {{ availableModels.length }} Live Endpoints
          </span>
        </div>
      </div>

      <!-- ================================================================= -->
      <!-- INDEPENDENT PER-AGENT MODEL ASSIGNMENT (Rich Icons & Responsive) -->
      <!-- ================================================================= -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-6 transition-colors">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <app-icon name="bot" size="18"></app-icon>
            </div>
            <div>
              <h2 class="font-bold text-slate-900 dark:text-white text-base">Independent Per-Agent Model Assignment</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Assign tailored models to each agent role based on task complexity, speed, and context requirements.
              </p>
            </div>
          </div>
        </div>

        <!-- Agent Rows List -->
        <div class="space-y-4">
          <div
            *ngFor="let a of coreAgents"
            class="p-4 sm:p-5 rounded-2xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-all flex flex-col 2xl:flex-row 2xl:items-center justify-between gap-4 min-w-0"
          >
            <!-- Agent Info (Left) -->
            <div class="flex items-start gap-3.5 min-w-0 flex-1">
              <div
                class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-base shrink-0 shadow-sm"
                [ngClass]="a.badgeColor"
              >
                <app-icon [name]="a.iconName" size="18"></app-icon>
              </div>
              <div class="min-w-0 flex-1">
                <div class="font-bold text-slate-900 dark:text-white text-sm">
                  {{ a.name }}
                </div>
                <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
                  {{ a.purpose }}
                </div>
              </div>
            </div>

            <!-- Agent Model Assignment Controls (Right: Provider Icons + Model Selector + Save) -->
            <div class="flex flex-wrap items-end gap-2.5 sm:gap-3 w-full 2xl:w-auto pt-3 2xl:pt-0 border-t border-slate-200/60 dark:border-slate-800/80 2xl:border-t-0 shrink-0">
              <!-- 1. Visual Provider Selector with Official Brand Icons -->
              <div class="flex flex-col gap-1 shrink-0">
                <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Provider
                </span>
                <div class="inline-flex items-center rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1 shadow-2xs h-[38px]">
                  <!-- Gemini Option Button -->
                  <button
                    type="button"
                    (click)="setProvider(a.id, 'gemini')"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer h-full"
                    [ngClass]="agentAssignments[a.id].provider === 'gemini' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'"
                    title="Select Google Gemini Provider"
                  >
                    <app-icon name="google" size="13"></app-icon>
                    <span>Gemini</span>
                  </button>

                  <!-- OpenAI Option Button -->
                  <button
                    type="button"
                    (click)="setProvider(a.id, 'openai')"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer h-full"
                    [ngClass]="agentAssignments[a.id].provider === 'openai' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'"
                    title="Select OpenAI Provider"
                  >
                    <app-icon name="openai" size="13"></app-icon>
                    <span>OpenAI</span>
                  </button>
                </div>
              </div>

              <!-- 2. Model Dropdown with Chip Icon -->
              <div class="flex flex-col gap-1 min-w-[170px] sm:min-w-[220px] flex-1 sm:flex-initial max-w-full">
                <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Model Endpoint
                </span>
                <div class="relative h-[38px]">
                  <select
                    [(ngModel)]="agentAssignments[a.id].model_id"
                    class="w-full h-full pl-8 pr-8 py-1.5 text-xs font-mono font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-2xs focus:border-blue-500 outline-none appearance-none cursor-pointer truncate"
                  >
                    <option
                      *ngFor="let m of getModelsForProvider(agentAssignments[a.id].provider)"
                      [value]="m.model_id"
                    >
                      {{ m.display_name }}
                    </option>
                  </select>
                  <!-- Leading Model Icon -->
                  <div class="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                    <app-icon name="cpu" size="14"></app-icon>
                  </div>
                  <!-- Trailing Chevron Icon -->
                  <div class="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                    <app-icon name="chevron-down" size="13"></app-icon>
                  </div>
                </div>
              </div>

              <!-- 3. Save Button with Feedback -->
              <div class="flex flex-col gap-1 shrink-0">
                <button
                  (click)="saveAgentModel(a.id)"
                  class="h-[38px] px-4 font-bold text-xs rounded-xl transition-all shadow-sm flex items-center justify-center gap-1.5 cursor-pointer shrink-0"
                  [ngClass]="savedState[a.id] ? 'bg-emerald-600 text-white' : 'bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white'"
                >
                  <app-icon [name]="savedState[a.id] ? 'check' : 'check-circle-2'" size="13"></app-icon>
                  <span>{{ savedState[a.id] ? 'Saved' : 'Save' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class ModelSettingsComponent implements OnInit {
  private api = inject(ApiService);

  geminiKey = '';
  openaiKey = '';
  showGeminiKey = false;
  showOpenaiKey = false;
  isRefreshing = false;

  providerStatus: Record<string, boolean> = {};
  credentialStatuses: Record<string, { provider?: string; is_configured?: boolean; masked?: string } | undefined> = {};
  availableModels: ModelInfo[] = [];
  savedState: Record<string, boolean> = {};

  coreAgents = [
    {
      id: 'agent_1_requirement_analysis',
      name: 'Requirement Analysis Agent',
      iconName: 'search',
      badgeColor: 'bg-blue-600',
      purpose: 'Extracts functional, non-functional, business rules, and acceptance criteria.',
    },
    {
      id: 'agent_2_scenario_generation',
      name: 'Test Scenario Generation Agent',
      iconName: 'check',
      badgeColor: 'bg-emerald-600',
      purpose: 'Generates positive, negative, boundary, and edge-case test scenarios.',
    },
    {
      id: 'agent_3_test_case_design',
      name: 'Test Case Design Agent',
      iconName: 'file-text',
      badgeColor: 'bg-purple-600',
      purpose: 'Produces executable step-by-step test cases and test data.',
    },
    {
      id: 'agent_4_test_automation',
      name: 'Test Automation Agent',
      iconName: 'rocket',
      badgeColor: 'bg-amber-600',
      purpose: 'Generates robust Playwright/Selenium code with resilient locators.',
    },
    {
      id: 'agent_5_test_execution',
      name: 'Test Execution Agent',
      iconName: 'play',
      badgeColor: 'bg-teal-600',
      purpose: 'Executes scripts in browser sandbox and classifies root cause failures.',
    },
    {
      id: 'agent_6_orchestration_reporting',
      name: 'Test Orchestration & Reporting Agent',
      iconName: 'bar-chart-3',
      badgeColor: 'bg-indigo-600',
      purpose: 'Coordinates quality gates and aggregates audit metrics.',
    },
  ];

  agentAssignments: Record<string, { provider: string; model_id: string }> = {
    agent_1_requirement_analysis: { provider: 'gemini', model_id: 'gemini-2.5-flash' },
    agent_2_scenario_generation: { provider: 'gemini', model_id: 'gemini-2.5-flash' },
    agent_3_test_case_design: { provider: 'gemini', model_id: 'gemini-2.5-flash' },
    agent_4_test_automation: { provider: 'gemini', model_id: 'gemini-2.5-flash' },
    agent_5_test_execution: { provider: 'gemini', model_id: 'gemini-2.5-flash' },
    agent_6_orchestration_reporting: { provider: 'gemini', model_id: 'gemini-2.5-flash' },
  };

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.api.testProviders().subscribe({
      next: (res) => (this.providerStatus = res),
    });
    this.api.getCredentialsStatus().subscribe({
      next: (res) => (this.credentialStatuses = res),
    });
    this.api.getModels().subscribe({
      next: (res) => {
        this.availableModels = res;
        this.ensureValidAssignments();
      },
    });
    this.api.getAgentConfigurations().subscribe({
      next: (res) => {
        for (const [key, val] of Object.entries(res)) {
          if (this.agentAssignments[key]) {
            this.agentAssignments[key] = {
              provider: val.provider || 'gemini',
              model_id: val.model_id || 'gemini-2.5-flash',
            };
          }
        }
      },
    });
  }

  setProvider(agentId: string, provider: 'gemini' | 'openai') {
    if (this.agentAssignments[agentId]) {
      this.agentAssignments[agentId].provider = provider;
      const providerModels = this.getModelsForProvider(provider);
      if (providerModels.length > 0) {
        this.agentAssignments[agentId].model_id = providerModels[0].model_id;
      }
    }
  }

  saveCredentials(provider: string, key: string) {
    if (!key || key.trim().length < 8) {
      alert('Please enter a valid API key.');
      return;
    }
    this.api.setCredentials(provider, key.trim()).subscribe({
      next: (res) => {
        alert(`${provider.toUpperCase()} credentials encrypted & saved! Discovered ${res.available_models_count} live models.`);
        if (provider === 'gemini') this.geminiKey = '';
        if (provider === 'openai') this.openaiKey = '';
        this.loadData();
      },
      error: (err) => alert(`Validation failed: ${err.error?.detail || err.message}`),
    });
  }

  deleteCredentials(provider: string) {
    if (!confirm(`Are you sure you want to remove the saved ${provider.toUpperCase()} API key from the encrypted vault?`)) {
      return;
    }
    this.api.deleteCredentials(provider).subscribe({
      next: () => {
        alert(`${provider.toUpperCase()} credentials removed from encrypted vault.`);
        this.loadData();
      },
      error: (err) => alert(`Failed to revoke key: ${err.error?.detail || err.message}`),
    });
  }

  refreshModels() {
    this.isRefreshing = true;
    this.api.refreshModels().subscribe({
      next: (res) => {
        this.availableModels = res;
        this.isRefreshing = false;
        this.ensureValidAssignments();
      },
      error: () => {
        this.isRefreshing = false;
      },
    });
  }

  getModelsForProvider(provider: string) {
    const list = this.availableModels.filter((m) => m.provider.toLowerCase() === provider.toLowerCase());
    if (list.length === 0) {
      if (provider.toLowerCase() === 'gemini') {
        return [
          { model_id: 'gemini-2.5-flash', display_name: 'Gemini 2.5 Flash', provider: 'gemini' },
          { model_id: 'gemini-2.5-pro', display_name: 'Gemini 2.5 Pro', provider: 'gemini' },
          { model_id: 'gemini-2.0-flash', display_name: 'Gemini 2.0 Flash', provider: 'gemini' },
          { model_id: 'gemini-2.0-flash-thinking', display_name: 'Gemini 2.0 Flash Thinking', provider: 'gemini' },
        ];
      } else {
        return [
          { model_id: 'gpt-4o', display_name: 'GPT-4o (Omni)', provider: 'openai' },
          { model_id: 'gpt-4o-mini', display_name: 'GPT-4o Mini', provider: 'openai' },
          { model_id: 'o1', display_name: 'o1 (Reasoning)', provider: 'openai' },
          { model_id: 'o3-mini', display_name: 'o3-mini', provider: 'openai' },
        ];
      }
    }
    return list;
  }

  ensureValidAssignments() {
    for (const a of this.coreAgents) {
      const current = this.agentAssignments[a.id];
      const valid = this.getModelsForProvider(current.provider);
      if (!valid.some((m) => m.model_id === current.model_id) && valid.length > 0) {
        current.model_id = valid[0].model_id;
      }
    }
  }

  saveAgentModel(agentId: string) {
    const config = this.agentAssignments[agentId];
    this.api.switchAgentModel(agentId, config.provider, config.model_id).subscribe({
      next: () => {
        this.savedState[agentId] = true;
        setTimeout(() => {
          this.savedState[agentId] = false;
        }, 2500);
      },
      error: (err) => alert(`Update failed: ${err.message}`),
    });
  }
}
