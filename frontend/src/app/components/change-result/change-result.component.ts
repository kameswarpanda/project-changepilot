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
    if (res?.applied_diff && res.applied_diff.trim()) return res.applied_diff;
    if (res?.patch_plan?.file_patches?.length) {
      return res.patch_plan.file_patches.map((fp: any) => {
        const rawContent = fp.patch_content || fp.content || '';
        const lines: string[] = rawContent.split('\n');
        const count = lines.length || 1;
        if (fp.change_type === 'CREATE') {
          return `diff --git a/${fp.file_path} b/${fp.file_path}\nnew file mode 100644\n--- /dev/null\n+++ b/${fp.file_path}\n@@ -0,0 +1,${count} @@\n` +
                 lines.map((l: string) => '+' + l).join('\n');
        } else if (fp.change_type === 'DELETE') {
          return `diff --git a/${fp.file_path} b/${fp.file_path}\ndeleted file mode 100644\n--- a/${fp.file_path}\n+++ /dev/null`;
        }
        return `diff --git a/${fp.file_path} b/${fp.file_path}\n--- a/${fp.file_path}\n+++ b/${fp.file_path}\n@@ -1,1 +1,${count} @@\n` +
               lines.map((l: string) => '+' + l).join('\n');
      }).join('\n\n');
    }
    const runs = this.state.recentRunsSubject.value;
    if (runs.length > 0 && runs[0].appliedDiff) return runs[0].appliedDiff;
    return '';
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
