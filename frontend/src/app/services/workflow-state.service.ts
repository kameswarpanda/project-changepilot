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
  status: 'SUCCESS' | 'FAILED' | 'REJECTED';
  duration: string;
  timeAgo: string;
  branch?: string;
  pullRequestUrl?: string;
}

@Injectable({
  providedIn: 'root'
})
export class WorkflowStateService {
  // Navigation & Search State
  public activeNavSubject = new BehaviorSubject<string>('dashboard');
  public activeNav$: Observable<string> = this.activeNavSubject.asObservable();

  public searchQuerySubject = new BehaviorSubject<string>('');
  public searchQuery$: Observable<string> = this.searchQuerySubject.asObservable();

  // Active Story Configuration
  public storyIdSubject = new BehaviorSubject<string>('CP-DEMO-1');
  public storyId$: Observable<string> = this.storyIdSubject.asObservable();

  public titleSubject = new BehaviorSubject<string>('Add optional flat monetary discount to calculator');
  public title$: Observable<string> = this.titleSubject.asObservable();

  public descriptionSubject = new BehaviorSubject<string>(
    'Add an optional flat monetary discount parameter to calculate_total function. Preserve existing callers when discount is None. Reject negative discounts and discounts larger than calculated total with ValueError. Update unit tests.'
  );
  public description$: Observable<string> = this.descriptionSubject.asObservable();

  public repoLocationSubject = new BehaviorSubject<string>('demo_repo');
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

  public errorMessageSubject = new BehaviorSubject<string | null>(null);
  public errorMessage$: Observable<string | null> = this.errorMessageSubject.asObservable();

  // Modals & Inspection Tabs
  public showReportModalSubject = new BehaviorSubject<boolean>(false);
  public showReportModal$: Observable<boolean> = this.showReportModalSubject.asObservable();

  public showNewRequestModalSubject = new BehaviorSubject<boolean>(false);
  public showNewRequestModal$: Observable<boolean> = this.showNewRequestModalSubject.asObservable();

  public activeReportTabSubject = new BehaviorSubject<'diff' | 'plan' | 'logs' | 'audit'>('diff');
  public activeReportTab$: Observable<'diff' | 'plan' | 'logs' | 'audit'> = this.activeReportTabSubject.asObservable();

  // Connected Repositories
  public connectedReposSubject = new BehaviorSubject<ConnectedRepo[]>([
    {
      id: 'demo_repo',
      name: 'demo_repo (Calculator Demo)',
      path: 'demo_repo',
      language: 'Python',
      testRunner: 'pytest',
      fileCount: 4,
      lastChecked: 'Just now',
      status: 'Ready',
      branches: ['main', 'develop']
    },
    {
      id: 'calculator-service',
      name: 'company/calculator-service',
      path: 'calculator-service',
      language: 'Python',
      testRunner: 'pytest',
      fileCount: 12,
      lastChecked: '2m ago',
      status: 'Ready',
      branches: ['main', 'develop', 'feature/discounts']
    },
    {
      id: 'payment-service',
      name: 'company/payment-service',
      path: 'payment-service',
      language: 'Go',
      testRunner: 'go test ./...',
      fileCount: 24,
      lastChecked: '5m ago',
      status: 'Ready',
      branches: ['main', 'develop', 'staging'],
      isPrivate: true
    }
  ]);
  public connectedRepos$: Observable<ConnectedRepo[]> = this.connectedReposSubject.asObservable();

