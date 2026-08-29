import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../../services/workflow-state.service';

@Component({
  selector: 'app-new-request-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './new-request-modal.component.html',
  styleUrls: ['./new-request-modal.component.css']
})
export class NewRequestModalComponent {
  storyId: string = '';
  title: string = '';
  description: string = '';
  repoLocation: string = '';

  constructor(public state: WorkflowStateService) {
    this.state.storyId$.subscribe((val: string) => this.storyId = val);
    this.state.title$.subscribe((val: string) => this.title = val);
    this.state.description$.subscribe((val: string) => this.description = val);
    this.state.repoLocation$.subscribe((val: string) => this.repoLocation = val);
  }

  close(): void {
    this.state.closeNewRequestModal();
  }

  loadDemo(): void {
    this.state.loadDemoPreset();
  }

  loadEnterprise(): void {
    this.state.loadEnterprisePreset();
  }

  inspect(): void {
    this.state.repoLocationSubject.next(this.repoLocation);
    this.state.inspectRepository();
  }

  submit(): void {
    this.state.storyIdSubject.next(this.storyId);
    this.state.titleSubject.next(this.title);
    this.state.descriptionSubject.next(this.description);
    this.state.repoLocationSubject.next(this.repoLocation);
    this.state.runWorkflow();
  }
}
