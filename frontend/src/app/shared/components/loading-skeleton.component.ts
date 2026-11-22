import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-skeleton',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- Card Skeleton Grid -->
    <div *ngIf="type === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        *ngFor="let item of items"
        class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-subtle flex flex-col justify-between animate-pulse"
      >
        <div>
          <div class="flex items-start justify-between gap-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-slate-200 dark:bg-slate-800"></div>
            <div class="w-16 h-5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
          </div>
          <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-800 mb-2"></div>
          <div class="h-3 w-full rounded bg-slate-100 dark:bg-slate-800/60 mb-1"></div>
          <div class="h-3 w-2/3 rounded bg-slate-100 dark:bg-slate-800/60"></div>

          <div class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 space-y-2">
            <div class="h-3 w-1/2 rounded bg-slate-100 dark:bg-slate-800/60"></div>
            <div class="h-3 w-2/3 rounded bg-slate-100 dark:bg-slate-800/60"></div>
          </div>
        </div>

        <div class="mt-5 pt-3.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div class="h-3 w-16 rounded bg-slate-100 dark:bg-slate-800/60"></div>
          <div class="flex gap-2">
            <div class="h-6 w-12 rounded-lg bg-slate-200 dark:bg-slate-800"></div>
            <div class="h-6 w-20 rounded-lg bg-slate-200 dark:bg-slate-800"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Skeleton Rows -->
    <div *ngIf="type === 'table'" class="space-y-2 p-4 animate-pulse">
      <div *ngFor="let item of items" class="h-12 w-full rounded-xl bg-slate-100 dark:bg-slate-800/60"></div>
    </div>
  `,
})
export class LoadingSkeletonComponent {
  @Input() type: 'cards' | 'table' = 'cards';
  @Input() set count(val: number) {
    this.items = Array.from({ length: val }, (_, i) => i);
  }
  items = [0, 1, 2, 3, 4, 5];
}
