import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ApiService } from './api.service';
import { NotificationService } from './notification.service';
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
  // Navigation State
  public activeNavSubject = new BehaviorSubject<string>('dashboard');
  public activeNav$: Observable<string> = this.activeNavSubject.asObservable();

  public searchQuerySubject = new BehaviorSubject<string>('');
  public searchQuery$: Observable<string> = this.searchQuerySubject.asObservable();

  // Active Story Configuration
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

  public reportsSubject = new BehaviorSubject<any>(null);
  public reports$: Observable<any> = this.reportsSubject.asObservable();

  public auditLogsSubject = new BehaviorSubject<any[]>([]);
  public auditLogs$: Observable<any[]> = this.auditLogsSubject.asObservable();

  // Modals & Inspection Tabs
  public showReportModalSubject = new BehaviorSubject<boolean>(false);
  public showReportModal$: Observable<boolean> = this.showReportModalSubject.asObservable();

  public showNewRequestModalSubject = new BehaviorSubject<boolean>(false);
  public showNewRequestModal$: Observable<boolean> = this.showNewRequestModalSubject.asObservable();

  public activeReportTabSubject = new BehaviorSubject<'diff' | 'plan' | 'logs' | 'audit'>('diff');
  public activeReportTab$: Observable<'diff' | 'plan' | 'logs' | 'audit'> = this.activeReportTabSubject.asObservable();

  // 9 Deterministic Safety Gate Stages
  public stages: PipelineStageItem[] = [
    { key: 'INITIALIZED', stage: 'INITIALIZED', number: 1, label: 'Intake & Boundaries', description: 'Parameter verification', color: '#8083ff' },
    { key: 'WORKSPACE_READY', stage: 'WORKSPACE_READY', number: 2, label: 'Sandbox Isolation', description: 'Disposable clone setup', color: '#8083ff' },
    { key: 'REPO_ANALYZED', stage: 'REPO_ANALYZED', number: 3, label: 'Repository Topology', description: 'AST & test runner inspection', color: '#8083ff' },
    { key: 'PLAN_GENERATED', stage: 'PLAN_GENERATED', number: 4, label: 'Deterministic Plan', description: 'Impact analysis & safety check', color: '#8083ff' },
    { key: 'PLAN_VALIDATED', stage: 'PLAN_VALIDATED', number: 5, label: 'Safety Gate Pass', description: 'Non-negotiable policy checks', color: '#4edea3' },
    { key: 'PATCH_GENERATED', stage: 'PATCH_GENERATED', number: 6, label: 'Patch Synthesis', description: 'Exact unified diff creation', color: '#4edea3' },
    { key: 'PATCH_APPLIED', stage: 'PATCH_APPLIED', number: 7, label: 'Isolated Apply', description: 'Sandboxed modification', color: '#4edea3' },
    { key: 'TESTS_EXECUTED', stage: 'TESTS_EXECUTED', number: 8, label: 'Automated Tests', description: 'Test runner execution', color: '#4edea3' },
    { key: 'COMPLETED', stage: 'COMPLETED', number: 9, label: 'Branch & PR Sync', description: 'GitHub App pull request', color: '#4edea3' }
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
    private notif: NotificationService
  ) {
    this.refreshHealth();
    this.refreshAllData();
  }

  public refreshAllData(): void {
    this.loadRepositories();
    this.loadChangeRequests();
    this.loadPipelines();
    this.loadSystemConfig();
    this.loadReports();
    this.loadAuditLogs();
  }

  public setNav(nav: string): void {
    this.activeNavSubject.next(nav);
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
          'Change Request Created',
          `Registered change story ${req.story_id}.`,
          'success'
        );
        this.loadChangeRequests();
      },
      error: (err) => {
        this.notif.addNotification('Creation Failed', err.error?.detail || 'Failed to create request.', 'error');
      }
    });
  }

  public executeWorkflow(): void {
    const storyId = this.storyIdSubject.value.trim();
    const title = this.titleSubject.value.trim();
    const description = this.descriptionSubject.value.trim();
    const repoLocation = this.repoLocationSubject.value.trim();
    const baseBranch = this.baseBranchSubject.value.trim();
    const executionMode = this.executionModeSubject.value;

    if (!storyId || !title || !description || !repoLocation) {
      this.errorMessageSubject.next('Please complete all required fields.');
      return;
    }

    this.isRunningSubject.next(true);
    this.errorMessageSubject.next(null);
    this.resultSubject.next(null);

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
        this.isRunningSubject.next(false);
        this.resultSubject.next(res);

        if (res.success) {
          this.notif.addNotification(
            'Change Succeeded',
            `${storyId} verified and completed safely across 9 gates.`,
            'success',
            storyId
          );
        } else {
          this.notif.addNotification(
            'Safety Gate Violation',
            `${storyId} halted safely: ${res.current_stage}`,
            'error',
            storyId
          );
        }
        this.refreshAllData();
      },
      error: (err) => {
        this.isRunningSubject.next(false);
        const detail = err.error?.detail || 'Workflow execution encountered an unexpected error.';
        this.errorMessageSubject.next(detail);
        this.notif.addNotification('Execution Error', detail, 'error');
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

  public inspectRepository(path?: string): void {
    const target = path || this.repoLocationSubject.value;
    this.isInspectingSubject.next(true);
    this.api.analyzeRepository(target).subscribe({
      next: (ctx) => {
        this.isInspectingSubject.next(false);
        this.notif.addNotification(
          'Analysis Completed',
          `Detected ${ctx.languages.join(', ')} with runner: ${ctx.test_runner_command || 'Auto'}`,
          'info'
        );
      },
      error: (err) => {
        this.isInspectingSubject.next(false);
        this.notif.addNotification(
          'Analysis Warning',
          err.error?.detail || 'Repository structure cached.',
          'info'
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
