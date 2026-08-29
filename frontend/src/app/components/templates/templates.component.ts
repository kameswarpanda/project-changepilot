import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStateService } from '../../services/workflow-state.service';
import { StoryTemplate } from '../../models';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-templates',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.css']
})
export class TemplatesComponent {
  filteredTemplates$: Observable<StoryTemplate[]>;

  constructor(public state: WorkflowStateService) {
    this.filteredTemplates$ = this.state.searchQuery$.pipe(
      map(query => {
        if (!query.trim()) return this.state.storyTemplates;
        const q = query.toLowerCase();
        return this.state.storyTemplates.filter((t: StoryTemplate) =>
          t.title.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q) ||
          t.category.toLowerCase().includes(q) ||
          t.tags.some((tag: string) => tag.toLowerCase().includes(q))
        );
      })
    );
  }

  useTemplate(tmpl: StoryTemplate): void {
    this.state.applyTemplate(tmpl);
  }
}
