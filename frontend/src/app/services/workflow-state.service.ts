import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ApiService } from './api.service';
import { NotificationService } from './notification.service';
import { AuthService } from './auth.service';
import {
  ChangeRequestPayload,
  ConnectedRepo,
  ExecutionMode,
  HealthResponse,
  StoryTemplate,
  WorkflowResult,
  WorkflowStage
} from '../models';

export interface RecentRun {
  storyId: string;
  title: string;
  repository: string;
  status: 'SUCCESS' | 'FAILED' | 'REJECTED';
  duration: string;
  timeAgo: string;
  branch?: string;
  pullRequestUrl?: string;
  appliedDiff?: string;
}

export interface ChangeRequestItem {
  id: string;
  story_id: string;
  title: string;
  description: string;
  repository: string;
  base_branch: string;
  status: string;
  priority: string;
  created_at?: string;
}

export interface PipelineStageItem {
  id: WorkflowStage;
  key: WorkflowStage;
  stage: WorkflowStage;
  number: number;
  label: string;
  description: string;
  color: string;
}

@Injectable({
  providedIn: 'root'
})
export class WorkflowStateService {
  // Navigation & Layout State
  public activeNavSubject = new BehaviorSubject<string>('dashboard');
  public activeNav$: Observable<string> = this.activeNavSubject.asObservable();

  public isSidebarCollapsedSubject = new BehaviorSubject<boolean>(false);
  public isSidebarCollapsed$: Observable<boolean> = this.isSidebarCollapsedSubject.asObservable();

  public isMobileSidebarOpenSubject = new BehaviorSubject<boolean>(false);
  public isMobileSidebarOpen$: Observable<boolean> = this.isMobileSidebarOpenSubject.asObservable();

  public toggleSidebar(): void {
    this.isSidebarCollapsedSubject.next(!this.isSidebarCollapsedSubject.value);
  }

  public setSidebarCollapsed(collapsed: boolean): void {
    this.isSidebarCollapsedSubject.next(collapsed);
  }

  public toggleMobileSidebar(): void {
    this.isMobileSidebarOpenSubject.next(!this.isMobileSidebarOpenSubject.value);
  }

  public closeMobileSidebar(): void {
    this.isMobileSidebarOpenSubject.next(false);
  }

  // Selected / Active View Detail
  public selectedStoryIdSubject = new BehaviorSubject<string | null>(null);
  public selectedStoryId$: Observable<string | null> = this.selectedStoryIdSubject.asObservable();

  // Search & Global Filters
  public searchQuerySubject = new BehaviorSubject<string>('');
  public searchQuery$: Observable<string> = this.searchQuerySubject.asObservable();

  // Inspection Modal
  public inspectionDetailsSubject = new BehaviorSubject<any | null>(null);
  public inspectionDetails$: Observable<any | null> = this.inspectionDetailsSubject.asObservable();
  public showInspectionModalSubject = new BehaviorSubject<boolean>(false);
  public showInspectionModal$: Observable<boolean> = this.showInspectionModalSubject.asObservable();

  // Pipeline Execution Confirmation Modal
  public showConfirmModalSubject = new BehaviorSubject<boolean>(false);
  public showConfirmModal$: Observable<boolean> = this.showConfirmModalSubject.asObservable();
  public confirmModalDataSubject = new BehaviorSubject<{
    storyId: string;
    title: string;
    description: string;
    repository: string;
    baseBranch: string;
    executionMode: string;
  } | null>(null);
  public confirmModalData$: Observable<any> = this.confirmModalDataSubject.asObservable();

  // Current Working Change Request State
  public storyIdSubject = new BehaviorSubject<string>('');
  public storyId$: Observable<string> = this.storyIdSubject.asObservable();

  public titleSubject = new BehaviorSubject<string>('');
  public title$: Observable<string> = this.titleSubject.asObservable();

  public descriptionSubject = new BehaviorSubject<string>('');
  public description$: Observable<string> = this.descriptionSubject.asObservable();

