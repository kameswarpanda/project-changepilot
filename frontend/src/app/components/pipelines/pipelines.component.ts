import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { WorkflowStage } from '../../models';

@Component({
  selector: 'app-pipelines',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pipelines.component.html',
  styleUrls: ['./pipelines.component.css']
})
export class PipelinesComponent {
  constructor(public state: WorkflowStateService) {}

  trigger(): void {
    this.state.runWorkflow();
  }

  getStageStatus(stageKey: WorkflowStage, result: any, isRunning: boolean): 'completed' | 'current' | 'failed' | 'pending' {
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

  openReport(tab: 'diff' | 'plan' | 'logs' | 'audit'): void {
    this.state.openReportModal(tab);
  }
}
