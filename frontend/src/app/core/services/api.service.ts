import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
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
  MCPServerStatus,
  MCPToolInfo,
  ProjectMCPMapping,
  MCPApprovalRequest,
  MCPInvocationLog,
  PaginatedResponse,
  BulkDeleteResponse,
  BulkApproveResponse,
} from '../models/types';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = this.resolveBaseUrl();

  private resolveBaseUrl(): string {
    if (typeof window !== 'undefined' && window.location.port !== '4200') {
      return '/api/v1';
    }
    return environment.apiBaseUrl;
  }

  // Dashboard
  getDashboardOverview(): Observable<DashboardOverview> {
    return this.http.get<DashboardOverview>(`${this.baseUrl}/dashboard/overview`);
  }

  // Projects
  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.baseUrl}/projects`);
  }

  getProjectsPaginated(options?: {
    page?: number;
    page_size?: number;
    search?: string;
    framework?: string;
    sort_by?: string;
    sort_order?: string;
  }): Observable<PaginatedResponse<Project>> {
    let params = new HttpParams();
    if (options?.page) params = params.set('page', options.page.toString());
    if (options?.page_size) params = params.set('page_size', options.page_size.toString());
    if (options?.search) params = params.set('search', options.search);
    if (options?.framework) params = params.set('framework', options.framework);
    if (options?.sort_by) params = params.set('sort_by', options.sort_by);
    if (options?.sort_order) params = params.set('sort_order', options.sort_order);
    return this.http.get<PaginatedResponse<Project>>(`${this.baseUrl}/projects`, { params });
  }

  bulkDeleteProjects(ids: string[]): Observable<BulkDeleteResponse> {
    return this.http.post<BulkDeleteResponse>(`${this.baseUrl}/projects/bulk-delete`, { ids });
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

  getTestCasesPaginated(
    projectId: string,
    filters?: {
      priority?: string;
      test_type?: string;
      is_approved?: boolean;
      search?: string;
      page?: number;
      page_size?: number;
      sort_by?: string;
      sort_order?: string;
    }
  ): Observable<PaginatedResponse<TestCase>> {
    let params = new HttpParams();
    if (filters?.priority) params = params.set('priority', filters.priority);
    if (filters?.test_type) params = params.set('test_type', filters.test_type);
    if (filters?.is_approved !== undefined) params = params.set('is_approved', filters.is_approved);
    if (filters?.search) params = params.set('search', filters.search);
    if (filters?.page) params = params.set('page', filters.page.toString());
    if (filters?.page_size) params = params.set('page_size', filters.page_size.toString());
    if (filters?.sort_by) params = params.set('sort_by', filters.sort_by);
    if (filters?.sort_order) params = params.set('sort_order', filters.sort_order);
    return this.http.get<PaginatedResponse<TestCase>>(`${this.baseUrl}/test-cases/project/${projectId}`, { params });
  }

  bulkDeleteTestCases(ids: string[]): Observable<BulkDeleteResponse> {
    return this.http.post<BulkDeleteResponse>(`${this.baseUrl}/test-cases/bulk-delete`, { ids });
  }

  bulkApproveTestCases(ids: string[]): Observable<BulkApproveResponse> {
    return this.http.post<BulkApproveResponse>(`${this.baseUrl}/test-cases/bulk-approve`, { ids });
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

  getExecutionsPaginated(
    projectId: string,
    options?: {
      page?: number;
      page_size?: number;
      search?: string;
      runner_type?: string;
      status_filter?: string;
    }
  ): Observable<PaginatedResponse<TestExecution>> {
    let params = new HttpParams();
    if (options?.page) params = params.set('page', options.page.toString());
    if (options?.page_size) params = params.set('page_size', options.page_size.toString());
    if (options?.search) params = params.set('search', options.search);
    if (options?.runner_type) params = params.set('runner_type', options.runner_type);
    if (options?.status_filter) params = params.set('status_filter', options.status_filter);
    return this.http.get<PaginatedResponse<TestExecution>>(`${this.baseUrl}/executions/project/${projectId}`, { params });
  }

  bulkDeleteExecutions(ids: string[]): Observable<BulkDeleteResponse> {
    return this.http.post<BulkDeleteResponse>(`${this.baseUrl}/executions/bulk-delete`, { ids });
  }

  getExecution(executionId: string): Observable<TestExecution> {
    return this.http.get<TestExecution>(`${this.baseUrl}/executions/${executionId}`);
  }

  downloadJunitXmlUrl(executionId: string): string {
    return `${this.baseUrl}/executions/${executionId}/export-junit`;
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

  getCredentialsStatus(): Observable<Record<string, { provider: string; is_configured: boolean; masked?: string }>> {
    return this.http.get<Record<string, { provider: string; is_configured: boolean; masked?: string }>>(`${this.baseUrl}/models/credentials/status`);
  }

  deleteCredentials(provider: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/models/credentials/${provider}`);
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

  getWorkflowStatus(workflowId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/workflows/${workflowId}/status`);
  }

  cancelWorkflow(workflowId: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/workflows/${workflowId}/cancel`, {});
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

  getWorkflowStreamUrl(
    projectId: string,
    options?: { requirementsText?: string; framework?: string; browser?: string; headed?: boolean }
  ): string {
    let url = `${this.baseUrl}/workflows/project/${projectId}/stream`;
    const params = new URLSearchParams();
    if (options?.requirementsText) {
      params.set('requirements_text', options.requirementsText);
    }
    if (options?.framework) {
      params.set('framework', options.framework);
    }
    if (options?.browser) {
      params.set('browser', options.browser);
    }
    if (options?.headed !== undefined) {
      params.set('headed', options.headed ? 'true' : 'false');
    }
    const qs = params.toString();
    return qs ? `${url}?${qs}` : url;
  }

  downloadDefectPack(projectId: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/workflows/project/${projectId}/export-zip`, {
      responseType: 'blob',
    });
  }

  getFirstRunStatus(): Observable<{
    needs_setup: boolean;
    gemini_configured: boolean;
    openai_configured: boolean;
    browser_ready: boolean;
    default_provider: string;
  }> {
    return this.http.get<{
      needs_setup: boolean;
      gemini_configured: boolean;
      openai_configured: boolean;
      browser_ready: boolean;
      default_provider: string;
    }>(`${this.baseUrl}/models/first-run-status`);
  }

  cancelProjectWorkflow(projectId: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/workflows/project/${projectId}/cancel`, {});
  }

  getProjectMcpActivity(projectId: string, limit: number = 15): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/workflows/project/${projectId}/mcp-activity?limit=${limit}`);
  }

  retryFailedAgent(projectId: string, agentId: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/workflows/project/${projectId}/retry-agent/${agentId}`, {});
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

  // Model Context Protocol (MCP) Integration Endpoints
  getMcpServers(): Observable<MCPServerStatus[]> {
    return this.http.get<MCPServerStatus[]>(`${this.baseUrl}/mcp/servers`);
  }

  connectMcpGithub(payload: { personal_access_token?: string; read_only?: boolean }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/mcp/github/connect`, payload);
  }

  connectMcpAtlassian(payload: {
    transport?: string;
    server_url?: string;
    email?: string;
    api_token?: string;
    read_only?: boolean;
  }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/mcp/atlassian/connect`, payload);
  }

  disconnectMcpServer(serverId: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/mcp/servers/${serverId}/disconnect`, {});
  }

  getMcpTools(provider?: string): Observable<MCPToolInfo[]> {
    let params = new HttpParams();
    if (provider) params = params.set('provider', provider);
    return this.http.get<MCPToolInfo[]>(`${this.baseUrl}/mcp/tools`, { params });
  }

  getMcpGithubRepos(query?: string): Observable<Array<{ name: string; full_name: string; private: boolean; default_branch: string }>> {
    let params = new HttpParams();
    if (query) params = params.set('query', query);
    return this.http.get<Array<{ name: string; full_name: string; private: boolean; default_branch: string }>>(
      `${this.baseUrl}/mcp/github/repositories`,
      { params }
    );
  }

  getMcpJiraProjects(): Observable<Array<{ id: string; key: string; name: string }>> {
    return this.http.get<Array<{ id: string; key: string; name: string }>>(
      `${this.baseUrl}/mcp/jira/projects`
    );
  }

  getProjectMcpMapping(projectId: string, provider: string): Observable<ProjectMCPMapping> {
    const params = new HttpParams().set('provider', provider);
    return this.http.get<ProjectMCPMapping>(`${this.baseUrl}/mcp/projects/${projectId}/mapping`, { params });
  }

  saveProjectMcpMapping(projectId: string, payload: any): Observable<any> {
    return this.http.post<ProjectMCPMapping>(`${this.baseUrl}/mcp/projects/${projectId}/mapping`, payload);
  }

  getPendingMcpApprovals(projectId?: string): Observable<MCPApprovalRequest[]> {
    let params = new HttpParams();
    if (projectId) params = params.set('project_id', projectId);
    return this.http.get<MCPApprovalRequest[]>(`${this.baseUrl}/mcp/approvals/pending`, { params });
  }

  decideMcpApproval(approvalId: string, decision: 'approved' | 'rejected', notes?: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/mcp/approvals/${approvalId}/decision`, { decision, notes });
  }

  getMcpLogs(limit: number = 50, projectId?: string): Observable<MCPInvocationLog[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (projectId) params = params.set('project_id', projectId);
    return this.http.get<MCPInvocationLog[]>(`${this.baseUrl}/mcp/logs`, { params });
  }
}
