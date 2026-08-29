import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService, RecentRun } from '../../../services/workflow-state.service';
import { Observable, combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-recent-runs-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './recent-runs-card.component.html',
  styleUrls: ['./recent-runs-card.component.css']
})
export class RecentRunsCardComponent {
  filteredRuns$: Observable<RecentRun[]>;

  constructor(public state: WorkflowStateService) {
    this.filteredRuns$ = combineLatest([
      this.state.recentRuns$,
      this.state.searchQuery$
    ]).pipe(
      map(([runs, query]: [RecentRun[], string]) => {
        if (!query || !query.trim()) return runs;
        const q = query.toLowerCase();
        return runs.filter((r: RecentRun) =>
          r.storyId.toLowerCase().includes(q) ||
          r.title.toLowerCase().includes(q) ||
          r.status.toLowerCase().includes(q)
        );
      })
    );
  }

  openRunDetails(run: RecentRun): void {
    this.state.openReportModal('diff');
  }

  openNewRequest(): void {
    this.state.openNewRequestModal();
  }

  viewAll(): void {
    this.state.setNav('requests');
  }
}
