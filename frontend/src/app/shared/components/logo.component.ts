import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="inline-flex items-center gap-3 select-none" [class]="class">
      <!-- Precision Vector Quality Emblem -->
      <svg
        [attr.width]="size"
        [attr.height]="size"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        class="shrink-0 transition-transform duration-200 group-hover:scale-105"
      >
        <defs>
          <linearGradient [attr.id]="'brand-primary-' + uniqueId" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#1d4ed8" />
            <stop offset="100%" stop-color="#3b82f6" />
          </linearGradient>
          <linearGradient [attr.id]="'brand-accent-' + uniqueId" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#0284c7" />
            <stop offset="50%" stop-color="#38bdf8" />
            <stop offset="100%" stop-color="#818cf8" />
          </linearGradient>
        </defs>

        <!-- Precision Rounded SaaS Base Tile -->
        <rect
          width="32"
          height="32"
          rx="7.5"
          fill="#090f1d"
          stroke="rgba(255, 255, 255, 0.14)"
          stroke-width="0.75"
        />

        <!-- Left Execution Bracket Pillar ('A' / '<' code test geometry) -->
        <path
          d="M7.5 24L14 6.5C14.4 5.5 15.6 5.5 16 6.5L18.5 13L13.5 24H7.5Z"
          [attr.fill]="'url(#brand-primary-' + uniqueId + ')'"
        />

        <!-- Precision Verification Vector ('✓' QA checkmark) -->
        <path
          d="M11 17.5L15 21.5C15.5 22 16.5 22 17 21.3L25.5 10C26 9.3 25.8 8.3 25 7.8C24.2 7.3 23.2 7.5 22.7 8.3L16.2 17.2L13.2 14.2C12.5 13.5 11.5 13.5 10.8 14.2C10.2 15 10.2 16.7 11 17.5Z"
          [attr.fill]="'url(#brand-accent-' + uniqueId + ')'"
        />

        <!-- Precision Apex Focus Node -->
        <circle cx="15.8" cy="5.8" r="1.2" fill="#38bdf8" />
      </svg>

      <!-- Optional Accompanying Wordmark -->
      <div *ngIf="showText" class="truncate min-w-0">
        <div class="font-bold text-slate-900 dark:text-white text-sm leading-tight tracking-tight">AI Testing</div>
        <div class="font-extrabold text-blue-500 dark:text-blue-400 text-[10px] leading-tight tracking-wider uppercase">Agent</div>
      </div>
    </div>
  `,
})
export class LogoComponent {
  @Input() size: number = 32;
  @Input() showText: boolean = false;
  @Input() class: string = '';

  uniqueId = Math.random().toString(36).substring(2, 9);
}
