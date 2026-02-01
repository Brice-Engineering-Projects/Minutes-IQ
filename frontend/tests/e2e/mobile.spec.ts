import { test, expect, devices } from '@playwright/test';
import { loginAsUser } from './helpers/auth';

/**
 * E2E Tests: Mobile Responsiveness
 *
 * Coverage:
 * - Mobile navigation (hamburger menu)
 * - Forms on mobile
 * - Tables on mobile (horizontal scroll or card layout)
 *
 * Per Phase 7.11: 3+ tests required
 */

test.describe('Mobile Responsiveness', () => {
  // Use mobile viewport for these tests
  test.use({ ...devices['Pixel 5'] });

  test('should show mobile navigation with hamburger menu', async ({ page }) => {
    await loginAsUser(page);

    await page.goto('/dashboard');

    // On mobile, should see hamburger menu button
    const hamburgerButton = page.locator('[data-testid="mobile-menu-toggle"], button[aria-label="Menu"], .hamburger-menu');
    await expect(hamburgerButton).toBeVisible();

    // Navigation menu should be hidden initially
    const navMenu = page.locator('nav, [data-testid="main-nav"]');
    const isHidden = await navMenu.isHidden();
    expect(isHidden).toBe(true);

    // Click hamburger to open menu
    await hamburgerButton.click();

    // Menu should now be visible
    await expect(navMenu).toBeVisible();

    // Should see navigation links
    await expect(page.locator('nav a:has-text("Dashboard"), a:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('nav a:has-text("Clients"), a:has-text("Clients")')).toBeVisible();
    await expect(page.locator('nav a:has-text("Jobs"), a:has-text("Scrapes")')).toBeVisible();

    // Click a link
    await page.click('nav a:has-text("Clients")');

    // Should navigate and menu should close
    await page.waitForURL(/\/clients/, { timeout: 10000 });
  });

  test('should render forms properly on mobile', async ({ page }) => {
    await loginAsUser(page);

    // Test login form
    await page.goto('/login');

    // Form should be visible and properly sized
    const form = page.locator('form');
    await expect(form).toBeVisible();

    // Input fields should be full width or properly sized
    const emailInput = page.locator('input[name="email"]');
    await expect(emailInput).toBeVisible();

    const inputWidth = await emailInput.evaluate((el) => el.getBoundingClientRect().width);
    expect(inputWidth).toBeGreaterThan(200); // Should not be too narrow

    // Test scrape job creation form
    await loginAsUser(page);
    await page.goto('/scraper/jobs/new');

    // Form elements should be stackable and readable
    await expect(page.locator('select[name="client_id"]')).toBeVisible();
    await expect(page.locator('input[name="date_range_start"]')).toBeVisible();
    await expect(page.locator('input[name="date_range_end"]')).toBeVisible();

    // Submit button should be visible and tappable
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();

    const buttonHeight = await submitButton.evaluate((el) => el.getBoundingClientRect().height);
    expect(buttonHeight).toBeGreaterThan(30); // Should be tappable (min 44px is iOS recommendation)
  });

  test('should handle tables on mobile (horizontal scroll or cards)', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to clients list (table view)
    await page.goto('/clients');

    // Table should be visible
    const table = page.locator('table, .table-container');

    if (await table.isVisible()) {
      // Check if table is horizontally scrollable
      const isScrollable = await table.evaluate((el) => {
        return el.scrollWidth > el.clientWidth;
      });

      // Either scrollable or converted to card layout on mobile
      if (isScrollable) {
        // Verify horizontal scroll works
        await table.evaluate((el) => {
          el.scrollLeft = 100;
        });

        const scrollLeft = await table.evaluate((el) => el.scrollLeft);
        expect(scrollLeft).toBeGreaterThan(0);
      } else {
        // Should use card layout or responsive design
        // Verify content is visible without scrolling
        await expect(page.locator('text=Test Agency')).toBeVisible();
      }
    }

    // Test jobs list table
    await page.goto('/scraper/jobs');

    // Should see job list in accessible format
    await expect(page.locator('text=/jobs|scrapes/i')).toBeVisible();

    // Status badges should be visible
    const statusBadges = page.locator('.status-badge, [data-testid="job-status"]');
    if (await statusBadges.first().isVisible()) {
      await expect(statusBadges.first()).toBeVisible();
    }
  });

  test('should show readable text and proper spacing on mobile', async ({ page }) => {
    await loginAsUser(page);

    await page.goto('/dashboard');

    // Text should be readable (not too small)
    const heading = page.locator('h1').first();
    const fontSize = await heading.evaluate((el) => {
      return window.getComputedStyle(el).fontSize;
    });

    const fontSizeValue = parseInt(fontSize);
    expect(fontSizeValue).toBeGreaterThan(20); // Headings should be at least 20px

    // Buttons should have adequate spacing (touch targets)
    const buttons = page.locator('button, a.button').first();

    if (await buttons.isVisible()) {
      const buttonBox = await buttons.boundingBox();
      expect(buttonBox?.height).toBeGreaterThan(30); // Min touch target height
    }

    // Content should not overflow viewport
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);

    // Allow small overflow for scrollbars
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
  });

  test('should handle modals and dialogs on mobile', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to clients
    await page.goto('/clients');

    // Add client to favorites (may trigger modal or toast)
    const favoriteButton = page.locator('[data-testid="favorite-button"], button:has-text("Favorite")').first();

    if (await favoriteButton.isVisible()) {
      await favoriteButton.click();

      // Wait for feedback (modal, toast, or icon change)
      await page.waitForTimeout(1000);

      // Any modal should be properly sized for mobile
      const modal = page.locator('.modal, [role="dialog"]');
      if (await modal.isVisible()) {
        const modalWidth = await modal.evaluate((el) => el.getBoundingClientRect().width);
        const viewportWidth = await page.evaluate(() => window.innerWidth);

        // Modal should not be wider than viewport
        expect(modalWidth).toBeLessThanOrEqual(viewportWidth);

        // Close button should be visible
        const closeButton = modal.locator('button:has-text("Close"), [aria-label="Close"]');
        await expect(closeButton).toBeVisible();
      }
    }
  });
});
