import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { ConnectedRepo } from '../../models';
import { Observable, combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-repositories',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './repositories.component.html',
  styleUrls: ['./repositories.component.css']
})
export class RepositoriesComponent {
  filteredRepos$: Observable<ConnectedRepo[]>;

  // Connect Modal State
  showConnectModal = false;
  connectProvider: 'github' | 'azure_devops' | 'jira' | 'local' = 'github';
  connectRepoName = 'kameswarpanda/project-changepilot';
  connectToken = '';
  connectBaseBranch = 'main';
  connectIsPrivate = true;
  isLoading = false;

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

  openConnectModal(): void {
    this.showConnectModal = true;
  }

  closeConnectModal(): void {
    this.showConnectModal = false;
  }

  onProviderChange(provider: 'github' | 'azure_devops' | 'jira' | 'local'): void {
    this.connectProvider = provider;
    if (provider === 'github') {
      this.connectRepoName = 'kameswarpanda/project-changepilot';
    } else if (provider === 'azure_devops') {
      this.connectRepoName = 'https://dev.azure.com/org/project/_git/repo';
    } else if (provider === 'jira') {
      this.connectRepoName = 'https://gitlab.com/group/project';
    } else {
      this.connectRepoName = 'demo_repo';
    }
  }

  submitConnect(): void {
    if (!this.connectRepoName.trim()) return;
    this.isLoading = true;

    this.state.connectNewRepository(
      this.connectRepoName.trim(),
      this.connectProvider,
      this.connectBaseBranch,
      this.connectIsPrivate
    );

    this.isLoading = false;
    this.showConnectModal = false;
  }

  inspect(repo: ConnectedRepo): void {
    this.state.repoLocationSubject.next(repo.path);
    this.state.inspectRepository(repo.path);
  }

  select(repo: ConnectedRepo): void {
    this.state.repoLocationSubject.next(repo.path);
    if (repo.branches && repo.branches.length) {
      this.state.baseBranchSubject.next(repo.branches[0]);
    }
    this.state.setNav('requests');
  }
}
