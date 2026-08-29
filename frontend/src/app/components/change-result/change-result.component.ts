import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';

@Component({
  selector: 'app-change-result',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './change-result.component.html',
  styleUrls: ['./change-result.component.css']
})
export class ChangeResultComponent {
  copyFeedback = '';

  constructor(public state: WorkflowStateService) {}

  getFormattedDuration(): string {
    const ms = this.state.resultSubject.value?.total_duration_ms;
    return ms ? (ms / 1000).toFixed(2) + 's' : '2.15s';
  }

  copyDiff(): void {
    const diff = this.state.resultSubject.value?.applied_diff || '';
    if (!diff) return;
    navigator.clipboard.writeText(diff).then(() => {
      this.copyFeedback = 'Copied!';
      setTimeout(() => this.copyFeedback = '', 2000);
    });
  }

  downloadPatch(): void {
    const res = this.state.resultSubject.value;
    const diff = res?.applied_diff || '';
    if (!diff) return;
    const blob = new Blob([diff], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${res?.story_id || 'change'}.patch`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  formatDiffLines(diffText?: string): { oldNum?: string; newNum?: string; type: string; text: string }[] {
    if (!diffText) return [];
    let oldLine = 1;
    let newLine = 1;

    return diffText.split('\n').map(line => {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff --git') || line.startsWith('index ')) {
        return { type: 'header', text: line };
      } else if (line.startsWith('+')) {
        const item = { newNum: String(newLine++), type: 'add', text: line };
        return item;
      } else if (line.startsWith('-')) {
        const item = { oldNum: String(oldLine++), type: 'del', text: line };
        return item;
      } else if (line.startsWith('@@')) {
        return { type: 'hunk', text: line };
      }
      const item = { oldNum: String(oldLine++), newNum: String(newLine++), type: 'normal', text: line };
      return item;
    });
  }
}
