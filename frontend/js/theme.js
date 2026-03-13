/* ============================================================
   Theme Engine — Dual Theme Toggle (Dark / Light)
   Persists user preference in localStorage
   ============================================================ */

(function () {
    const STORAGE_KEY = 'lp-theme';
    const DEFAULT_THEME = 'dark';

    // Apply saved theme immediately to prevent flash
    function getPreferredTheme() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) return saved;
        // Respect OS preference if no saved choice
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
        return DEFAULT_THEME;
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        updateToggleIcons(theme);
    }

    function updateToggleIcons(theme) {
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            const sunIcon = btn.querySelector('.icon-sun');
            const moonIcon = btn.querySelector('.icon-moon');
            if (sunIcon && moonIcon) {
                if (theme === 'light') {
                    sunIcon.style.display = 'none';
                    moonIcon.style.display = 'inline';
                } else {
                    sunIcon.style.display = 'inline';
                    moonIcon.style.display = 'none';
                }
            }
        });
    }

    // Apply immediately (before DOM ready) to prevent FOUC
    applyTheme(getPreferredTheme());

    // Expose global toggle function
    window.toggleTheme = function () {
        const current = document.documentElement.getAttribute('data-theme') || DEFAULT_THEME;
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
    };

    // Re-apply icons once DOM is ready (buttons may not exist at script parse time)
    document.addEventListener('DOMContentLoaded', function () {
        updateToggleIcons(getPreferredTheme());
    });
})();