  public repoLocationSubject = new BehaviorSubject<string>('');
  public repoLocation$: Observable<string> = this.repoLocationSubject.asObservable();

  public baseBranchSubject = new BehaviorSubject<string>('main');
  public baseBranch$: Observable<string> = this.baseBranchSubject.asObservable();

  public executionModeSubject = new BehaviorSubject<ExecutionMode>('BRANCH_COMMIT_PR');
  public executionMode$: Observable<ExecutionMode> = this.executionModeSubject.asObservable();

  // Execution & Health State
  public isRunningSubject = new BehaviorSubject<boolean>(false);
  public isRunning$: Observable<boolean> = this.isRunningSubject.asObservable();

  public activeStageIndexSubject = new BehaviorSubject<number>(0);
  public activeStageIndex$: Observable<number> = this.activeStageIndexSubject.asObservable();

  private stageTimer: any = null;

  public isInspectingSubject = new BehaviorSubject<boolean>(false);
  public isInspecting$: Observable<boolean> = this.isInspectingSubject.asObservable();

  public resultSubject = new BehaviorSubject<WorkflowResult | null>(null);
  public result$: Observable<WorkflowResult | null> = this.resultSubject.asObservable();

  public healthSubject = new BehaviorSubject<HealthResponse | null>(null);
  public health$: Observable<HealthResponse | null> = this.healthSubject.asObservable();

  public systemConfigSubject = new BehaviorSubject<any | null>(null);
  public systemConfig$: Observable<any | null> = this.systemConfigSubject.asObservable();

  public errorMessageSubject = new BehaviorSubject<string | null>(null);
  public errorMessage$: Observable<string | null> = this.errorMessageSubject.asObservable();

  // Dynamic Data Lists
  public connectedReposSubject = new BehaviorSubject<ConnectedRepo[]>([]);
  public connectedRepos$: Observable<ConnectedRepo[]> = this.connectedReposSubject.asObservable();

  public changeRequestsSubject = new BehaviorSubject<ChangeRequestItem[]>([]);
  public changeRequests$: Observable<ChangeRequestItem[]> = this.changeRequestsSubject.asObservable();

  public recentRunsSubject = new BehaviorSubject<RecentRun[]>([]);
  public recentRuns$: Observable<RecentRun[]> = this.recentRunsSubject.asObservable();

  public assignedTicketsSubject = new BehaviorSubject<any[]>([]);
  public assignedTickets$: Observable<any[]> = this.assignedTicketsSubject.asObservable();

  public reportsSubject = new BehaviorSubject<any>(null);
  public reports$: Observable<any> = this.reportsSubject.asObservable();

  public auditLogsSubject = new BehaviorSubject<any[]>([]);
  public auditLogs$: Observable<any[]> = this.auditLogsSubject.asObservable();

  // GitHub Account Integration Status
  public githubStatusSubject = new BehaviorSubject<any>(null);
  public githubStatus$: Observable<any> = this.githubStatusSubject.asObservable();

  // Modals & Inspection Tabs
  public showReportModalSubject = new BehaviorSubject<boolean>(false);
  public showReportModal$: Observable<boolean> = this.showReportModalSubject.asObservable();

  public showNewRequestModalSubject = new BehaviorSubject<boolean>(false);
  public showNewRequestModal$: Observable<boolean> = this.showNewRequestModalSubject.asObservable();

  public activeReportTabSubject = new BehaviorSubject<'diff' | 'plan' | 'logs' | 'audit'>('diff');
  public activeReportTab$: Observable<'diff' | 'plan' | 'logs' | 'audit'> = this.activeReportTabSubject.asObservable();

