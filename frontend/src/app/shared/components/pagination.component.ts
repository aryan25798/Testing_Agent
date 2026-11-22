import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IconComponent } from './icon.component';

@Component({
  selector: 'app-pagination',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div
      class="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4 py-3 px-4 sm:px-5 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-subtle text-xs transition-colors"
      *ngIf="totalItems > 0"
    >
      <!-- Left: Item Range & Total Count -->
      <div class="text-slate-600 dark:text-slate-400 font-medium text-[11px] sm:text-xs text-center sm:text-left">
        Showing
        <span class="font-bold text-slate-900 dark:text-white">{{ startItem }}</span>
        to
        <span class="font-bold text-slate-900 dark:text-white">{{ endItem }}</span>
        of
        <span class="font-bold text-slate-900 dark:text-white">{{ totalItems }}</span>
        records
      </div>

      <!-- Right: Page Controls + Page Size Selector -->
      <div class="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
        <!-- Page Size Selector -->
        <div class="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-[11px]">
          <span>Per page:</span>
          <select
            [ngModel]="pageSize"
            (ngModelChange)="onPageSizeChange($event)"
            class="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold focus:border-blue-500 outline-none cursor-pointer"
          >
            <option *ngFor="let opt of pageSizeOptions" [value]="opt">{{ opt }}</option>
          </select>
        </div>

        <!-- Vertical Divider -->
        <div class="h-4 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>

        <!-- Navigation Buttons -->
        <div class="flex items-center gap-1">
          <!-- First Page -->
          <button
            (click)="goToPage(1)"
            [disabled]="currentPage <= 1 || isLoading"
            class="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="First page"
          >
            <app-icon name="chevrons-left" size="14"></app-icon>
          </button>

          <!-- Previous Page -->
          <button
            (click)="goToPage(currentPage - 1)"
            [disabled]="currentPage <= 1 || isLoading"
            class="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Previous page"
          >
            <app-icon name="chevron-left" size="14"></app-icon>
          </button>

          <!-- Numbered Pages -->
          <ng-container *ngFor="let page of visiblePages">
            <span
              *ngIf="page === -1"
              class="px-2 text-slate-400 dark:text-slate-600 select-none font-bold"
            >
              ...
            </span>

            <button
              *ngIf="page !== -1"
              (click)="goToPage(page)"
              [disabled]="isLoading"
              class="min-w-[28px] h-7 px-2 rounded-lg text-xs font-semibold transition-all cursor-pointer"
              [ngClass]="{
                'bg-blue-600 text-white font-bold shadow-sm shadow-blue-500/20': page === currentPage,
                'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800': page !== currentPage
              }"
            >
              {{ page }}
            </button>
          </ng-container>

          <!-- Next Page -->
          <button
            (click)="goToPage(currentPage + 1)"
            [disabled]="currentPage >= totalPages || isLoading"
            class="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Next page"
          >
            <app-icon name="chevron-right" size="14"></app-icon>
          </button>

          <!-- Last Page -->
          <button
            (click)="goToPage(totalPages)"
            [disabled]="currentPage >= totalPages || isLoading"
            class="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Last page"
          >
            <app-icon name="chevrons-right" size="14"></app-icon>
          </button>
        </div>
      </div>
    </div>
  `,
})
export class PaginationComponent implements OnChanges {
  @Input() currentPage = 1;
  @Input() pageSize = 10;
  @Input() totalItems = 0;
  @Input() pageSizeOptions = [10, 20, 50, 100];
  @Input() isLoading = false;

  @Output() pageChange = new EventEmitter<number>();
  @Output() pageSizeChange = new EventEmitter<number>();

  totalPages = 1;
  startItem = 0;
  endItem = 0;
  visiblePages: number[] = [];

  ngOnChanges(_changes: SimpleChanges) {
    this.computePagination();
  }

  computePagination() {
    this.totalPages = Math.max(1, Math.ceil(this.totalItems / this.pageSize));
    if (this.totalItems === 0) {
      this.startItem = 0;
      this.endItem = 0;
      this.visiblePages = [];
      return;
    }

    this.startItem = (this.currentPage - 1) * this.pageSize + 1;
    this.endItem = Math.min(this.totalItems, this.currentPage * this.pageSize);

    // Calculate smart page numbers with ellipsis
    const total = this.totalPages;
    const current = this.currentPage;

    if (total <= 7) {
      this.visiblePages = Array.from({ length: total }, (_, i) => i + 1);
    } else if (current <= 4) {
      this.visiblePages = [1, 2, 3, 4, 5, -1, total];
    } else if (current >= total - 3) {
      this.visiblePages = [1, -1, total - 4, total - 3, total - 2, total - 1, total];
    } else {
      this.visiblePages = [1, -1, current - 1, current, current + 1, -1, total];
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages && page !== this.currentPage && !this.isLoading) {
      this.pageChange.emit(page);
    }
  }

  onPageSizeChange(newSize: number) {
    const size = Number(newSize);
    if (size !== this.pageSize) {
      this.pageSizeChange.emit(size);
    }
  }
}
