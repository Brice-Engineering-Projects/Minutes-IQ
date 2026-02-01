/**
 * Lazy Loading for Images
 *
 * Automatically lazy loads images using the Intersection Observer API
 * Falls back to immediate loading for browsers that don't support it
 *
 * Usage:
 *   <img data-src="path/to/image.jpg" alt="Description" class="lazy">
 *
 * Or with srcset:
 *   <img data-src="image.jpg" data-srcset="image-2x.jpg 2x" alt="Description" class="lazy">
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check for Intersection Observer support
    if ('IntersectionObserver' in window) {
        initLazyLoading();
    } else {
        // Fallback: load all images immediately
        loadAllImages();
    }
});

/**
 * Initialize lazy loading with Intersection Observer
 */
function initLazyLoading() {
    const lazyImages = document.querySelectorAll('img.lazy, iframe.lazy');

    const imageObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const lazyElement = entry.target;
                loadElement(lazyElement);
                lazyElement.classList.remove('lazy');
                imageObserver.unobserve(lazyElement);
            }
        });
    }, {
        // Start loading when image is 50px from viewport
        rootMargin: '50px 0px',
        threshold: 0.01
    });

    lazyImages.forEach(function(lazyElement) {
        imageObserver.observe(lazyElement);
    });

    // Also observe dynamically added images
    observeDynamicImages(imageObserver);
}

/**
 * Load an individual image or iframe
 * @param {HTMLElement} element - The element to load
 */
function loadElement(element) {
    if (element.dataset.src) {
        if (element.tagName === 'IMG') {
            // Handle images
            element.src = element.dataset.src;

            if (element.dataset.srcset) {
                element.srcset = element.dataset.srcset;
            }

            // Add loading class
            element.classList.add('lazy-loading');

            // Remove loading class when loaded
            element.addEventListener('load', function() {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-loaded');
            });

            // Handle load errors
            element.addEventListener('error', function() {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-error');
                console.error('Failed to load image:', element.dataset.src);
            });
        } else if (element.tagName === 'IFRAME') {
            // Handle iframes
            element.src = element.dataset.src;
            element.classList.add('lazy-loaded');
        }
    }
}

/**
 * Fallback: Load all images immediately
 */
function loadAllImages() {
    const lazyElements = document.querySelectorAll('img.lazy, iframe.lazy');
    lazyElements.forEach(function(element) {
        loadElement(element);
        element.classList.remove('lazy');
    });
}

/**
 * Observe dynamically added images (e.g., from htmx)
 * @param {IntersectionObserver} observer - The observer instance
 */
function observeDynamicImages(observer) {
    // Listen for htmx content swaps
    document.body.addEventListener('htmx:afterSwap', function(event) {
        const newLazyElements = event.detail.target.querySelectorAll('img.lazy, iframe.lazy');
        newLazyElements.forEach(function(element) {
            observer.observe(element);
        });
    });

    // Also use MutationObserver for other dynamic content
    const mutationObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    // Check if node itself is lazy
                    if (node.classList && node.classList.contains('lazy')) {
                        observer.observe(node);
                    }
                    // Check for lazy children
                    const lazyChildren = node.querySelectorAll && node.querySelectorAll('img.lazy, iframe.lazy');
                    if (lazyChildren) {
                        lazyChildren.forEach(function(child) {
                            observer.observe(child);
                        });
                    }
                }
            });
        });
    });

    mutationObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
}

/**
 * Helper function to manually trigger lazy loading for specific elements
 * Useful for images added via JavaScript
 * @param {HTMLElement|string} elementOrSelector - Element or CSS selector
 */
function triggerLazyLoad(elementOrSelector) {
    const elements = typeof elementOrSelector === 'string'
        ? document.querySelectorAll(elementOrSelector)
        : [elementOrSelector];

    elements.forEach(function(element) {
        if (element && element.classList.contains('lazy')) {
            loadElement(element);
            element.classList.remove('lazy');
        }
    });
}

// Expose for global use
window.triggerLazyLoad = triggerLazyLoad;


/**
 * Add CSS for lazy loading states
 */
(function addLazyLoadingCSS() {
    const style = document.createElement('style');
    style.textContent = `
        /* Lazy loading states */
        img.lazy {
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
        }

        img.lazy-loading {
            opacity: 0.5;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading-shimmer 1.5s infinite;
        }

        img.lazy-loaded {
            opacity: 1;
        }

        img.lazy-error {
            opacity: 1;
            background: #fee;
            border: 2px dashed #fcc;
        }

        @keyframes loading-shimmer {
            0% {
                background-position: 200% 0;
            }
            100% {
                background-position: -200% 0;
            }
        }

        /* Placeholder for lazy images */
        img.lazy[data-src]:not([src]) {
            background: #f3f4f6;
            min-height: 200px;
        }

        /* Aspect ratio preservation */
        img.lazy.aspect-16-9 {
            aspect-ratio: 16 / 9;
        }

        img.lazy.aspect-4-3 {
            aspect-ratio: 4 / 3;
        }

        img.lazy.aspect-1-1 {
            aspect-ratio: 1 / 1;
        }
    `;
    document.head.appendChild(style);
})();
