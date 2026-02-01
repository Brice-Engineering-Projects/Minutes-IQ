/**
 * Accessibility Enhancements
 *
 * This file provides accessibility improvements including:
 * - Skip to main content link
 * - Focus management for modals and dynamic content
 * - Keyboard navigation helpers
 * - ARIA live region updates
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add skip-to-main link if not present
    addSkipLink();

    // Trap focus in modals
    setupModalFocusTrap();

    // Enhance keyboard navigation
    enhanceKeyboardNavigation();

    // Setup ARIA live regions for htmx updates
    setupAriaLiveRegions();

    // Add focus indicators for keyboard navigation
    addFocusIndicators();
});

/**
 * Add skip-to-main-content link for keyboard users
 */
function addSkipLink() {
    if (document.querySelector('.skip-link')) return; // Already exists

    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded';
    skipLink.textContent = 'Skip to main content';
    skipLink.setAttribute('tabindex', '0');

    document.body.insertBefore(skipLink, document.body.firstChild);

    // Ensure main content has ID
    const mainContent = document.querySelector('main') || document.querySelector('[role="main"]');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
        mainContent.setAttribute('tabindex', '-1'); // Make focusable programmatically
    }
}

/**
 * Trap focus inside modals when open
 */
function setupModalFocusTrap() {
    document.addEventListener('click', function(e) {
        const modal = e.target.closest('[role="dialog"]');
        if (!modal) return;

        const focusableElements = modal.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // Focus first element when modal opens
        setTimeout(() => firstElement.focus(), 100);

        // Trap focus
        modal.addEventListener('keydown', function trapFocus(e) {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    });
}

/**
 * Enhance keyboard navigation
 */
function enhanceKeyboardNavigation() {
    // Escape key closes modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close any open modals
            const openModals = document.querySelectorAll('[role="dialog"]:not(.hidden)');
            openModals.forEach(modal => {
                modal.classList.add('hidden');

                // Return focus to trigger element if stored
                if (modal.dataset.triggerElement) {
                    const trigger = document.querySelector(modal.dataset.triggerElement);
                    if (trigger) trigger.focus();
                }
            });

            // Close dropdowns
            const openDropdowns = document.querySelectorAll('[x-data]');
            openDropdowns.forEach(dropdown => {
                if (dropdown.__x) {
                    dropdown.__x.$data.open = false;
                }
            });
        }
    });

    // Enter/Space activates buttons and links
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            const target = e.target;
            if (target.getAttribute('role') === 'button' && target.tagName !== 'BUTTON') {
                e.preventDefault();
                target.click();
            }
        }
    });
}

/**
 * Setup ARIA live regions for dynamic content updates
 */
function setupAriaLiveRegions() {
    // Add live region for htmx updates if not present
    if (!document.getElementById('aria-live-region')) {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'aria-live-region';
        liveRegion.className = 'sr-only';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        document.body.appendChild(liveRegion);
    }

    // Announce htmx content swaps
    document.body.addEventListener('htmx:afterSwap', function(event) {
        const liveRegion = document.getElementById('aria-live-region');
        if (!liveRegion) return;

        // Check if swap includes a table or list
        const target = event.detail.target;
        if (target.querySelector('table')) {
            liveRegion.textContent = 'Table updated';
        } else if (target.querySelector('ul, ol')) {
            liveRegion.textContent = 'List updated';
        } else if (target.querySelector('form')) {
            liveRegion.textContent = 'Form updated';
        } else {
            liveRegion.textContent = 'Content updated';
        }

        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    });

    // Announce loading states
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        const liveRegion = document.getElementById('aria-live-region');
        if (liveRegion) {
            liveRegion.textContent = 'Loading...';
        }
    });
}

/**
 * Add visible focus indicators for keyboard users
 */
function addFocusIndicators() {
    // Detect if user is using keyboard
    let usingKeyboard = false;

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            usingKeyboard = true;
            document.body.classList.add('keyboard-nav');
        }
    });

    document.addEventListener('mousedown', function() {
        usingKeyboard = false;
        document.body.classList.remove('keyboard-nav');
    });

    // Add CSS for keyboard navigation
    const style = document.createElement('style');
    style.textContent = `
        /* Enhanced focus indicators for keyboard navigation */
        .keyboard-nav *:focus {
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }

        .keyboard-nav button:focus,
        .keyboard-nav a:focus,
        .keyboard-nav input:focus,
        .keyboard-nav select:focus,
        .keyboard-nav textarea:focus {
            ring: 2px !important;
            ring-color: #3b82f6 !important;
            ring-offset: 2px !important;
        }

        /* Screen reader only text */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }

        .focus\\:not-sr-only:focus {
            position: static;
            width: auto;
            height: auto;
            padding: inherit;
            margin: inherit;
            overflow: visible;
            clip: auto;
            white-space: normal;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Announce page navigation to screen readers
 * Call this function when navigating to a new page
 * @param {string} pageName - Name of the new page
 */
function announcePageNavigation(pageName) {
    const liveRegion = document.getElementById('aria-live-region');
    if (liveRegion) {
        liveRegion.textContent = `Navigated to ${pageName}`;
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 2000);
    }
}

/**
 * Make an element announce its content to screen readers
 * @param {HTMLElement} element - The element to announce
 * @param {string} message - Optional custom message
 */
function announceElement(element, message = null) {
    const liveRegion = document.getElementById('aria-live-region');
    if (!liveRegion) return;

    const text = message || element.textContent.trim();
    liveRegion.textContent = text;

    setTimeout(() => {
        liveRegion.textContent = '';
    }, 2000);
}

// Export functions for global use
window.announcePageNavigation = announcePageNavigation;
window.announceElement = announceElement;
