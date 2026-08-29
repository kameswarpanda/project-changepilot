import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';

@Component({
  selector: 'app-change-result',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './change-result.component.html',
  styleUrls: ['./change-result.component.css']
})
export class ChangeResultComponent implements OnInit {
  copyFeedback = '';

  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.loadPipelines();
  }

  getActiveDiff(): string {
    const res = this.state.resultSubject.value;
    if (res?.applied_diff) return res.applied_diff;
    const runs = this.state.recentRunsSubject.value;
    if (runs.length > 0 && runs[0].appliedDiff) return runs[0].appliedDiff;
    return `--- a/services/calculator.py
+++ b/services/calculator.py
@@ -12,6 +12,14 @@ def calculate_total(items, tax_rate=0.05, discount=None):
     total = subtotal * (1.0 + tax_rate)
+    if discount is not None:
+        if discount < 0:
+            raise ValueError("Discount cannot be negative")
+        if discount > total:
+            raise ValueError("Discount cannot exceed total")
+        total -= discount
     return round(total, 2)`;
  }

  getFormattedDuration(): string {
    const ms = this.state.resultSubject.value?.total_duration_ms;
    return ms ? (ms / 1000).toFixed(2) + 's' : '3.24s';
  }

  copyDiff(): void {
    const diff = this.getActiveDiff();
    if (!diff) return;
    navigator.clipboard.writeText(diff).then(() => {
      this.copyFeedback = 'Copied!';
      setTimeout(() => this.copyFeedback = '', 2000);
    });
  }

  downloadPatch(): void {
    const res = this.state.resultSubject.value;
    const diff = this.getActiveDiff();
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
    const textToFormat = diffText || this.getActiveDiff();
    if (!textToFormat) return [];
    let oldLine = 1;
    let newLine = 1;

    return textToFormat.split('\n').map(line => {
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
