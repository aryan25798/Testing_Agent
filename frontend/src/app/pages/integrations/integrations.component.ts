import { Component, OnInit, OnDestroy, HostListener, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { IconComponent } from '../../shared/components/icon.component';
import {
  MCPServerStatus,
  MCPToolInfo,
  Project,
  ProjectMCPMapping,
  MCPApprovalRequest,
  MCPInvocationLog,
} from '../../core/models/types';

@Component({
  selector: 'app-integrations',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="space-y-8 max-w-7xl mx-auto pb-16">
      <!-- 1. Header Banner -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div class="flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center p-2 rounded-xl bg-blue-600/10 text-blue-500 dark:text-blue-400">
              <app-icon name="network" size="22"></app-icon>
            </span>
            <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Model Context Protocol (MCP) Integration Center
            </h1>
          </div>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Official GitHub and Atlassian MCP clients. Real tool capability negotiation, strict least-privilege agent restrictions, and human-in-the-loop approval gates.
          </p>
        </div>

        <!-- Global Status Badges -->
        <div class="flex items-center gap-3">
          <div class="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-xs flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" [ngClass]="connectedCount > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'"></span>
            <span class="font-semibold text-slate-700 dark:text-slate-200">{{ connectedCount }} / 2 Connected</span>
          </div>
          <div *ngIf="pendingApprovals.length > 0" class="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-500 dark:text-amber-400 text-xs font-semibold flex items-center gap-1.5">
            <app-icon name="alert-circle" size="14"></app-icon>
            <span>{{ pendingApprovals.length }} Approvals Pending</span>
          </div>
          <button
            (click)="refreshAll()"
            [disabled]="loading"
            class="p-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
            title="Refresh All"
          >
            <app-icon name="rotate-ccw" size="16" [class.animate-spin]="loading"></app-icon>
          </button>
        </div>
      </div>

      <!-- Notification Toast -->
      <div
        *ngIf="notification"
        class="p-4 rounded-xl text-xs font-medium flex items-center justify-between shadow-lg transition-all animate-fadeIn"
        [ngClass]="notification.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400' : 'bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400'"
      >
        <div class="flex items-center gap-2.5">
          <app-icon [name]="notification.type === 'success' ? 'check-circle-2' : 'alert-circle'" size="16"></app-icon>
          <span>{{ notification.message }}</span>
        </div>
        <button (click)="notification = null" class="p-1 hover:opacity-75">
          <app-icon name="x" size="14"></app-icon>
        </button>
      </div>

      <!-- 2. Navigation Tabs (Responsive & Non-overlapping with shrink-0) -->
      <div class="flex items-center border-b border-slate-200/80 dark:border-slate-800 gap-1 sm:gap-2.5 overflow-x-auto pb-px">
        <button
          (click)="activeTab = 'servers'"
          class="shrink-0 pb-3 px-2.5 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-1.5 sm:gap-2 whitespace-nowrap cursor-pointer select-none"
          [ngClass]="activeTab === 'servers' ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'"
        >
          <app-icon name="network" size="16"></app-icon>
          <span>MCP Server Connections</span>
        </button>

        <button
          (click)="activeTab = 'mappings'"
          class="shrink-0 pb-3 px-2.5 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-1.5 sm:gap-2 whitespace-nowrap cursor-pointer select-none"
          [ngClass]="activeTab === 'mappings' ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'"
        >
          <app-icon name="folder" size="16"></app-icon>
          <span>Project Resource Mapping</span>
        </button>

        <button
          (click)="activeTab = 'tools'"
          class="shrink-0 pb-3 px-2.5 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-1.5 sm:gap-2 whitespace-nowrap cursor-pointer select-none"
          [ngClass]="activeTab === 'tools' ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'"
        >
          <app-icon name="workflow" size="16"></app-icon>
          <span>Discovered Tools ({{ tools.length }})</span>
        </button>

        <button
          (click)="activeTab = 'approvals'"
          class="shrink-0 pb-3 px-2.5 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-1.5 sm:gap-2 whitespace-nowrap cursor-pointer select-none"
          [ngClass]="activeTab === 'approvals' ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'"
        >
          <app-icon name="shield-check" size="16"></app-icon>
          <span>Approval Queue</span>
          <span *ngIf="pendingApprovals.length > 0" class="px-1.5 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-bold">
            {{ pendingApprovals.length }}
          </span>
        </button>

        <button
          (click)="activeTab = 'logs'"
          class="shrink-0 pb-3 px-2.5 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-1.5 sm:gap-2 whitespace-nowrap cursor-pointer select-none"
          [ngClass]="activeTab === 'logs' ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'"
        >
          <app-icon name="clock" size="16"></app-icon>
          <span>Audit Log</span>
        </button>
      </div>

      <!-- ========================================== -->
      <!-- TAB 1: MCP Server Connections (Cards)      -->
      <!-- ========================================== -->
      <div *ngIf="activeTab === 'servers'" class="space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
          <!-- 1. Official GitHub MCP Server Card -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 sm:p-6 flex flex-col justify-between shadow-subtle hover:border-slate-300 dark:hover:border-slate-700 transition-all min-w-0">
            <div class="space-y-4 min-w-0">
              <!-- Top Provider Header -->
              <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4 min-w-0">
                <div class="flex items-start gap-3 min-w-0 flex-1">
                  <div class="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center font-black text-xl shadow-md border border-slate-700 shrink-0">
                    <svg class="w-5 h-5 sm:w-6 sm:h-6 fill-current" viewBox="0 0 24 24">
                      <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
                    </svg>
                  </div>
                  <div class="min-w-0 flex-1">
                    <h3 class="font-bold text-slate-900 dark:text-white text-base">Official GitHub MCP Server</h3>
                    <p class="text-[11px] text-slate-400 break-words mt-0.5">Official protocol stdio client via &#64;modelcontextprotocol/server-github</p>
                  </div>
                </div>

                <!-- Status Pill -->
                <span
                  class="px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 shrink-0 self-start whitespace-nowrap"
                  [ngClass]="getServer('github')?.status === 'connected' ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border border-emerald-500/20' : 'bg-slate-200 dark:bg-slate-800 text-slate-500 border border-slate-300 dark:border-slate-700'"
                >
                  <span class="w-1.5 h-1.5 rounded-full shrink-0" [ngClass]="getServer('github')?.status === 'connected' ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                  {{ getServer('github')?.status || 'Disconnected' }}
                </span>
              </div>

              <!-- Technical Details Matrix -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 text-xs">
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Transport Layer</span>
                  <span class="font-mono text-slate-700 dark:text-slate-200 font-semibold truncate block">stdio (Subprocess)</span>
                </div>
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Execution Mode</span>
                  <span class="font-semibold truncate block" [ngClass]="getServer('github')?.is_read_only ? 'text-amber-500 dark:text-amber-400' : 'text-blue-500'">
                    {{ getServer('github')?.is_read_only ? 'Read-Only (Enforced)' : 'Read & Write' }}
                  </span>
                </div>
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Discovered Tools</span>
                  <span class="font-bold text-slate-900 dark:text-white font-mono truncate block">{{ getServer('github')?.available_tools_count || 0 }} tools active</span>
                </div>
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Authenticated User</span>
                  <span class="font-semibold text-slate-700 dark:text-slate-200 truncate block">
                    {{ getServer('github')?.account_login || 'Not logged in' }}
                  </span>
                </div>
              </div>

              <!-- Capabilities Highlight -->
              <div class="text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                <div class="flex items-center gap-1.5">
                  <app-icon name="check" size="12" class="text-emerald-500 shrink-0"></app-icon>
                  <span>Repository tree browsing, file inspection, and commit tracking.</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <app-icon name="check" size="12" class="text-emerald-500 shrink-0"></app-icon>
                  <span>Read PRs, issues, and test code for context-aware automation.</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <app-icon name="shield-check" size="12" class="text-blue-500 shrink-0"></app-icon>
                  <span>Tokens stored exclusively in AES-256 backend vault. Never sent to browser.</span>
                </div>
              </div>

              <!-- Error Box if any -->
              <div *ngIf="getServer('github')?.last_error" class="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs break-words">
                {{ getServer('github')?.last_error }}
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-5 mt-4 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
              <button
                *ngIf="getServer('github')?.status === 'connected'"
                (click)="disconnectServer('github')"
                [disabled]="connectingGithub"
                class="px-4 py-2.5 rounded-xl text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 transition-colors w-full sm:w-auto text-center"
              >
                Disconnect
              </button>

              <button
                (click)="openGithubModal()"
                [disabled]="connectingGithub"
                class="sm:ml-auto w-full sm:w-auto px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                <app-icon name="network" size="14"></app-icon>
                <span>{{ getServer('github')?.status === 'connected' ? 'Configure & Reconnect' : 'Connect GitHub MCP' }}</span>
              </button>
            </div>
          </div>

          <!-- 2. Official Atlassian / Jira MCP Server Card -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 sm:p-6 flex flex-col justify-between shadow-subtle hover:border-slate-300 dark:hover:border-slate-700 transition-all min-w-0">
            <div class="space-y-4 min-w-0">
              <!-- Top Provider Header -->
              <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4 min-w-0">
                <div class="flex items-start gap-3 min-w-0 flex-1">
                  <div class="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-xl shadow-md shrink-0">
                    <svg class="w-5 h-5 sm:w-6 sm:h-6 fill-current" viewBox="0 0 24 24">
                      <path d="M11.53 2c0 2.4-1.97 4.35-4.4 4.35H2.8C2.36 6.35 2 6.71 2 7.15v4.33c0 .44.36.8.8.8h4.33c2.4 0 4.4 1.95 4.4 4.35 0 2.4-1.97 4.35-4.4 4.35H2.8c-.44 0-.8.36-.8.8v.22c0 .44.36.8.8.8h4.33c4.2 0 7.6-3.4 7.6-7.6 0-1.87-.67-3.58-1.8-4.9 1.13-1.32 1.8-3.03 1.8-4.9 0-4.2-3.4-7.6-7.6-7.6H2.8c-.44 0-.8.36-.8.8v.22c0 .44.36.8.8.8h4.33c2.43 0 4.4 1.95 4.4 4.35z"/>
                    </svg>
                  </div>
                  <div class="min-w-0 flex-1">
                    <h3 class="font-bold text-slate-900 dark:text-white text-base">Official Atlassian MCP Server</h3>
                    <p class="text-[11px] text-slate-400 break-words mt-0.5">Jira Software Cloud tools via official MCP server (SSE & stdio)</p>
                  </div>
                </div>

                <!-- Status Pill -->
                <span
                  class="px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 shrink-0 self-start whitespace-nowrap"
                  [ngClass]="getServer('atlassian')?.status === 'connected' ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border border-emerald-500/20' : 'bg-slate-200 dark:bg-slate-800 text-slate-500 border border-slate-300 dark:border-slate-700'"
                >
                  <span class="w-1.5 h-1.5 rounded-full shrink-0" [ngClass]="getServer('atlassian')?.status === 'connected' ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                  {{ getServer('atlassian')?.status || 'Disconnected' }}
                </span>
              </div>

              <!-- Technical Details Matrix -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 text-xs">
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Transport Layer</span>
                  <span class="font-mono text-slate-700 dark:text-slate-200 font-semibold truncate block">{{ getServer('atlassian')?.transport || 'stdio / sse' }}</span>
                </div>
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Execution Mode</span>
                  <span class="font-semibold truncate block" [ngClass]="getServer('atlassian')?.is_read_only ? 'text-amber-500 dark:text-amber-400' : 'text-blue-500'">
                    {{ getServer('atlassian')?.is_read_only ? 'Read-Only (Enforced)' : 'Read & Write' }}
                  </span>
                </div>
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Discovered Tools</span>
                  <span class="font-bold text-slate-900 dark:text-white font-mono truncate block">{{ getServer('atlassian')?.available_tools_count || 0 }} tools active</span>
                </div>
                <div class="min-w-0">
                  <span class="text-slate-400 text-[10px] block uppercase font-bold">Host Endpoint</span>
                  <span class="font-semibold text-slate-700 dark:text-slate-200 truncate block">
                    {{ getServer('atlassian')?.server_url || 'mcp.atlassian.com' }}
                  </span>
                </div>
              </div>

              <!-- Capabilities Highlight -->
              <div class="text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                <div class="flex items-center gap-1.5">
                  <app-icon name="check" size="12" class="text-emerald-500 shrink-0"></app-icon>
                  <span>Query Jira user stories, acceptance criteria, and issues via JQL.</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <app-icon name="check" size="12" class="text-emerald-500 shrink-0"></app-icon>
                  <span>Dynamic issue schema inspection with zero hardcoded endpoints.</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <app-icon name="shield-check" size="12" class="text-blue-500 shrink-0"></app-icon>
                  <span>Human approval required for any mutating actions (status changes, comments).</span>
                </div>
              </div>

              <!-- Error Box if any -->
              <div *ngIf="getServer('atlassian')?.last_error" class="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs break-words">
                {{ getServer('atlassian')?.last_error }}
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-5 mt-4 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
              <button
                *ngIf="getServer('atlassian')?.status === 'connected'"
                (click)="disconnectServer('atlassian')"
                [disabled]="connectingAtlassian"
                class="px-4 py-2.5 rounded-xl text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 transition-colors w-full sm:w-auto text-center"
              >
                Disconnect
              </button>

              <button
                (click)="openAtlassianModal()"
                [disabled]="connectingAtlassian"
                class="sm:ml-auto w-full sm:w-auto px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                <app-icon name="network" size="14"></app-icon>
                <span>{{ getServer('atlassian')?.status === 'connected' ? 'Configure & Reconnect' : 'Connect Atlassian MCP' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 2: Project Resource Mapping            -->
      <!-- ========================================== -->
      <div *ngIf="activeTab === 'mappings'" class="space-y-6">
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-subtle space-y-6">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">Project-Level Integration Mapping</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Assign specific GitHub repositories and Jira project keys to each internal client project. Enforces strict boundary isolation.
              </p>
            </div>

            <!-- Project Selector Dropdown -->
            <div class="flex items-center gap-2">
              <label class="text-xs font-bold text-slate-500">Internal Project:</label>
              <select
                [(ngModel)]="selectedProjectId"
                (change)="loadProjectMapping()"
                class="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs font-medium focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option *ngFor="let p of projects" [value]="p.id">{{ p.name }} ({{ p.framework }})</option>
              </select>
            </div>
          </div>

          <!-- Mapping Forms Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <!-- GitHub Repo Mapping -->
            <div class="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <app-icon name="folder" size="18" class="text-slate-700 dark:text-slate-200"></app-icon>
                  <h3 class="font-bold text-sm text-slate-900 dark:text-white">GitHub Repository Scope</h3>
                </div>
                <span class="text-[11px] font-mono text-blue-500">MCP Tool: get_file_contents</span>
              </div>

              <div>
                <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Target Repository (owner/repo)</label>
                <div class="flex gap-2">
                  <input
                    type="text"
                    [(ngModel)]="activeMapping.githubRepo"
                    placeholder="e.g. aryan25798/Testing_Agent"
                    class="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                  />
                  <button
                    (click)="discoverRepos()"
                    [disabled]="discoveringRepos || getServer('github')?.status !== 'connected'"
                    class="px-3 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-white text-xs font-semibold disabled:opacity-50"
                    title="Discover Repositories via MCP"
                  >
                    {{ discoveringRepos ? 'Scanning...' : 'Discover' }}
                  </button>
                </div>
                <p class="text-[10px] text-slate-400 mt-1">Cross-project access outside this repository will be blocked by the MCP Tool Registry.</p>
              </div>

              <!-- Discovered Repos Picker if loaded -->
              <div *ngIf="discoveredRepos.length > 0" class="space-y-1 max-h-36 overflow-y-auto p-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">Select from your GitHub repos:</span>
                <div
                  *ngFor="let r of discoveredRepos"
                  (click)="activeMapping.githubRepo = r.full_name"
                  class="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 cursor-pointer text-xs flex items-center justify-between"
                  [ngClass]="activeMapping.githubRepo === r.full_name ? 'bg-blue-50 dark:bg-blue-900/30' : ''"
                >
                  <span class="font-mono font-medium text-slate-800 dark:text-slate-200">{{ r.full_name }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-500">{{ r.default_branch }}</span>
                </div>
              </div>

              <div>
                <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Default Branch</label>
                <input
                  type="text"
                  [(ngModel)]="activeMapping.githubBranch"
                  placeholder="main"
                  class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
                />
              </div>
            </div>

            <!-- Jira Project Mapping -->
            <div class="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <app-icon name="workflow" size="18" class="text-blue-500"></app-icon>
                  <h3 class="font-bold text-sm text-slate-900 dark:text-white">Jira Project Key Scope</h3>
                </div>
                <span class="text-[11px] font-mono text-blue-500">MCP Tool: jira_search</span>
              </div>

              <div>
                <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Jira Project Key</label>
                <div class="flex gap-2">
                  <input
                    type="text"
                    [(ngModel)]="activeMapping.jiraKey"
                    placeholder="e.g. TEST, PROJ, QA"
                    class="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white uppercase focus:border-blue-500 outline-none"
                  />
                  <button
                    (click)="discoverJiraProjects()"
                    [disabled]="discoveringJira || getServer('atlassian')?.status !== 'connected'"
                    class="px-3 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-white text-xs font-semibold disabled:opacity-50"
                    title="Discover Jira Projects via MCP"
                  >
                    {{ discoveringJira ? 'Scanning...' : 'Discover' }}
                  </button>
                </div>
                <p class="text-[10px] text-slate-400 mt-1">Queries for issues outside this key will be restricted.</p>
              </div>

              <!-- Discovered Jira Projects Picker if loaded -->
              <div *ngIf="discoveredJiraProjects.length > 0" class="space-y-1 max-h-36 overflow-y-auto p-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">Select from your Jira projects:</span>
                <div
                  *ngFor="let jp of discoveredJiraProjects"
                  (click)="activeMapping.jiraKey = jp.key"
                  class="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 cursor-pointer text-xs flex items-center justify-between"
                  [ngClass]="activeMapping.jiraKey === jp.key ? 'bg-blue-50 dark:bg-blue-900/30' : ''"
                >
                  <span class="font-bold text-slate-800 dark:text-slate-200">{{ jp.key }}</span>
                  <span class="text-[11px] text-slate-500">{{ jp.name }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Save Button -->
          <div class="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              (click)="saveMapping()"
              [disabled]="savingMapping"
              class="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <app-icon name="check" size="14"></app-icon>
              <span>{{ savingMapping ? 'Saving...' : 'Save Integration Mapping' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 3: Discovered Tools Matrix             -->
      <!-- ========================================== -->
      <div *ngIf="activeTab === 'tools'" class="space-y-6">
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-subtle space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">Dynamically Discovered MCP Tools</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Tools negotiated via standard MCP capabilities protocol. Each tool is bound to a least-privilege agent permission matrix.
              </p>
            </div>

            <!-- Provider Filter -->
            <div class="flex items-center gap-2">
              <button
                (click)="toolFilter = 'all'"
                class="px-3 py-1.5 rounded-xl text-xs font-bold transition-colors"
                [ngClass]="toolFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'"
              >
                All ({{ tools.length }})
              </button>
              <button
                (click)="toolFilter = 'github'"
                class="px-3 py-1.5 rounded-xl text-xs font-bold transition-colors"
                [ngClass]="toolFilter === 'github' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'"
              >
                GitHub
              </button>
              <button
                (click)="toolFilter = 'atlassian'"
                class="px-3 py-1.5 rounded-xl text-xs font-bold transition-colors"
                [ngClass]="toolFilter === 'atlassian' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'"
              >
                Atlassian
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div *ngIf="filteredTools.length === 0" class="text-center py-12 text-slate-400 space-y-2">
            <app-icon name="workflow" size="32" class="mx-auto opacity-50"></app-icon>
            <p class="text-sm font-semibold">No tools discovered yet</p>
            <p class="text-xs">Connect to the GitHub or Atlassian MCP server to dynamically negotiate tool capabilities.</p>
          </div>

          <!-- Tools Grid -->
          <div *ngIf="filteredTools.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            <div
              *ngFor="let t of filteredTools"
              class="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 hover:border-blue-500/40 transition-all flex flex-col justify-between space-y-3"
            >
              <div>
                <div class="flex items-center justify-between gap-2">
                  <span class="font-mono font-bold text-xs text-blue-600 dark:text-blue-400 truncate">{{ t.tool_name }}</span>
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                    [ngClass]="t.is_read_only ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'"
                  >
                    {{ t.is_read_only ? 'Read-Only' : 'Mutating' }}
                  </span>
                </div>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                  {{ t.description || 'No description provided by server.' }}
                </p>
              </div>

              <div class="pt-2 border-t border-slate-200/60 dark:border-slate-800/80 space-y-1.5">
                <div class="flex items-center justify-between text-[10px]">
                  <span class="text-slate-400 uppercase font-bold">Authorized Agents</span>
                  <span class="font-semibold text-slate-700 dark:text-slate-300">{{ t.allowed_agents.length || 1 }} agents</span>
                </div>
                <div class="flex flex-wrap gap-1">
                  <span
                    *ngFor="let a of t.allowed_agents"
                    class="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-[9px] font-mono"
                  >
                    {{ a.replace('agent_', 'A') }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 4: Human Approval Queue                -->
      <!-- ========================================== -->
      <div *ngIf="activeTab === 'approvals'" class="space-y-6">
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-subtle space-y-4">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-white">Human Approval Queue (Mutating Operations)</h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Strict human-in-the-loop requirement. Any tool that alters files, creates branches, updates PRs, or modifies Jira issues pauses until you approve.
            </p>
          </div>

          <!-- Empty State -->
          <div *ngIf="pendingApprovals.length === 0" class="text-center py-12 text-slate-400 space-y-2">
            <app-icon name="shield-check" size="32" class="mx-auto text-emerald-500 opacity-80"></app-icon>
            <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">No Pending Approvals</p>
            <p class="text-xs">All agent operations are within read-only boundaries. No mutating actions require review.</p>
          </div>

          <!-- Pending Cards -->
          <div *ngIf="pendingApprovals.length > 0" class="space-y-4 pt-2">
            <div
              *ngFor="let req of pendingApprovals"
              class="p-5 rounded-xl border border-amber-500/30 bg-amber-500/5 dark:bg-amber-500/10 space-y-4"
            >
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="p-1.5 rounded-lg bg-amber-500 text-white">
                    <app-icon name="alert-circle" size="16"></app-icon>
                  </span>
                  <div>
                    <h3 class="font-bold text-sm text-slate-900 dark:text-white">{{ req.tool_name }} on {{ req.target_object }}</h3>
                    <p class="text-xs text-slate-500 dark:text-slate-400">{{ req.operation_description }}</p>
                  </div>
                </div>

                <div class="flex items-center gap-2">
                  <button
                    (click)="decideApproval(req.id, 'rejected')"
                    class="px-4 py-2 rounded-xl text-xs font-bold text-rose-600 dark:text-rose-400 bg-white dark:bg-slate-800 border border-rose-200 dark:border-rose-900/60 hover:bg-rose-50"
                  >
                    Reject
                  </button>
                  <button
                    (click)="decideApproval(req.id, 'approved')"
                    class="px-5 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-md flex items-center gap-1.5"
                  >
                    <app-icon name="check" size="14"></app-icon>
                    <span>Approve & Execute</span>
                  </button>
                </div>
              </div>

              <!-- Proposed Arguments / Diff Box -->
              <div *ngIf="req.proposed_diff" class="p-3 rounded-lg bg-slate-950 text-emerald-400 font-mono text-[11px] overflow-x-auto max-h-48 border border-slate-800">
                <pre>{{ req.proposed_diff }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 5: MCP Invocation Audit Log            -->
      <!-- ========================================== -->
      <div *ngIf="activeTab === 'logs'" class="space-y-6">
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-subtle space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">MCP Invocation Audit Log</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Every MCP request and protocol tool invocation is recorded with timing, requesting agent, and status.
              </p>
            </div>
            <button
              (click)="loadLogs()"
              class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Refresh Logs
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase font-bold text-[10px]">
                <tr>
                  <th class="py-3 px-4">Timestamp</th>
                  <th class="py-3 px-4">Tool Name</th>
                  <th class="py-3 px-4">Agent ID</th>
                  <th class="py-3 px-4">Status</th>
                  <th class="py-3 px-4">Latency</th>
                  <th class="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                <tr *ngFor="let log of logs" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                  <td class="py-2.5 px-4 text-slate-500 whitespace-nowrap">{{ log.invoked_at | date:'HH:mm:ss' }}</td>
                  <td class="py-2.5 px-4 font-bold text-blue-600 dark:text-blue-400">{{ log.tool_name }}</td>
                  <td class="py-2.5 px-4 text-slate-600 dark:text-slate-300">{{ log.agent_id }}</td>
                  <td class="py-2.5 px-4">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                      [ngClass]="log.status === 'success' ? 'bg-emerald-500/10 text-emerald-500' : (log.status === 'blocked' ? 'bg-amber-500/10 text-amber-500' : 'bg-rose-500/10 text-rose-500')"
                    >
                      {{ log.status }}
                    </span>
                  </td>
                  <td class="py-2.5 px-4 text-slate-500">{{ log.duration_ms }}ms</td>
                  <td class="py-2.5 px-4 text-slate-400 truncate max-w-xs">{{ log.error_message || 'OK' }}</td>
                </tr>
                <tr *ngIf="logs.length === 0">
                  <td colspan="6" class="py-8 text-center text-slate-400 font-sans">No MCP invocations recorded yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- MODAL 1: Connect GitHub MCP Server         -->
      <!-- ========================================== -->
      <div
        *ngIf="showGithubModal"
        (click)="closeGithubModal()"
        class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/75 backdrop-blur-sm animate-fadeIn"
      >
        <div
          (click)="$event.stopPropagation()"
          class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-lg w-full max-h-[min(90vh,680px)] flex flex-col shadow-2xl overflow-hidden"
        >
          <!-- Modal Header (shrink-0) -->
          <div class="p-5 sm:p-6 pb-3 sm:pb-4 border-b border-slate-100 dark:border-slate-800 shrink-0 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold shrink-0">
                <app-icon name="folder" size="20"></app-icon>
              </div>
              <div class="min-w-0">
                <h3 class="font-bold text-slate-900 dark:text-white text-base truncate">Connect Official GitHub MCP</h3>
                <p class="text-[11px] text-slate-400 truncate">Subprocess transport via &#64;modelcontextprotocol/server-github</p>
              </div>
            </div>
            <button
              (click)="closeGithubModal()"
              class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0"
              aria-label="Close dialog"
            >
              <app-icon name="x" size="16"></app-icon>
            </button>
          </div>

          <!-- Modal Body (Scrollable flex-1) -->
          <div class="p-5 sm:p-6 overflow-y-auto flex-1 space-y-4">
            <div class="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-xs space-y-1">
              <div class="font-bold flex items-center gap-1.5">
                <app-icon name="shield-check" size="14"></app-icon>
                <span>Zero-Exposure Security Guarantee</span>
              </div>
              <p class="text-[11px] text-blue-500 dark:text-blue-300">
                Your Personal Access Token is saved into the backend encrypted vault (AES-256-GCM). It is never sent to the browser or stored in localStorage.
              </p>
            </div>

            <div class="space-y-4">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  GitHub Personal Access Token (classic or fine-grained)
                </label>
                <input
                  type="password"
                  [(ngModel)]="githubTokenInput"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx (Leave blank to use vaulted secret)"
                  class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none font-mono"
                />
                <p class="text-[10px] text-slate-400 mt-1">Required scopes: <code class="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">repo</code>, <code class="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">read:org</code>.</p>
              </div>

              <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                <div>
                  <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">Enforce Read-Only Mode</span>
                  <span class="text-[10px] text-slate-400">Restricts AI agents to reading files and issues only.</span>
                </div>
                <input type="checkbox" [(ngModel)]="githubReadOnly" class="w-4 h-4 rounded text-blue-600 cursor-pointer" />
              </div>
            </div>
          </div>

          <!-- Modal Footer (shrink-0) -->
          <div class="p-4 sm:p-5 border-t border-slate-100 dark:border-slate-800 shrink-0 flex items-center justify-end gap-3 bg-slate-50/50 dark:bg-slate-900/50">
            <button
              (click)="closeGithubModal()"
              class="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              (click)="submitGithubConnect()"
              [disabled]="connectingGithub"
              class="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <app-icon name="network" size="14" [class.animate-spin]="connectingGithub"></app-icon>
              <span>{{ connectingGithub ? 'Connecting Subprocess...' : 'Start MCP Session' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- MODAL 2: Connect Atlassian MCP Server      -->
      <!-- ========================================== -->
      <div
        *ngIf="showAtlassianModal"
        (click)="closeAtlassianModal()"
        class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/75 backdrop-blur-sm animate-fadeIn"
      >
        <div
          (click)="$event.stopPropagation()"
          class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-lg w-full max-h-[min(90vh,680px)] flex flex-col shadow-2xl overflow-hidden"
        >
          <!-- Modal Header (shrink-0) -->
          <div class="p-5 sm:p-6 pb-3 sm:pb-4 border-b border-slate-100 dark:border-slate-800 shrink-0 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold shrink-0">
                <app-icon name="workflow" size="20"></app-icon>
              </div>
              <div class="min-w-0">
                <h3 class="font-bold text-slate-900 dark:text-white text-base truncate">Connect Official Atlassian MCP</h3>
                <p class="text-[11px] text-slate-400 truncate">Standard MCP connection to Jira Software Cloud</p>
              </div>
            </div>
            <button
              (click)="closeAtlassianModal()"
              class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0"
              aria-label="Close dialog"
            >
              <app-icon name="x" size="16"></app-icon>
            </button>
          </div>

          <!-- Modal Body (Scrollable flex-1) -->
          <div class="p-5 sm:p-6 overflow-y-auto flex-1 space-y-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Transport Mode
              </label>
              <select
                [(ngModel)]="atlassianTransport"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              >
                <option value="stdio">Local Subprocess (mcp-atlassian stdio)</option>
                <option value="sse">Remote Server-Sent Events (mcp.atlassian.com/v2/mcp)</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Jira Instance URL
              </label>
              <input
                type="text"
                [(ngModel)]="atlassianUrl"
                placeholder="https://your-domain.atlassian.net"
                class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Atlassian Account Email
              </label>
              <input
                type="email"
                [(ngModel)]="atlassianEmail"
                placeholder="user&#64;example.com"
                class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Atlassian API Token
              </label>
              <input
                type="password"
                [(ngModel)]="atlassianToken"
                placeholder="Leave blank to use vaulted secret"
                class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 outline-none font-mono"
              />
            </div>

            <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
              <div>
                <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">Enforce Read-Only Mode</span>
                <span class="text-[10px] text-slate-400">Restricts AI agents to reading Jira issues and user stories.</span>
              </div>
              <input type="checkbox" [(ngModel)]="atlassianReadOnly" class="w-4 h-4 rounded text-blue-600 cursor-pointer" />
            </div>
          </div>

          <!-- Modal Footer (shrink-0) -->
          <div class="p-4 sm:p-5 border-t border-slate-100 dark:border-slate-800 shrink-0 flex items-center justify-end gap-3 bg-slate-50/50 dark:bg-slate-900/50">
            <button
              (click)="closeAtlassianModal()"
              class="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              (click)="submitAtlassianConnect()"
              [disabled]="connectingAtlassian"
              class="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-glow-blue flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <app-icon name="network" size="14" [class.animate-spin]="connectingAtlassian"></app-icon>
              <span>{{ connectingAtlassian ? 'Negotiating Protocol...' : 'Start Atlassian MCP' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class IntegrationsComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);

  activeTab: 'servers' | 'mappings' | 'tools' | 'approvals' | 'logs' = 'servers';
  toolFilter: 'all' | 'github' | 'atlassian' = 'all';

  loading = false;
  servers: MCPServerStatus[] = [];
  tools: MCPToolInfo[] = [];
  projects: Project[] = [];
  pendingApprovals: MCPApprovalRequest[] = [];
  logs: MCPInvocationLog[] = [];

  // Mappings
  selectedProjectId = '';
  activeMapping = {
    githubRepo: '',
    githubBranch: 'main',
    jiraKey: '',
  };
  discoveredRepos: Array<{ name: string; full_name: string; default_branch: string }> = [];
  discoveredJiraProjects: Array<{ id: string; key: string; name: string }> = [];
  discoveringRepos = false;
  discoveringJira = false;
  savingMapping = false;

  // Modals & Forms
  showGithubModal = false;
  githubTokenInput = '';
  githubReadOnly = true;
  connectingGithub = false;

  showAtlassianModal = false;
  atlassianTransport = 'stdio';
  atlassianUrl = 'https://mcp.atlassian.com/v2/mcp';
  atlassianEmail = '';
  atlassianToken = '';
  atlassianReadOnly = true;
  connectingAtlassian = false;

  notification: { type: 'success' | 'error'; message: string } | null = null;

  ngOnInit() {
    this.refreshAll();
  }

  get connectedCount(): number {
    return this.servers.filter((s) => s.status === 'connected').length;
  }

  getServer(provider: string): MCPServerStatus | undefined {
    return this.servers.find((s) => s.provider === provider);
  }

  get filteredTools(): MCPToolInfo[] {
    if (this.toolFilter === 'all') return this.tools;
    const s = this.getServer(this.toolFilter);
    if (!s) return [];
    return this.tools.filter((t) => t.server_id === s.server_name || t.tool_name.toLowerCase().includes(this.toolFilter));
  }

  refreshAll() {
    this.loading = true;
    this.loadServers();
    this.loadTools();
    this.loadProjects();
    this.loadApprovals();
    this.loadLogs();
  }

  loadServers() {
    this.api.getMcpServers().subscribe({
      next: (data) => {
        this.servers = data;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.showToast('error', 'Failed to retrieve MCP server statuses: ' + (err.error?.detail || err.message));
      },
    });
  }

  loadTools() {
    this.api.getMcpTools().subscribe({
      next: (data) => {
        this.tools = data;
      },
      error: () => {},
    });
  }

  loadProjects() {
    this.api.getProjects().subscribe({
      next: (data) => {
        this.projects = data;
        if (data.length > 0 && !this.selectedProjectId) {
          this.selectedProjectId = data[0].id;
          this.loadProjectMapping();
        }
      },
      error: () => {},
    });
  }

  loadProjectMapping() {
    if (!this.selectedProjectId) return;
    this.api.getProjectMcpMapping(this.selectedProjectId, 'github').subscribe({
      next: (map) => {
        this.activeMapping.githubRepo = map.selected_resources?.[0] || map.external_id || '';
        this.activeMapping.githubBranch = map.default_branch || 'main';
      },
      error: () => {},
    });

    this.api.getProjectMcpMapping(this.selectedProjectId, 'atlassian').subscribe({
      next: (map) => {
        this.activeMapping.jiraKey = map.selected_resources?.[0] || '';
      },
      error: () => {},
    });
  }

  loadApprovals() {
    this.api.getPendingMcpApprovals().subscribe({
      next: (data) => {
        this.pendingApprovals = data;
      },
      error: () => {},
    });
  }

  loadLogs() {
    this.api.getMcpLogs(50).subscribe({
      next: (data) => {
        this.logs = data;
      },
      error: () => {},
    });
  }

  @HostListener('document:keydown.escape')
  onEscapeKey() {
    if (this.showGithubModal) this.closeGithubModal();
    if (this.showAtlassianModal) this.closeAtlassianModal();
  }

  openGithubModal() {
    this.githubTokenInput = '';
    this.showGithubModal = true;
    this.updateBodyScrollLock();
  }

  closeGithubModal() {
    this.showGithubModal = false;
    this.updateBodyScrollLock();
  }

  submitGithubConnect() {
    this.connectingGithub = true;
    this.api
      .connectMcpGithub({
        personal_access_token: this.githubTokenInput || undefined,
        read_only: this.githubReadOnly,
      })
      .subscribe({
        next: (res) => {
          this.connectingGithub = false;
          this.closeGithubModal();
          this.showToast('success', res.message || 'GitHub MCP Server connected successfully!');
          this.refreshAll();
        },
        error: (err) => {
          this.connectingGithub = false;
          this.showToast('error', 'Connection failed: ' + (err.error?.detail || err.message));
        },
      });
  }

  openAtlassianModal() {
    this.atlassianToken = '';
    this.showAtlassianModal = true;
    this.updateBodyScrollLock();
  }

  closeAtlassianModal() {
    this.showAtlassianModal = false;
    this.updateBodyScrollLock();
  }

  submitAtlassianConnect() {
    this.connectingAtlassian = true;
    this.api
      .connectMcpAtlassian({
        transport: this.atlassianTransport,
        server_url: this.atlassianUrl,
        email: this.atlassianEmail || undefined,
        api_token: this.atlassianToken || undefined,
        read_only: this.atlassianReadOnly,
      })
      .subscribe({
        next: (res) => {
          this.connectingAtlassian = false;
          this.closeAtlassianModal();
          this.showToast('success', res.message || 'Atlassian MCP Server connected successfully!');
          this.refreshAll();
        },
        error: (err) => {
          this.connectingAtlassian = false;
          this.showToast('error', 'Connection failed: ' + (err.error?.detail || err.message));
        },
      });
  }

  private updateBodyScrollLock() {
    if (typeof document !== 'undefined') {
      if (this.showGithubModal || this.showAtlassianModal) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }
  }

  ngOnDestroy() {
    if (typeof document !== 'undefined') {
      document.body.style.overflow = '';
    }
  }

  disconnectServer(provider: string) {
    this.api.disconnectMcpServer(provider).subscribe({
      next: () => {
        this.showToast('success', `${provider} MCP server disconnected.`);
        this.refreshAll();
      },
      error: (err) => {
        this.showToast('error', 'Failed to disconnect: ' + (err.error?.detail || err.message));
      },
    });
  }

  discoverRepos() {
    this.discoveringRepos = true;
    this.api.getMcpGithubRepos().subscribe({
      next: (repos) => {
        this.discoveredRepos = repos;
        this.discoveringRepos = false;
        this.showToast('success', `Discovered ${repos.length} repositories via GitHub MCP.`);
      },
      error: (err) => {
        this.discoveringRepos = false;
        this.showToast('error', 'Repo discovery failed: ' + (err.error?.detail || err.message));
      },
    });
  }

  discoverJiraProjects() {
    this.discoveringJira = true;
    this.api.getMcpJiraProjects().subscribe({
      next: (projs) => {
        this.discoveredJiraProjects = projs;
        this.discoveringJira = false;
        this.showToast('success', `Discovered ${projs.length} Jira projects via Atlassian MCP.`);
      },
      error: (err) => {
        this.discoveringJira = false;
        this.showToast('error', 'Jira discovery failed: ' + (err.error?.detail || err.message));
      },
    });
  }

  saveMapping() {
    if (!this.selectedProjectId) return;
    this.savingMapping = true;

    // 1. Save GitHub Mapping
    this.api
      .saveProjectMcpMapping(this.selectedProjectId, {
        provider: 'github',
        external_id: this.activeMapping.githubRepo,
        selected_resources: this.activeMapping.githubRepo ? [this.activeMapping.githubRepo] : [],
        default_branch: this.activeMapping.githubBranch || 'main',
      })
      .subscribe({
        next: () => {
          // 2. Save Atlassian Mapping
          this.api
            .saveProjectMcpMapping(this.selectedProjectId, {
              provider: 'atlassian',
              external_id: this.activeMapping.jiraKey,
              selected_resources: this.activeMapping.jiraKey ? [this.activeMapping.jiraKey] : [],
            })
            .subscribe({
              next: () => {
                this.savingMapping = false;
                this.showToast('success', 'Project integration mappings saved and isolated successfully!');
              },
              error: (err) => {
                this.savingMapping = false;
                this.showToast('error', 'Failed to save Jira mapping: ' + (err.error?.detail || err.message));
              },
            });
        },
        error: (err) => {
          this.savingMapping = false;
          this.showToast('error', 'Failed to save GitHub mapping: ' + (err.error?.detail || err.message));
        },
      });
  }

  decideApproval(approvalId: string, decision: 'approved' | 'rejected') {
    this.api.decideMcpApproval(approvalId, decision).subscribe({
      next: () => {
        this.showToast('success', `Approval request ${decision}.`);
        this.loadApprovals();
        this.loadLogs();
      },
      error: (err) => {
        this.showToast('error', 'Action failed: ' + (err.error?.detail || err.message));
      },
    });
  }

  showToast(type: 'success' | 'error', message: string) {
    this.notification = { type, message };
    setTimeout(() => {
      if (this.notification?.message === message) {
        this.notification = null;
      }
    }, 6000);
  }
}
