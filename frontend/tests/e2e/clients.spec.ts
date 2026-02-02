import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAsUser } from './helpers/auth';
import { deleteClient, generateTestId } from './helpers/cleanup';

/**
 * E2E Tests: Client Management
 *
 * Coverage:
 * - Viewing client list
 * - Viewing client details
 * - Adding to favorites
 * - Creating new client (admin)
 * - Editing client (admin)
 *
 * Per Phase 7.11: 5+ tests required
 */

test.describe('Client Management', () => {
  test('should view client list as authenticated user', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to clients page
    await page.goto('/clients');

    // Should see client list
    await expect(page.locator('h1')).toContainText(/clients/i);

    // Should see the baseline "Test Agency" client
    await expect(page.locator('text=Test Agency')).toBeVisible();

    // Should have search functionality
    await expect(page.locator('input[type="search"], input[placeholder*="search"]')).toBeVisible();
  });

  test('should view client details', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to clients page
    await page.goto('/clients');

    // Click on Test Agency
    await page.click('text=Test Agency');

    // Should navigate to client detail page
    await page.waitForURL(/\/clients\/\d+/, { timeout: 10000 });

    // Should see client information
    await expect(page.locator('h1, h2')).toContainText(/Test Agency/i);
    await expect(page.locator('text=/sample agency|description/i')).toBeVisible();

    // Should see associated keywords
    await expect(page.locator('text=infrastructure')).toBeVisible();
    await expect(page.locator('text=budget')).toBeVisible();

    // Should see "Start New Scrape" button
    await expect(page.locator('button, a').filter({ hasText: /start.*scrape|new.*scrape/i })).toBeVisible();
  });

  test('should add and remove client from favorites', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to clients page
    await page.goto('/clients');

    // Add to favorites
    const favoriteButton = page.locator('[data-testid="favorite-button"], button:has-text("Favorite"), .favorite-toggle').first();
    await favoriteButton.click();

    // Should show confirmation (toast or icon change)
    await page.waitForTimeout(500); // Wait for UI update

    // Navigate to favorites page
    await page.goto('/clients/favorites');

    // Should see Test Agency in favorites
    await expect(page.locator('text=Test Agency')).toBeVisible();

    // Remove from favorites
    await page.goto('/clients');
    await favoriteButton.click();

    // Verify removed from favorites
    await page.goto('/clients/favorites');
    await expect(page.locator('text=Test Agency')).not.toBeVisible();
  });

  test('should create new client as admin', async ({ page }) => {
    await loginAsAdmin(page);

    const testId = generateTestId();
    const clientName = `E2E Test Client ${testId}`;

    // Navigate to clients page
    await page.goto('/clients');

    // Click "New Client" button (admin only)
    await page.click('button:has-text("New Client"), a:has-text("New Client")');

    // Should navigate to create form
    await page.waitForURL(/\/clients\/new/, { timeout: 10000 });

    // Fill in client details
    await page.fill('input[name="name"]', clientName);
    await page.fill('textarea[name="description"], input[name="description"]', 'Automated test client for E2E testing');
    await page.fill('input[name="website_url"]', 'https://example.com/test');

    // Associate keywords (multi-select)
    const keywordSelect = page.locator('select[name="keywords"], [data-testid="keyword-select"]');
    if (await keywordSelect.isVisible()) {
      await keywordSelect.selectOption(['infrastructure', 'sustainability']);
    }

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to client list or detail page
    await page.waitForURL(/\/clients/, { timeout: 10000 });

    // Verify client was created
    await page.goto('/clients');
    await expect(page.locator(`text=${clientName}`)).toBeVisible();

    // Cleanup
    await deleteClient(page, clientName);
  });

  test('should edit client as admin', async ({ page }) => {
    await loginAsAdmin(page);

    // First create a client to edit
    const testId = generateTestId();
    const originalName = `E2E Edit Client ${testId}`;
    const updatedName = `E2E Updated Client ${testId}`;

    // Create client
    await page.goto('/clients/new');
    await page.fill('input[name="name"]', originalName);
    await page.fill('textarea[name="description"], input[name="description"]', 'Original description');
    await page.fill('input[name="website_url"]', 'https://example.com/original');
    await page.click('button[type="submit"]');

    // Navigate to clients and find the new client
    await page.goto('/clients');
    await page.click(`text=${originalName}`);

    // Click edit button
    await page.click('[data-testid="edit-client-button"], button:has-text("Edit")');

    // Should navigate to edit form
    await page.waitForURL(/\/clients\/\d+\/edit/, { timeout: 10000 });

    // Update client details
    await page.fill('input[name="name"]', updatedName);
    await page.fill('textarea[name="description"], input[name="description"]', 'Updated description');

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect back to detail or list page
    await page.waitForURL(/\/clients/, { timeout: 10000 });

    // Verify update
    await page.goto('/clients');
    await expect(page.locator(`text=${updatedName}`)).toBeVisible();
    await expect(page.locator(`text=${originalName}`)).not.toBeVisible();

    // Cleanup
    await deleteClient(page, updatedName);
  });

  test('should restrict client creation to admin only', async ({ page }) => {
    await loginAsUser(page); // Login as regular user

    // Navigate to clients page
    await page.goto('/clients');

    // "New Client" button should NOT be visible for regular users
    await expect(page.locator('button:has-text("New Client"), a:has-text("New Client")')).not.toBeVisible();

    // Attempting direct access to create form should be blocked
    await page.goto('/clients/new');

    // Should redirect to 403 forbidden or back to list
    await expect(page).not.toHaveURL(/\/clients\/new/);
  });

  test('should search and filter clients', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to clients page
    await page.goto('/clients');

    // Use search functionality
    const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
    await searchInput.fill('Test Agency');

    // Should filter results
    await expect(page.locator('text=Test Agency')).toBeVisible();

    // Search for non-existent client
    await searchInput.fill('NonExistentClient12345');

    // Should show no results
    await expect(page.locator('text=/no.*results|no.*clients|not.*found/i')).toBeVisible();
  });
});