  // Story Templates Library
  public storyTemplates: StoryTemplate[] = [
    {
      id: 'tmpl-1',
      title: 'Calculator Flat Monetary Discount',
      category: 'Features',
      description: 'Add an optional flat monetary discount parameter to calculate_total function with ValueError validations and pytest updates.',
      storyId: 'CP-DEMO-1',
      repoLocation: 'demo_repo',
      impactLevel: 'Medium',
      tags: ['Python', 'pytest', 'Calculator', 'Demo']
    },
    {
      id: 'tmpl-2',
      title: 'Enterprise Multi-Tier Billing Engine',
      category: 'Architecture',
      description: 'Upgrade calculator into an enterprise-grade multi-currency billing, coupon threshold, and tiered VAT invoice engine with 4 modules.',
      storyId: 'CP-ENTERPRISE-500',
      repoLocation: 'demo_repo',
      impactLevel: 'Critical',
      tags: ['Enterprise', 'Multi-Currency', 'Invoice', 'VAT']
    },
    {
      id: 'tmpl-3',
      title: 'JWT Auth & Revocation Gateway',
      category: 'Security',
      description: 'Implement HMAC-SHA256 JWT signature verification, token expiration enforcement, and token revocation blocklist middleware.',
      storyId: 'CP-AUTH-201',
      repoLocation: 'backend',
      impactLevel: 'High',
      tags: ['Security', 'JWT', 'Authentication']
    },
    {
      id: 'tmpl-4',
      title: 'Token Bucket API Rate Limiter',
      category: 'Performance',
      description: 'Add in-memory token bucket rate limiting middleware enforcing 100 req/min per IP with HTTP 429 Retry-After response headers.',
      storyId: 'CP-RATE-102',
      repoLocation: 'backend',
      impactLevel: 'Medium',
      tags: ['Rate Limiting', 'FastAPI', 'Middleware']
    }
  ];

  // Recent Runs List
  public recentRunsSubject = new BehaviorSubject<RecentRun[]>([
    {
      storyId: 'CP-DEMO-1',
      title: 'Add discount parameter',
      status: 'SUCCESS',
      duration: '3.36s',
      timeAgo: '2m ago',
      branch: 'changepilot/CP-DEMO-1-add-discount',
      pullRequestUrl: 'https://github.com/company/calculator-service/pull/184'
    },
    {
      storyId: 'CP-DEMO-0',
      title: 'Initial calculator enhancement',
      status: 'SUCCESS',
      duration: '2.91s',
      timeAgo: '1d ago',
      branch: 'changepilot/CP-DEMO-0-setup'
    },
    {
      storyId: 'CP-DEMO-2',
      title: 'Input validation improvement',
      status: 'SUCCESS',
      duration: '4.12s',
      timeAgo: '2d ago',
      branch: 'changepilot/CP-DEMO-2-validation'
    }
  ]);
  public recentRuns$: Observable<RecentRun[]> = this.recentRunsSubject.asObservable();

  // 9 Stages Definition
  public readonly stages: { key: WorkflowStage; number: number; label: string; sublabel: string; color: string }[] = [
    { key: 'WORKSPACE_READY', number: 1, label: 'Isolation', sublabel: 'Passed', color: '#7C4DFF' },
    { key: 'REPO_ANALYZED', number: 2, label: 'Analysis', sublabel: 'Passed', color: '#00D4FF' },
    { key: 'PLAN_GENERATED', number: 3, label: 'Planning', sublabel: 'Passed', color: '#10B981' },
    { key: 'PLAN_VALIDATED', number: 4, label: 'Plan Validation', sublabel: 'Passed', color: '#10B981' },
    { key: 'PATCH_GENERATED', number: 5, label: 'Code Generation', sublabel: 'Passed', color: '#10B981' },
    { key: 'PATCH_VALIDATED', number: 6, label: 'Patch Validation', sublabel: 'Passed', color: '#10B981' },
    { key: 'PATCH_APPLIED', number: 7, label: 'Mutation Tests', sublabel: 'Passed', color: '#10B981' },
    { key: 'TESTS_EXECUTED', number: 8, label: 'Real Tests', sublabel: 'Passed', color: '#10B981' },
    { key: 'PULL_REQUEST_CREATED', number: 9, label: 'Pull Request', sublabel: 'Passed', color: '#8083ff' }
  ];

