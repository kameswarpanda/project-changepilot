import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AppNotification } from '../models';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationsSubject = new BehaviorSubject<AppNotification[]>([
    {
      id: 'notif-1',
      title: 'Deterministic Safety Active',
      message: 'Workspace isolation and 9-stage validation gates active in fail-closed mode.',
      type: 'success',
      timestamp: 'Just now',
      read: false
    }
  ]);

  public notifications$: Observable<AppNotification[]> = this.notificationsSubject.asObservable();
  public unreadCount$: Observable<number> = this.notifications$.pipe(
    map(list => list.filter(n => !n.read).length)
  );

  addNotification(
    title: string,
    message: string,
    type: 'success' | 'info' | 'warning' | 'error' = 'info',
    storyId?: string
  ): void {
    const newNotif: AppNotification = {
      id: `notif-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      title,
      message,
      type,
      timestamp: 'Just now',
      read: false,
      storyId
    };
    this.notificationsSubject.next([newNotif, ...this.notificationsSubject.value]);
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
    const updated = this.notificationsSubject.value.filter(n => n.id !== id);
    this.notificationsSubject.next(updated);
  }

  clearAll(): void {
    this.notificationsSubject.next([]);
  }
}
