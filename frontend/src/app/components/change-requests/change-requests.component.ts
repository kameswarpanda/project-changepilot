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
  ticketId = 'CP-DEMO-1';
  changeTitle = 'Add optional flat monetary discount to calculator';
  requirements = 'Add an optional flat monetary discount parameter to calculate_total function. Preserve existing callers when discount is None. Reject negative discounts and discounts larger than calculated total with ValueError. Update unit tests.';
  repository = 'demo_repo';
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
    this.state.runWorkflow();
    this.state.setNav('pipelines');
  }

  saveDraft(): void {
    this.onFormSync();
    this.notifService.addNotification(
      'Draft Saved',
      `Saved change request draft for ${this.ticketId}.`,
      'info',
      this.ticketId
    );
  }
}
