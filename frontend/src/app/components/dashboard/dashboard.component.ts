import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { WorkflowStage } from '../../models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.refreshAllData();
  }

  runPipeline(): void {
    this.state.executeWorkflow();
  }

  getFormattedDuration(): string {
    const ms = this.state.resultSubject.value?.total_duration_ms;
    return ms ? (ms / 1000).toFixed(2) + 's' : '3.24s';
  }

  getStageStatus(
    stageId: string,
    index: number,
    result: any,
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

  getStageMessage(stageId: string, result: any): string | null {
    if (!result || !result.audit_trail) return null;
    const rec = result.audit_trail.find((a: any) => a.stage === stageId);
    return rec?.message || null;
  }

  getStageDuration(stageId: string, result: any): string | null {
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
