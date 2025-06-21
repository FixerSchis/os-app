document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.querySelector('form');
    if (!loginForm) return; // Only run on login page

    loginForm.addEventListener('submit', function (event) {
        const emailInput = loginForm.querySelector('input[type="email"]');
        const passwordInput = loginForm.querySelector('input[type="password"]');

        if (!emailInput.value) {
            event.preventDefault();
            alert('Please enter your email');
            return;
        }

        if (!passwordInput.value) {
            event.preventDefault();
            alert('Please enter your password');
            return;
        }
    });
}); 