  // 9 Deterministic Safety Gate Stages with Clear, Intuitive Action Titles
  public stages: PipelineStageItem[] = [
    { id: 'INITIALIZED', key: 'INITIALIZED', stage: 'INITIALIZED', number: 1, label: 'Requirement Intake', description: 'Validate story & boundaries', color: '#8083ff' },
    { id: 'WORKSPACE_READY', key: 'WORKSPACE_READY', stage: 'WORKSPACE_READY', number: 2, label: 'Sandbox Setup', description: 'Prepare isolated Git workspace', color: '#8083ff' },
    { id: 'REPO_ANALYZED', key: 'REPO_ANALYZED', stage: 'REPO_ANALYZED', number: 3, label: 'Stack & Topology', description: 'Analyze AST, files & toolchains', color: '#8083ff' },
    { id: 'PLAN_GENERATED', key: 'PLAN_GENERATED', stage: 'PLAN_GENERATED', number: 4, label: 'Architecture Plan', description: 'Synthesize change plan & impact', color: '#8083ff' },
    { id: 'PLAN_VALIDATED', key: 'PLAN_VALIDATED', stage: 'PLAN_VALIDATED', number: 5, label: 'Safety Policy Gate', description: 'Verify security & path rules', color: '#4edea3' },
    { id: 'PATCH_GENERATED', key: 'PATCH_GENERATED', stage: 'PATCH_GENERATED', number: 6, label: 'AI Code Synthesis', description: 'Generate code & unified diff', color: '#4edea3' },
    { id: 'PATCH_APPLIED', key: 'PATCH_APPLIED', stage: 'PATCH_APPLIED', number: 7, label: 'Patch Application', description: 'Apply atomic changes to workspace', color: '#4edea3' },
    { id: 'TESTS_EXECUTED', key: 'TESTS_EXECUTED', stage: 'TESTS_EXECUTED', number: 8, label: 'Test Verification', description: 'Run test suite & syntax checks', color: '#4edea3' },
    { id: 'COMPLETED', key: 'COMPLETED', stage: 'COMPLETED', number: 9, label: 'Branch & PR Sync', description: 'Push branch & create GitHub PR', color: '#4edea3' }
  ];

  public storyTemplates: StoryTemplate[] = [
    {
      id: 'tmpl-1',
      title: 'Calculator Flat Monetary Discount',
      category: 'Features',
      description: 'Add an optional flat monetary discount parameter to calculate_total function.',
      storyId: 'CP-1042',
      repoLocation: 'project-changepilot',
      impactLevel: 'Medium',
      tags: ['Python', 'pytest', 'Calculator']
    }
  ];

  constructor(
    private api: ApiService,
    private notif: NotificationService,
    private auth: AuthService
  ) {
    this.refreshHealth();
    this.auth.currentUser$.subscribe(user => {
      if (user) {
        this.clearAllUserData();
        this.refreshAllData();
      } else {
        this.clearAllUserData();
      }
    });
  }

  public clearAllUserData(): void {
    this.connectedReposSubject.next([]);
    this.changeRequestsSubject.next([]);
    this.assignedTicketsSubject.next([]);
    this.recentRunsSubject.next([]);
    this.reportsSubject.next(null);
    this.auditLogsSubject.next([]);
    this.githubStatusSubject.next({ connected: false, username: null, avatar_url: null, message: null });
    this.resultSubject.next(null);
    this.storyIdSubject.next('');
    this.titleSubject.next('');
    this.descriptionSubject.next('');
    this.repoLocationSubject.next('');
  }

  public refreshAllData(): void {
    this.loadRepositories();
    this.loadChangeRequests();
    this.loadAssignedTickets();
    this.loadPipelines();
    this.loadSystemConfig();
    this.loadReports();
    this.loadAuditLogs();
    this.loadGitHubStatus();
  }

  public loadGitHubStatus(): void {
    this.api.getGitHubStatus().subscribe({
      next: (st) => this.githubStatusSubject.next(st),
      error: () => this.githubStatusSubject.next({ connected: false })
    });
  }

  public connectGitHubToken(token: string): Observable<any> {
    return this.api.connectGitHub(token);
  }

  public disconnectGitHub(): void {
    this.api.disconnectGitHub().subscribe({
      next: () => {
        this.githubStatusSubject.next({ connected: false });
        this.notif.addNotification('GitHub Disconnected', 'Disconnected GitHub account credentials.', 'info');
      },
      error: () => {}
    });
  }

  public setNav(nav: string): void {
    this.activeNavSubject.next(nav);
    this.closeMobileSidebar();
  }

