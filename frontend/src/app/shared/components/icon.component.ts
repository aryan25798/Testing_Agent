import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-icon',
  standalone: true,
  imports: [CommonModule],
  template: `
    <svg
      xmlns="http://www.w3.org/2000/svg"
      [attr.width]="size"
      [attr.height]="size"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      [attr.stroke-width]="strokeWidth"
      stroke-linecap="round"
      stroke-linejoin="round"
      [class]="class"
      [ngSwitch]="normalizedName"
    >
      <!-- ========================================== -->
      <!-- 1. NAVIGATION & CORE APP ICONS (LUCIDE)   -->
      <!-- ========================================== -->

      <!-- Home / Dashboard -->
      <g *ngSwitchCase="'home'">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </g>
      <g *ngSwitchCase="'layout-dashboard'">
        <rect width="7" height="9" x="3" y="3" rx="1" />
        <rect width="7" height="5" x="14" y="3" rx="1" />
        <rect width="7" height="9" x="14" y="12" rx="1" />
        <rect width="7" height="5" x="3" y="16" rx="1" />
      </g>

      <!-- Folder / Projects -->
      <g *ngSwitchCase="'folder'">
        <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
      </g>
      <g *ngSwitchCase="'folder-git-2'">
        <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
        <circle cx="12" cy="13" r="2" />
        <path d="M12 15v3" />
      </g>

      <!-- Users / Team / Agents -->
      <g *ngSwitchCase="'users'">
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </g>
      <g *ngSwitchCase="'bot'">
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" /><path d="M20 14h2" />
        <path d="M15 13v2" /><path d="M9 13v2" />
      </g>

      <!-- Workflows / Git Merge -->
      <g *ngSwitchCase="'workflow'">
        <rect width="8" height="8" x="3" y="3" rx="2" />
        <path d="M7 11v4a2 2 0 0 0 2 2h4" />
        <rect width="8" height="8" x="13" y="13" rx="2" />
      </g>
      <g *ngSwitchCase="'git-merge'">
        <circle cx="18" cy="18" r="3" />
        <circle cx="6" cy="6" r="3" />
        <path d="M6 21V9a9 9 0 0 0 9 9" />
      </g>
      <g *ngSwitchCase="'git-branch'">
        <line x1="6" x2="6" y1="3" y2="15" />
        <circle cx="18" cy="6" r="3" />
        <circle cx="6" cy="18" r="3" />
        <path d="M18 9a9 9 0 0 1-9 9" />
      </g>

      <!-- Clipboard / Test Cases -->
      <g *ngSwitchCase="'clipboard-list'">
        <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <path d="M12 11h4" /><path d="M12 16h4" />
        <path d="M8 11h.01" /><path d="M8 16h.01" />
      </g>
      <g *ngSwitchCase="'clipboard-check'">
        <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <path d="m9 14 2 2 4-4" />
      </g>

      <!-- Automation / Terminal / Code -->
      <g *ngSwitchCase="'terminal'">
        <polyline points="4 17 10 11 4 5" />
        <line x1="12" x2="20" y1="19" y2="19" />
      </g>
      <g *ngSwitchCase="'code-2'">
        <path d="m18 16 4-4-4-4" />
        <path d="m6 8-4 4 4 4" />
        <path d="m14.5 4-5 16" />
      </g>
      <g *ngSwitchCase="'cog'">
        <path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" />
        <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
        <path d="M12 2v2" /><path d="M12 20v2" />
        <path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" />
        <path d="M2 12h2" /><path d="M20 12h2" />
        <path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
      </g>

      <!-- Executions / Clock / History -->
      <g *ngSwitchCase="'clock'">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </g>
      <g *ngSwitchCase="'history'">
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
        <polyline points="12 7 12 12 15 15" />
      </g>

      <!-- Reports / Bar Chart -->
      <g *ngSwitchCase="'bar-chart-3'">
        <path d="M3 3v18h18" />
        <path d="M18 17V9" />
        <path d="M13 17V5" />
        <path d="M8 17v-3" />
      </g>
      <g *ngSwitchCase="'bar-chart-2'">
        <line x1="18" x2="18" y1="20" y2="10" />
        <line x1="12" x2="12" y1="20" y2="4" />
        <line x1="6" x2="6" y1="20" y2="14" />
      </g>

      <!-- CPU / AI Engine -->
      <g *ngSwitchCase="'cpu'">
        <rect width="16" height="16" x="4" y="4" rx="2" />
        <rect width="6" height="6" x="9" y="9" rx="1" />
        <path d="M15 2v2" /><path d="M15 20v2" />
        <path d="M2 15h2" /><path d="M2 9h2" />
        <path d="M20 15h2" /><path d="M20 9h2" />
        <path d="M9 2v2" /><path d="M9 20v2" />
      </g>

      <!-- MCP Integrations / Network -->
      <g *ngSwitchCase="'network'">
        <rect x="16" y="16" width="6" height="6" rx="1" />
        <rect x="2" y="16" width="6" height="6" rx="1" />
        <rect x="9" y="2" width="6" height="6" rx="1" />
        <path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3" />
        <path d="M12 12V8" />
      </g>
      <g *ngSwitchCase="'blocks'">
        <rect width="7" height="7" x="14" y="3" rx="1" />
        <path d="M10 21V8a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5a1 1 0 0 0-1-1H3" />
      </g>

      <!-- Settings -->
      <g *ngSwitchCase="'settings'">
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
        <circle cx="12" cy="12" r="3" />
      </g>
      <g *ngSwitchCase="'sliders'">
        <line x1="4" x2="4" y1="21" y2="14" /><line x1="4" x2="4" y1="10" y2="3" />
        <line x1="12" x2="12" y1="21" y2="12" /><line x1="12" x2="12" y1="8" y2="3" />
        <line x1="20" x2="20" y1="21" y2="16" /><line x1="20" x2="20" y1="12" y2="3" />
        <line x1="1" x2="7" y1="14" y2="14" /><line x1="9" x2="15" y1="8" y2="8" />
        <line x1="17" x2="23" y1="16" y2="16" />
      </g>

      <!-- ========================================== -->
      <!-- 2. COMMON ACTION & SYSTEM ICONS (LUCIDE)   -->
      <!-- ========================================== -->

      <!-- Search -->
      <g *ngSwitchCase="'search'">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </g>
      <g *ngSwitchCase="'command'">
        <path d="M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3" />
      </g>

      <!-- Theme Controls -->
      <g *ngSwitchCase="'sun'">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2" /><path d="M12 20v2" />
        <path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" />
        <path d="M2 12h2" /><path d="M20 12h2" />
        <path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
      </g>
      <g *ngSwitchCase="'moon'">
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
      </g>
      <g *ngSwitchCase="'monitor'">
        <rect width="20" height="14" x="2" y="3" rx="2" />
        <line x1="8" x2="16" y1="21" y2="21" />
        <line x1="12" x2="12" y1="17" y2="21" />
      </g>

      <!-- UI Menu & Close -->
      <g *ngSwitchCase="'menu'">
        <line x1="4" x2="20" y1="12" y2="12" />
        <line x1="4" x2="20" y1="6" y2="6" />
        <line x1="4" x2="20" y1="18" y2="18" />
      </g>
      <g *ngSwitchCase="'x'">
        <path d="M18 6 6 18" />
        <path d="m6 6 12 12" />
      </g>
      <g *ngSwitchCase="'plus'">
        <path d="M5 12h14" />
        <path d="M12 5v14" />
      </g>
      <g *ngSwitchCase="'play'">
        <polygon points="6 3 20 12 6 21 6 3" />
      </g>
      <g *ngSwitchCase="'check'">
        <path d="M20 6 9 17l-5-5" />
      </g>
      <g *ngSwitchCase="'check-circle-2'">
        <circle cx="12" cy="12" r="10" />
        <path d="m9 12 2 2 4-4" />
      </g>
      <g *ngSwitchCase="'alert-circle'">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" x2="12" y1="8" y2="12" />
        <line x1="12" x2="12.01" y1="16" y2="16" />
      </g>
      <g *ngSwitchCase="'alert-triangle'">
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
        <line x1="12" x2="12" y1="9" y2="13" />
        <line x1="12" x2="12.01" y1="17" y2="17" />
      </g>
      <g *ngSwitchCase="'x-circle'">
        <circle cx="12" cy="12" r="10" />
        <path d="m15 9-6 6" />
        <path d="m9 9 6 6" />
      </g>
      <g *ngSwitchCase="'arrow-right'">
        <path d="M5 12h14" />
        <path d="m12 5 7 7-7 7" />
      </g>
      <g *ngSwitchCase="'arrow-left'">
        <path d="m12 19-7-7 7-7" />
        <path d="M19 12H5" />
      </g>
      <g *ngSwitchCase="'chevron-down'">
        <polyline points="6 9 12 15 18 9" />
      </g>
      <g *ngSwitchCase="'chevron-right'">
        <polyline points="9 18 15 12 9 6" />
      </g>
      <g *ngSwitchCase="'chevron-left'">
        <polyline points="15 18 9 12 15 6" />
      </g>
      <g *ngSwitchCase="'more-vertical'">
        <circle cx="12" cy="12" r="1" />
        <circle cx="12" cy="5" r="1" />
        <circle cx="12" cy="19" r="1" />
      </g>

      <!-- File & Edit Actions -->
      <g *ngSwitchCase="'download'">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" x2="12" y1="15" y2="3" />
      </g>
      <g *ngSwitchCase="'upload'">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" x2="12" y1="3" y2="15" />
      </g>
      <g *ngSwitchCase="'copy'">
        <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
        <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
      </g>
      <g *ngSwitchCase="'trash-2'">
        <path d="M3 6h18" />
        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
        <line x1="10" x2="10" y1="11" y2="17" />
        <line x1="14" x2="14" y1="11" y2="17" />
      </g>
      <g *ngSwitchCase="'edit'">
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
      </g>
      <g *ngSwitchCase="'refresh-cw'">
        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
        <path d="M21 3v5h-5" />
        <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
        <path d="M8 16H3v5" />
      </g>
      <g *ngSwitchCase="'rotate-ccw'">
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
      </g>
      <g *ngSwitchCase="'filter'">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
      </g>
      <g *ngSwitchCase="'external-link'">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
        <polyline points="15 3 21 3 21 9" />
        <line x1="10" x2="21" y1="14" y2="3" />
      </g>
      <g *ngSwitchCase="'eye'">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
        <circle cx="12" cy="12" r="3" />
      </g>
      <g *ngSwitchCase="'eye-off'">
        <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
        <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
        <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
        <line x1="2" x2="22" y1="2" y2="22" />
      </g>
      <g *ngSwitchCase="'database'">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M3 5v14a9 3 0 0 0 18 0V5" />
        <path d="M3 12a9 3 0 0 0 18 0" />
      </g>
      <g *ngSwitchCase="'file-text'">
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
        <path d="M14 2v4a2 2 0 0 0 2 2h4" />
        <path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" />
      </g>
      <g *ngSwitchCase="'zap'">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </g>
      <g *ngSwitchCase="'sparkles'">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
        <path d="M5 3v4" /><path d="M19 17v4" /><path d="M3 5h4" /><path d="M17 19h4" />
      </g>
      <g *ngSwitchCase="'shield-check'">
        <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
        <path d="m9 12 2 2 4-4" />
      </g>
      <g *ngSwitchCase="'activity'">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </g>
      <g *ngSwitchCase="'layers'">
        <polygon points="12 2 2 7 12 12 22 7 12 2" />
        <polyline points="2 17 12 22 22 17" />
        <polyline points="2 12 12 17 22 12" />
      </g>
      <g *ngSwitchCase="'rocket'">
        <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
        <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
        <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
        <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
      </g>

      <!-- ========================================== -->
      <!-- 3. AUTHENTIC TECHNOLOGY BRAND LOGOS        -->
      <!-- Sourced from Simple Icons / Official Specs -->
      <!-- ========================================== -->

      <!-- GitHub Official Mark -->
      <g *ngSwitchCase="'github'">
        <path
          fill="currentColor"
          stroke="none"
          fill-rule="evenodd"
          clip-rule="evenodd"
          d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"
        />
      </g>

      <!-- Atlassian Official Mark -->
      <g *ngSwitchCase="'atlassian'">
        <path
          fill="currentColor"
          stroke="none"
          d="m11.53 2c0 2.4-1.97 4.35-4.4 4.35H2.8C2.36 6.35 2 6.71 2 7.15v4.33c0 .44.36.8.8.8h4.33c2.4 0 4.4 1.95 4.4 4.35 0 2.4-1.97 4.35-4.4 4.35H2.8c-.44 0-.8.36-.8.8v.22c0 .44.36.8.8.8h4.33c4.2 0 7.6-3.4 7.6-7.6 0-1.87-.67-3.58-1.8-4.9 1.13-1.32 1.8-3.03 1.8-4.9 0-4.2-3.4-7.6-7.6-7.6H2.8c-.44 0-.8.36-.8.8v.22c0 .44.36.8.8.8h4.33c2.43 0 4.4 1.95 4.4 4.35z"
        />
      </g>

      <!-- Jira Official Mark -->
      <g *ngSwitchCase="'jira'">
        <path
          fill="currentColor"
          stroke="none"
          d="M11.571 11.514H.057a.057.057 0 0 1-.057-.057v-5.68A5.771 5.771 0 0 1 5.771 0h5.743a.057.057 0 0 1 .057.057v11.4a.057.057 0 0 1-.057.057zm12.372 0H12.43a.057.057 0 0 1-.058-.057v-5.68A5.771 5.771 0 0 1 18.143 0h5.743a.057.057 0 0 1 .057.057v11.4a.057.057 0 0 1-.057.057zM11.571 24H.057A.057.057 0 0 1 0 23.943v-5.68a5.771 5.771 0 0 1 5.771-5.772h5.743a.057.057 0 0 1 .057.057v11.4a.057.057 0 0 1-.057.057z"
        />
      </g>

      <!-- Google Gemini Official 4-Point Sparkling Star Mark -->
      <g *ngSwitchCase="'gemini'">
        <path
          fill="currentColor"
          stroke="none"
          d="M11.04 19.32Q12 21.6 12 24q0-2.4.96-4.68.99-2.28 2.67-3.96t3.96-2.67Q21.6 12 24 12q-2.4 0-4.68-.96-2.28-.99-3.96-2.67t-2.67-3.96Q12 2.4 12 0q0 2.4-.96 4.68-.99 2.28-2.67 3.96T4.41 11.31Q2.4 12 0 12q2.4 0 4.68.96 2.28.99 3.96 2.67t2.4 3.69z"
        />
      </g>
      <!-- Google 'G' Mark (Fallback/Alias) -->
      <g *ngSwitchCase="'google'">
        <path
          fill="currentColor"
          stroke="none"
          d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2c2.72 0 5.2 1.01 7.07 2.68l-2.47 2.47C15.42 6.03 13.8 5.3 12 5.3 8.3 5.3 5.3 8.3 5.3 12s3 6.7 6.7 6.7c3.4 0 5.8-2.2 6.3-5.2H12v-3.3h9.6c.1.6.2 1.2.2 1.9 0 5.5-3.8 9.9-10.1 9.9z"
        />
      </g>

      <!-- OpenAI Official Knot Mark -->
      <g *ngSwitchCase="'openai'">
        <path
          fill="currentColor"
          stroke="none"
          d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.182a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.758a.771.771 0 0 0 .78 0l5.843-3.368v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.814 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.787A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.856-5.833-3.388 2.015-1.164a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.104v-5.677a.79.79 0 0 0-.407-.666zm2.01-3.023-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.41 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zM8.307 12.863l-2.02-1.164a.08.08 0 0 1-.038-.056V6.075a4.5 4.5 0 0 1 7.376-3.454l-.142.08-4.78 2.758a.795.795 0 0 0-.393.681zm1.097-2.365 2.602-1.5 2.607 1.5v3l-2.597 1.5-2.607-1.5z"
        />
      </g>

      <!-- Playwright Official Mark -->
      <g *ngSwitchCase="'playwright'">
        <path
          fill="currentColor"
          stroke="none"
          d="M18.895 8.653c-.318-.466-.757-.84-1.272-1.082-.515-.244-1.089-.333-1.662-.26-.574.074-1.114.331-1.564.743-.45.413-.767.949-.917 1.55l-.133.535a3.864 3.864 0 0 1-.58 1.18c-.287.397-.664.71-1.1.91-.437.2-.919.278-1.397.226a3.57 3.57 0 0 1-1.32-.475 3.395 3.395 0 0 1-.986-.983c-.267-.403-.435-.867-.492-1.353a3.593 3.593 0 0 1 .147-1.442l.307-1.077c.22-.76.623-1.447 1.173-1.996.55-.548 1.226-.94 1.968-1.14.742-.2 1.524-.2 2.274.002.75.202 1.433.587 1.987 1.121l.138.134 1.414-1.414-.138-.135C17.65 3.167 16.7 2.645 15.65 2.36c-1.05-.285-2.146-.285-3.197 0-1.05.285-2.002.839-2.775 1.616-.774.777-1.34 1.745-1.65 2.822L7.72 7.876c-.22.766-.23 1.574-.03 2.344.2.77.6 1.472 1.164 2.036.564.564 1.266.963 2.036 1.163.77.2 1.578.19 2.348-.03a5.55 5.55 0 0 0 1.93-1.074c.264-.22.5-.47.704-.747.27.608.68 1.144 1.196 1.56.516.417 1.127.697 1.776.816.65.12 1.317.067 1.938-.152.622-.22 1.177-.6 1.617-1.107.44-.508.736-1.127.863-1.796.126-.67.068-1.36-.17-1.99-.236-.63-.642-1.18-1.178-1.597z"
        />
      </g>

      <!-- Selenium Official Mark -->
      <g *ngSwitchCase="'selenium'">
        <path
          fill="currentColor"
          stroke="none"
          d="M16.924 0a3.918 3.918 0 0 0-3.918 3.918c0 .245.023.484.067.716L4.634 9.07a3.916 3.916 0 1 0 0 5.86l8.439 4.436a3.914 3.914 0 1 0 3.851-4.632l-8.439-4.436a3.924 3.924 0 0 0 0-.596l8.439-4.436A3.918 3.918 0 1 0 16.924 0zm0 2a1.918 1.918 0 1 1 0 3.836 1.918 1.918 0 0 1 0-3.836zM3.918 10.082a1.918 1.918 0 1 1 0 3.836 1.918 1.918 0 0 1 0-3.836zm13.006 8a1.918 1.918 0 1 1 0 3.836 1.918 1.918 0 0 1 0-3.836z"
        />
      </g>

      <!-- Python Official Mark -->
      <g *ngSwitchCase="'python'">
        <path
          fill="currentColor"
          stroke="none"
          d="M11.914 0C5.82 0 6.2 2.656 6.2 2.656l.006 2.75h5.808v.825H3.832S0 5.786 0 11.914c0 6.13 3.375 5.922 3.375 5.922h2.013v-2.822s-.11-3.375 3.31-3.375h5.688s3.197.052 3.197-3.14V2.656S18.01 0 11.914 0zm-1.71 1.706a1.006 1.006 0 1 1 0 2.012 1.006 1.006 0 0 1 0-2.012zM12.086 24c6.094 0 5.714-2.656 5.714-2.656l-.006-2.75H11.986v-.825h8.182S24 18.214 24 12.086c0-6.13-3.375-5.922-3.375-5.922h-2.013v2.822s.11 3.375-3.31 3.375H9.614s-3.197-.052-3.197 3.14v5.828S5.99 24 12.086 24zm1.71-1.706a1.006 1.006 0 1 1 0-2.012 1.006 1.006 0 0 1 0 2.012z"
        />
      </g>

      <!-- Angular Official Mark -->
      <g *ngSwitchCase="'angular'">
        <path
          fill="currentColor"
          stroke="none"
          d="M12 2.225 2.14 5.73l1.495 12.985L12 23.775l8.365-5.06 1.495-12.985L12 2.225zM12 4.41l6.735 2.39-1.07 9.295L12 19.34l-5.665-3.245-1.07-9.295L12 4.41zm0 2.59-4.22 9.5h1.745l.84-2.14h3.27l.84 2.14h1.745L12 7zm0 2.82 1.07 2.73h-2.14L12 9.82z"
        />
      </g>

      <!-- ========================================== -->
      <!-- 4. DEFAULT FALLBACK ICON                   -->
      <!-- ========================================== -->
      <circle *ngSwitchDefault cx="12" cy="12" r="9" />
    </svg>
  `,
})
export class IconComponent {
  @Input() name = 'circle';
  @Input() size: number | string = 18;
  @Input() strokeWidth: number | string = 2;
  @Input() class = '';

  get normalizedName(): string {
    return (this.name || 'circle').toLowerCase().trim();
  }
}
