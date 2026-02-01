// Main JavaScript for MinutesIQ

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Global error handler for htmx requests
document.body.addEventListener('htmx:responseError', (event) => {
    showToast('An error occurred. Please try again.', 'error');
});

// Success handler
document.body.addEventListener('htmx:afterRequest', (event) => {
    if (event.detail.successful && event.detail.xhr.status === 200) {
        const successMessage = event.detail.xhr.getResponseHeader('X-Success-Message');
        if (successMessage) {
            showToast(successMessage, 'success');
        }
    }
});

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const inputs = form.querySelectorAll('input[required], textarea[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('border-red-500');
            isValid = false;
        } else {
            input.classList.remove('border-red-500');
        }
    });

    return isValid;
}

// Handle logout
document.body.addEventListener('htmx:afterRequest', (event) => {
    // Check if this is a logout request
    if (event.detail.xhr.responseURL && event.detail.xhr.responseURL.includes('/auth/logout')) {
        if (event.detail.successful) {
            showToast('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = '/auth/login';
            }, 500);
        }
    }
});

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuIconOpen = document.getElementById('menu-icon-open');
    const menuIconClose = document.getElementById('menu-icon-close');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';

            // Toggle menu visibility
            mobileMenu.classList.toggle('hidden');

            // Toggle icons
            menuIconOpen.classList.toggle('hidden');
            menuIconOpen.classList.toggle('block');
            menuIconClose.classList.toggle('hidden');
            menuIconClose.classList.toggle('block');

            // Update aria-expanded
            mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
        });
    }
});

// Export functions for global use
window.showToast = showToast;
window.validateForm = validateForm;
