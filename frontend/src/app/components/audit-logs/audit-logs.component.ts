import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './audit-logs.component.html',
  styleUrls: ['./audit-logs.component.css']
})
export class AuditLogsComponent {
  constructor(public state: WorkflowStateService) {}

  exportLogs(): void {
    const result = this.state.resultSubject.value;
    const runs = this.state.recentRunsSubject.value;
    const data = {
      exported_at: new Date().toISOString(),
      story_id: this.state.storyIdSubject.value,
      result,
      recent_runs: runs
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `changepilot-audit-${Date.now()}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}
