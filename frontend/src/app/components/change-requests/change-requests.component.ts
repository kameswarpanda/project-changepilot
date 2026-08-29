import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService, RecentRun } from '../../services/workflow-state.service';
import { Observable, combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-change-requests',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './change-requests.component.html',
  styleUrls: ['./change-requests.component.css']
})
export class ChangeRequestsComponent {
  filteredRuns$: Observable<RecentRun[]>;

  constructor(public state: WorkflowStateService) {
    this.filteredRuns$ = combineLatest([
      this.state.recentRuns$,
      this.state.searchQuery$
    ]).pipe(
      map(([runs, query]) => {
        if (!query.trim()) return runs;
        const q = query.toLowerCase();
        return runs.filter(r =>
          r.storyId.toLowerCase().includes(q) ||
          r.title.toLowerCase().includes(q) ||
          r.status.toLowerCase().includes(q)
        );
      })
    );
  }

  openNewRequest(): void {
    this.state.openNewRequestModal();
  }

  inspectRun(run: RecentRun): void {
    this.state.openReportModal('diff');
  }

  reRun(run: RecentRun): void {
    this.state.storyIdSubject.next(run.storyId);
    this.state.runWorkflow();
  }
}
