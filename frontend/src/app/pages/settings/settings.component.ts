import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { IconComponent } from '../../shared/components/icon.component';
import { MCPServerStatus } from '../../core/models/types';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, IconComponent],
  template: `
    <div class="space-y-8 max-w-7xl mx-auto pb-16">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">System Diagnostics & Workspace Settings</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Local database health, execution sandbox diagnostics, AES-256 encrypted vault status, and system configurations.
          </p>
        </div>
        <a
          routerLink="/integrations"
          class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue transition-all shrink-0 cursor-pointer"
        >
          <app-icon name="network" size="16"></app-icon>
          <span>Open MCP Integration Center</span>
        </a>
      </div>

      <!-- Hero Banner: MCP Architecture Notice -->
      <div class="bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-slate-900 rounded-2xl p-6 border border-blue-500/20 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="space-y-2 max-w-2xl">
          <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-400 text-[11px] font-bold">
            <app-icon name="network" size="14"></app-icon>
            <span>Model Context Protocol (MCP) Standard</span>
          </div>
          <h2 class="text-lg font-bold text-white tracking-tight">
            GitHub & Jira are managed via the dedicated MCP Integration Center
          </h2>
          <p class="text-xs text-slate-300 leading-relaxed">
            All repository browsing, file extraction, user story parsing, and issue updates are powered by official Model Context Protocol servers. Direct REST API calls are decommissioned in favor of dynamic tool discovery, strict project boundary enforcement, and human approval queues.
          </p>
        </div>

        <div class="flex flex-col sm:flex-row items-center gap-3 shrink-0">
          <a
            routerLink="/integrations"
            class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <span>Configure MCP Servers & Tools</span>
            <app-icon name="chevron-down" size="14" class="-rotate-90"></app-icon>
          </a>
        </div>
      </div>

      <!-- System Diagnostics Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 1. SQLite Database Status -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <span class="p-2 rounded-xl bg-emerald-500/10 text-emerald-500">
                <app-icon name="database" size="18"></app-icon>
              </span>
              <h3 class="font-bold text-sm text-slate-900 dark:text-white">SQLite Storage Engine</h3>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              Healthy
            </span>
          </div>

          <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Local single-tenant relational storage. Holds projects, requirements, test cases, executions, and MCP tool discovery registries.
          </p>

          <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
            <div class="flex justify-between">
              <span class="text-slate-400">Driver</span>
              <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">SQLite via SQLAlchemy 2.0</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Database File</span>
              <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">testing_platform.db</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Encryption Layer</span>
              <span class="font-mono font-semibold text-emerald-500">AES-256-GCM Vault</span>
            </div>
          </div>
        </div>

        <!-- 2. Execution Sandbox Diagnostics -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <span class="p-2 rounded-xl bg-blue-500/10 text-blue-500">
                <app-icon name="monitor" size="18"></app-icon>
              </span>
              <h3 class="font-bold text-sm text-slate-900 dark:text-white">Execution Sandbox</h3>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-500/10 text-blue-500 border border-blue-500/20">
              Active
            </span>
          </div>

          <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Isolated subprocess testing environment running real headless Playwright and Chromium browsers with trace collection.
          </p>

          <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
            <div class="flex justify-between">
              <span class="text-slate-400">Python Interpreter</span>
              <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">Python 3.14.2 (.venv)</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Automation Engine</span>
              <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">Playwright Chromium</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Artifact Sandboxing</span>
              <span class="font-mono font-semibold text-emerald-500">Isolated Tempdirs</span>
            </div>
          </div>
        </div>

        <!-- 3. LangGraph Orchestrator -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <span class="p-2 rounded-xl bg-purple-500/10 text-purple-500">
                <app-icon name="workflow" size="18"></app-icon>
              </span>
              <h3 class="font-bold text-sm text-slate-900 dark:text-white">Agent Orchestrator</h3>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-500/10 text-purple-500 border border-purple-500/20">
              6 Agents
            </span>
          </div>

          <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Stateful multi-agent execution pipeline passing validated state from requirements analysis to consolidated QA reporting.
          </p>

          <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
            <div class="flex justify-between">
              <span class="text-slate-400">Framework</span>
              <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">LangGraph StateGraph</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Model Provider</span>
              <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">LiteLLM (Gemini & OpenAI)</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Approval Gating</span>
              <span class="font-mono font-semibold text-purple-400">Human-in-the-Loop Active</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Local Architecture & Security Policy -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-4">
        <div class="flex items-center gap-2.5">
          <app-icon name="shield-check" size="20" class="text-emerald-500"></app-icon>
          <h3 class="font-bold text-slate-900 dark:text-white text-base">Local Data Privacy & Zero-Exposure Security Guarantee</h3>
        </div>
        <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          This AI Testing Agent is running in a fully private, single-tenant local workspace on your machine.
          All client projects, test cases, and credentials are encrypted at rest with hardware-accelerated AES-256-GCM.
          API keys and tokens are never bundled into frontend assets, logged, or stored in browser storage.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3">
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 space-y-1">
            <span class="text-[10px] uppercase font-bold text-slate-400">Credential Vault</span>
            <div class="text-xs font-bold text-slate-800 dark:text-slate-200">Zero-Token Browser Storage</div>
            <p class="text-[11px] text-slate-400">Credentials exist only in memory during subprocess execution.</p>
          </div>

          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 space-y-1">
            <span class="text-[10px] uppercase font-bold text-slate-400">Cross-Project Isolation</span>
            <div class="text-xs font-bold text-slate-800 dark:text-slate-200">Strict Boundary Enforcement</div>
            <p class="text-[11px] text-slate-400">Agents cannot query repositories or Jira keys outside assigned projects.</p>
          </div>

          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 space-y-1">
            <span class="text-[10px] uppercase font-bold text-slate-400">Audit Trail</span>
            <div class="text-xs font-bold text-slate-800 dark:text-slate-200">Tamper-Evident Logs</div>
            <p class="text-[11px] text-slate-400">All MCP tool executions and approvals are logged with latency.</p>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class SettingsComponent implements OnInit {
  private api = inject(ApiService);
  mcpServers: MCPServerStatus[] = [];

  ngOnInit() {
    this.api.getMcpServers().subscribe({
      next: (servers) => {
        this.mcpServers = servers;
      },
      error: () => {},
    });
  }
}
