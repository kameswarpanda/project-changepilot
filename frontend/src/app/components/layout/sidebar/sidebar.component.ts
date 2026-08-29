import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../../services/workflow-state.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  constructor(
    public state: WorkflowStateService,
    public authService: AuthService
  ) {}

  navigate(nav: string): void {
    this.state.setNav(nav);
  }
}
