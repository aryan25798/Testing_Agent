import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'projects',
    loadComponent: () =>
      import('./pages/projects/projects.component').then((m) => m.ProjectsComponent),
  },
  {
    path: 'agents',
    loadComponent: () =>
      import('./pages/agents/agents.component').then((m) => m.AgentsComponent),
  },
  {
    path: 'workflows',
    loadComponent: () =>
      import('./pages/workflows/workflows.component').then((m) => m.WorkflowsComponent),
  },
  {
    path: 'test-cases',
    loadComponent: () =>
      import('./pages/test-cases/test-cases.component').then((m) => m.TestCasesComponent),
  },
  {
    path: 'automation',
    loadComponent: () =>
      import('./pages/automation/automation.component').then((m) => m.AutomationComponent),
  },
  {
    path: 'executions',
    loadComponent: () =>
      import('./pages/executions/executions.component').then((m) => m.ExecutionsComponent),
  },
  {
    path: 'reports',
    loadComponent: () =>
      import('./pages/reports/reports.component').then((m) => m.ReportsComponent),
  },
  {
    path: 'models',
    loadComponent: () =>
      import('./pages/model-settings/model-settings.component').then((m) => m.ModelSettingsComponent),
  },
  {
    path: 'settings',
    loadComponent: () =>
      import('./pages/settings/settings.component').then((m) => m.SettingsComponent),
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
