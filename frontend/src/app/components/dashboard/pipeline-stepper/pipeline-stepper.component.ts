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

  getStageStatus(stageKey: WorkflowStage, result: WorkflowResult | null, isRunning: boolean): 'completed' | 'current' | 'failed' | 'pending' {
    if (!result) {
      return isRunning ? 'current' : 'completed';
    }

    const rec = result.audit_trail?.find((a: any) => a.stage === stageKey);
    if (!rec) return 'pending';

    if (rec.status === 'SUCCESS') return 'completed';
    if (rec.status === 'FAILED' || rec.status === 'REJECTED') return 'failed';
    if (rec.status === 'IN_PROGRESS') return 'current';
    return 'pending';
  }

  viewDetails(): void {
    this.state.openReportModal('audit');
  }
}
