import { defineConfig, devices } from '@playwright/test';

/**
 * E2E Test Configuration for Minutes IQ Platform
 *
 * Per Phase 7.11 instructions:
 * - Chromium only initially (browser-agnostic design)
 * - Dedicated test database
 * - Tests must be repeatable and self-contained
 */
export default defineConfig({
  testDir: './tests/e2e',

  // Timeouts
  timeout: 30 * 1000, // 30 seconds per test
  expect: {
    timeout: 5000, // 5 seconds for assertions
  },

  // Test execution settings
  fullyParallel: true, // Run tests in parallel
  forbidOnly: !!process.env.CI, // Fail CI if test.only is used
  retries: process.env.CI ? 2 : 0, // Retry twice on CI
  workers: process.env.CI ? 1 : undefined, // Limit workers in CI

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'], // Console output
    process.env.CI ? ['github'] : ['null'], // GitHub Actions annotations
  ],

  // Shared settings for all tests
  use: {
    // Base URL for tests
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:8000',

    // Browser behavior
    trace: 'on-first-retry', // Capture trace on first retry
    screenshot: 'only-on-failure', // Screenshot on failure
    video: 'retain-on-failure', // Video on failure

    // Timeouts
    actionTimeout: 10 * 1000, // 10 seconds for actions
    navigationTimeout: 30 * 1000, // 30 seconds for navigation
  },

  // Projects - Chromium only initially
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Mobile viewport for responsive tests
    {
      name: 'mobile-chromium',
      use: { ...devices['Pixel 5'] },
    },

    // Future expansion (commented out per Phase 7.11)
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Dev server configuration (optional - for local testing)
  // Uncomment if you want Playwright to start the server
  // webServer: {
  //   command: 'uvicorn src.main:app --host 0.0.0.0 --port 8000',
  //   url: 'http://localhost:8000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },
});
