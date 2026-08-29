import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../../services/workflow-state.service';

@Component({
  selector: 'app-pipeline-status-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pipeline-status-card.component.html',
  styleUrls: ['./pipeline-status-card.component.css']
})
export class PipelineStatusCardComponent {
  constructor(public state: WorkflowStateService) {}

  viewReport(): void {
    this.state.openReportModal('diff');
  }
}
