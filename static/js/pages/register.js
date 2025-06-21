document.addEventListener('DOMContentLoaded', function () {
    const registerForm = document.querySelector('form');
    if (!registerForm) return; // Only run on register page

    registerForm.addEventListener('submit', function (event) {
        const emailInput = registerForm.querySelector('input[type="email"]');
        const passwordInput = registerForm.querySelector('input[type="password"]');

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

        if (passwordInput.value.length < 8) {
            event.preventDefault();
            alert('Password must be at least 8 characters long');
            return;
        }

        if (!/[a-z]/.test(passwordInput.value) || 
            !/[A-Z]/.test(passwordInput.value) || 
            !/([0-9]|[^a-zA-Z0-9])/.test(passwordInput.value)) {
            event.preventDefault();
            alert('Password must contain at least one lowercase letter, one uppercase letter, and one numeric or special character');
            return;
        }
    });
}); 