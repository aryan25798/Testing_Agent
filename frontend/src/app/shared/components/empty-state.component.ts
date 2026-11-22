import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from './icon.component';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="p-10 sm:p-14 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 transition-colors">
      <div class="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 mx-auto flex items-center justify-center mb-4 shadow-inner">
        <app-icon [name]="icon" size="28"></app-icon>
      </div>
      <h3 class="font-bold text-slate-800 dark:text-white text-base">
        {{ title }}
      </h3>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1.5 mb-5 max-w-sm mx-auto leading-relaxed">
        {{ description }}
      </p>
      <div class="flex items-center justify-center gap-3">
        <button
          *ngIf="secondaryActionText"
          type="button"
          (click)="secondaryAction.emit()"
          class="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold rounded-xl text-xs transition-colors cursor-pointer"
        >
          {{ secondaryActionText }}
        </button>
        <button
          *ngIf="actionText"
          type="button"
          (click)="action.emit()"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all shadow-sm cursor-pointer"
        >
          {{ actionText }}
        </button>
      </div>
    </div>
  `,
})
export class EmptyStateComponent {
  @Input() icon = 'folder';
  @Input() title = 'No Records Found';
  @Input() description = 'There are no items to display right now.';
  @Input() actionText?: string;
  @Input() secondaryActionText?: string;

  @Output() action = new EventEmitter<void>();
  @Output() secondaryAction = new EventEmitter<void>();
}
