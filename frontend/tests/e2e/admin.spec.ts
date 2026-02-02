import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAsUser } from './helpers/auth';
import { generateTestId } from './helpers/cleanup';

/**
 * E2E Tests: Admin Panel
 *
 * Coverage:
 * - User management
 * - Auth code generation
 * - Storage cleanup
 * - Admin access control (role-based gating)
 * - Admin dashboard statistics
 *
 * Per Phase 7.11: 5+ tests required
 */

test.describe('Admin Panel', () => {
  test('should access admin dashboard as admin', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to admin panel
    await page.goto('/admin');

    // Should see admin dashboard
    await expect(page.locator('h1')).toContainText(/admin/i);

    // Should see system statistics
    await expect(page.locator('text=/total.*users|users.*count/i')).toBeVisible();
    await expect(page.locator('text=/total.*clients|clients.*count/i')).toBeVisible();
    await expect(page.locator('text=/total.*keywords|keywords.*count/i')).toBeVisible();

    // Should see quick links to admin functions
    await expect(page.locator('a:has-text("User Management"), a:has-text("Users")')).toBeVisible();
    await expect(page.locator('a:has-text("Auth Codes"), a:has-text("Authorization")')).toBeVisible();
  });

  test('should restrict admin panel access to admin role only', async ({ page }) => {
    await loginAsUser(page); // Login as regular user

    // Attempt to access admin panel
    await page.goto('/admin');

    // Should be redirected or show 403 forbidden
    await expect(page).not.toHaveURL(/\/admin$/);

    // Should show access denied message or redirect to dashboard
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/dashboard|\/login|\/403/);
  });

  test('should manage users (view user list)', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to user management
    await page.goto('/admin/users');

    // Should see user list
    await expect(page.locator('h1, h2')).toContainText(/users|user.*management/i);

    // Should see baseline test users
    await expect(page.locator('text=admin@test.local')).toBeVisible();
    await expect(page.locator('text=user@test.local')).toBeVisible();

    // Should have search/filter functionality
    const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('admin@test.local');
      await expect(page.locator('text=admin@test.local')).toBeVisible();
    }

    // Should show user roles
    await expect(page.locator('text=/admin|user/i')).toBeVisible();

    // Should show user status (active/inactive)
    await expect(page.locator('text=/active|inactive/i')).toBeVisible();
  });

  test('should generate authorization code', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to auth codes management
    await page.goto('/admin/auth-codes');

    // Should see auth codes list
    await expect(page.locator('h1, h2')).toContainText(/auth.*codes|authorization/i);

    // Click "Generate New Code" button
    await page.click('button:has-text("Generate"), button:has-text("New Code"), [data-testid="generate-code"]');

    // Should see form or modal for code generation
    // Fill in code parameters (if form exists)
    const maxUsesInput = page.locator('input[name="max_uses"]');
    if (await maxUsesInput.isVisible()) {
      await maxUsesInput.fill('5');
    }

    const expiresInDays = page.locator('input[name="expires_in_days"]');
    if (await expiresInDays.isVisible()) {
      await expiresInDays.fill('30');
    }

    // Submit
    const submitButton = page.locator('button[type="submit"], button:has-text("Generate")');
    await submitButton.click();

    // Should show generated code
    await expect(page.locator('text=/code.*generated|success/i')).toBeVisible();

    // Should see new code in list with copy button
    const copyButton = page.locator('button:has-text("Copy"), [data-testid="copy-code"]').first();
    await expect(copyButton).toBeVisible();
  });

  test('should view and revoke authorization codes', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to auth codes
    await page.goto('/admin/auth-codes');

    // Should see existing codes (including baseline test code)
    await expect(page.locator('text=E2E-TEST-CODE-2026')).toBeVisible();

    // Find an active code and revoke it
    const revokeButton = page.locator('button:has-text("Revoke"), [data-testid="revoke-code"]').first();

    if (await revokeButton.isVisible()) {
      await revokeButton.click();

      // Confirm revocation
      const confirmButton = page.locator('button:has-text("Confirm"), [data-testid="confirm-revoke"]');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }

      // Should show success message
      await expect(page.locator('text=/revoked|success/i')).toBeVisible();

      // Code status should change to revoked/inactive
      await expect(page.locator('text=/revoked|inactive/i')).toBeVisible();
    }
  });

  test('should view storage cleanup information', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to storage cleanup
    await page.goto('/admin/cleanup');

    // Should see storage usage information
    await expect(page.locator('h1, h2')).toContainText(/storage|cleanup/i);

    // Should see storage usage metrics
    await expect(page.locator('text=/storage.*used|disk.*space/i')).toBeVisible();

    // Should see list of old jobs or files
    const oldJobsList = page.locator('text=/old.*jobs|cleanup.*candidates/i');
    if (await oldJobsList.isVisible()) {
      // Should have bulk cleanup button
      const bulkCleanupButton = page.locator('button:has-text("Cleanup"), button:has-text("Delete Old Files")');
      await expect(bulkCleanupButton).toBeVisible();
    }
  });

  test('should show admin-only navigation items', async ({ page }) => {
    await loginAsAdmin(page);

    await page.goto('/dashboard');

    // Should see admin menu item in navigation
    const adminNavItem = page.locator('nav a:has-text("Admin"), [data-testid="admin-nav-link"]');
    await expect(adminNavItem).toBeVisible();

    // Logout and login as regular user
    await page.goto('/login');
    await loginAsUser(page);
    await page.goto('/dashboard');

    // Admin menu item should NOT be visible for regular users
    await expect(adminNavItem).not.toBeVisible();
  });

  test('should view usage statistics for auth codes', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to auth codes
    await page.goto('/admin/auth-codes');

    // Click on a code to view details
    await page.click('text=E2E-TEST-CODE-2026');

    // Should show usage history
    await expect(page.locator('h2, h3').filter({ hasText: /usage|history/i })).toBeVisible();

    // Should show:
    // - Times used
    // - Max uses
    // - Users who registered with this code
    await expect(page.locator('text=/used|max.*uses/i')).toBeVisible();
  });

  test('should update user role (admin capability)', async ({ page }) => {
    await loginAsAdmin(page);

    // Create a test user first (via registration or direct creation)
    const testId = generateTestId();
    const testEmail = `roletest-${testId}@test.local`;

    // Navigate to user management
    await page.goto('/admin/users');

    // Find the test user (assuming it exists from previous tests)
    // Or create one via registration first

    // Click on user to view details
    const userRow = page.locator('tr:has-text("user@test.local")').first();
    if (await userRow.isVisible()) {
      await userRow.click();

      // Look for "Edit" or "Change Role" button
      const editButton = page.locator('button:has-text("Edit"), a:has-text("Edit"), [data-testid="edit-user"]');

      if (await editButton.isVisible()) {
        await editButton.click();

        // Change role
        const roleSelect = page.locator('select[name="role"]');
        if (await roleSelect.isVisible()) {
          const currentRole = await roleSelect.inputValue();

          // Toggle role (if user, make admin; if admin, make user)
          const newRole = currentRole === 'admin' ? 'user' : 'admin';
          await roleSelect.selectOption(newRole);

          // Save changes
          await page.click('button[type="submit"], button:has-text("Save")');

          // Should show success message
          await expect(page.locator('text=/updated|success/i')).toBeVisible();
        }
      }
    }
  });
});