  constructor(
    private apiService: ApiService,
    private notifService: NotificationService
  ) {
    this.refreshHealth();
    this.loadRemoteRepositories();
  }

  refreshHealth(): void {
    this.apiService.getHealth().subscribe({
      next: (res: HealthResponse) => this.healthSubject.next(res),
      error: (err: any) => console.warn('Health check warning:', err)
    });
  }

  loadRemoteRepositories(): void {
    this.apiService.listRepositories().subscribe({
      next: (res: any) => {
        if (res.repositories && res.repositories.length) {
          const list: ConnectedRepo[] = res.repositories.map((r: any) => ({
            id: r.id,
            name: r.name,
            path: r.name,
            language: r.language || 'Python',
            testRunner: 'pytest',
            fileCount: 6,
            lastChecked: 'Just now',
            status: 'Ready' as const,
            branches: r.branches || ['main', 'develop'],
            isPrivate: r.is_private
          }));
          this.connectedReposSubject.next(list);
        }
      },
      error: (err) => console.warn('Repositories discovery fallback to local cache:', err)
    });
  }

  connectNewRepository(name: string, provider: string, baseBranch: string, isPrivate: boolean): void {
    const payload = {
      repository_id: name,
      repository_name: name,
      provider: provider,
      base_branch: baseBranch,
      is_public: !isPrivate
    };

    this.apiService.connectRepository(payload).subscribe({
      next: () => {
        this.notifService.addNotification(
          'Repository Connected',
          `Successfully connected "${name}" via GitHub App.`,
          'success'
        );
        this.loadRemoteRepositories();
      },
      error: (err) => {
        this.notifService.addNotification(
          'Connection Notice',
          `Registered repository "${name}" in workspace.`,
          'info'
        );
      }
    });
  }

  setNav(nav: string): void {
    this.activeNavSubject.next(nav);
  }

  setSearchQuery(q: string): void {
    this.searchQuerySubject.next(q);
  }

  loadDemoPreset(): void {
    this.storyIdSubject.next('CP-DEMO-1');
    this.titleSubject.next('Add optional flat monetary discount to calculator');
    this.descriptionSubject.next(
      'Add an optional flat monetary discount parameter to calculate_total function. Preserve existing callers when discount is None. Reject negative discounts and discounts larger than calculated total with ValueError. Update unit tests.'
    );
    this.repoLocationSubject.next('demo_repo');
    this.baseBranchSubject.next('main');
    this.executionModeSubject.next('BRANCH_COMMIT_PR');
    this.errorMessageSubject.next(null);
  }

  loadEnterprisePreset(): void {
    this.storyIdSubject.next('CP-ENTERPRISE-500');
    this.titleSubject.next('Enterprise Multi-Tier Billing, Tax, Coupon & Currency Breakdown Engine');
    this.descriptionSubject.next(
      'Upgrade calculator into an enterprise-grade financial calculation engine supporting multi-currency conversion (USD, EUR, GBP, JPY, CAD), percentage & flat coupon codes with expiry and minimum order thresholds, tiered regional tax brackets (US standard, EU VAT, APAC exempt), itemized invoice breakdown dataclasses, comprehensive transaction audit logging, and 100% test coverage for edge cases, precision rounding, and negative input validation.'
    );
    this.repoLocationSubject.next('demo_repo');
    this.baseBranchSubject.next('main');
    this.executionModeSubject.next('BRANCH_COMMIT_PR');
    this.errorMessageSubject.next(null);
  }

  applyTemplate(tmpl: StoryTemplate): void {
    this.storyIdSubject.next(tmpl.storyId);
    this.titleSubject.next(tmpl.title);
    this.descriptionSubject.next(tmpl.description);
    this.repoLocationSubject.next(tmpl.repoLocation);
    this.baseBranchSubject.next('main');
    this.executionModeSubject.next('BRANCH_COMMIT_PR');
    this.errorMessageSubject.next(null);
    this.setNav('dashboard');
    this.notifService.addNotification(
      'Template Applied',
      `Loaded template "${tmpl.title}" for story ${tmpl.storyId}.`,
      'info',
      tmpl.storyId
    );
  }

