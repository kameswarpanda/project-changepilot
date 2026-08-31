import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';

export interface PipelineRunExecution {
  execution_id: string;
  timestamp: string;
  status: 'PASSED' | 'FAILED';
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  error_step?: string;
  steps: any[];
}

export interface StoryAuditGroup {
  story_id: string;
  repository: string;
  user_email: string;
  total_events: number;
  passed_events: number;
  failed_events: number;
  total_runs: number;
  latest_timestamp: string;
  final_status: string;
  latest_step_summary: string;
  runs: PipelineRunExecution[];
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
  selectedRunIndex = 0;
  showDetailModal = false;

  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.loadAuditLogs();
  }

  get groupedStories(): StoryAuditGroup[] {
    const rawLogs = this.state.auditLogsSubject.value || [];
    const groupsMap = new Map<string, StoryAuditGroup>();

    // 1. Group events by story_id
    for (const log of rawLogs) {
      const storyId = log.story_id || 'UNKNOWN';
      if (!groupsMap.has(storyId)) {
        groupsMap.set(storyId, {
          story_id: storyId,
          repository: log.target_repository || 'repository',
          user_email: log.user_email || 'developer@changepilot.dev',
          total_events: 0,
          passed_events: 0,
          failed_events: 0,
          total_runs: 0,
          latest_timestamp: log.timestamp,
          final_status: 'PASSED',
          latest_step_summary: '',
          runs: [],
          events: []
        });
      }

      const group = groupsMap.get(storyId)!;
      group.total_events++;
      if (log.status === 'PASSED') {
        group.passed_events++;
      } else {
        group.failed_events++;
      }
      group.events.push(log);
    }

    // 2. Break down each story into distinct runs (by correlation_id)
    for (const group of groupsMap.values()) {
      const runMap = new Map<string, any[]>();
      for (const ev of group.events) {
        const corrId = ev.correlation_id || 'run-default';
        if (!runMap.has(corrId)) {
          runMap.set(corrId, []);
        }
        runMap.get(corrId)!.push(ev);
      }

      const runs: PipelineRunExecution[] = [];
      for (const [corrId, evList] of runMap.entries()) {
        const passedSteps = evList.filter(e => e.status === 'PASSED').length;
        const failedStep = evList.find(e => e.status === 'FAILED');
        const isRunPassed = !failedStep && passedSteps > 0;
        
        runs.push({
          execution_id: corrId,
          timestamp: evList[0]?.timestamp || group.latest_timestamp,
          status: isRunPassed ? 'PASSED' : 'FAILED',
          total_steps: evList.length,
          passed_steps: passedSteps,
          failed_steps: failedStep ? 1 : 0,
          error_step: failedStep?.stage,
          steps: evList
        });
      }

      // Sort runs chronologically (latest first)
      runs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      group.runs = runs;
      group.total_runs = runs.length;

      if (runs.length > 0) {
        const latestRun = runs[0];
        group.final_status = latestRun.status;
        if (latestRun.status === 'PASSED') {
          group.latest_step_summary = `${latestRun.passed_steps} of ${latestRun.total_steps} steps passed`;
        } else {
          group.latest_step_summary = `${latestRun.passed_steps} of ${latestRun.total_steps} steps passed (Halted at ${latestRun.error_step || 'Gate'})`;
        }
      }
    }

    let list = Array.from(groupsMap.values());
    if (this.filterSearch.trim()) {
      const q = this.filterSearch.toLowerCase();
      list = list.filter(g =>
        g.story_id.toLowerCase().includes(q) ||
        g.repository.toLowerCase().includes(q) ||
        g.user_email.toLowerCase().includes(q) ||
        g.final_status.toLowerCase().includes(q) ||
        g.latest_step_summary.toLowerCase().includes(q)
      );
    }
    return list;
  }

  openStoryDetail(group: StoryAuditGroup): void {
    this.selectedStoryGroup = group;
    this.selectedRunIndex = 0;
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
