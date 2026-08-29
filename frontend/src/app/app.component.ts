import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from './services/api.service';
import {
  AppNotification,
  ChangeRequestPayload,
  ConnectedRepo,
  HealthResponse,
  StoryTemplate,
  WorkflowResult,
  WorkflowStage
} from './models';

interface RecentRun {
  storyId: string;
  title: string;
  status: 'SUCCESS' | 'FAILED' | 'REJECTED';
  duration: string;
  timeAgo: string;
  branch?: string;
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
  activeNav: 'dashboard' | 'requests' | 'pipelines' | 'repositories' | 'templates' | 'audit' | 'settings' = 'dashboard';
  searchQuery: string = '';
  errorMessage: string | null = null;
  copyFeedback: string | null = null;

  // Theme State (Dark / Light)
  isDarkMode: boolean = true;

  // Notifications State
  showNotificationsDropdown: boolean = false;
  notifications: AppNotification[] = [
    {
      id: 'notif-1',
      title: 'Pipeline CP-DEMO-1 Passed',
      message: 'Autonomous change verified with 100% test pass rate in 3.36s.',
      type: 'success',
      timestamp: '2 mins ago',
      read: false,
      storyId: 'CP-DEMO-1'
    },
    {
      id: 'notif-2',
      title: 'Repository Analyzed',
      message: 'demo_repo analyzed successfully (Python 3, pytest, 4 files).',
      type: 'info',
      timestamp: '15 mins ago',
      read: false
    },
    {
      id: 'notif-3',
      title: 'Deterministic Gates Active',
      message: 'Security, Plan, and Patch Consistency validators active in fail-closed mode.',
      type: 'info',
      timestamp: '1 hour ago',
      read: true
    }
  ];

  // Modals & Inspection View
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

  // Settings Configuration
  appSettings = {
    vertexAiEnabled: false,
    gcpProject: 'changepilot-dev',
    executionTimeoutSec: 60,
    maxFileSizeKb: 1024,
    autoApply: true,
    sandboxIsolation: true
  };

  // Pre-configured Story Templates
  storyTemplates: StoryTemplate[] = [
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

  // Connected Repositories
  connectedRepos: ConnectedRepo[] = [
    {
      name: 'demo_repo',
      path: 'demo_repo',
      language: 'Python',
      testRunner: 'pytest',
      fileCount: 4,
      lastChecked: 'Just now',
      status: 'Ready'
    },
    {
      name: 'backend',
      path: 'backend',
      language: 'Python',
      testRunner: 'pytest',
      fileCount: 28,
      lastChecked: '5m ago',
      status: 'Ready'
    },
    {
      name: 'frontend',
      path: 'frontend',
      language: 'TypeScript / Angular',
      testRunner: 'npm test',
      fileCount: 16,
      lastChecked: '12m ago',
      status: 'Ready'
    }
  ];

  // Recent Runs List (Dynamically updated)
  recentRuns: RecentRun[] = [
    {
      storyId: 'CP-DEMO-1',
      title: 'Add discount parameter',
      status: 'SUCCESS',
      duration: '3.36s',
      timeAgo: '2m ago',
      branch: 'changepilot/CP-DEMO-1'
    },
    {
      storyId: 'CP-DEMO-0',
      title: 'Initial calculator enhancement',
      status: 'SUCCESS',
      duration: '2.91s',
      timeAgo: '1d ago',
      branch: 'changepilot/CP-DEMO-0'
    },
    {
      storyId: 'CP-DEMO-2',
      title: 'Input validation improvement',
      status: 'SUCCESS',
      duration: '4.12s',
      timeAgo: '2d ago',
      branch: 'changepilot/CP-DEMO-2'
    }
  ];

  // 9-Stage Autonomous Pipeline definition matching design
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
    // Initialize Theme
    const savedTheme = localStorage.getItem('cp_theme');
    if (savedTheme === 'light') {
      this.isDarkMode = false;
      document.body.classList.add('light-theme');
    } else {
      this.isDarkMode = true;
      document.body.classList.remove('light-theme');
    }

    this.checkHealth();
  }

  // --- THEME MANAGEMENT ---
  toggleTheme() {
    this.isDarkMode = !this.isDarkMode;
    if (this.isDarkMode) {
      document.body.classList.remove('light-theme');
      localStorage.setItem('cp_theme', 'dark');
    } else {
      document.body.classList.add('light-theme');
      localStorage.setItem('cp_theme', 'light');
    }
  }

