import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { CustomAgent } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';

@Component({
  selector: 'app-agents',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-8 max-w-7xl mx-auto pb-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 min-w-0">
        <div class="min-w-0 flex-1">
          <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight break-words min-w-0">My Agent Library</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            Six specialized autonomous testing agents plus your custom QA engineers.
          </p>
        </div>
        <button
          (click)="showCreateModal = true"
          class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all shadow-sm cursor-pointer shrink-0 self-start sm:self-auto"
        >
          <app-icon name="plus" size="14"></app-icon>
          <span>Build Custom Agent</span>
        </button>
      </div>

      <!-- Core 6 Agents Section -->
      <div>
        <div class="flex items-center gap-2 mb-4">
          <app-icon name="users" size="18" class="text-blue-600 dark:text-blue-400"></app-icon>
          <h2 class="font-bold text-slate-900 dark:text-white text-base">Predefined Core Testing Agents</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            *ngFor="let a of coreAgents"
            class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col justify-between hover:shadow-card transition-all"
          >
            <div>
              <div class="flex items-start justify-between gap-3 mb-3">
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center text-sm shadow-sm"
                  [style.background-color]="a.bgColor"
                  [style.color]="a.textColor"
                >
                  <app-icon [name]="a.icon" size="18"></app-icon>
                </div>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  Ready
                </span>
              </div>

              <h3 class="font-bold text-slate-900 dark:text-white text-sm leading-snug">{{ a.name }}</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">{{ a.description }}</p>
            </div>

            <div class="mt-5 pt-3.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
              <span class="text-slate-400 dark:text-slate-500">Assigned Model:</span>
              <span class="font-mono font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2 py-0.5 rounded-md">
                {{ agentConfigs[a.id]?.model_id || 'gemini-2.5-flash' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Custom QA Agents Section -->
      <div>
        <div class="flex items-center gap-2 mb-4">
          <app-icon name="bot" size="18" class="text-purple-600 dark:text-purple-400"></app-icon>
          <h2 class="font-bold text-slate-900 dark:text-white text-base">Custom Specialized Agents</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" *ngIf="customAgents.length; else noCustomTpl">
          <div
            *ngFor="let ca of customAgents"
            class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-purple-200/80 dark:border-purple-900/60 shadow-subtle flex flex-col justify-between"
          >
            <div>
              <div class="flex items-start justify-between gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                  <app-icon name="bot" size="18"></app-icon>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300">
                    {{ ca.category }}
                  </span>
                  <button
                    (click)="deleteCustomAgent(ca.id)"
                    class="text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 p-1"
                    title="Delete Custom Agent"
                  >
                    <app-icon name="trash-2" size="14"></app-icon>
                  </button>
                </div>
              </div>

              <h3 class="font-bold text-slate-900 dark:text-white text-sm">{{ ca.name }}</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{{ ca.description || 'Custom tester instructions configured.' }}</p>
            </div>

            <div class="mt-5 pt-3.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
              <span class="text-slate-400 dark:text-slate-500">Provider & Model:</span>
              <span class="font-mono text-slate-700 dark:text-slate-300 font-medium">
                {{ ca.provider }} / {{ ca.model_id }}
              </span>
            </div>
          </div>
        </div>

        <ng-template #noCustomTpl>
          <div class="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800">
            <app-icon name="bot" size="32" class="text-slate-400 mx-auto mb-2"></app-icon>
            <div class="font-semibold text-slate-700 dark:text-slate-300 text-sm">No Custom Agents Created</div>
            <div class="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
              Need specialized testing like API Security, Performance, or Accessibility? Build one and reuse it anywhere.
            </div>
            <button
              (click)="showCreateModal = true"
              class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl text-xs shadow-sm cursor-pointer"
            >
              + Build Custom Agent
            </button>
          </div>
        </ng-template>
      </div>

      <!-- Build Custom Agent Modal -->
      <div
        *ngIf="showCreateModal"
        class="fixed inset-0 !m-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4"
      >
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-5 sm:p-6 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-base font-bold text-slate-900 dark:text-white">Build Specialized Custom Agent</h2>
            <button (click)="showCreateModal = false" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <app-icon name="x" size="18"></app-icon>
            </button>
          </div>

          <form (ngSubmit)="createCustomAgent()" class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Agent Name *</label>
              <input
                type="text"
                [(ngModel)]="newAgent.name"
                name="name"
                required
                placeholder="e.g. API Security Testing Agent"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Category</label>
                <select
                  [(ngModel)]="newAgent.category"
                  name="category"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
                >
                  <option value="API Security">API Security</option>
                  <option value="Performance & Load">Performance & Load</option>
                  <option value="Database Validation">Database Validation</option>
                  <option value="Accessibility (a11y)">Accessibility (a11y)</option>
                  <option value="Regression Testing">Regression Testing</option>
                  <option value="Specialized QA">Specialized QA</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">AI Provider</label>
                <select
                  [(ngModel)]="newAgent.provider"
                  name="provider"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none"
                >
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Model ID</label>
              <input
                type="text"
                [(ngModel)]="newAgent.model_id"
                name="model_id"
                placeholder="gemini-2.5-flash or gpt-4o"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none font-mono"
              />
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">System Instructions *</label>
              <textarea
                [(ngModel)]="newAgent.system_instructions"
                name="system_instructions"
                rows="4"
                required
                placeholder="Specify the QA agent's role, heuristics, boundary conditions, and test verification standards..."
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-white focus:border-blue-500 outline-none font-mono"
              ></textarea>
            </div>

            <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                (click)="showCreateModal = false"
                class="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Cancel
              </button>
              <button
                type="submit"
                [disabled]="!newAgent.name || !newAgent.system_instructions"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow-sm disabled:opacity-50"
              >
                Save Agent
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
})
export class AgentsComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  showCreateModal = false;
  agentConfigs: Record<string, any> = {};
  customAgents: CustomAgent[] = [];

  coreAgents = [
    {
      id: 'agent_1_requirement_analysis',
      name: 'Requirement Analysis Agent',
      icon: 'search',
      bgColor: '#eff6ff',
      textColor: '#2563eb',
      description: 'Extracts structured requirements, acceptance criteria, and edge cases from Jira, Git, and documents.',
    },
    {
      id: 'agent_2_scenario_generation',
      name: 'Test Scenario Generator',
      icon: 'check',
      bgColor: '#ecfdf5',
      textColor: '#059669',
      description: 'Generates positive, negative, boundary, and edge-case test scenarios directly from requirements.',
    },
    {
      id: 'agent_3_test_case_design',
      name: 'Test Case Designer',
      icon: 'clipboard-list',
      bgColor: '#f5f3ff',
      textColor: '#6366f1',
      description: 'Designs executable step-by-step test cases with realistic test data and assertions.',
    },
    {
      id: 'agent_4_test_automation',
      name: 'Test Automation Agent',
      icon: 'cog',
      bgColor: '#fff7ed',
      textColor: '#ea580c',
      description: 'Converts test cases into robust Playwright and Selenium Python browser scripts targeting your Live URL.',
    },
    {
      id: 'agent_5_test_execution',
      name: 'Test Execution Agent',
      icon: 'play',
      bgColor: '#f0fdfa',
      textColor: '#0d9488',
      description: 'Runs automated test suites in isolated sandboxes and classifies failures with AI triage.',
    },
    {
      id: 'agent_6_orchestration_reporting',
      name: 'Test Reporting Agent',
      icon: 'bar-chart-3',
      bgColor: '#faf5ff',
      textColor: '#7c3aed',
      description: 'Coordinates execution lifecycle gates, calculates coverage metrics, and generates audit reports.',
    },
  ];

  newAgent = {
    name: '',
    description: '',
    category: 'API Security',
    system_instructions: '',
    provider: 'gemini',
    model_id: 'gemini-2.5-flash',
  };

  ngOnInit() {
    this.loadData();
    this.route.queryParams.subscribe((params) => {
      if (params['action'] === 'create') {
        this.showCreateModal = true;
      }
    });
  }

  loadData() {
    this.api.getAgentConfigurations().subscribe({
      next: (res) => (this.agentConfigs = res),
    });
    this.api.getCustomAgents().subscribe({
      next: (res) => (this.customAgents = res),
    });
  }

  createCustomAgent() {
    this.api.createCustomAgent(this.newAgent).subscribe({
      next: () => {
        this.showCreateModal = false;
        this.newAgent = {
          name: '',
          description: '',
          category: 'API Security',
          system_instructions: '',
          provider: 'gemini',
          model_id: 'gemini-2.5-flash',
        };
        this.loadData();
      },
    });
  }

  deleteCustomAgent(id: string) {
    if (confirm('Delete this custom agent?')) {
      this.api.deleteCustomAgent(id).subscribe({
        next: () => this.loadData(),
      });
    }
  }
}
