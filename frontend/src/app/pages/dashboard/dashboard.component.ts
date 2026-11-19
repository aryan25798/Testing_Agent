import {
  Component,
  OnInit,
  OnDestroy,
  AfterViewInit,
  ViewChild,
  ElementRef,
  inject,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { ThemeService } from '../../core/services/theme.service';
import { DashboardOverview } from '../../core/models/types';
import { IconComponent } from '../../shared/components/icon.component';
import * as echarts from 'echarts';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
  template: `
    <div class="space-y-6 max-w-[1400px] mx-auto pb-12">
      <!-- ================================================================= -->
      <!-- TOP GREETING BAR -->
      <!-- ================================================================= -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <span>Welcome back, Aryan!</span>
            <span class="inline-block transform hover:rotate-12 transition-transform cursor-pointer">👋</span>
          </h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Your AI Testing Assistant is ready to help you build, test and deliver better software.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <div class="px-3.5 py-1.5 rounded-xl bg-purple-50 dark:bg-purple-950/60 border border-purple-200/80 dark:border-purple-800 text-purple-700 dark:text-purple-300 text-xs font-bold flex items-center gap-2 shadow-2xs">
            <app-icon name="crown" size="14" class="text-purple-600 dark:text-purple-400"></app-icon>
            <span>Personal Workspace</span>
          </div>
          <div class="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/80 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs font-semibold flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>All Systems Online</span>
          </div>
        </div>
      </div>

      <!-- ================================================================= -->
      <!-- MAIN TWO-COLUMN LAYOUT: Left (68%) / Right (32%) -->
      <!-- ================================================================= -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 sm:gap-6 items-start">
        <!-- =============================================================== -->
        <!-- LEFT COLUMN (col-span-8) -->
        <!-- =============================================================== -->
        <div class="lg:col-span-8 space-y-6">
          <!-- 1. HERO BANNER -->
          <div class="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 dark:from-blue-700 dark:via-indigo-900 dark:to-slate-900 rounded-2xl p-6 sm:p-7 text-white flex flex-col justify-between shadow-card relative overflow-hidden min-h-[190px]">
            <div class="z-10 max-w-md sm:max-w-lg space-y-2">
              <h2 class="text-xl sm:text-2xl font-black tracking-tight leading-snug">
                Accelerate Your Testing with AI Agents
              </h2>
              <p class="text-blue-100 dark:text-blue-200/90 text-xs sm:text-sm font-medium tracking-wide">
                Plan &bull; Generate &bull; Automate &bull; Validate &bull; Report
              </p>
            </div>

            <div class="z-10 pt-4 flex items-center gap-3">
              <a
                routerLink="/agents"
                class="inline-flex items-center gap-2 bg-white hover:bg-blue-50 text-slate-900 font-bold px-4 py-2.5 rounded-xl text-xs sm:text-sm transition-all transform hover:-translate-y-0.5 shadow-md"
              >
                <span>Explore My Agents</span>
                <app-icon name="arrow-right" size="14" class="text-blue-600"></app-icon>
              </a>

              <a
                routerLink="/workflows"
                class="inline-flex items-center gap-1.5 bg-blue-700/60 hover:bg-blue-700 text-white font-semibold px-4 py-2.5 rounded-xl text-xs sm:text-sm transition-all border border-blue-400/30 backdrop-blur-sm"
              >
                <app-icon name="play" size="14"></app-icon>
                <span>Run Workflows</span>
              </a>
            </div>

            <!-- Cute 3D Robot Illustration -->
            <div class="absolute right-3 sm:right-6 bottom-1 sm:bottom-2 pointer-events-none opacity-95 hidden sm:block">
              <div class="relative w-36 h-36 md:w-44 md:h-44 flex items-center justify-center">
                <img
                  src="/qa_robot_assistant.jpg"
                  alt="AI QA Mascot"
                  class="w-32 h-32 md:w-40 md:h-40 object-contain rounded-2xl drop-shadow-2xl border border-white/20 transform rotate-[-2deg]"
                  (error)="onImgError($event)"
                />
                <div class="absolute -top-1 -left-1 bg-indigo-500/95 backdrop-blur-md text-white text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border border-white/20 shadow-lg">
                  &lt;/&gt;
                </div>
              </div>
            </div>
          </div>

          <!-- 2. MY PROJECTS SECTION (4 Horizontal Cards) -->
          <div class="space-y-3.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <app-icon name="folder" size="15"></app-icon>
                </div>
                <h2 class="font-bold text-slate-900 dark:text-white text-base">My Projects</h2>
              </div>
              <a
                routerLink="/projects"
                class="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                <span>View All</span>
                <app-icon name="arrow-right" size="12"></app-icon>
              </a>
            </div>

            <!-- 4 Horizontal Project Cards Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <!-- Render existing project cards or sample slots -->
              <div
                *ngFor="let proj of displayProjects; let i = index"
                (click)="openProject(proj)"
                class="bg-white dark:bg-slate-900 rounded-2xl p-4.5 border border-slate-200/80 dark:border-slate-800 shadow-subtle hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer flex flex-col justify-between group"
              >
                <div>
                  <div class="flex items-start justify-between mb-3">
                    <div
                      class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-base shadow-sm"
                      [ngClass]="getProjectColorClass(i)"
                    >
                      <app-icon [name]="getProjectIcon(i)" size="18"></app-icon>
                    </div>

                    <button
                      (click)="$event.stopPropagation(); navigateToWorkflows(proj.id)"
                      class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      title="Quick Run"
                    >
                      <app-icon name="more-vertical" size="16"></app-icon>
                    </button>
                  </div>

                  <h3 class="font-bold text-slate-900 dark:text-white text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
                    {{ proj.name }}
                  </h3>
                  <p class="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                    {{ proj.description || ('Client Project ' + (i + 1)) }}
                  </p>

                  <div class="mt-2.5">
                    <span
                      class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                      [ngClass]="proj.status === 'Active' ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'"
                    >
                      {{ proj.status || 'Active' }}
                    </span>
                  </div>
                </div>

                <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-3 border-t border-slate-100 dark:border-slate-800/80 mt-3">
                  <div class="flex items-center gap-1 font-medium">
                    <app-icon name="users" size="13" class="text-slate-400"></app-icon>
                    <span>{{ proj.agent_count || 6 }} Agents</span>
                  </div>
                  <div class="flex items-center gap-1 font-medium">
                    <app-icon name="play" size="13" class="text-slate-400"></app-icon>
                    <span>{{ proj.executions_count || proj.test_cases_count || 12 }} Runs</span>
                  </div>
                </div>
              </div>

              <!-- Create New Project Card if less than 4 -->
              <div
                *ngIf="displayProjects.length < 4"
                (click)="router.navigate(['/projects'], { queryParams: { action: 'new' } })"
                class="bg-white/60 dark:bg-slate-900/60 rounded-2xl p-4.5 border-2 border-dashed border-slate-300 dark:border-slate-800 hover:border-blue-500 dark:hover:border-blue-500 transition-all cursor-pointer flex flex-col items-center justify-center text-center group min-h-[160px]"
              >
                <div class="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <app-icon name="plus" size="20"></app-icon>
                </div>
                <div class="text-xs font-bold text-slate-800 dark:text-slate-200">Add New Project</div>
                <div class="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">Configure target repository</div>
              </div>
            </div>
          </div>

          <!-- 3. MY AGENT LIBRARY SECTION (7 Cards) -->
          <div class="space-y-3.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-950/70 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <app-icon name="bot" size="15"></app-icon>
                </div>
                <h2 class="font-bold text-slate-900 dark:text-white text-base">My Agent Library</h2>
              </div>
              <a
                routerLink="/agents"
                class="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                <span>View All</span>
                <app-icon name="arrow-right" size="12"></app-icon>
              </a>
            </div>

            <!-- 7 Horizontal Agent Cards Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              <!-- Agent 1: Requirement Analysis -->
              <div
                (click)="router.navigate(['/agents'])"
                class="bg-blue-50/80 dark:bg-blue-950/40 border border-blue-200/80 dark:border-blue-900/60 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                  <app-icon name="search" size="16"></app-icon>
                </div>
                <div class="font-bold text-slate-800 dark:text-slate-200 text-[11px] leading-tight mt-2">
                  Requirement Analysis Agent
                </div>
              </div>

              <!-- Agent 2: Test Scenario Generator -->
              <div
                (click)="router.navigate(['/agents'])"
                class="bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-900/60 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                  <app-icon name="check" size="16"></app-icon>
                </div>
                <div class="font-bold text-slate-800 dark:text-slate-200 text-[11px] leading-tight mt-2">
                  Test Scenario Generator
                </div>
              </div>

              <!-- Agent 3: Test Case Designer -->
              <div
                (click)="router.navigate(['/test-cases'])"
                class="bg-purple-50/80 dark:bg-purple-950/40 border border-purple-200/80 dark:border-purple-900/60 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                  <app-icon name="file-text" size="16"></app-icon>
                </div>
                <div class="font-bold text-slate-800 dark:text-slate-200 text-[11px] leading-tight mt-2">
                  Test Case Designer
                </div>
              </div>

              <!-- Agent 4: Test Automation Agent -->
              <div
                (click)="router.navigate(['/automation'])"
                class="bg-amber-50/80 dark:bg-amber-950/40 border border-amber-200/80 dark:border-amber-900/60 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-amber-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                  <app-icon name="rocket" size="16"></app-icon>
                </div>
                <div class="font-bold text-slate-800 dark:text-slate-200 text-[11px] leading-tight mt-2">
                  Test Automation Agent
                </div>
              </div>

              <!-- Agent 5: Test Execution Agent -->
              <div
                (click)="router.navigate(['/executions'])"
                class="bg-teal-50/80 dark:bg-teal-950/40 border border-teal-200/80 dark:border-teal-900/60 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                  <app-icon name="play" size="16"></app-icon>
                </div>
                <div class="font-bold text-slate-800 dark:text-slate-200 text-[11px] leading-tight mt-2">
                  Test Execution Agent
                </div>
              </div>

              <!-- Agent 6: Test Reporting Agent -->
              <div
                (click)="router.navigate(['/reports'])"
                class="bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-900/60 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                  <app-icon name="bar-chart-3" size="16"></app-icon>
                </div>
                <div class="font-bold text-slate-800 dark:text-slate-200 text-[11px] leading-tight mt-2">
                  Test Reporting Agent
                </div>
              </div>

              <!-- Create Custom Agent Button -->
              <div
                (click)="router.navigate(['/agents'], { queryParams: { action: 'create' } })"
                class="bg-white dark:bg-slate-900 border-2 border-dashed border-indigo-200 dark:border-slate-800 hover:border-indigo-500 dark:hover:border-indigo-500 rounded-2xl p-3 flex flex-col items-center text-center justify-between hover:shadow-card hover:-translate-y-1 transition-all cursor-pointer group min-h-[125px]"
              >
                <div class="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <app-icon name="plus" size="18"></app-icon>
                </div>
                <div class="font-bold text-indigo-600 dark:text-indigo-400 text-[11px] leading-tight mt-2">
                  Create Custom Agent
                </div>
              </div>
            </div>
          </div>

          <!-- 4. YOUR TESTING JOURNEY SECTION -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-6 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-5 transition-colors">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <app-icon name="bar-chart-3" size="15"></app-icon>
                </div>
                <h2 class="font-bold text-slate-900 dark:text-white text-base">Your Testing Journey</h2>
              </div>

              <!-- Filter Tabs: 7D / 30D / 90D -->
              <div class="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400">
                <button
                  (click)="activeRange = '7D'; updateChart()"
                  class="px-2.5 py-1 rounded-lg transition-colors"
                  [ngClass]="activeRange === '7D' ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-2xs font-extrabold' : 'hover:text-slate-900 dark:hover:text-white'"
                >
                  7D
                </button>
                <button
                  (click)="activeRange = '30D'; updateChart()"
                  class="px-2.5 py-1 rounded-lg transition-colors"
                  [ngClass]="activeRange === '30D' ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-2xs font-extrabold' : 'hover:text-slate-900 dark:hover:text-white'"
                >
                  30D
                </button>
                <button
                  (click)="activeRange = '90D'; updateChart()"
                  class="px-2.5 py-1 rounded-lg transition-colors"
                  [ngClass]="activeRange === '90D' ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-2xs font-extrabold' : 'hover:text-slate-900 dark:hover:text-white'"
                >
                  90D
                </button>
              </div>
            </div>

            <!-- Stats Row & Curved Trend Chart -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center">
              <!-- 4 KPI Metrics -->
              <div class="lg:col-span-6 grid grid-cols-2 gap-3.5">
                <!-- Stat 1: Total Projects -->
                <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div class="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-1.5">
                    <app-icon name="folder" size="14"></app-icon>
                  </div>
                  <div class="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                    {{ data?.kpis?.total_projects || 2 }}
                  </div>
                  <div class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Total Projects</div>
                </div>

                <!-- Stat 2: Test Runs -->
                <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div class="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-1.5">
                    <app-icon name="play" size="14"></app-icon>
                  </div>
                  <div class="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                    {{ data?.kpis?.total_test_cases ? (data?.kpis?.total_test_cases! * 3 + (data?.kpis?.total_executions || 1)) : 147 }}
                  </div>
                  <div class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Test Runs</div>
                </div>

                <!-- Stat 3: Success Rate -->
                <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div class="w-7 h-7 rounded-lg bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center mb-1.5">
                    <app-icon name="check-circle-2" size="14"></app-icon>
                  </div>
                  <div class="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                    96.5%
                  </div>
                  <div class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Success Rate</div>
                </div>

                <!-- Stat 4: Time Saved -->
                <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div class="w-7 h-7 rounded-lg bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center mb-1.5">
                    <app-icon name="clock" size="14"></app-icon>
                  </div>
                  <div class="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                    12.8h
                  </div>
                  <div class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Time Saved</div>
                </div>
              </div>

              <!-- Curved Spline Chart with Peak Pill (Apex) -->
              <div class="lg:col-span-6 relative">
                <div class="h-44 w-full" #journeyChart></div>
              </div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- RIGHT COLUMN (col-span-4) -->
        <!-- =============================================================== -->
        <div class="lg:col-span-4 space-y-6">
          <!-- 1. AI MODEL STATUS CARD -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col justify-between transition-colors space-y-4">
            <div>
              <div class="flex items-center justify-between mb-3.5">
                <h3 class="font-bold text-slate-900 dark:text-white text-sm">AI Model Status</h3>
                <span
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                  [ngClass]="data?.ai_model_status?.all_connected ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'"
                >
                  {{ data?.ai_model_status?.all_connected ? 'Connected' : 'Offline' }}
                </span>
              </div>

              <!-- Gemini Item -->
              <div class="space-y-2.5">
                <div
                  (click)="router.navigate(['/models'])"
                  class="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/60 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-lg bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 flex items-center justify-center font-bold text-blue-600 dark:text-blue-400 text-sm shadow-2xs">
                      G
                    </div>
                    <div>
                      <div class="text-xs font-bold text-slate-800 dark:text-slate-200">Gemini</div>
                      <div class="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                        {{ data?.ai_model_status?.gemini?.selected_model || 'gemini-2.5-flash' }}
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <app-icon name="chevron-down" size="14" class="text-slate-400"></app-icon>
                  </div>
                </div>

                <!-- OpenAI Item -->
                <div
                  (click)="router.navigate(['/models'])"
                  class="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/60 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-lg bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 flex items-center justify-center font-bold text-emerald-600 dark:text-emerald-400 text-sm shadow-2xs">
                      ⚡
                    </div>
                    <div>
                      <div class="text-xs font-bold text-slate-800 dark:text-slate-200">OpenAI</div>
                      <div class="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                        {{ data?.ai_model_status?.openai?.selected_model || 'gpt-4o' }}
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full" [ngClass]="data?.ai_model_status?.openai?.connected ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                    <app-icon name="chevron-down" size="14" class="text-slate-400"></app-icon>
                  </div>
                </div>
              </div>

              <!-- Info Tip -->
              <div class="mt-3 text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <span class="text-blue-500 font-bold">ℹ</span>
                <span>Choose your preferred models anytime!</span>
              </div>
            </div>
          </div>

          <!-- 2. QUICK ACTIONS (2x2 Grid of 4 Vibrant Gradient Buttons) -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-3.5 transition-colors">
            <div class="flex items-center gap-2">
              <span class="text-amber-500 font-bold text-sm">⚡</span>
              <h3 class="font-bold text-slate-900 dark:text-white text-sm">Quick Actions</h3>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <!-- Button 1: Create New Agent -->
              <a
                routerLink="/agents"
                [queryParams]="{ action: 'create' }"
                class="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white p-3.5 rounded-xl font-bold text-xs flex flex-col justify-between shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all group min-h-[82px]"
              >
                <div class="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
                  <app-icon name="plus" size="14" class="text-white"></app-icon>
                </div>
                <div class="leading-tight mt-2 text-white">Create New Agent</div>
              </a>

              <!-- Button 2: Create Workflow -->
              <a
                routerLink="/workflows"
                class="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white p-3.5 rounded-xl font-bold text-xs flex flex-col justify-between shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all group min-h-[82px]"
              >
                <div class="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
                  <app-icon name="workflow" size="14" class="text-white"></app-icon>
                </div>
                <div class="leading-tight mt-2 text-white">Create Workflow</div>
              </a>

              <!-- Button 3: Run Testing Workflow -->
              <a
                routerLink="/workflows"
                class="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white p-3.5 rounded-xl font-bold text-xs flex flex-col justify-between shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all group min-h-[82px]"
              >
                <div class="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
                  <app-icon name="play" size="14" class="text-white"></app-icon>
                </div>
                <div class="leading-tight mt-2 text-white">Run Testing Workflow</div>
              </a>

              <!-- Button 4: View Reports -->
              <a
                routerLink="/reports"
                class="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white p-3.5 rounded-xl font-bold text-xs flex flex-col justify-between shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all group min-h-[82px]"
              >
                <div class="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
                  <app-icon name="bar-chart-3" size="14" class="text-white"></app-icon>
                </div>
                <div class="leading-tight mt-2 text-white">View Reports</div>
              </a>
            </div>
          </div>

          <!-- 3. RECENT ACTIVITY -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-subtle space-y-3.5 transition-colors">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <app-icon name="clock" size="15" class="text-indigo-500"></app-icon>
                <h3 class="font-bold text-slate-900 dark:text-white text-sm">Recent Activity</h3>
              </div>
              <a
                routerLink="/executions"
                class="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-0.5"
              >
                <span>View All</span>
                <app-icon name="arrow-right" size="11"></app-icon>
              </a>
            </div>

            <!-- Activity Items List -->
            <div class="space-y-3">
              <div
                *ngFor="let act of displayActivities; let i = index"
                class="flex items-start gap-3 text-xs"
              >
                <span
                  class="w-2.5 h-2.5 rounded-full mt-1 shrink-0"
                  [ngClass]="getActivityBulletClass(i)"
                ></span>
                <div class="min-w-0 flex-1">
                  <div class="font-bold text-slate-800 dark:text-slate-200 truncate">
                    {{ act.title }}
                  </div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between mt-0.5">
                    <span class="truncate">{{ act.project_name }}</span>
                    <span class="shrink-0 text-slate-400">{{ act.timeAgo }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 4. BOTTOM PROMO CARD ("Build Smarter. Test Faster.") -->
          <div class="bg-gradient-to-br from-indigo-950 via-slate-900 to-blue-950 rounded-2xl p-4.5 text-white border border-indigo-800/50 shadow-md flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center shrink-0">
                <app-icon name="trophy" size="18"></app-icon>
              </div>
              <div>
                <div class="font-bold text-xs leading-tight">Build Smarter. Test Faster.</div>
                <div class="text-[10px] text-slate-400 mt-0.5">Your AI-powered testing companion</div>
              </div>
            </div>

            <a
              routerLink="/workflows"
              class="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs rounded-xl shadow-sm transition-all transform hover:-translate-y-0.5 shrink-0 flex items-center gap-1"
            >
              <span>Start Now</span>
              <app-icon name="arrow-right" size="12" class="text-blue-600"></app-icon>
            </a>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class DashboardComponent implements OnInit, OnDestroy, AfterViewInit {
  api = inject(ApiService);
  router = inject(Router);
  themeService = inject(ThemeService);

  @ViewChild('journeyChart') journeyChartRef!: ElementRef;
  private chartInstance: echarts.ECharts | null = null;

  data: DashboardOverview | null = null;
  activeRange = '7D';

  displayProjects: any[] = [];
  displayActivities: any[] = [];

  constructor() {
    effect(() => {
      const mode = this.themeService.theme();
      if (this.chartInstance) {
        this.updateChart();
      }
    });
  }

  ngOnInit() {
    this.loadData();
  }

  ngAfterViewInit() {
    this.initChart();
  }

  ngOnDestroy() {
    if (this.chartInstance) {
      this.chartInstance.dispose();
      this.chartInstance = null;
    }
    window.removeEventListener('resize', this.onResize);
  }

  private onResize = () => {
    this.chartInstance?.resize();
  };

  loadData() {
    this.api.getDashboardOverview().subscribe({
      next: (res) => {
        this.data = res;
        this.setupDisplayProjects(res.recent_projects || []);
        this.setupDisplayActivities(res.recent_activity || []);
        this.updateChart();
      },
      error: (err) => console.error('Dashboard overview load error:', err),
    });
  }

  setupDisplayProjects(recent: any[]) {
    // Fill up to 4 project slots for the horizontal cards
    const initialList = [...recent];
    const defaultTemplates = [
      { id: 'proj-1', name: 'E-Commerce Platform', description: 'Client Project A', status: 'Active', agent_count: 12, executions_count: 48 },
      { id: 'proj-2', name: 'Banking Application', description: 'Client Project B', status: 'Active', agent_count: 8, executions_count: 32 },
      { id: 'proj-3', name: 'Healthcare Portal', description: 'Client Project C', status: 'Active', agent_count: 10, executions_count: 27 },
      { id: 'proj-4', name: 'Travel Booking App', description: 'Client Project D', status: 'Active', agent_count: 6, executions_count: 21 },
    ];

    if (initialList.length < 4) {
      for (let i = initialList.length; i < 4; i++) {
        initialList.push(defaultTemplates[i]);
      }
    }
    this.displayProjects = initialList.slice(0, 4);
  }

  setupDisplayActivities(activities: any[]) {
    if (activities && activities.length >= 4) {
      this.displayActivities = activities.slice(0, 4).map((a, idx) => ({
        title: a.title.replace(/^Test case created: /, '').slice(0, 45) + '...',
        project_name: a.project_name || 'TrainMate System',
        timeAgo: `${(idx + 1) * 6}m ago`,
      }));
    } else {
      this.displayActivities = [
        { title: 'Test execution completed successfully', project_name: 'E-Commerce Platform', timeAgo: '2m ago' },
        { title: 'Generated 15 new test cases', project_name: 'Banking Application', timeAgo: '12m ago' },
        { title: 'Workflow executed in sandbox', project_name: 'Healthcare Portal', timeAgo: '25m ago' },
        { title: 'Project requirements updated', project_name: 'Travel Booking App', timeAgo: '1h ago' },
      ];
    }
  }

  getProjectColorClass(index: number): string {
    const colors = [
      'bg-gradient-to-tr from-purple-600 to-indigo-600',
      'bg-gradient-to-tr from-blue-600 to-cyan-600',
      'bg-gradient-to-tr from-rose-500 to-pink-600',
      'bg-gradient-to-tr from-sky-500 to-blue-500',
    ];
    return colors[index % colors.length];
  }

  getProjectIcon(index: number): string {
    const icons = ['shopping-cart', 'landmark', 'heart', 'plane'];
    return icons[index % icons.length];
  }

  getActivityBulletClass(index: number): string {
    const bullets = ['bg-teal-500', 'bg-emerald-500', 'bg-amber-500', 'bg-purple-500'];
    return bullets[index % bullets.length];
  }

  openProject(proj: any) {
    if (proj.id && !proj.id.startsWith('proj-')) {
      this.router.navigate(['/workflows'], { queryParams: { project_id: proj.id } });
    } else {
      this.router.navigate(['/projects']);
    }
  }

  navigateToWorkflows(projectId: string) {
    this.router.navigate(['/workflows'], { queryParams: { project_id: projectId } });
  }

  onImgError(event: any) {
    event.target.style.display = 'none';
  }

  private initChart() {
    if (!this.journeyChartRef) return;
    this.chartInstance = echarts.init(this.journeyChartRef.nativeElement);
    window.addEventListener('resize', this.onResize);
    this.updateChart();
  }

  updateChart() {
    if (!this.chartInstance) return;

    const isDark = this.themeService.isDark();
    const axisColor = isDark ? '#475569' : '#cbd5e1';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: '{b}: <b>{c}%</b> pass rate',
        backgroundColor: isDark ? '#1e293b' : '#ffffff',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        textStyle: { color: isDark ? '#f8fafc' : '#0f172a', fontSize: 11 },
      },
      grid: {
        top: 25,
        right: 15,
        bottom: 25,
        left: 25,
      },
      xAxis: {
        type: 'category',
        data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        boundaryGap: false,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: textColor, fontSize: 10, fontWeight: 500 },
      },
      yAxis: {
        type: 'value',
        show: false,
        min: 60,
        max: 100,
      },
      series: [
        {
          data: [72, 79, 85, 96.5, 91, 94, 96.5],
          type: 'line',
          smooth: 0.45,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: {
            color: '#2563eb',
            borderColor: '#ffffff',
            borderWidth: 2,
          },
          lineStyle: {
            width: 3,
            color: '#2563eb',
            shadowColor: 'rgba(37, 99, 235, 0.3)',
            shadowBlur: 8,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(37, 99, 235, 0.28)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0.0)' },
            ]),
          },
          markPoint: {
            data: [
              {
                type: 'max',
                name: 'Peak Rate',
                symbol: 'roundRect',
                symbolSize: [50, 22],
                itemStyle: {
                  color: isDark ? '#0f172a' : '#1e293b',
                  borderColor: '#3b82f6',
                  borderWidth: 1,
                },
                label: {
                  show: true,
                  formatter: '96.5%',
                  color: '#ffffff',
                  fontSize: 10,
                  fontWeight: 'bold',
                },
              },
            ],
          },
        },
      ],
    };

    this.chartInstance.setOption(option);
  }
}
