import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { ApiService } from '../../services/api.service';
import { NotificationService } from '../../services/notification.service';
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
export class RepositoriesComponent implements OnInit {
  filteredRepos$: Observable<ConnectedRepo[]>;

  // Connect Modal State
  showConnectModal = false;
  connectMode: 'platform' | 'public_url' = 'platform';
  connectProvider: 'github' | 'azure_devops' = 'github';

  // Platform Repos Discovery
  userPlatformRepos: any[] = [];
  selectedPlatformRepo: any = null;
  isLoadingPlatformRepos = false;

  // Public Git URL input
  publicGitUrl = '';
  publicBaseBranch = 'main';

  isLoading = false;

  constructor(
    public state: WorkflowStateService,
    private api: ApiService,
    private notif: NotificationService
  ) {
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

  ngOnInit(): void {
    this.state.loadRepositories();
  }

  openConnectModal(): void {
    this.showConnectModal = true;
    this.fetchUserPlatformRepos();
  }

  closeConnectModal(): void {
    this.showConnectModal = false;
  }

  switchConnectMode(mode: 'platform' | 'public_url'): void {
    this.connectMode = mode;
    if (mode === 'platform' && this.userPlatformRepos.length === 0) {
      this.fetchUserPlatformRepos();
    }
  }

  fetchUserPlatformRepos(): void {
    this.isLoadingPlatformRepos = true;
    this.api.listUserPlatformRepos().subscribe({
      next: (repos) => {
        this.isLoadingPlatformRepos = false;
        this.userPlatformRepos = repos;
        if (repos.length > 0) {
          this.selectedPlatformRepo = repos[0];
        }
      },
      error: () => {
        this.isLoadingPlatformRepos = false;
      }
    });
  }

  submitPlatformConnect(): void {
    if (!this.selectedPlatformRepo) return;
    this.isLoading = true;

    this.state.connectNewRepository(
      this.selectedPlatformRepo.full_name || this.selectedPlatformRepo.name,
      this.connectProvider,
      this.selectedPlatformRepo.default_branch || 'main',
      this.selectedPlatformRepo.is_private || false
    );

    this.isLoading = false;
    this.showConnectModal = false;
  }

  submitPublicUrlConnect(): void {
    if (!this.publicGitUrl.trim()) return;
    this.isLoading = true;

    this.state.importPublicRepository(
      this.publicGitUrl.trim(),
      this.publicBaseBranch.trim()
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
