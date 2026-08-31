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
  selectedStoryId: string | null = null;

  // Delete Confirmation State
  deletingRequest: any = null;
  showDeleteConfirm = false;

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

  selectStory(req: any): void {
    this.selectedStoryId = req.story_id;
    this.ticketId = req.story_id || '';
    this.changeTitle = req.title || '';
    this.requirements = req.description || '';
    this.repository = req.repository || '';
    this.branch = req.base_branch || 'main';
    this.onFormSync();

    this.notifService.addNotification(
      'Story Loaded',
      `Loaded details for #${req.story_id} into form.`,
      'info',
      req.story_id
    );

    // Smooth scroll to form
    const formElement = document.getElementById('change-request-form-card');
    if (formElement) {
      formElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  clearForm(): void {
    this.selectedStoryId = null;
    this.ticketId = '';
    this.changeTitle = '';
    this.requirements = '';
    this.repository = '';
    this.branch = 'main';
    this.onFormSync();
  }

  runChangePilot(): void {
    this.onFormSync();
    if (!this.ticketId.trim() || !this.changeTitle.trim() || !this.requirements.trim() || !this.repository.trim()) {
      this.notifService.addNotification(
        'Incomplete Change Request',
        'Please enter Ticket ID, Change Title, Requirements, and Target Repository before running the pipeline.',
        'warning'
      );
      return;
    }

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
    if (!this.ticketId.trim() || !this.changeTitle.trim() || !this.requirements.trim() || !this.repository.trim()) {
      this.notifService.addNotification(
        'Missing Fields',
        'Please fill in Ticket ID, Change Title, Requirements, and Target Repository to save.',
        'warning'
      );
      return;
    }

    this.state.createChangeRequest({
      story_id: this.ticketId.trim(),
      title: this.changeTitle.trim(),
      description: this.requirements.trim(),
      repository: this.repository.trim(),
      base_branch: this.branch.trim() || 'main',
      priority: 'HIGH'
    });
  }

  promptDeleteStory(req: any, event: Event): void {
    event.stopPropagation();
    this.deletingRequest = req;
    this.showDeleteConfirm = true;
  }

  confirmDelete(): void {
    if (this.deletingRequest) {
      const idToDelete = this.deletingRequest.id || this.deletingRequest.story_id;
      this.state.deleteChangeRequest(idToDelete);
      if (this.selectedStoryId === this.deletingRequest.story_id) {
        this.clearForm();
      }
    }
    this.showDeleteConfirm = false;
    this.deletingRequest = null;
  }

  cancelDelete(): void {
    this.showDeleteConfirm = false;
    this.deletingRequest = null;
  }
}
