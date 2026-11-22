import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="inline-flex items-center gap-3 select-none" [class]="class">
      <!-- Precision Vector Emblem Symbol -->
      <svg
        [attr.width]="size"
        [attr.height]="size"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        class="shrink-0 transition-transform duration-200 group-hover:scale-105"
      >
        <defs>
          <linearGradient [attr.id]="'logo-bg-' + uniqueId" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1e1b4b" />
            <stop offset="50%" stop-color="#0f172a" />
            <stop offset="100%" stop-color="#020617" />
          </linearGradient>
          <linearGradient [attr.id]="'logo-left-' + uniqueId" x1="0%" y1="100%" x2="50%" y2="0%">
            <stop offset="0%" stop-color="#2563eb" />
            <stop offset="100%" stop-color="#38bdf8" />
          </linearGradient>
          <linearGradient [attr.id]="'logo-check-' + uniqueId" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#38bdf8" />
            <stop offset="60%" stop-color="#60a5fa" />
            <stop offset="100%" stop-color="#a855f7" />
          </linearGradient>
          <filter [attr.id]="'glow-' + uniqueId" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#2563eb" flood-opacity="0.35" />
          </filter>
        </defs>

        <!-- Luxury Squircle Frame -->
        <rect width="48" height="48" rx="12" [attr.fill]="'url(#logo-bg-' + uniqueId + ')'" [attr.filter]="'url(#glow-' + uniqueId + ')'" />
        <rect x="0.5" y="0.5" width="47" height="47" rx="11.5" stroke="rgba(255,255,255,0.18)" stroke-width="1" />

        <!-- Left Ascender Pillar of 'A' -->
        <path d="M12 37L22.5 11C23.1 9.5 24.9 9.5 25.5 11L28 17.5L20 37H12Z" [attr.fill]="'url(#logo-left-' + uniqueId + ')'" />

        <!-- Interlocking QA Verification Checkmark -->
        <path
          d="M17.5 28.5L23.5 35C24.2 35.8 25.5 35.8 26.2 34.9L38 18.5C38.6 17.7 38.3 16.5 37.4 16.1C36.5 15.7 35.4 16 34.8 16.8L24.8 30.5L20.2 25.5C19.5 24.8 18.4 24.8 17.7 25.5C17 26.2 17 27.8 17.5 28.5Z"
          [attr.fill]="'url(#logo-check-' + uniqueId + ')'"
        />

        <!-- Optical Apex Jewel (AI Precision Node) -->
        <circle cx="24" cy="10" r="1.75" fill="#38bdf8" />
      </svg>

      <!-- Optional Accompanying Wordmark -->
      <div *ngIf="showText" class="truncate min-w-0">
        <div class="font-bold text-white text-sm leading-tight tracking-tight">AI Testing</div>
        <div class="font-extrabold text-blue-400 text-xs leading-tight tracking-wider uppercase">Agent</div>
      </div>
    </div>
  `,
})
export class LogoComponent {
  @Input() size: number = 36;
  @Input() showText: boolean = false;
  @Input() class: string = '';

  uniqueId = Math.random().toString(36).substring(2, 9);
}
