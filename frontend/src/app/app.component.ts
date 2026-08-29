import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from './services/api.service';
import { ChangeRequestPayload, HealthResponse, WorkflowResult, WorkflowStage } from './models';

interface RecentRun {
  storyId: string;
  title: string;
  status: 'SUCCESS' | 'FAILED' | 'REJECTED';
  duration: string;
  timeAgo: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  // Application State
  health: HealthResponse | null = null;
  isRunning: boolean = false;
  isInspecting: boolean = false;
  activeNav: string = 'dashboard';
  searchQuery: string = '';
  errorMessage: string | null = null;

  // Modals & Panels
  showReportModal: boolean = false;
  showNewRequestModal: boolean = false;
  activeTab: 'diff' | 'plan' | 'logs' | 'audit' = 'diff';

  // Change Request Form
  storyId: string = 'CP-DEMO-1';
  title: string = 'Add optional flat monetary discount to calculator';
  description: string = 'Add an optional flat monetary discount parameter to calculate_total function. Preserve existing callers when discount is None. Reject negative discounts and discounts larger than calculated total with ValueError. Update unit tests.';
  repoLocation: string = 'demo_repo';
  baseBranch: string = 'main';

  // Execution Result
  result: WorkflowResult | null = null;
  analyzedContext: any = null;

  // KPI Dashboard Metrics
  kpiMetrics = {
    totalPipelines: 24,
    pipelinesTrend: '+12% vs last week',
    successRate: '98.7%',
    successTrend: '+4.2% vs last week',
    avgDuration: '3.36s',
    durationTrend: '▼ 1.2s vs last week',
    testsPassed: 342,
    testsTrend: '+18 vs last week',
    activeRepos: 12,
    reposTrend: '+2 vs last week'
  };

  // Recent Runs List (Exact from reference design)
  recentRuns: RecentRun[] = [
    {
      storyId: 'CP-DEMO-1',
      title: 'Add discount parameter',
      status: 'SUCCESS',
      duration: '3.36s',
      timeAgo: '2m ago'
    },
    {
      storyId: 'CP-DEMO-0',
      title: 'Initial calculator enhancement',
      status: 'SUCCESS',
      duration: '2.91s',
      timeAgo: '1d ago'
    },
    {
      storyId: 'CP-DEMO-2',
      title: 'Input validation improvement',
      status: 'SUCCESS',
      duration: '4.12s',
      timeAgo: '2d ago'
    }
  ];

