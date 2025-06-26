// Cookie consent management
class CookieConsentManager {
    constructor() {
        this.consentKey = 'cookie_consent';
        this.init();
    }

    init() {
        // Check if user has already made a choice
        const consent = this.getCookie(this.consentKey);
        console.log('Cookie consent check:', consent);

        if (consent === null) {
            // No consent choice made yet, show the popup
            console.log('No consent found, showing popup');
            this.showConsentPopup();
        } else if (consent === 'declined') {
            // User declined cookies, ensure no cookies are set
            console.log('Consent declined, disabling cookies');
            this.disableCookies();
        } else if (consent === 'accepted') {
            // User accepted cookies, enable cookie functionality
            console.log('Consent accepted, enabling cookies');
            this.enableCookies();
        }
    }

    showConsentPopup() {
        // Create the popup HTML
        const popup = document.createElement('div');
        popup.className = 'cookie-consent';
        popup.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <h3>🍪 We use cookies to enhance your experience</h3>
                    <p>
                        This app uses cookies to remember your theme preference (dark/light mode)
                        and to keep you logged in. These cookies are for convenience only and
                        the app will work without them. We don't track you or share your data.
                    </p>
                </div>
                <div class="cookie-consent-buttons">
                    <button class="cookie-consent-btn decline" onclick="cookieConsentManager.handleDecline()">
                        Decline
                    </button>
                    <button class="cookie-consent-btn accept" onclick="cookieConsentManager.handleAccept()">
                        Accept
                    </button>
                </div>
            </div>
        `;

        // Add to page
        document.body.appendChild(popup);

        // Show the popup with animation
        setTimeout(() => {
            popup.classList.add('show');
        }, 100);
    }

    handleAccept() {
        this.setCookie(this.consentKey, 'accepted', 365); // Remember for 1 year
        this.hideConsentPopup();
        this.enableCookies();
    }

    handleDecline() {
        this.setCookie(this.consentKey, 'declined', 365); // Remember for 1 year
        this.hideConsentPopup();
        this.disableCookies();
    }

    hideConsentPopup() {
        const popup = document.querySelector('.cookie-consent');
        if (popup) {
            popup.classList.remove('show');
            setTimeout(() => {
                if (popup.parentNode) {
                    popup.parentNode.removeChild(popup);
                }
            }, 300);
        }
    }

    enableCookies() {
        // Enable cookie functionality
        window.cookiesEnabled = true;

        // If dark mode manager exists, allow it to use cookies
        if (window.darkModeManager) {
            window.darkModeManager.cookiesEnabled = true;
        }
    }

    disableCookies() {
        // Disable cookie functionality
        window.cookiesEnabled = false;

        // If dark mode manager exists, disable its cookie usage
        if (window.darkModeManager) {
            window.darkModeManager.cookiesEnabled = false;
        }

        // Remove any existing theme cookie
        this.deleteCookie('theme');
    }

    // Cookie utility methods
    getCookie(name) {
        // Always allow reading the consent cookie to avoid circular dependency
        if (name === this.consentKey) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        // For other cookies, check if cookies are enabled
        if (!window.cookiesEnabled) {
            return null;
        }

        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    setCookie(name, value, days) {
        // Always allow setting the consent cookie
        if (name === this.consentKey) {
            const expires = new Date();
            expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
            document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
            return;
        }

        // For other cookies, check if cookies are enabled
        if (!window.cookiesEnabled) {
            return;
        }

        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }

    deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }
}

// Initialize cookie consent manager when DOM is loaded
let cookieConsentManager;
document.addEventListener('DOMContentLoaded', () => {
    cookieConsentManager = new CookieConsentManager();
    window.cookieConsentManager = cookieConsentManager;
});
