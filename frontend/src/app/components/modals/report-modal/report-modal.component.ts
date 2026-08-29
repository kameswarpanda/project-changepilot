import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../../services/workflow-state.service';

@Component({
  selector: 'app-report-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './report-modal.component.html',
  styleUrls: ['./report-modal.component.css']
})
export class ReportModalComponent {
  copyFeedback: string | null = null;

  constructor(public state: WorkflowStateService) {}

  close(): void {
    this.state.closeReportModal();
  }

  setTab(tab: 'diff' | 'plan' | 'logs' | 'audit'): void {
    this.state.activeReportTabSubject.next(tab);
  }

  formatDiffLines(diffText?: string): { type: 'add' | 'del' | 'header' | 'normal'; text: string }[] {
    if (!diffText) return [];
    return diffText.split('\n').map(line => {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff --git') || line.startsWith('index ')) {
        return { type: 'header', text: line };
      } else if (line.startsWith('+')) {
        return { type: 'add', text: line };
      } else if (line.startsWith('-')) {
        return { type: 'del', text: line };
      }
      return { type: 'normal', text: line };
    });
  }

  copyDiff(): void {
    const diff = this.state.resultSubject.value?.applied_diff;
    if (!diff) return;
    navigator.clipboard.writeText(diff).then(() => {
      this.copyFeedback = 'Copied diff!';
      setTimeout(() => this.copyFeedback = null, 2500);
    });
  }

  downloadPatch(): void {
    const diff = this.state.resultSubject.value?.applied_diff;
    if (!diff) return;
    const storyId = this.state.storyIdSubject.value;
    const blob = new Blob([diff], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${storyId}.patch`;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}
