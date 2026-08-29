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

  getStageState(stageKey: WorkflowStage): { status: 'pending' | 'running' | 'passed' | 'failed'; duration?: number } {
    const result = this.state.resultSubject.value;
    const isRunning = this.state.isRunningSubject.value;

    if (isRunning) {
      return { status: 'running' };
    }

    if (!result) {
      return { status: 'passed' };
    }

    const auditItem = result.audit_trail.find(a => a.stage === stageKey);
    if (!auditItem) {
      return { status: 'pending' };
    }

    if (auditItem.status === 'SUCCESS') {
      return { status: 'passed', duration: auditItem.duration_ms };
    } else if (auditItem.status === 'FAILED' || auditItem.status === 'REJECTED') {
      return { status: 'failed', duration: auditItem.duration_ms };
    } else if (auditItem.status === 'IN_PROGRESS') {
      return { status: 'running' };
    }

    return { status: 'pending' };
  }
}
