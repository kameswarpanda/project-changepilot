import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { ConnectedRepo } from '../../models';
import { Observable, combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-repositories',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './repositories.component.html',
  styleUrls: ['./repositories.component.css']
})
export class RepositoriesComponent {
  filteredRepos$: Observable<ConnectedRepo[]>;

  constructor(public state: WorkflowStateService) {
    this.filteredRepos$ = combineLatest([
      this.state.connectedRepos$,
      this.state.searchQuery$
    ]).pipe(
      map(([repos, query]) => {
        if (!query.trim()) return repos;
        const q = query.toLowerCase();
        return repos.filter(r =>
          r.name.toLowerCase().includes(q) ||
          r.language.toLowerCase().includes(q) ||
          r.testRunner.toLowerCase().includes(q)
        );
      })
    );
  }

  inspect(repo: ConnectedRepo): void {
    this.state.repoLocationSubject.next(repo.path);
    this.state.inspectRepository(repo.path);
  }

  select(repo: ConnectedRepo): void {
    this.state.repoLocationSubject.next(repo.path);
    this.state.setNav('dashboard');
  }
}
