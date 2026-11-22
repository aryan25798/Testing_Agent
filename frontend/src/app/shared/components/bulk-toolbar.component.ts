import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from './icon.component';

@Component({
  selector: 'app-bulk-toolbar',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div
      *ngIf="selectedCount > 0"
      class="sticky bottom-4 z-40 bg-slate-900/95 dark:bg-slate-950/95 text-white p-3.5 sm:p-4 rounded-2xl shadow-2xl border border-slate-700/80 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 animate-slideUp transition-all"
    >
      <!-- Left: Selection Counter & Select All -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white font-extrabold text-xs">
            {{ selectedCount }}
          </span>
          <span class="text-xs font-bold text-slate-200">
            {{ selectedCount }} {{ itemLabel }}{{ selectedCount > 1 ? 's' : '' }} selected
          </span>
        </div>

        <button
          type="button"
          (click)="onToggleSelectAll()"
          class="text-xs text-blue-400 hover:text-blue-300 font-semibold underline decoration-blue-500/50 underline-offset-2 cursor-pointer transition-colors"
        >
          {{ isAllSelected ? 'Deselect All' : 'Select All (' + totalCount + ')' }}
        </button>
      </div>

      <!-- Right: Action Buttons + Clear Selection -->
      <div class="flex items-center gap-2">
        <!-- Approve Action -->
        <button
          *ngIf="showApprove"
          type="button"
          (click)="approveSelected.emit()"
          [disabled]="isLoading"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition-all cursor-pointer disabled:opacity-50"
        >
          <app-icon name="check-circle-2" size="14"></app-icon>
          <span>Approve ({{ selectedCount }})</span>
        </button>

        <!-- Export Action -->
        <button
          *ngIf="showExport"
          type="button"
          (click)="exportSelected.emit()"
          [disabled]="isLoading"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 shadow-sm transition-all cursor-pointer disabled:opacity-50"
        >
          <app-icon name="download" size="14"></app-icon>
          <span>Export</span>
        </button>

        <!-- Delete Action -->
        <button
          *ngIf="showDelete"
          type="button"
          (click)="deleteSelected.emit()"
          [disabled]="isLoading"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-sm transition-all cursor-pointer disabled:opacity-50"
        >
          <app-icon name="trash-2" size="14"></app-icon>
          <span>Delete ({{ selectedCount }})</span>
        </button>

        <!-- Vertical Divider -->
        <div class="h-4 w-px bg-slate-700"></div>

        <!-- Clear Selection Button -->
        <button
          type="button"
          (click)="clearSelection.emit()"
          [disabled]="isLoading"
          class="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          title="Clear selection"
        >
          <app-icon name="x" size="16"></app-icon>
        </button>
      </div>
    </div>
  `,
})
export class BulkToolbarComponent {
  @Input() selectedCount = 0;
  @Input() totalCount = 0;
  @Input() isAllSelected = false;
  @Input() itemLabel = 'project';
  @Input() showApprove = false;
  @Input() showExport = false;
  @Input() showDelete = true;
  @Input() isLoading = false;

  @Output() selectAll = new EventEmitter<void>();
  @Output() clearSelection = new EventEmitter<void>();
  @Output() deleteSelected = new EventEmitter<void>();
  @Output() approveSelected = new EventEmitter<void>();
  @Output() exportSelected = new EventEmitter<void>();

  onToggleSelectAll() {
    this.selectAll.emit();
  }
}
