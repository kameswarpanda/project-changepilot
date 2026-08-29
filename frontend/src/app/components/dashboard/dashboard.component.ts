import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KpiMetricsComponent } from './kpi-metrics/kpi-metrics.component';
import { PipelineStepperComponent } from './pipeline-stepper/pipeline-stepper.component';
import { ChangeRequestCardComponent } from './change-request-card/change-request-card.component';
import { PipelineStatusCardComponent } from './pipeline-status-card/pipeline-status-card.component';
import { RecentRunsCardComponent } from './recent-runs-card/recent-runs-card.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    KpiMetricsComponent,
    PipelineStepperComponent,
    ChangeRequestCardComponent,
    PipelineStatusCardComponent,
    RecentRunsCardComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {}