  public setSearchQuery(q: string): void {
    this.searchQuerySubject.next(q);
  }

  public refreshHealth(): void {
    this.api.getHealth().subscribe({
      next: (h) => this.healthSubject.next(h),
      error: () => this.healthSubject.next({
        status: 'error',
        app_name: 'ChangePilot',
        environment: 'development',
        vertex_ai_configured: false,
        version: '1.0.0'
      })
    });
  }

  public loadSystemConfig(): void {
    this.api.getSystemConfig().subscribe({
      next: (cfg) => this.systemConfigSubject.next(cfg),
      error: () => {}
    });
  }

  public loadRepositories(): void {
    this.api.listRepositories().subscribe({
      next: (res) => {
        const repos: ConnectedRepo[] = (res.repositories || []).map((r: any) => ({
          id: r.id || r.name,
          name: r.name,
          path: r.full_name || r.name,
          provider: r.provider || 'github',
          language: r.language || 'Python',
          testRunner: r.test_runner || 'pytest',
          fileCount: 12,
          lastChecked: 'Active',
          status: 'Ready',
          branches: r.branches || ['main'],
          isPrivate: r.is_private
        }));
        this.connectedReposSubject.next(repos);
      },
      error: () => {}
    });
  }

  public loadChangeRequests(): void {
    this.api.listChangeRequests().subscribe({
      next: (reqs) => this.changeRequestsSubject.next(reqs),
      error: () => {}
    });
  }

  public loadAssignedTickets(): void {
    this.api.getAssignedTickets().subscribe({
      next: (tkts) => this.assignedTicketsSubject.next(tkts),
      error: () => {}
    });
  }

  public selectAssignedTicket(tkt: any): void {
    this.storyIdSubject.next(tkt.story_id);
    this.titleSubject.next(tkt.title);
    this.descriptionSubject.next(tkt.description + (tkt.acceptance_criteria ? '\n\nAcceptance Criteria:\n- ' + tkt.acceptance_criteria.join('\n- ') : ''));
    if (tkt.repository) {
      this.repoLocationSubject.next(tkt.repository);
    }
    if (tkt.base_branch) {
      this.baseBranchSubject.next(tkt.base_branch);
    }
    this.setNav('requests');
  }

  public loadPipelines(): void {
    this.api.listPipelines().subscribe({
      next: (runs) => {
        const mapped: RecentRun[] = (runs || []).map((r: any) => ({
          storyId: r.story_id,
          title: r.title,
          repository: r.repository,
          status: r.success ? 'SUCCESS' : (r.status === 'REJECTED' ? 'REJECTED' : 'FAILED'),
          duration: r.duration_ms ? `${(r.duration_ms / 1000).toFixed(1)}s` : '3.2s',
          timeAgo: r.started_at ? 'Recently' : 'Just now',
          branch: r.branch_name,
          pullRequestUrl: r.pull_request?.pr_url,
          appliedDiff: r.applied_diff
        }));
        this.recentRunsSubject.next(mapped);
      },
      error: () => {}
    });
  }

  public loadReports(): void {
    this.api.getReports().subscribe({
      next: (rep) => this.reportsSubject.next(rep),
      error: () => {}
    });
  }

  public loadAuditLogs(storyId?: string, repo?: string): void {
    this.api.getAuditLogs(storyId, repo).subscribe({
      next: (logs) => this.auditLogsSubject.next(logs),
      error: () => {}
    });
  }

  public connectNewRepository(
    name: string,
    provider: string,
    baseBranch: string,
    isPrivate: boolean
  ): void {
    this.api.connectRepository({
      repository_name: name,
      provider: provider,
      base_branch: baseBranch,
      is_public: !isPrivate
    }).subscribe({
      next: () => {
        this.notif.addNotification(
          'Repository Connected',
          `Connected ${name} (${provider.toUpperCase()}) successfully.`,
          'success'
        );
        this.loadRepositories();
      },
      error: (err) => {
        this.notif.addNotification(
          'Connection Failed',
          err.error?.detail || 'Could not connect repository.',
          'error'
        );
      }
    });
  }

