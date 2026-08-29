import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../../services/workflow-state.service';

@Component({
  selector: 'app-change-request-card',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './change-request-card.component.html',
  styleUrls: ['./change-request-card.component.css']
})
export class ChangeRequestCardComponent {
  constructor(public state: WorkflowStateService) {}

  loadDemo(): void {
    this.state.loadDemoPreset();
  }

  loadEnterprise(): void {
    this.state.loadEnterprisePreset();
  }

  run(): void {
    this.state.runWorkflow();
  }
}
