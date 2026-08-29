import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.css']
})
export class ReportsComponent implements OnInit {
  timeframe = 'Live Analytics';

  constructor(public state: WorkflowStateService) {}

  ngOnInit(): void {
    this.state.loadReports();
  }

  exportPdf(): void {
    window.print();
  }
}
