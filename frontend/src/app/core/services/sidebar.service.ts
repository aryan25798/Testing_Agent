import { Injectable, signal, effect } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class SidebarService {
  private readonly COLLAPSED_KEY = 'ai_testing_sidebar_collapsed';

  // Desktop collapsed state
  isCollapsed = signal<boolean>(false);

  // Mobile drawer state
  isMobileOpen = signal<boolean>(false);

  constructor() {
    // Load persisted state
    const saved = localStorage.getItem(this.COLLAPSED_KEY);
    if (saved !== null) {
      this.isCollapsed.set(saved === 'true');
    }

    // Reactively persist desktop state
    effect(() => {
      localStorage.setItem(this.COLLAPSED_KEY, String(this.isCollapsed()));
    });

    // Handle escape key to close mobile drawer
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isMobileOpen()) {
        this.closeMobile();
      }
    });

    // Auto-close mobile drawer on window resize to desktop
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 1024 && this.isMobileOpen()) {
        this.closeMobile();
      }
    });
  }

  toggleCollapse() {
    this.isCollapsed.update((val) => !val);
  }

  toggleMobile() {
    if (this.isMobileOpen()) {
      this.closeMobile();
    } else {
      this.openMobile();
    }
  }

  openMobile() {
    this.isMobileOpen.set(true);
    document.body.style.overflow = 'hidden';
  }

  closeMobile() {
    this.isMobileOpen.set(false);
    document.body.style.overflow = '';
  }
}
