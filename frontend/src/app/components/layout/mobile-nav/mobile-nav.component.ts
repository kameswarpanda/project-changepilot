import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../../services/workflow-state.service';

@Component({
  selector: 'app-mobile-nav',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mobile-nav.component.html',
  styleUrls: ['./mobile-nav.component.css']
})
export class MobileNavComponent {
  constructor(public state: WorkflowStateService) {}

  navigate(nav: string): void {
    this.state.setNav(nav);
  }

  openNewRequest(): void {
    this.state.openNewRequestModal();
  }
}