  public syncRepositories(): void {
    this.api.syncRepositories().subscribe({
      next: (res) => {
        this.notif.addNotification(
          'Repositories Synced',
          `Discovered and synced ${res.synced_count || 0} repositories from GitHub.`,
          'success'
        );
        this.loadRepositories();
      },
      error: (err) => {
        this.notif.addNotification(
          'Sync Failed',
          err.error?.detail || 'Could not sync repositories from GitHub.',
          'error'
        );
      }
    });
  }

  public importPublicRepository(gitUrl: string, baseBranch: string = 'main'): void {
    this.api.importPublicRepository(gitUrl, baseBranch).subscribe({
      next: (res) => {
        this.notif.addNotification(
          'Public Repository Imported',
          `Discovered branches and registered ${res.repository?.name || gitUrl}.`,
          'success'
        );
        this.loadRepositories();
      },
      error: (err) => {
        this.notif.addNotification(
          'Import Failed',
          err.error?.detail || 'Could not import public repository.',
          'error'
        );
      }
    });
  }

  public createChangeRequest(req: { story_id: string; title: string; description: string; repository: string; base_branch: string; priority: string }): void {
    this.api.createChangeRequest(req).subscribe({
      next: () => {
        this.notif.addNotification(
          'Change Request Saved',
          `Saved change request #${req.story_id}.`,
          'success'
        );
        this.loadChangeRequests();
      },
      error: (err) => {
        this.notif.addNotification('Creation Failed', err.error?.detail || 'Failed to create request.', 'error');
      }
    });
  }

  public deleteChangeRequest(requestId: string): void {
    this.api.deleteChangeRequest(requestId).subscribe({
      next: () => {
        this.notif.addNotification('Change Request Deleted', `Removed change request #${requestId}.`, 'info');
        this.loadChangeRequests();
        if (this.storyIdSubject.value === requestId) {
          this.storyIdSubject.next('');
          this.titleSubject.next('');
          this.descriptionSubject.next('');
          this.repoLocationSubject.next('');
        }
      },
      error: (err) => {
        this.notif.addNotification('Delete Failed', err.error?.detail || 'Failed to delete change request.', 'error');
      }
    });
  }

  public isCurrentPipelineCompletedWithPR(): boolean {
    const result = this.resultSubject.value;
    const currentStory = this.storyIdSubject.value?.trim();
    if (!result || !currentStory) return false;

    const isMatchingStory = (result.story_id === currentStory);
    const isSuccessful = result.success === true || result.status === 'SUCCESS';
    const hasPR = !!(result.pull_request?.pr_url || result.pull_request?.pr_number);

    return isMatchingStory && isSuccessful && hasPR;
  }

  public promptRunPipeline(customPayload?: Partial<{ storyId: string; title: string; description: string; repository: string; baseBranch: string; executionMode: string }>): void {
    if (this.isRunningSubject.value) {
      return;
    }

    if (customPayload) {
      if (customPayload.storyId !== undefined) this.storyIdSubject.next(customPayload.storyId);
      if (customPayload.title !== undefined) this.titleSubject.next(customPayload.title);
      if (customPayload.description !== undefined) this.descriptionSubject.next(customPayload.description);
      if (customPayload.repository !== undefined) this.repoLocationSubject.next(customPayload.repository);
      if (customPayload.baseBranch !== undefined) this.baseBranchSubject.next(customPayload.baseBranch);
      if (customPayload.executionMode !== undefined) this.executionModeSubject.next(customPayload.executionMode as any);
    }

    const storyId = this.storyIdSubject.value?.trim();
    const title = this.titleSubject.value?.trim();
    const description = this.descriptionSubject.value?.trim();
    const repository = this.repoLocationSubject.value?.trim();
    const baseBranch = this.baseBranchSubject.value?.trim() || 'main';
    const executionMode = this.executionModeSubject.value || 'BRANCH_COMMIT_PR';

    if (!storyId || !title || !description || !repository) {
      this.notif.addNotification(
        'Incomplete Change Request',
        'Please enter the Story ID, Title, Requirements, and Target Repository before running the pipeline.',
        'warning'
      );
      this.setNav('requests');
      return;
    }

    if (this.isCurrentPipelineCompletedWithPR()) {
      const res = this.resultSubject.value;
      const prNum = res?.pull_request?.pr_number ? `#${res.pull_request.pr_number}` : '';
      this.notif.addNotification(
        'Pipeline Already Completed',
        `Pull Request ${prNum} is already raised and open for this change. Rerunning a successfully completed change request is prevented.`,
        'warning',
        storyId
      );
      return;
    }

    this.confirmModalDataSubject.next({
      storyId,
      title,
      description,
      repository,
      baseBranch,
      executionMode
    });
    this.showConfirmModalSubject.next(true);
  }

