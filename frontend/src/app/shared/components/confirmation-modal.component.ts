import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from './icon.component';

@Component({
  selector: 'app-confirmation-modal',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div
      *ngIf="isOpen"
      class="fixed inset-0 !m-0 z-50 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 animate-fadeIn"
      (click)="onBackdropClick($event)"
      role="dialog"
      aria-modal="true"
    >
      <div
        class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-5 sm:p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-4 max-h-[90vh] overflow-y-auto"
        (click)="$event.stopPropagation()"
      >
        <!-- Modal Header with Warning Icon -->
        <div class="flex items-start gap-3.5">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            [ngClass]="isDestructive ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800' : 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800'"
          >
            <app-icon [name]="isDestructive ? 'alert-triangle' : 'help-circle'" size="20"></app-icon>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-base font-bold text-slate-900 dark:text-white leading-snug break-words">
              {{ title }}
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed break-words">
              {{ message }}
            </p>
          </div>
          <button
            (click)="onCancel()"
            [disabled]="isLoading"
            class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg transition-colors"
            aria-label="Close dialog"
          >
            <app-icon name="x" size="18"></app-icon>
          </button>
        </div>

        <!-- Impact / Warning Alert Box -->
        <div
          *ngIf="warningText"
          class="p-3.5 rounded-xl text-xs flex items-start gap-2.5 leading-relaxed"
          [ngClass]="isDestructive ? 'bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-300' : 'bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-300'"
        >
          <app-icon name="alert-circle" size="16" class="shrink-0 mt-0.5"></app-icon>
          <div class="flex-1">
            <span class="font-bold">Important Notice: </span>
            {{ warningText }}
          </div>
        </div>

        <!-- Affected Items Preview (Tag Chips) -->
        <div *ngIf="itemsList && itemsList.length" class="space-y-1.5">
          <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Affected Items ({{ itemsList.length }}):
          </div>
          <div class="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-2 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-800">
            <span
              *ngFor="let item of itemsList"
              class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-600 truncate max-w-[200px]"
              [title]="item"
            >
              {{ item }}
            </span>
          </div>
        </div>

        <!-- Modal Actions Footer -->
        <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            (click)="onCancel()"
            [disabled]="isLoading"
            class="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
          >
            {{ cancelText }}
          </button>
          <button
            type="button"
            (click)="onConfirm()"
            [disabled]="isLoading"
            class="px-4 py-2 text-white text-xs font-bold rounded-xl shadow-sm flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
            [ngClass]="isDestructive ? 'bg-rose-600 hover:bg-rose-700' : 'bg-blue-600 hover:bg-blue-700'"
          >
            <app-icon *ngIf="isLoading" name="rotate-ccw" size="14" class="animate-spin"></app-icon>
            <app-icon *ngIf="!isLoading && isDestructive" name="trash-2" size="14"></app-icon>
            <span>{{ isLoading ? 'Processing...' : confirmText }}</span>
          </button>
        </div>
      </div>
    </div>
  `,
})
export class ConfirmationModalComponent {
  @Input() isOpen = false;
  @Input() title = 'Confirm Action';
  @Input() message = 'Are you sure you want to proceed with this action?';
  @Input() warningText = '';
  @Input() itemsList: string[] = [];
  @Input() confirmText = 'Confirm Delete';
  @Input() cancelText = 'Cancel';
  @Input() isDestructive = true;
  @Input() isLoading = false;

  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  @HostListener('document:keydown.escape', ['$event'])
  onEscape(_event: KeyboardEvent) {
    if (this.isOpen && !this.isLoading) {
      this.onCancel();
    }
  }

  onBackdropClick(_event: MouseEvent) {
    if (!this.isLoading) {
      this.onCancel();
    }
  }

  onConfirm() {
    if (!this.isLoading) {
      this.confirm.emit();
    }
  }

  onCancel() {
    if (!this.isLoading) {
      this.cancel.emit();
    }
  }
}
