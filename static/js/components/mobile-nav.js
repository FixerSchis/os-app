document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburger-menu-btn');
    const navWrapper = document.querySelector('.nav-wrapper');
    const mainNav = document.getElementById('main-nav');
    const dropdowns = document.querySelectorAll('.main-nav .dropdown');
    const desktopDarkModeToggle = document.getElementById('dark-mode-toggle');
    const mobileDarkModeToggle = document.getElementById('mobile-dark-mode-toggle');
    const mobileDevNoticeBtn = document.getElementById('mobile-dev-notice-btn');
    const body = document.body;
    const mobileNavClose = document.getElementById('mobile-nav-close');

    // Hamburger menu toggle
    if (hamburgerBtn && navWrapper) {
        hamburgerBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            navWrapper.classList.toggle('nav-open');
            body.classList.toggle('nav-open');
        });
    }

    // Mobile close (X) button
    if (mobileNavClose && navWrapper) {
        mobileNavClose.addEventListener('click', function(e) {
            navWrapper.classList.remove('nav-open');
            body.classList.remove('nav-open');
            dropdowns.forEach(dd => dd.classList.remove('open'));
        });
    }

    // Mobile development notice button
    if (mobileDevNoticeBtn) {
        mobileDevNoticeBtn.addEventListener('click', function(e) {
            e.preventDefault();

            // Create or show the notice modal
            let noticeModal = document.getElementById('dev-notice-modal');
            if (!noticeModal) {
                noticeModal = document.createElement('div');
                noticeModal.id = 'dev-notice-modal';
                noticeModal.className = 'dev-notice-modal';
                noticeModal.innerHTML = `
                    <div class="dev-notice-content">
                        <div class="dev-notice-header">
                            <h3><i class="fas fa-exclamation-triangle"></i> Development Notice</h3>
                            <button class="dev-notice-close" id="dev-notice-close">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div class="dev-notice-body">
                            <p>This application is under active development. If you encounter any issues or have feedback, please report them below.</p>
                        </div>
                        <div class="dev-notice-footer">
                            <a href="https://github.com/FixerSchis/os-app/issues" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
                                <i class="fas fa-bug"></i> Report Issues
                            </a>
                        </div>
                    </div>
                `;
                document.body.appendChild(noticeModal);

                // Add close functionality
                const closeBtn = noticeModal.querySelector('#dev-notice-close');
                closeBtn.addEventListener('click', function() {
                    noticeModal.classList.remove('active');
                    body.classList.remove('modal-open');
                });

                // Close on outside click
                noticeModal.addEventListener('click', function(e) {
                    if (e.target === noticeModal) {
                        noticeModal.classList.remove('active');
                        body.classList.remove('modal-open');
                    }
                });

                // Close on escape key
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' && noticeModal.classList.contains('active')) {
                        noticeModal.classList.remove('active');
                        body.classList.remove('modal-open');
                    }
                });
            }

            // Show the modal
            noticeModal.classList.add('active');
            body.classList.add('modal-open');
        });
    }

    // Close menu on outside click (mobile only)
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && navWrapper.classList.contains('nav-open')) {
            if (!navWrapper.contains(e.target)) {
                navWrapper.classList.remove('nav-open');
                body.classList.remove('nav-open');
                // Close all open dropdowns
                dropdowns.forEach(dd => dd.classList.remove('open'));
            }
        }
    });

    // Close menu on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navWrapper.classList.contains('nav-open')) {
            navWrapper.classList.remove('nav-open');
            body.classList.remove('nav-open');
            dropdowns.forEach(dd => dd.classList.remove('open'));
        }
    });

    // Close menu if resizing to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && navWrapper.classList.contains('nav-open')) {
            navWrapper.classList.remove('nav-open');
            body.classList.remove('nav-open');
            dropdowns.forEach(dd => dd.classList.remove('open'));
        }
    });

    // Dropdowns: open on click in mobile, hover in desktop
    dropdowns.forEach(dropdown => {
        const btn = dropdown.querySelector('.dropbtn');
        if (!btn) return;

        // Remove any existing click listeners to prevent conflicts
        btn.removeEventListener('click', btn._dropdownClickHandler);

        // Create a new click handler
        btn._dropdownClickHandler = function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();

                // Close other dropdowns first
                dropdowns.forEach(dd => {
                    if (dd !== dropdown) {
                        dd.classList.remove('open');
                    }
                });

                // Toggle current dropdown
                const isOpen = dropdown.classList.contains('open');
                if (isOpen) {
                    dropdown.classList.remove('open');
                } else {
                    dropdown.classList.add('open');
                }

                return false;
            }
        };

        // Add the click listener
        btn.addEventListener('click', btn._dropdownClickHandler);
    });

    // Prevent dropdown click from closing nav
    mainNav && mainNav.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && e.target.closest('.dropdown')) {
            e.stopPropagation();
        }
    });

    // Synchronize mobile and desktop theme toggles
    function syncThemeToggles() {
        const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';

        if (mobileDarkModeToggle) {
            mobileDarkModeToggle.checked = isDarkMode;
        }
    }

    // Mobile theme toggle functionality
    if (mobileDarkModeToggle) {
        mobileDarkModeToggle.addEventListener('change', function() {
            const isDark = this.checked;
            document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');

            // Trigger the same event as the desktop toggle
            if (desktopDarkModeToggle) {
                desktopDarkModeToggle.click();
            }
        });
    }

    // Desktop theme toggle functionality (update mobile toggle when desktop is used)
    if (desktopDarkModeToggle) {
        desktopDarkModeToggle.addEventListener('click', function() {
            // Small delay to ensure the theme has been updated
            setTimeout(syncThemeToggles, 100);
        });
    }

    // Initialize theme toggle sync
    syncThemeToggles();
});
