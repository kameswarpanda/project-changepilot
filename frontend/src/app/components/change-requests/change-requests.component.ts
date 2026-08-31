import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { NotificationService } from '../../services/notification.service';
import { ExecutionMode } from '../../models';

@Component({
  selector: 'app-change-requests',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './change-requests.component.html',
  styleUrls: ['./change-requests.component.css']
})
export class ChangeRequestsComponent implements OnInit {
  ticketId = '';
  changeTitle = '';
  requirements = '';
  repository = '';
  branch = 'main';
  executionMode: ExecutionMode = 'BRANCH_COMMIT_PR';

  constructor(
    public state: WorkflowStateService,
    private notifService: NotificationService
  ) {}

  ngOnInit(): void {
    this.state.storyId$.subscribe(val => this.ticketId = val);
    this.state.title$.subscribe(val => this.changeTitle = val);
    this.state.description$.subscribe(val => this.requirements = val);
    this.state.repoLocation$.subscribe(val => this.repository = val);
    this.state.baseBranch$.subscribe(val => this.branch = val);
    this.state.executionMode$.subscribe(val => this.executionMode = val);
    this.state.loadChangeRequests();
  }

  setExecutionMode(mode: ExecutionMode): void {
    this.executionMode = mode;
    this.state.executionModeSubject.next(mode);
  }

  onFormSync(): void {
    this.state.storyIdSubject.next(this.ticketId);
    this.state.titleSubject.next(this.changeTitle);
    this.state.descriptionSubject.next(this.requirements);
    this.state.repoLocationSubject.next(this.repository);
    this.state.baseBranchSubject.next(this.branch);
    this.state.executionModeSubject.next(this.executionMode);
  }

  runChangePilot(): void {
    this.onFormSync();
    if (this.state.isCurrentPipelineCompletedWithPR()) {
      this.notifService.addNotification(
        'Pipeline Already Completed',
        'This change request has already completed successfully with a Pull Request open on GitHub. Rerunning a completed change request is disabled.',
        'warning',
        this.ticketId
      );
      return;
    }
    this.state.promptRunPipeline({
      storyId: this.ticketId,
      title: this.changeTitle,
      description: this.requirements,
      repository: this.repository,
      baseBranch: this.branch,
      executionMode: this.executionMode
    });
  }

  saveDraft(): void {
    this.onFormSync();
    this.state.createChangeRequest({
      story_id: this.ticketId,
      title: this.changeTitle,
      description: this.requirements,
      repository: this.repository,
      base_branch: this.branch,
      priority: 'HIGH'
    });
  }
}
