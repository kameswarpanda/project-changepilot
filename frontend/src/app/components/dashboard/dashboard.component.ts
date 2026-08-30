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

  getStageState(stageKey: WorkflowStage, stageIndex: number): { status: 'pending' | 'running' | 'passed' | 'failed'; duration?: number } {
    const isRunning = this.state.isRunningSubject.value;
    const activeIndex = this.state.activeStageIndexSubject.value ?? 0;
    const result = this.state.resultSubject.value;

    // 1. When actively executing a pipeline
    if (isRunning) {
      if (stageIndex < activeIndex) {
        return { status: 'passed' };
      } else if (stageIndex === activeIndex) {
        return { status: 'running' };
      } else {
        return { status: 'pending' };
      }
    }

    // 2. When a pipeline execution result is present
    if (result) {
      if (result.success) {
        return { status: 'passed' };
      } else {
        const failedStageId = result.error_stage || result.current_stage;
        const failedIdx = this.state.stages.findIndex(s => s.id === failedStageId);
        const resolvedFailedIdx = failedIdx !== -1 ? failedIdx : 3;
        
        if (stageIndex < resolvedFailedIdx) {
          return { status: 'passed' };
        } else if (stageIndex === resolvedFailedIdx) {
          return { status: 'failed' };
        } else {
          return { status: 'pending' };
        }
      }
    }

    // 3. Initial idle state before running
    return { status: 'pending' };
  }
}