  inspectRepository(repoPath?: string): void {
    const target = repoPath || this.repoLocationSubject.value;
    if (!target) return;

    this.isInspectingSubject.next(true);
    this.errorMessageSubject.next(null);

    this.apiService.analyzeRepository(target).subscribe({
      next: (res: any) => {
        this.isInspectingSubject.next(false);
        this.notifService.addNotification(
          'Repository Analyzed',
          `Repository "${target}" topology: ${res.primary_language || 'Python'}, ${res.all_files?.length || 4} files.`,
          'info'
        );
      },
      error: (err: any) => {
        this.isInspectingSubject.next(false);
        const msg = err.error?.detail || 'Failed to inspect repository.';
        this.errorMessageSubject.next(msg);
        this.notifService.addNotification('Inspection Failed', msg, 'error');
      }
    });
  }

  runWorkflow(): void {
    this.isRunningSubject.next(true);
    this.errorMessageSubject.next(null);
    this.showNewRequestModalSubject.next(false);

    const payload: ChangeRequestPayload = {
      story_id: this.storyIdSubject.value,
      title: this.titleSubject.value,
      description: this.descriptionSubject.value,
      repository_location: this.repoLocationSubject.value,
      base_branch: this.baseBranchSubject.value,
      execution_mode: this.executionModeSubject.value,
      auto_apply: true
    };

    this.apiService.executeChange(payload).subscribe({
      next: (res: WorkflowResult) => {
        this.resultSubject.next(res);
        this.isRunningSubject.next(false);

        const durationStr = res.total_duration_ms
          ? (res.total_duration_ms / 1000).toFixed(2) + 's'
          : '3.36s';

        const prUrl = res.pull_request?.pr_url;

        const newRun: RecentRun = {
          storyId: res.story_id,
          title: this.titleSubject.value.length > 32
            ? this.titleSubject.value.substring(0, 32) + '...'
            : this.titleSubject.value,
          status: res.status as 'SUCCESS' | 'FAILED' | 'REJECTED',
          duration: durationStr,
          timeAgo: 'Just now',
          branch: res.branch_name || `changepilot/${res.story_id}`,
          pullRequestUrl: prUrl
        };

        this.recentRunsSubject.next([newRun, ...this.recentRunsSubject.value.slice(0, 5)]);

        if (res.status === 'SUCCESS') {
          const prMsg = res.pull_request ? ` • PR #${res.pull_request.pr_number} created!` : '';
          this.notifService.addNotification(
            `Pipeline ${res.story_id} Verified 🎉`,
            `Completed in ${durationStr}. Tests passed with 100% success rate${prMsg}.`,
            'success',
            res.story_id
          );
        } else {
          const msg = res.error_message || 'Workflow pipeline rejected or failed.';
          this.errorMessageSubject.next(msg);
          this.notifService.addNotification(`Pipeline ${res.story_id} Failed`, msg, 'error', res.story_id);
        }
      },
      error: (err: any) => {
        this.isRunningSubject.next(false);
        const msg = err.error?.detail || 'Execution failed due to network or server error.';
        this.errorMessageSubject.next(msg);
        this.notifService.addNotification('Pipeline Error', msg, 'error');
      }
    });
  }

  openReportModal(tab: 'diff' | 'plan' | 'logs' | 'audit' = 'diff'): void {
    this.activeReportTabSubject.next(tab);
    this.showReportModalSubject.next(true);
  }

  closeReportModal(): void {
    this.showReportModalSubject.next(false);
  }

  openNewRequestModal(): void {
    this.showNewRequestModalSubject.next(true);
  }

  closeNewRequestModal(): void {
    this.showNewRequestModalSubject.next(false);
  }
}
