import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowStateService } from '../../../services/workflow-state.service';
import { ThemeService } from '../../../services/theme.service';
import { NotificationService } from '../../../services/notification.service';
import { AuthService } from '../../../services/auth.service';

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
  showUserDropdown: boolean = false;

  constructor(
    public state: WorkflowStateService,
    public themeService: ThemeService,
    public notifService: NotificationService,
    public authService: AuthService
  ) {}

  getUserInitials(user: any): string {
    if (!user || !user.display_name) return 'CP';
    const name = user.display_name.trim();
    const parts = name.split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  onSearchChange(): void {
    this.state.setSearchQuery(this.searchQuery);
  }

  toggleNotifications(): void {
    this.showNotificationsDropdown = !this.showNotificationsDropdown;
    this.showUserDropdown = false;
  }

  toggleUserDropdown(): void {
    this.showUserDropdown = !this.showUserDropdown;
    this.showNotificationsDropdown = false;
  }

  switchUser(username: string): void {
    this.authService.loginDemo(username).subscribe(() => {
      this.notifService.addNotification('Identity Switched', `Logged in as ${username}`, 'info');
      this.showUserDropdown = false;
    });
  }

  logout(): void {
    this.authService.logout();
    this.showUserDropdown = false;
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
