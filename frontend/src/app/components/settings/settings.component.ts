import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {
  constructor(
    public state: WorkflowStateService,
    private notifService: NotificationService
  ) {}

  ngOnInit(): void {
    this.state.loadSystemConfig();
  }

  save(): void {
    this.state.loadSystemConfig();
    this.notifService.addNotification('Settings Synchronized', 'Platform environment configuration verified.', 'success');
  }
}
