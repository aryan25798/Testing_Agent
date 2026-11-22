export interface Project {
  id: string;
  name: string;
  description?: string;
  framework: string;
  jira_project_key?: string;
  git_repo_url?: string;
  git_branch?: string;
  base_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Requirement {
  id: string;
  project_id: string;
  requirement_key: string;
  source_type: string;
  title: string;
  description: string;
  business_objective?: string;
  functional_requirements?: string[];
  non_functional_requirements?: string[];
  acceptance_criteria?: string[];
  business_rules?: string[];
  dependencies?: string[];
  missing_information?: string[];
  clarification_questions?: string[];
  risk_level: string;
  priority: string;
  testability_status: string;
  is_approved: boolean;
  approval_notes?: string;
  created_at?: string;
}

export interface TestScenario {
  id: string;
  project_id: string;
  requirement_id: string;
  scenario_key: string;
  title: string;
  description: string;
  test_type: string;
  preconditions?: string;
  test_objective?: string;
  priority: string;
  risk: string;
  expected_outcome: string;
  automation_suitability: string;
  is_approved: boolean;
  created_at?: string;
}

export interface TestCase {
  id: string;
  project_id: string;
  scenario_id?: string;
  requirement_id?: string;
  test_case_key: string;
  title: string;
  objective: string;
  test_type: string;
  priority: string;
  preconditions?: string;
  test_environment?: string;
  test_data?: any;
  execution_steps?: Array<{ step_number: number; action: string; expected: string }>;
  expected_results: string;
  actual_results?: string;
  status: string;
  automation_suitability: string;
  tags?: string[];
  is_approved: boolean;
  created_at?: string;
}

export interface AutomationScript {
  id: string;
  project_id: string;
  test_case_id?: string;
  framework: string;
  script_name: string;
  file_path: string;
  code_content: string;
  language: string;
  syntax_valid: boolean;
  is_approved: boolean;
  created_at?: string;
}

export interface TestExecutionResult {
  id: string;
  execution_id: string;
  test_case_id?: string;
  test_title: string;
  status: string;
  failing_step?: string;
  expected_result?: string;
  actual_result?: string;
  error_message?: string;
  stack_trace?: string;
  screenshot_path?: string;
  trace_path?: string;
  log_output?: string;
  failure_classification?: string;
  suggested_fix?: string;
  execution_duration_seconds: number;
}

export interface TestExecution {
  id: string;
  project_id: string;
  execution_key: string;
  runner_type: string;
  target_environment: string;
  base_url?: string;
  browser: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  blocked_tests: number;
  execution_duration_seconds: number;
  status: string;
  created_at?: string;
  results?: TestExecutionResult[];
}

export interface CustomAgent {
  id: string;
  name: string;
  description?: string;
  category: string;
  system_instructions: string;
  provider: string;
  model_id: string;
  is_active: boolean;
  created_at?: string;
}

export interface ModelInfo {
  provider: string;
  model_id: string;
  display_name: string;
  description: string;
  is_available: boolean;
}

export interface DashboardOverview {
  kpis: {
    total_projects: number;
    total_agents: number;
    total_test_cases: number;
    total_executions: number;
    passed_tests: number;
    failed_tests: number;
    blocked_tests: number;
    skipped_tests: number;
    success_rate: number;
  };
  ai_model_status: {
    gemini: {
      name: string;
      connected: boolean;
      selected_model: string;
    };
    openai: {
      name: string;
      connected: boolean;
      selected_model: string;
    };
    all_connected: boolean;
  };
  recent_projects: Array<{
    id: string;
    name: string;
    description: string;
    framework: string;
    base_url?: string;
    status: string;
    agent_count: number;
    test_cases_count: number;
    executions_count: number;
    last_updated: string;
  }>;
  testing_overview: {
    days: string[];
    trend: number[];
    success_rate: number;
    passed: number;
    failed: number;
    blocked: number;
  };
  recent_activity: Array<{
    id: string;
    type: string;
    status: string;
    title: string;
    project_name: string;
    project_id: string;
    timestamp: string;
  }>;
}

export interface MCPServerStatus {
  provider: 'github' | 'atlassian';
  server_name: string;
  transport: string;
  server_url: string;
  account_login: string;
  account_name: string;
  status: 'connected' | 'disconnected' | 'error' | 'connecting';
  is_read_only: boolean;
  available_tools_count: number;
  last_connected_at?: string;
  last_error?: string;
}

export interface MCPToolInfo {
  id: string;
  server_id: string;
  tool_name: string;
  description: string;
  input_schema: any;
  is_read_only: boolean;
  allowed_agents: string[];
  risk_level: string;
}

export interface ProjectMCPMapping {
  id?: string;
  project_id: string;
  provider: string;
  external_id: string;
  selected_resources: string[];
  default_branch: string;
  status: string;
  last_synced_at?: string;
  last_error?: string;
}

export interface MCPApprovalRequest {
  id: string;
  project_id: string;
  provider: string;
  agent_id: string;
  tool_name: string;
  target_object: string;
  operation_description: string;
  proposed_diff?: string;
  risk_level: string;
  status: 'pending' | 'approved' | 'rejected';
  requested_at: string;
}

export interface MCPInvocationLog {
  id: string;
  server_id: string;
  project_id?: string;
  agent_id: string;
  tool_name: string;
  status: 'success' | 'error' | 'blocked';
  duration_ms: number;
  error_message?: string;
  invoked_at: string;
}
