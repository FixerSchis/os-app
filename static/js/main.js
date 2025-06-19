// Add flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function () {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function (message) {
        setTimeout(function () {
            message.style.opacity = '0';
            setTimeout(function () {
                message.remove();
            }, 300);
        }, 3000);
    });
}); 