import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Project,
  Requirement,
  TestScenario,
  TestCase,
  AutomationScript,
  TestExecution,
  CustomAgent,
  ModelInfo,
  DashboardOverview,
} from '../models/types';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://127.0.0.1:8000/api/v1';

  // Dashboard
  getDashboardOverview(): Observable<DashboardOverview> {
    return this.http.get<DashboardOverview>(`${this.baseUrl}/dashboard/overview`);
  }

  // Projects
  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.baseUrl}/projects`);
  }

  getProject(id: string): Observable<Project> {
    return this.http.get<Project>(`${this.baseUrl}/projects/${id}`);
  }

  createProject(payload: Partial<Project>): Observable<Project> {
    return this.http.post<Project>(`${this.baseUrl}/projects`, payload);
  }

  updateProject(id: string, payload: Partial<Project>): Observable<Project> {
    return this.http.put<Project>(`${this.baseUrl}/projects/${id}`, payload);
  }

  deleteProject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/projects/${id}`);
  }

  getProjectDashboard(projectId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/projects/${projectId}/dashboard`);
  }

  // Requirements & Scenarios
  getRequirements(projectId: string): Observable<Requirement[]> {
    return this.http.get<Requirement[]>(`${this.baseUrl}/requirements/project/${projectId}`);
  }

  getScenarios(projectId: string): Observable<TestScenario[]> {
    return this.http.get<TestScenario[]>(`${this.baseUrl}/scenarios/project/${projectId}`);
  }

  // Test Cases
  getTestCases(
    projectId: string,
    filters?: { priority?: string; test_type?: string; is_approved?: boolean; search?: string }
  ): Observable<TestCase[]> {
    let params = new HttpParams();
    if (filters?.priority) params = params.set('priority', filters.priority);
    if (filters?.test_type) params = params.set('test_type', filters.test_type);
    if (filters?.is_approved !== undefined) params = params.set('is_approved', filters.is_approved);
    if (filters?.search) params = params.set('search', filters.search);
    return this.http.get<TestCase[]>(`${this.baseUrl}/test-cases/project/${projectId}`, { params });
  }

  approveTestCase(caseId: string): Observable<TestCase> {
    return this.http.post<TestCase>(`${this.baseUrl}/test-cases/${caseId}/approve`, {});
  }

  deleteTestCase(caseId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/test-cases/${caseId}`);
  }

  // Automation Scripts
  getAutomationScripts(projectId: string): Observable<AutomationScript[]> {
    return this.http.get<AutomationScript[]>(`${this.baseUrl}/automation/project/${projectId}`);
  }

  downloadAutomationZipUrl(projectId: string): string {
    return `${this.baseUrl}/automation/project/${projectId}/download-zip`;
  }

  // Executions
  getExecutions(projectId: string): Observable<TestExecution[]> {
    return this.http.get<TestExecution[]>(`${this.baseUrl}/executions/project/${projectId}`);
  }

  getExecution(executionId: string): Observable<TestExecution> {
    return this.http.get<TestExecution>(`${this.baseUrl}/executions/${executionId}`);
  }

  // AI Models & Agent Routing
  getModels(): Observable<ModelInfo[]> {
    return this.http.get<ModelInfo[]>(`${this.baseUrl}/models`);
  }

  refreshModels(): Observable<ModelInfo[]> {
    return this.http.post<ModelInfo[]>(`${this.baseUrl}/models/refresh`, {});
  }

  testProviders(): Observable<Record<string, boolean>> {
    return this.http.post<Record<string, boolean>>(`${this.baseUrl}/models/test`, {});
  }

  setCredentials(provider: string, apiKey: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/models/credentials`, { provider, api_key: apiKey });
  }

  getAgentConfigurations(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.baseUrl}/agents/configuration`);
  }

  switchAgentModel(agentId: string, provider: string, modelId: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/agents/${agentId}/switch-model`, {
      provider,
      model_id: modelId,
    });
  }

  // Custom Agents
  getCustomAgents(): Observable<CustomAgent[]> {
    return this.http.get<CustomAgent[]>(`${this.baseUrl}/custom-agents`);
  }

  createCustomAgent(agent: Partial<CustomAgent>): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/custom-agents`, agent);
  }

  deleteCustomAgent(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/custom-agents/${id}`);
  }

  // Workflows
  startWorkflow(payload: {
    project_id: string;
    requirements_text?: string;
    source_type?: string;
    framework?: string;
  }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/workflows/start`, payload);
  }

  getProjectReport(projectId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/workflows/project/${projectId}/report`);
  }

  getPdfReportUrl(projectId: string): string {
    return `${this.baseUrl}/workflows/project/${projectId}/report/pdf`;
  }

  getCsvReportUrl(projectId: string): string {
    return `${this.baseUrl}/workflows/project/${projectId}/report/csv`;
  }

  // Integrations
  testJira(payload: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/integrations/jira/test`, payload);
  }

  listJiraProjects(payload: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/integrations/jira/projects`, payload);
  }

  listJiraIssues(payload: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/integrations/jira/issues`, payload);
  }

  testGit(payload: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/integrations/git/test`, payload);
  }

  inspectGit(payload: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/integrations/git/inspect`, payload);
  }

  uploadRequirementFile(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.baseUrl}/integrations/upload`, formData);
  }
}
