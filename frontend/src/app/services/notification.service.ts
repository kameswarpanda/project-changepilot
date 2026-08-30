import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AppNotification } from '../models';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationsSubject = new BehaviorSubject<AppNotification[]>([]);
  public notifications$: Observable<AppNotification[]> = this.notificationsSubject.asObservable();
  public unreadCount$: Observable<number> = this.notifications$.pipe(
    map(list => list.filter(n => !n.read).length)
  );

  // Active floating toasts
  private activeToastsSubject = new BehaviorSubject<AppNotification[]>([]);
  public activeToasts$: Observable<AppNotification[]> = this.activeToastsSubject.asObservable();

  addNotification(
    title: string,
    message: string,
    type: 'success' | 'info' | 'warning' | 'error' = 'info',
    storyId?: string,
    detail?: string
  ): void {
    const newNotif: AppNotification = {
      id: `notif-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      title,
      message,
      type,
      timestamp: 'Just now',
      read: false,
      storyId,
      detail
    };

    // Add to persistent notification list
    this.notificationsSubject.next([newNotif, ...this.notificationsSubject.value]);

    // Add to floating toasts
    const currentToasts = this.activeToastsSubject.value;
    // Limit to max 4 concurrent toasts
    const updatedToasts = [newNotif, ...currentToasts].slice(0, 4);
    this.activeToastsSubject.next(updatedToasts);

    // Auto dismiss after 6 seconds (or 10s for errors)
    const duration = type === 'error' ? 10000 : 6000;
    setTimeout(() => {
      this.dismissToast(newNotif.id);
    }, duration);
  }

  dismissToast(id: string): void {
    const updated = this.activeToastsSubject.value.filter(t => t.id !== id);
    this.activeToastsSubject.next(updated);
  }

  markAllAsRead(): void {
    const updated = this.notificationsSubject.value.map(n => ({ ...n, read: true }));
    this.notificationsSubject.next(updated);
  }

  markAsRead(id: string): void {
    const updated = this.notificationsSubject.value.map(n =>
      n.id === id ? { ...n, read: true } : n
    );
    this.notificationsSubject.next(updated);
  }

  dismiss(id: string): void {
    this.dismissToast(id);
    const updated = this.notificationsSubject.value.filter(n => n.id !== id);
    this.notificationsSubject.next(updated);
  }

  clearAll(): void {
    this.notificationsSubject.next([]);
    this.activeToastsSubject.next([]);
  }
}