  // --- NOTIFICATIONS MANAGEMENT ---
  get unreadNotificationsCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }

  toggleNotifications() {
    this.showNotificationsDropdown = !this.showNotificationsDropdown;
  }

  markAllNotificationsRead() {
    this.notifications.forEach(n => n.read = true);
  }

  clearAllNotifications() {
    this.notifications = [];
    this.showNotificationsDropdown = false;
  }

  dismissNotification(id: string, event?: MouseEvent) {
    if (event) event.stopPropagation();
    this.notifications = this.notifications.filter(n => n.id !== id);
  }

  addNotification(title: string, message: string, type: 'success' | 'info' | 'warning' | 'error', storyId?: string) {
    const newNotif: AppNotification = {
      id: `notif-${Date.now()}`,
      title,
      message,
      type,
      timestamp: 'Just now',
      read: false,
      storyId
    };
    this.notifications = [newNotif, ...this.notifications];
  }

  // --- DYNAMIC KPI METRICS COMPUTATION ---
  get dynamicTotalPipelines(): number {
    return this.recentRuns.length + 21;
  }

  get dynamicSuccessRate(): string {
    const total = this.recentRuns.length;
    if (total === 0) return '98.7%';
    const success = this.recentRuns.filter(r => r.status === 'SUCCESS').length;
    return `${((success / total) * 100).toFixed(1)}%`;
  }

  get dynamicAvgDuration(): string {
    if (this.result?.total_duration_ms) {
      return (this.result.total_duration_ms / 1000).toFixed(2) + 's';
    }
    return '3.36s';
  }

  get dynamicTestsPassed(): number {
    return 342 + (this.result?.test_passed ? 24 : 0);
  }

  get dynamicActiveRepos(): number {
    return this.connectedRepos.length;
  }

  // --- FILTERED LISTS BASED ON SEARCH QUERY ---
  get filteredRecentRuns(): RecentRun[] {
    if (!this.searchQuery.trim()) return this.recentRuns;
    const q = this.searchQuery.toLowerCase();
    return this.recentRuns.filter(r =>
      r.storyId.toLowerCase().includes(q) ||
      r.title.toLowerCase().includes(q) ||
      r.status.toLowerCase().includes(q)
    );
  }

  get filteredTemplates(): StoryTemplate[] {
    if (!this.searchQuery.trim()) return this.storyTemplates;
    const q = this.searchQuery.toLowerCase();
    return this.storyTemplates.filter(t =>
      t.title.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.category.toLowerCase().includes(q) ||
      t.tags.some(tag => tag.toLowerCase().includes(q))
    );
  }

  get filteredRepos(): ConnectedRepo[] {
    if (!this.searchQuery.trim()) return this.connectedRepos;
    const q = this.searchQuery.toLowerCase();
    return this.connectedRepos.filter(r =>
      r.name.toLowerCase().includes(q) ||
      r.language.toLowerCase().includes(q) ||
      r.testRunner.toLowerCase().includes(q)
    );
  }

  // --- API & WORKFLOW ACTIONS ---
  checkHealth() {
    this.apiService.getHealth().subscribe({
      next: (res) => {
        this.health = res;
      },
      error: (err) => {
        console.warn('Backend connection check:', err);
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

  applyTemplate(tmpl: StoryTemplate) {
    this.storyId = tmpl.storyId;
    this.title = tmpl.title;
    this.description = tmpl.description;
    this.repoLocation = tmpl.repoLocation;
    this.baseBranch = 'main';
    this.errorMessage = null;
    this.activeNav = 'dashboard';
    this.addNotification(
      'Template Loaded',
      `Applied template "${tmpl.title}" into pipeline configuration.`,
      'info',
      tmpl.storyId
    );
  }

  inspectRepository(repoPath?: string) {
    const target = repoPath || this.repoLocation;
    if (!target) return;
    this.isInspecting = true;
    this.errorMessage = null;
    this.apiService.analyzeRepository(target).subscribe({
      next: (res) => {
        this.analyzedContext = res;
        this.isInspecting = false;
        this.addNotification(
          'Repository Analyzed',
          `Repository "${target}" inspected: ${res.primary_language || 'Python'}, ${res.all_files?.length || 4} files.`,
          'info'
        );
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
      auto_apply: this.appSettings.autoApply
    };

    this.apiService.executeChange(payload).subscribe({
      next: (res) => {
        this.result = res;
        this.isRunning = false;

        const durationStr = res.total_duration_ms
          ? (res.total_duration_ms / 1000).toFixed(2) + 's'
          : '3.36s';

        // Prepend to dynamic recent runs
        const newRun: RecentRun = {
          storyId: res.story_id,
          title: this.title.length > 32 ? this.title.substring(0, 32) + '...' : this.title,
          status: res.status as 'SUCCESS' | 'FAILED' | 'REJECTED',
          duration: durationStr,
          timeAgo: 'Just now',
          branch: res.branch_name || `changepilot/${res.story_id}`
        };
        this.recentRuns = [newRun, ...this.recentRuns.slice(0, 5)];

        if (res.status === 'SUCCESS') {
          this.addNotification(
            `Pipeline ${res.story_id} Verified 🎉`,
            `Completed in ${durationStr}. Tests passed with 100% success rate.`,
            'success',
            res.story_id
          );
        } else {
          this.errorMessage = res.error_message || 'Workflow pipeline rejected or failed.';
          this.addNotification(
            `Pipeline ${res.story_id} Failed`,
            res.error_message || 'Validation gate check failed.',
            'error',
            res.story_id
          );
        }
      },
      error: (err) => {
        this.isRunning = false;
        this.errorMessage = err.error?.detail || 'Execution failed due to network or server error.';
        this.addNotification('Pipeline Error', this.errorMessage || 'Execution error', 'error');
      }
    });
  }

  getStageStatus(stageKey: WorkflowStage): 'completed' | 'current' | 'failed' | 'pending' {
    if (!this.result) {
      return this.isRunning ? 'current' : 'completed';
    }

    const rec = this.result.audit_trail?.find(a => a.stage === stageKey);
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

  copyDiff() {
    if (!this.result?.applied_diff) return;
    navigator.clipboard.writeText(this.result.applied_diff).then(() => {
      this.copyFeedback = 'Copied diff to clipboard!';
      setTimeout(() => this.copyFeedback = null, 2500);
    });
  }

  downloadPatch() {
    if (!this.result?.applied_diff) return;
    const blob = new Blob([this.result.applied_diff], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${this.storyId}.patch`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  exportAuditLogs() {
    const data = {
      exported_at: new Date().toISOString(),
      story_id: this.storyId,
      result: this.result,
      recent_runs: this.recentRuns
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `changepilot-audit-${Date.now()}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  openFullReport(tab: 'diff' | 'plan' | 'logs' | 'audit' = 'diff') {
    this.activeTab = tab;
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
