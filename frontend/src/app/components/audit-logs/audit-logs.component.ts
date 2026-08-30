import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';

export interface StoryAuditGroup {
  story_id: string;
  repository: string;
  user_email: string;
  total_events: number;
  passed_events: number;
  failed_events: number;
  latest_timestamp: string;
  final_status: string;
  events: any[];
}

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './audit-logs.component.html',
  styleUrls: ['./audit-logs.component.css']
})
export class AuditLogsComponent implements OnInit {
  filterSearch = '';
  selectedStoryGroup: StoryAuditGroup | null = null;
  showDetailModal = false;

  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.loadAuditLogs();
  }

  get groupedStories(): StoryAuditGroup[] {
    const rawLogs = this.state.auditLogsSubject.value || [];
    const groupsMap = new Map<string, StoryAuditGroup>();

    for (const log of rawLogs) {
      const storyId = log.story_id || 'UNKNOWN';
      if (!groupsMap.has(storyId)) {
        groupsMap.set(storyId, {
          story_id: storyId,
          repository: log.target_repository || 'repository',
          user_email: log.user_email || 'developer',
          total_events: 0,
          passed_events: 0,
          failed_events: 0,
          latest_timestamp: log.timestamp,
          final_status: 'PASSED',
          events: []
        });
      }

      const group = groupsMap.get(storyId)!;
      group.total_events++;
      if (log.status === 'PASSED') {
        group.passed_events++;
      } else {
        group.failed_events++;
        group.final_status = 'FAILED';
      }
      group.events.push(log);
    }

    let list = Array.from(groupsMap.values());
    if (this.filterSearch.trim()) {
      const q = this.filterSearch.toLowerCase();
      list = list.filter(g =>
        g.story_id.toLowerCase().includes(q) ||
        g.repository.toLowerCase().includes(q) ||
        g.user_email.toLowerCase().includes(q) ||
        g.final_status.toLowerCase().includes(q)
      );
    }
    return list;
  }

  openStoryDetail(group: StoryAuditGroup): void {
    this.selectedStoryGroup = group;
    this.showDetailModal = true;
  }

  closeStoryDetail(): void {
    this.showDetailModal = false;
    this.selectedStoryGroup = null;
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
