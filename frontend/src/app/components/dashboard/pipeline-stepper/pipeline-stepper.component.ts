import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../../services/workflow-state.service';
import { WorkflowStage, WorkflowResult } from '../../../models';

@Component({
  selector: 'app-pipeline-stepper',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pipeline-stepper.component.html',
  styleUrls: ['./pipeline-stepper.component.css']
})
export class PipelineStepperComponent {
  constructor(public state: WorkflowStateService) {}

  getStageStatus(
    stageKey: string,
    index: number,
    result: WorkflowResult | null,
    isRunning: boolean,
    activeStageIndex: number
  ): 'completed' | 'current' | 'failed' | 'pending' {
    if (isRunning) {
      if (index < activeStageIndex) return 'completed';
      if (index === activeStageIndex) return 'current';
      return 'pending';
    }

    if (!result) {
      return 'pending';
    }

    if (result.success) {
      return 'completed';
    }

    const failedStage = result.error_stage || result.current_stage || '';
    const failedIdx = this.state.stages.findIndex(s => s.id === failedStage);
    const resolvedFailedIdx = failedIdx !== -1 ? failedIdx : activeStageIndex;

    if (index < resolvedFailedIdx) return 'completed';
    if (index === resolvedFailedIdx) return 'failed';
    return 'pending';
  }

  getStageDuration(stageKey: string, result: WorkflowResult | null): string | null {
    if (!result || !result.audit_trail) return null;
    const rec = result.audit_trail.find((a: any) => a.stage === stageKey);
    if (rec && rec.duration_ms !== undefined && rec.duration_ms !== null) {
      return `${(rec.duration_ms / 1000).toFixed(1)}s`;
    }
    return null;
  }

  viewDetails(): void {
    this.state.openReportModal('audit');
  }
}
