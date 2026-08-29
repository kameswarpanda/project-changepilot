import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from './components/layout/sidebar/sidebar.component';
import { TopbarComponent } from './components/layout/topbar/topbar.component';
import { MobileNavComponent } from './components/layout/mobile-nav/mobile-nav.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ChangeRequestsComponent } from './components/change-requests/change-requests.component';
import { PipelinesComponent } from './components/pipelines/pipelines.component';
import { RepositoriesComponent } from './components/repositories/repositories.component';
import { TemplatesComponent } from './components/templates/templates.component';
import { AuditLogsComponent } from './components/audit-logs/audit-logs.component';
import { SettingsComponent } from './components/settings/settings.component';
import { ReportModalComponent } from './components/modals/report-modal/report-modal.component';
import { NewRequestModalComponent } from './components/modals/new-request-modal/new-request-modal.component';
import { WorkflowStateService } from './services/workflow-state.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    SidebarComponent,
    TopbarComponent,
    MobileNavComponent,
    DashboardComponent,
    ChangeRequestsComponent,
    PipelinesComponent,
    RepositoriesComponent,
    TemplatesComponent,
    AuditLogsComponent,
    SettingsComponent,
    ReportModalComponent,
    NewRequestModalComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  constructor(public state: WorkflowStateService) {}
}
