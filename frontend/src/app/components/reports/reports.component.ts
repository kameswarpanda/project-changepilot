import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.css']
})
export class ReportsComponent {
  timeframe = 'Last 30 Days';

  constructor(public state: WorkflowStateService) {}

  exportPdf(): void {
    window.print();
  }
}
