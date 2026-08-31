import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { WorkflowResult } from '../../models';

@Component({
  selector: 'app-pipelines',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pipelines.component.html',
  styleUrls: ['./pipelines.component.css']
})
export class PipelinesComponent implements OnInit {
  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.loadPipelines();
  }

  trigger(): void {
    this.state.executeWorkflow();
  }

  getStageStatus(
    stageId: string,
    index: number,
    result: WorkflowResult | null,
    isRunning: boolean,
    activeStageIndex: number
  ): 'success' | 'failed' | 'running' | 'pending' {
    if (isRunning) {
      if (index < activeStageIndex) return 'success';
      if (index === activeStageIndex) return 'running';
      return 'pending';
    }

    if (!result) {
      return 'pending';
    }

    if (result.success) {
      return 'success';
    }

    // Workflow failed
    const failedStage = result.error_stage || result.current_stage || '';
    const failedIdx = this.state.stages.findIndex(s => s.id === failedStage);
    const resolvedFailedIdx = failedIdx !== -1 ? failedIdx : activeStageIndex;

    if (index < resolvedFailedIdx) return 'success';
    if (index === resolvedFailedIdx) return 'failed';
    return 'pending';
  }

  getStageMessage(stageId: string, result: WorkflowResult | null): string | null {
    if (!result || !result.audit_trail) return null;
    const rec = result.audit_trail.find(a => a.stage === stageId);
    return rec?.message || null;
  }

  getStageDuration(stageId: string, result: WorkflowResult | null): string | null {
    if (!result || !result.audit_trail) return null;
    const rec = result.audit_trail.find((a: any) => a.stage === stageId);
    if (rec && rec.duration_ms !== undefined && rec.duration_ms !== null) {
      return `${(rec.duration_ms / 1000).toFixed(1)}s`;
    }
    return null;
  }

  openReport(tab: 'diff' | 'plan' | 'logs' | 'audit'): void {
    this.state.openReportModal(tab);
  }
}
