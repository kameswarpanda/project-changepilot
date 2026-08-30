import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService } from '../../../services/notification.service';
import { AppNotification } from '../../../models';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast-container.component.html',
  styleUrls: ['./toast-container.component.css']
})
export class ToastContainerComponent {
  expandedDetails: { [key: string]: boolean } = {};
  copiedToastId: string | null = null;

  constructor(public notifService: NotificationService) {}

  toggleDetail(id: string): void {
    this.expandedDetails[id] = !this.expandedDetails[id];
  }

  copyError(toast: AppNotification): void {
    const textToCopy = `${toast.title}\n${toast.message}${toast.detail ? '\nDetail: ' + toast.detail : ''}`;
    navigator.clipboard.writeText(textToCopy).then(() => {
      this.copiedToastId = toast.id;
      setTimeout(() => {
        if (this.copiedToastId === toast.id) {
          this.copiedToastId = null;
        }
      }, 2000);
    });
  }
}
