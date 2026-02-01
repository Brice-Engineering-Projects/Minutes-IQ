/**
 * Toast Notification System
 *
 * Usage:
 *   showToast('Operation successful!', 'success');
 *   showToast('An error occurred', 'error');
 *   showToast('Processing...', 'info');
 *
 * Can also be triggered via htmx events:
 *   <button hx-post="/api/action" hx-on::after-request="handleHtmxResponse(event)">
 */

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast (success, error, info)
 * @param {number} duration - How long to show the toast in ms (default: 5000)
 */
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    const toastId = 'toast-' + Date.now();
    toast.id = toastId;
    toast.className = `toast toast-${type} flex items-start p-4 rounded-lg shadow-lg min-w-[300px] max-w-md`;
    toast.setAttribute('role', 'alert');

    // Icon based on type
    let icon = '';
    if (type === 'success') {
        icon = `
            <svg class="w-6 h-6 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
        `;
    } else if (type === 'error') {
        icon = `
            <svg class="w-6 h-6 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
        `;
    } else {
        icon = `
            <svg class="w-6 h-6 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
        `;
    }

    toast.innerHTML = `
        ${icon}
        <div class="flex-1 text-sm font-medium">
            ${escapeHtml(message)}
        </div>
        <button
            onclick="closeToast('${toastId}')"
            class="ml-4 flex-shrink-0 inline-flex text-white hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue'}-600 rounded"
            aria-label="Close"
        >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
        </button>
    `;

    // Add to container
    container.appendChild(toast);

    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            closeToast(toastId);
        }, duration);
    }
}

/**
 * Close a toast notification
 * @param {string} toastId - The ID of the toast to close
 */
function closeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        // Fade out animation
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease-out';

        setTimeout(() => {
            toast.remove();

            // Remove container if empty
            const container = document.getElementById('toast-container');
            if (container && container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - The text to escape
 * @returns {string} - The escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Handle htmx responses and show appropriate toasts
 * Can be used with hx-on::after-request attribute
 * @param {CustomEvent} event - The htmx event
 */
function handleHtmxResponse(event) {
    const xhr = event.detail.xhr;
    const statusCode = xhr.status;

    // Check for custom toast header
    const toastMessage = xhr.getResponseHeader('X-Toast-Message');
    const toastType = xhr.getResponseHeader('X-Toast-Type') || 'info';

    if (toastMessage) {
        showToast(toastMessage, toastType);
        return;
    }

    // Default messages based on status code
    if (statusCode >= 200 && statusCode < 300) {
        // Success - only show if explicitly requested
        // (to avoid showing toast on every successful htmx request)
        return;
    } else if (statusCode >= 400 && statusCode < 500) {
        showToast('Request failed. Please check your input and try again.', 'error');
    } else if (statusCode >= 500) {
        showToast('Server error. Please try again later.', 'error');
    }
}

/**
 * Show success toast (convenience function)
 * @param {string} message - The success message
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show error toast (convenience function)
 * @param {string} message - The error message
 */
function showError(message) {
    showToast(message, 'error');
}

/**
 * Show info toast (convenience function)
 * @param {string} message - The info message
 */
function showInfo(message) {
    showToast(message, 'info');
}

// Listen for custom events
document.addEventListener('DOMContentLoaded', function() {
    // Listen for custom toast events
    document.addEventListener('toast', function(e) {
        showToast(e.detail.message, e.detail.type || 'info', e.detail.duration);
    });

    // Optionally handle all htmx errors globally
    document.body.addEventListener('htmx:responseError', function(event) {
        showError('An error occurred. Please try again.');
    });

    document.body.addEventListener('htmx:sendError', function(event) {
        showError('Network error. Please check your connection.');
    });
});
