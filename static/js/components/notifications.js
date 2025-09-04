/**
 * Notification Bell Component
 * Handles the notification bell functionality including hover behavior and mobile interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const notificationBell = document.getElementById('notification-bell');
    const notificationDropdown = document.getElementById('notification-dropdown');

    if (!notificationBell || !notificationDropdown) {
        return; // Exit if elements don't exist
    }

    let hoverTimeout;
    let isDropdownVisible = false;

    // Show dropdown on hover (desktop)
    notificationBell.addEventListener('mouseenter', function() {
        if (window.innerWidth > 768) {
            clearTimeout(hoverTimeout);
            showDropdown();
        }
    });

    // Hide dropdown when mouse leaves (desktop)
    notificationBell.addEventListener('mouseleave', function() {
        if (window.innerWidth > 768) {
            hoverTimeout = setTimeout(hideDropdown, 300);
        }
    });

    // Keep dropdown open when hovering over it
    notificationDropdown.addEventListener('mouseenter', function() {
        if (window.innerWidth > 768) {
            clearTimeout(hoverTimeout);
        }
    });

    // Hide dropdown when mouse leaves it
    notificationDropdown.addEventListener('mouseleave', function() {
        if (window.innerWidth > 768) {
            hoverTimeout = setTimeout(hideDropdown, 300);
        }
    });

    // Click handler for mobile
    notificationBell.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        if (window.innerWidth <= 768) {
            toggleDropdown();
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!notificationBell.contains(e.target) && !notificationDropdown.contains(e.target)) {
            hideDropdown();
        }
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && isDropdownVisible) {
            hideDropdown();
        }
    });

    // Handle escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isDropdownVisible) {
            hideDropdown();
        }
    });

    function showDropdown() {
        notificationDropdown.style.display = 'block';
        isDropdownVisible = true;

        // Add a small delay to prevent flickering
        setTimeout(() => {
            notificationDropdown.style.opacity = '1';
            notificationDropdown.style.transform = 'translateY(0)';
        }, 10);
    }

    function hideDropdown() {
        notificationDropdown.style.opacity = '0';
        notificationDropdown.style.transform = 'translateY(-10px)';

        setTimeout(() => {
            notificationDropdown.style.display = 'none';
            isDropdownVisible = false;
        }, 200);
    }

    function toggleDropdown() {
        if (isDropdownVisible) {
            hideDropdown();
        } else {
            showDropdown();
        }
    }

    // Initialize dropdown styles
    notificationDropdown.style.opacity = '0';
    notificationDropdown.style.transform = 'translateY(-10px)';
    notificationDropdown.style.transition = 'opacity 0.2s ease, transform 0.2s ease';

    // Auto-refresh notifications every 30 seconds
    setInterval(function() {
        if (isDropdownVisible) {
            refreshNotifications();
        }
    }, 30000);

    function refreshNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.count > 0);
                updateNotificationList(data.notifications);
            })
            .catch(error => {
                console.error('Error refreshing notifications:', error);
            });
    }

    function updateNotificationBadge(hasNotifications) {
        const badge = notificationBell.querySelector('.notification-badge');
        if (hasNotifications && !badge) {
            const newBadge = document.createElement('span');
            newBadge.className = 'notification-badge';
            notificationBell.appendChild(newBadge);
        } else if (!hasNotifications && badge) {
            badge.remove();
        }
    }

    function updateNotificationList(notifications) {
        const notificationList = notificationDropdown.querySelector('.notification-list');
        if (!notificationList) return;

        if (notifications.length === 0) {
            notificationList.innerHTML = '<div class="notification-empty"><p>No notifications</p></div>';
            return;
        }

        const html = notifications.map(notification => `
            <div class="notification-item" data-priority="${notification.priority}">
                <div class="notification-content">
                    <div class="notification-title">${escapeHtml(notification.title)}</div>
                    <div class="notification-message">${escapeHtml(notification.message)}</div>
                </div>
                <div class="notification-action">
                    <a href="${escapeHtml(notification.url)}" class="btn btn-sm btn-primary">View</a>
                </div>
            </div>
        `).join('');

        notificationList.innerHTML = html;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
