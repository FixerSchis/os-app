// Dark mode functionality
class DarkModeManager {
    constructor() {
        this.navbarToggleButton = document.getElementById('dark-mode-toggle');
        this.settingsPageToggle = document.getElementById('dark_mode_preference_toggle');
        this.htmlElement = document.documentElement;
        // Check if user is authenticated by looking for settings link
        this.isAuthenticated = document.querySelector('a[href*="/settings/"]') !== null;

        // Initialize cookies enabled state
        this.cookiesEnabled = window.cookiesEnabled !== false;

        this.init();
    }

    init() {
        // Set initial theme based on user preference or session cookie
        this.setInitialTheme();

        // Add event listener to toggle button
        if (this.navbarToggleButton) {
            this.navbarToggleButton.addEventListener('click', () => this.toggleTheme());
        }
        if (this.settingsPageToggle) {
            this.settingsPageToggle.addEventListener('change', () => this.toggleTheme());
        }
    }

    setInitialTheme() {
        // Check if theme is already set in HTML (from server)
        const serverTheme = this.htmlElement.getAttribute('data-theme');
        if (serverTheme) {
            // Server has set the theme, use it
            this.setTheme(serverTheme);
            return;
        }

        // No server theme, check for session cookie (only if cookies are enabled)
        if (this.cookiesEnabled) {
            const sessionTheme = this.getCookie('theme');
            if (sessionTheme) {
                this.setTheme(sessionTheme);
                return;
            }
        }

        // No preference found, default to dark mode
        this.setTheme('dark');
    }

    toggleTheme() {
        const currentTheme = this.htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        this.setTheme(newTheme);

        // Persist preference
        this.persistPreference(newTheme);
    }

    setTheme(theme) {
        this.htmlElement.setAttribute('data-theme', theme);
        this.updateToggleStates(theme);
    }

    updateToggleStates(theme) {
        const isDarkMode = theme === 'dark';

        if (this.navbarToggleButton) {
            const icon = this.navbarToggleButton.querySelector('i');
            if (icon) {
                icon.className = isDarkMode ? 'fas fa-moon' : 'fas fa-sun';
                this.navbarToggleButton.title = isDarkMode ? 'Switch to light mode' : 'Switch to dark mode';
            }
        }

        if (this.settingsPageToggle) {
            this.settingsPageToggle.checked = isDarkMode;
        }
    }

    persistPreference(theme) {
        if (this.isAuthenticated) {
            // For authenticated users, save to server
            this.saveToServer(theme);
        } else if (this.cookiesEnabled) {
            // For non-authenticated users, save to session cookie (only if cookies are enabled)
            this.setCookie('theme', theme, 30); // 30 days
        }
        // If cookies are disabled, don't persist the preference
    }

    async saveToServer(theme) {
        try {
            const endpoint = this.isAuthenticated ? '/settings/toggle-dark-mode' : '/toggle-theme';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ theme: theme })
            });

            if (!response.ok) {
                console.error('Failed to save theme preference to server');
            }
        } catch (error) {
            console.error('Error saving theme preference:', error);
        }
    }

    getCookie(name) {
        if (!this.cookiesEnabled) {
            return null;
        }

        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    setCookie(name, value, days) {
        if (!this.cookiesEnabled) {
            return;
        }

        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }
}

// Initialize dark mode manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.darkModeManager = new DarkModeManager();
});
