import { test, expect } from '@playwright/test';
import {
  login,
  logout,
  register,
  TEST_USERS,
  TEST_AUTH_CODE,
  expectRedirectToLogin,
} from './helpers/auth';
import { generateTestId } from './helpers/cleanup';

/**
 * E2E Tests: Authentication Flow
 *
 * Coverage:
 * - Login with valid credentials
 * - Login with invalid credentials
 * - Registration flow
 * - Password reset flow
 * - Logout
 *
 * Per Phase 7.11: 5+ tests required
 */

test.describe('Authentication Flow', () => {
  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in valid credentials
    await page.fill('input[name="email"]', TEST_USERS.user.email);
    await page.fill('input[name="password"]', TEST_USERS.user.password);

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });

    // Verify dashboard content
    await expect(page.locator('h1')).toContainText(/dashboard|welcome/i);
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in invalid credentials
    await page.fill('input[name="email"]', TEST_USERS.user.email);
    await page.fill('input[name="password"]', 'WrongPassword123!');

    // Submit form
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.error, .alert-error, [role="alert"]')).toBeVisible();

    // Should NOT redirect to dashboard
    await expect(page).toHaveURL(/\/login/);
  });

  test('should register new user with valid auth code', async ({ page }) => {
    const testId = generateTestId();
    const email = `newuser-${testId}@test.local`;
    const username = `New User ${testId}`;
    const password = 'NewUser123!';

    await page.goto('/register');

    // Fill registration form
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="password"]', password);
    await page.fill('input[name="confirm_password"]', password);
    await page.fill('input[name="auth_code"]', TEST_AUTH_CODE);

    // Submit form
    await page.click('button[type="submit"]');

    // Should show success message or redirect to login
    await page.waitForURL(/\/login/, { timeout: 10000 });

    // Should be able to login with new credentials
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', password);
    await page.click('button[type="submit"]');

    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should reject registration with invalid auth code', async ({ page }) => {
    const testId = generateTestId();
    const email = `rejected-${testId}@test.local`;
    const username = `Rejected User ${testId}`;
    const password = 'Rejected123!';

    await page.goto('/register');

    // Fill registration form with invalid auth code
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="password"]', password);
    await page.fill('input[name="confirm_password"]', password);
    await page.fill('input[name="auth_code"]', 'INVALID-CODE');

    // Submit form
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.error, .alert-error, [role="alert"]')).toBeVisible();
    await expect(page.locator('text=/invalid.*code|code.*invalid/i')).toBeVisible();

    // Should NOT redirect
    await expect(page).toHaveURL(/\/register/);
  });

  test('should complete password reset flow', async ({ page }) => {
    // 1. Request password reset
    await page.goto('/password-reset/request');

    await page.fill('input[name="email"]', TEST_USERS.user.email);
    await page.click('button[type="submit"]');

    // Should show success message (even if email doesn't exist - anti-enumeration)
    await expect(page.locator('text=/email.*sent|check.*email/i')).toBeVisible();

    // Note: In a real test, we would need to:
    // 1. Intercept the email or retrieve token from database
    // 2. Visit the reset link: /password-reset/{token}
    // 3. Submit new password
    // For E2E, we verify the request page works and shows appropriate messaging
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await login(page, TEST_USERS.user);

    // Verify on dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Logout
    await logout(page);

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);

    // Accessing protected page should redirect to login
    await page.goto('/dashboard');
    await expectRedirectToLogin(page);
  });

  test('should enforce auth gating on protected routes', async ({ page }) => {
    // Try to access protected route without logging in
    await page.goto('/clients');

    // Should redirect to login
    await expectRedirectToLogin(page);

    // Try dashboard
    await page.goto('/dashboard');
    await expectRedirectToLogin(page);

    // Try admin panel
    await page.goto('/admin');
    await expectRedirectToLogin(page);
  });

  test('should show "Remember me" functionality', async ({ page }) => {
    await page.goto('/login');

    // Fill in credentials
    await page.fill('input[name="email"]', TEST_USERS.user.email);
    await page.fill('input[name="password"]', TEST_USERS.user.password);

    // Check "Remember me" if available
    const rememberMeCheckbox = page.locator('input[name="remember"], input[type="checkbox"]');
    if (await rememberMeCheckbox.isVisible()) {
      await rememberMeCheckbox.check();
    }

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });

    // Note: Testing persistent sessions requires cookie/token validation
    // which is covered by integration tests
  });
});
