import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './audit-logs.component.html',
  styleUrls: ['./audit-logs.component.css']
})
export class AuditLogsComponent implements OnInit {
  filterStoryId = '';
  filterRepo = '';

  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.loadAuditLogs();
  }

  applyFilter(): void {
    this.state.loadAuditLogs(
      this.filterStoryId.trim() || undefined,
      this.filterRepo.trim() || undefined
    );
  }

  resetFilter(): void {
    this.filterStoryId = '';
    this.filterRepo = '';
    this.state.loadAuditLogs();
  }

  exportLogs(): void {
    const logs = this.state.auditLogsSubject.value;
    const data = {
      exported_at: new Date().toISOString(),
      platform: 'ChangePilot Autonomous Infrastructure',
      total_events: logs.length,
      audit_events: logs
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