  // 9-Stage Autonomous Execution Pipeline matching reference visual
  readonly stages: { key: WorkflowStage; number: number; label: string; sublabel: string; color: string }[] = [
    { key: 'WORKSPACE_READY', number: 1, label: 'Isolation', sublabel: 'Passed', color: '#7C4DFF' },
    { key: 'REPO_ANALYZED', number: 2, label: 'Analysis', sublabel: 'Passed', color: '#00D4FF' },
    { key: 'PLAN_GENERATED', number: 3, label: 'Planning', sublabel: 'Passed', color: '#10B981' },
    { key: 'PLAN_VALIDATED', number: 4, label: 'Plan Validation', sublabel: 'Passed', color: '#10B981' },
    { key: 'PATCH_GENERATED', number: 5, label: 'Code Generation', sublabel: 'Passed', color: '#10B981' },
    { key: 'PATCH_VALIDATED', number: 6, label: 'Patch Validation', sublabel: 'Passed', color: '#10B981' },
    { key: 'PATCH_APPLIED', number: 7, label: 'Mutation Tests', sublabel: 'Passed', color: '#10B981' },
    { key: 'TESTS_EXECUTED', number: 8, label: 'Real Tests', sublabel: 'Passed', color: '#10B981' },
    { key: 'COMPLETED', number: 9, label: 'Verification', sublabel: 'Passed', color: '#EF4444' }
  ];

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.checkHealth();
  }

  checkHealth() {
    this.apiService.getHealth().subscribe({
      next: (res) => {
        this.health = res;
      },
      error: (err) => {
        console.warn('Backend connection warning:', err);
      }
    });
  }

  loadDemoPreset() {
    this.storyId = 'CP-DEMO-1';
    this.title = 'Add optional flat monetary discount to calculator';
    this.description = 'Add an optional flat monetary discount parameter to calculate_total function. Preserve existing callers when discount is None. Reject negative discounts and discounts larger than calculated total with ValueError. Update unit tests.';
    this.repoLocation = 'demo_repo';
    this.baseBranch = 'main';
    this.errorMessage = null;
  }

  loadEnterprisePreset() {
    this.storyId = 'CP-ENTERPRISE-500';
    this.title = 'Enterprise Multi-Tier Billing, Tax, Coupon & Currency Breakdown Engine';
    this.description = 'Upgrade calculator into an enterprise-grade financial calculation engine supporting multi-currency conversion (USD, EUR, GBP, JPY, CAD), percentage & flat coupon codes with expiry and minimum order thresholds, tiered regional tax brackets (US standard, EU VAT, APAC exempt), itemized invoice breakdown dataclasses, comprehensive transaction audit logging, and 100% test coverage for edge cases, precision rounding, and negative input validation.';
    this.repoLocation = 'demo_repo';
    this.baseBranch = 'main';
    this.errorMessage = null;
  }

  inspectRepository() {
    if (!this.repoLocation) return;
    this.isInspecting = true;
    this.errorMessage = null;
    this.apiService.analyzeRepository(this.repoLocation).subscribe({
      next: (res) => {
        this.analyzedContext = res;
        this.isInspecting = false;
      },
      error: (err) => {
        this.isInspecting = false;
        this.errorMessage = err.error?.detail || 'Failed to inspect repository.';
      }
    });
  }

  runWorkflow() {
    this.isRunning = true;
    this.errorMessage = null;
    this.showNewRequestModal = false;

    const payload: ChangeRequestPayload = {
      story_id: this.storyId,
      title: this.title,
      description: this.description,
      repository_location: this.repoLocation,
      base_branch: this.baseBranch,
      auto_apply: true
    };

    this.apiService.executeChange(payload).subscribe({
      next: (res) => {
        this.result = res;
        this.isRunning = false;

        // Add to recent runs dynamically
        const newRun: RecentRun = {
          storyId: res.story_id,
          title: this.title.length > 28 ? this.title.substring(0, 28) + '...' : this.title,
          status: res.status as 'SUCCESS' | 'FAILED' | 'REJECTED',
          duration: res.total_duration_ms ? (res.total_duration_ms / 1000).toFixed(2) + 's' : '3.36s',
          timeAgo: 'Just now'
        };
        this.recentRuns = [newRun, ...this.recentRuns.slice(0, 4)];

        if (res.status !== 'SUCCESS') {
          this.errorMessage = res.error_message || 'Workflow pipeline encountered an issue.';
        }
      },
      error: (err) => {
        this.isRunning = false;
        this.errorMessage = err.error?.detail || 'Execution failed due to network or server error.';
      }
    });
  }

  getStageStatus(stageKey: WorkflowStage): 'completed' | 'current' | 'failed' | 'pending' {
    if (!this.result) {
      return this.isRunning ? 'current' : 'completed'; // default preview state matches image
    }

    const rec = this.result.audit_trail.find(a => a.stage === stageKey);
    if (!rec) return 'pending';

    if (rec.status === 'SUCCESS') return 'completed';
    if (rec.status === 'FAILED' || rec.status === 'REJECTED') return 'failed';
    if (rec.status === 'IN_PROGRESS') return 'current';
    return 'pending';
  }

  formatDiffLines(diffText?: string): { type: 'add' | 'del' | 'header' | 'normal'; text: string }[] {
    if (!diffText) return [];
    return diffText.split('\n').map(line => {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff --git') || line.startsWith('index ')) {
        return { type: 'header', text: line };
      } else if (line.startsWith('+')) {
        return { type: 'add', text: line };
      } else if (line.startsWith('-')) {
        return { type: 'del', text: line };
      }
      return { type: 'normal', text: line };
    });
  }

  openFullReport() {
    this.showReportModal = true;
  }

  closeFullReport() {
    this.showReportModal = false;
  }

  openNewRequest() {
    this.showNewRequestModal = true;
  }

  closeNewRequest() {
    this.showNewRequestModal = false;
  }
}
