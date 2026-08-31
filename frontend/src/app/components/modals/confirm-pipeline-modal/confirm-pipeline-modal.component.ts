import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../../services/workflow-state.service';

@Component({
  selector: 'app-confirm-pipeline-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './confirm-pipeline-modal.component.html',
  styleUrls: ['./confirm-pipeline-modal.component.css']
})
export class ConfirmPipelineModalComponent {
  constructor(public state: WorkflowStateService) {}

  confirm(): void {
    this.state.confirmAndExecutePipeline();
  }

  cancel(): void {
    this.state.cancelConfirmModal();
  }
}