  public confirmAndExecutePipeline(): void {
    this.showConfirmModalSubject.next(false);
    this.executeWorkflow();
  }

  public cancelConfirmModal(): void {
    this.showConfirmModalSubject.next(false);
  }

  public executeWorkflow(): void {
    const storyId = this.storyIdSubject.value?.trim();
    const title = this.titleSubject.value?.trim();
    const description = this.descriptionSubject.value?.trim();
    const repoLocation = this.repoLocationSubject.value?.trim();
    const baseBranch = this.baseBranchSubject.value?.trim() || 'main';
    const executionMode = this.executionModeSubject.value || 'BRANCH_COMMIT_PR';

    if (!storyId || !title || !description || !repoLocation) {
      this.notif.addNotification(
        'Incomplete Change Request',
        'Please specify the Story ID, Title, Requirements, and Repository in the Change Request form.',
        'warning'
      );
      this.setNav('requests');
      return;
    }

    if (this.stageTimer) {
      clearTimeout(this.stageTimer);
      clearInterval(this.stageTimer);
      this.stageTimer = null;
    }

    this.isRunningSubject.next(true);
    this.activeStageIndexSubject.next(0);
    this.errorMessageSubject.next(null);
    this.resultSubject.next(null);

    // Realistic stage-aware progression matching actual AI agent execution time
    const stageDurations = [1200, 1800, 2200, 9500, 1400, 13500, 1800, 4000];
    let currentStageIdx = 0;
    
    const scheduleNextStage = () => {
      if (currentStageIdx < 7 && this.isRunningSubject.value) {
        const delay = stageDurations[currentStageIdx] || 3000;
        this.stageTimer = setTimeout(() => {
          if (this.isRunningSubject.value) {
            currentStageIdx++;
            this.activeStageIndexSubject.next(currentStageIdx);
            scheduleNextStage();
          }
        }, delay);
      }
    };
    scheduleNextStage();

    const payload: ChangeRequestPayload = {
      request_id: 'req-' + Math.random().toString(36).substring(2, 9),
      story_id: storyId,
      title: title,
      description: description,
      repository_location: repoLocation,
      base_branch: baseBranch,
      execution_mode: executionMode
    };

    this.api.executeChange(payload).subscribe({
      next: (res) => {
        if (this.stageTimer) {
          clearTimeout(this.stageTimer);
          clearInterval(this.stageTimer);
          this.stageTimer = null;
        }
        this.isRunningSubject.next(false);
        this.resultSubject.next(res);

        if (res.success) {
          this.activeStageIndexSubject.next(8);
          this.notif.addNotification(
            'Pipeline Succeeded',
            `${storyId} verified and completed safely across all 9 gates.`,
            'success',
            storyId
          );
        } else {
          const failedStageId = res.error_stage || res.current_stage || 'UNKNOWN';
          const failedIdx = this.stages.findIndex(s => s.id === failedStageId);
          this.activeStageIndexSubject.next(failedIdx !== -1 ? failedIdx : 3);
          const errorMsg = res.error_message || `Safety gate check failed at ${failedStageId}.`;
          this.errorMessageSubject.next(errorMsg);
          this.notif.addNotification(
            `Safety Gate Halted: ${failedStageId}`,
            errorMsg,
            'error',
            storyId,
            res.error_message || JSON.stringify(res.audit_trail || {}, null, 2)
          );
        }
        this.refreshAllData();
      },
      error: (err) => {
        if (this.stageTimer) {
          clearInterval(this.stageTimer);
          this.stageTimer = null;
        }
        this.isRunningSubject.next(false);
        const detail = err.error?.detail || err.message || 'Workflow execution encountered an unexpected server error.';
        this.errorMessageSubject.next(detail);
        this.notif.addNotification('Pipeline Execution Error', detail, 'error', storyId, typeof err.error === 'object' ? JSON.stringify(err.error, null, 2) : String(err));
      }
    });
  }

