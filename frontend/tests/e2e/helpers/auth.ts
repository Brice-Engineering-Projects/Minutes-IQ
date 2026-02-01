import { Page } from '@playwright/test';

/**
 * Authentication helpers for E2E tests
 *
 * Per Phase 7.11: Auth must be tested as a real user (no token injection)
 */

export interface Credentials {
  email: string;
  password: string;
}

/**
 * Baseline test users (seeded in global-setup.ts)
 */
export const TEST_USERS = {
  admin: {
    email: 'admin@test.local',
    password: 'Admin123!',
  },
  user: {
    email: 'user@test.local',
    password: 'User123!',
  },
} as const;

/**
 * Test auth code (seeded in global-setup.ts)
 */
export const TEST_AUTH_CODE = 'E2E-TEST-CODE-2026';

/**
 * Login as a user via the login form
 */
export async function login(page: Page, credentials: Credentials): Promise<void> {
  await page.goto('/login');

  // Fill in credentials
  await page.fill('input[name="email"]', credentials.email);
  await page.fill('input[name="password"]', credentials.password);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard
  await page.waitForURL(/\/dashboard/, { timeout: 10000 });
}

/**
 * Login as admin user
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await login(page, TEST_USERS.admin);
}

/**
 * Login as regular user
 */
export async function loginAsUser(page: Page): Promise<void> {
  await login(page, TEST_USERS.user);
}

/**
 * Logout via navigation menu
 */
export async function logout(page: Page): Promise<void> {
  // Open user dropdown
  await page.click('[data-testid="user-menu"]');

  // Click logout
  await page.click('[data-testid="logout-button"]');

  // Wait for redirect to login
  await page.waitForURL(/\/login/, { timeout: 10000 });
}

/**
 * Register a new user with auth code
 */
export async function register(
  page: Page,
  email: string,
  username: string,
  password: string,
  authCode: string = TEST_AUTH_CODE
): Promise<void> {
  await page.goto('/register');

  // Fill registration form
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.fill('input[name="confirm_password"]', password);
  await page.fill('input[name="auth_code"]', authCode);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for success message or redirect
  await page.waitForURL(/\/login/, { timeout: 10000 });
}

/**
 * Check if user is authenticated (on dashboard page)
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    await page.waitForURL(/\/dashboard/, { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Assert user is redirected to login (auth gating)
 */
export async function expectRedirectToLogin(page: Page): Promise<void> {
  await page.waitForURL(/\/login/, { timeout: 10000 });
}
