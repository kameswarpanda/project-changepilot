import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from './services/api.service';
import { ChangeRequestPayload, HealthResponse, WorkflowResult, WorkflowStage } from './models';

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
  activeTab: 'plan' | 'diff' | 'logs' | 'audit' = 'plan';
  errorMessage: string | null = null;

  // Change Request Form
  storyId: string = 'CP-DEMO-1';
  title: string = 'Add optional flat monetary discount to calculator';
  description: string = 'Add an optional flat monetary discount parameter to calculate_total function. Preserve existing callers when discount is None. Reject negative discounts and discounts larger than calculated total with ValueError. Update unit tests.';
  repoLocation: string = 'demo_repo';
  baseBranch: string = 'main';

  // Execution Result
  result: WorkflowResult | null = null;
  analyzedContext: any = null;

  // Workflow Pipeline Stages Definition
  readonly stages: { key: WorkflowStage; label: string; description: string }[] = [
    { key: 'WORKSPACE_READY', label: '1. Isolation', description: 'Isolated branch & sandbox' },
    { key: 'REPO_ANALYZED', label: '2. Analysis', description: 'Deterministic topology' },
    { key: 'PLAN_GENERATED', label: '3. Planning', description: 'Change Analyst Agent' },
    { key: 'PLAN_VALIDATED', label: '4. Plan Gate', description: 'Deterministic validation' },
    { key: 'PATCH_GENERATED', label: '5. Codegen', description: 'Code Generator Agent' },
    { key: 'PATCH_VALIDATED', label: '6. Patch Gate', description: 'Consistency & bounds' },
    { key: 'PATCH_APPLIED', label: '7. Mutation', description: 'Safe workspace apply' },
    { key: 'TESTS_EXECUTED', label: '8. Real Tests', description: 'Bounded pytest runner' },
    { key: 'COMPLETED', label: '9. Verified', description: 'Auditable success' }
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
        console.warn('Backend currently unreachable', err);
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
    this.result = null;

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
        if (res.status === 'SUCCESS') {
          this.activeTab = 'diff';
        } else {
          this.errorMessage = res.error_message || 'Workflow did not succeed.';
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
      return this.isRunning && stageKey === 'WORKSPACE_READY' ? 'current' : 'pending';
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
}