  public runWorkflow(): void {
    this.executeWorkflow();
  }

  public loadDemoPreset(): void {
    this.storyIdSubject.next('CP-1042');
    this.titleSubject.next('Add Percentage Discount Rule to Calculator Engine');
    this.descriptionSubject.next('Implement apply_discount(total, percent) method with validation that percentage is between 0 and 100.');
    this.repoLocationSubject.next('project-changepilot');
    this.baseBranchSubject.next('main');
  }

  public loadEnterprisePreset(): void {
    this.storyIdSubject.next('CP-1043');
    this.titleSubject.next('Refactor Session Expiration & Refresh Token Strategy');
    this.descriptionSubject.next('Update auth middleware to reject revoked JWT tokens and enforce strict expiration timeouts.');
    this.repoLocationSubject.next('project-changepilot');
    this.baseBranchSubject.next('main');
  }

  public applyTemplate(tmpl: StoryTemplate): void {
    this.storyIdSubject.next(tmpl.storyId);
    this.titleSubject.next(tmpl.title);
    this.descriptionSubject.next(tmpl.description);
    this.repoLocationSubject.next(tmpl.repoLocation);
  }

  public deleteRepository(repoId: string, repoName?: string): void {
    this.api.deleteRepository(repoId).subscribe({
      next: () => {
        this.notif.addNotification(
          'Repository Unlinked',
          `Unlinked and removed ${repoName || repoId} from ChangePilot.`,
          'success'
        );
        this.loadRepositories();
      },
      error: (err) => {
        this.notif.addNotification(
          'Unlink Failed',
          err.error?.detail || 'Failed to remove repository.',
          'error'
        );
      }
    });
  }

  public closeInspectionModal(): void {
    this.showInspectionModalSubject.next(false);
  }

  public inspectRepository(path?: string): void {
    const target = path || this.repoLocationSubject.value;
    if (!target) return;
    this.isInspectingSubject.next(true);
    this.api.analyzeRepository(target).subscribe({
      next: (ctx) => {
        this.isInspectingSubject.next(false);
        this.inspectionDetailsSubject.next({
          target: target,
          ...ctx
        });
        this.showInspectionModalSubject.next(true);
        this.notif.addNotification(
          'Topology Inspected',
          `${target}: Detected ${ctx.primary_language} (${(ctx.frameworks || []).join(', ') || 'Standard'}) with runner: ${ctx.test_runner_command || 'Auto'}`,
          'info'
        );
        this.loadRepositories();
      },
      error: (err) => {
        this.isInspectingSubject.next(false);
        this.notif.addNotification(
          'Inspection Warning',
          err.error?.detail || 'Failed to analyze repository topology.',
          'error'
        );
      }
    });
  }

  public openNewRequestModal(): void {
    this.showNewRequestModalSubject.next(true);
  }

  public closeNewRequestModal(): void {
    this.showNewRequestModalSubject.next(false);
  }

  public openReportModal(tab: 'diff' | 'plan' | 'logs' | 'audit' = 'diff'): void {
    this.activeReportTabSubject.next(tab);
    this.showReportModalSubject.next(true);
  }

  public closeReportModal(): void {
    this.showReportModalSubject.next(false);
  }

  public setReportTab(tab: 'diff' | 'plan' | 'logs' | 'audit'): void {
    this.activeReportTabSubject.next(tab);
  }
}
