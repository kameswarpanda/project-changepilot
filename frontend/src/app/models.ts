export type ExecutionMode = 'ANALYZE_ONLY' | 'LOCAL_WORKSPACE' | 'BRANCH_COMMIT_PR';

export interface User {
  id: string;
  identity_provider_id: string;
  username: string;
  display_name: string;
  email: string;
  avatar_url?: string;
  provider: 'github' | 'google' | 'local' | 'azure_devops';
  roles: string[];
}

export interface AuthSessionResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface PullRequestInfo {
  pr_number: number;
  pr_url: string;
  title: string;
  body: string;
  base_branch: string;
  head_branch: string;
  status: string;
}

export interface ChangeRequestPayload {
  request_id?: string;
  story_id: string;
  title: string;
  description: string;
  repository_location: string;
  base_branch: string;
  target_branch?: string;
  execution_mode?: ExecutionMode;
  auto_apply?: boolean;
}

export type ChangeType = 'CREATE' | 'MODIFY' | 'DELETE';

export interface ImpactedFile {
  path: string;
  reason: string;
  confidence: number;
}

export interface PlannedChange {
  file_path: string;
  change_type: ChangeType;
  description: string;
}

export interface ChangePlan {
  story_id: string;
  summary: string;
  impacted_files: ImpactedFile[];
  planned_changes: PlannedChange[];
  dependencies: string[];
  risks: string[];
  testing_strategy: string[];
  clarifications: string[];
}

export interface FilePatch {
  file_path: string;
  change_type: ChangeType;
  content?: string;
  explanation?: string;
}

export interface PatchPlan {
  story_id: string;
  summary: string;
  file_patches: FilePatch[];
  notes?: string;
}

export type WorkflowStage =
  | 'INITIALIZED'
  | 'WORKSPACE_READY'
  | 'REPO_ANALYZED'
  | 'PLAN_GENERATED'
  | 'PLAN_VALIDATED'
  | 'PATCH_GENERATED'
  | 'PATCH_VALIDATED'
  | 'PATCH_APPLIED'
  | 'TESTS_EXECUTED'
  | 'PULL_REQUEST_CREATED'
  | 'COMPLETED'
  | 'FAILED';

export type WorkflowStatus = 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'REJECTED' | 'FAILED';

export interface StageExecutionRecord {
  stage: WorkflowStage;
  status: WorkflowStatus;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  message?: string;
  details?: Record<string, any>;
}

export interface ValidationResult {
  validator_name: string;
  passed: boolean;
  errors: string[];
  warnings: string[];
  output?: string;
  details?: Record<string, any>;
}

export interface WorkflowResult {
  execution_id: string;
  request_id: string;
  story_id: string;
  status: WorkflowStatus;
  current_stage: WorkflowStage;
  success: boolean;
  started_at: string;
  completed_at?: string;
  total_duration_ms?: number;
  repository_summary?: {
    primary_language: string;
    detected_languages: string[];
    detected_frameworks: string[];
    test_runner?: string;
    total_files: number;
  };
  change_plan?: ChangePlan;
  patch_plan?: PatchPlan;
  validation_results: ValidationResult[];
  applied_diff?: string;
  test_output?: string;
  test_passed?: boolean;
  branch_name?: string;
  commit_sha?: string;
  pull_request?: PullRequestInfo;
  audit_trail: StageExecutionRecord[];
  error_stage?: WorkflowStage;
  error_message?: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  vertex_ai_configured: boolean;
  version: string;
}

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
  timestamp: string;
  read: boolean;
  storyId?: string;
  detail?: string;
}

export interface StoryTemplate {
  id: string;
  title: string;
  category: string;
  description: string;
  storyId: string;
  repoLocation: string;
  impactLevel: 'Low' | 'Medium' | 'High' | 'Critical';
  tags: string[];
}

export interface ConnectedRepo {
  id?: string;
  name: string;
  path: string;
  provider?: string;
  language: string;
  testRunner: string;
  fileCount: number;
  lastChecked: string;
  status: 'ACTIVE' | 'INACTIVE' | 'Ready' | 'Needs Inspection' | string;
  branches?: string[];
  isPrivate?: boolean;
}
