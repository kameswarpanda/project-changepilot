import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../../services/workflow-state.service';
import { ThemeService } from '../../../services/theme.service';
import { NotificationService } from '../../../services/notification.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './topbar.component.html',
  styleUrls: ['./topbar.component.css']
})
export class TopbarComponent {
  searchQuery: string = '';
  showNotificationsDropdown: boolean = false;

  constructor(
    public state: WorkflowStateService,
    public themeService: ThemeService,
    public notifService: NotificationService
  ) {}

  onSearchChange(): void {
    this.state.setSearchQuery(this.searchQuery);
  }

  toggleNotifications(): void {
    this.showNotificationsDropdown = !this.showNotificationsDropdown;
  }

  onNotificationClick(n: any): void {
    this.notifService.markAsRead(n.id);
    if (n.storyId) {
      this.state.openReportModal();
    }
  }

  dismiss(id: string, event: MouseEvent): void {
    event.stopPropagation();
    this.notifService.dismiss(id);
  }

  markAllRead(): void {
    this.notifService.markAllAsRead();
  }

  clearAll(): void {
    this.notifService.clearAll();
    this.showNotificationsDropdown = false;
  }
}
