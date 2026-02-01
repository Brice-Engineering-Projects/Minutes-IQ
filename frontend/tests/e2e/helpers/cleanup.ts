import { Page } from '@playwright/test';

/**
 * Cleanup helpers for E2E tests
 *
 * Per Phase 7.11: Tests must create and cleanup additional data within each test
 */

/**
 * Delete a client (admin only)
 */
export async function deleteClient(page: Page, clientName: string): Promise<void> {
  // Navigate to clients list
  await page.goto('/clients');

  // Find and click the client
  await page.click(`text=${clientName}`);

  // Click delete button (admin only)
  await page.click('[data-testid="delete-client-button"]');

  // Confirm deletion
  await page.click('[data-testid="confirm-delete-button"]');

  // Wait for redirect back to list
  await page.waitForURL(/\/clients$/, { timeout: 10000 });
}

/**
 * Delete a keyword (admin only)
 */
export async function deleteKeyword(page: Page, keyword: string): Promise<void> {
  // Navigate to keywords list
  await page.goto('/keywords');

  // Find and click the keyword
  await page.click(`text=${keyword}`);

  // Click delete button (admin only)
  await page.click('[data-testid="delete-keyword-button"]');

  // Confirm deletion
  await page.click('[data-testid="confirm-delete-button"]');

  // Wait for redirect back to list
  await page.waitForURL(/\/keywords$/, { timeout: 10000 });
}

/**
 * Delete a scrape job
 */
export async function deleteScrapeJob(page: Page, jobId: string): Promise<void> {
  // Navigate to job details
  await page.goto(`/scraper/jobs/${jobId}`);

  // Click delete button
  await page.click('[data-testid="delete-job-button"]');

  // Confirm deletion
  await page.click('[data-testid="confirm-delete-button"]');

  // Wait for redirect to jobs list
  await page.waitForURL(/\/scraper\/jobs$/, { timeout: 10000 });
}

/**
 * Cancel a running scrape job
 */
export async function cancelScrapeJob(page: Page, jobId: string): Promise<void> {
  // Navigate to job details
  await page.goto(`/scraper/jobs/${jobId}`);

  // Click cancel button
  await page.click('[data-testid="cancel-job-button"]');

  // Confirm cancellation
  await page.click('[data-testid="confirm-cancel-button"]');

  // Wait for status update
  await page.waitForSelector('text=cancelled', { timeout: 10000 });
}

/**
 * Generate a unique test identifier (for creating unique test data)
 */
export function generateTestId(): string {
  return `test-${Date.now()}-${Math.random().toString(36).substring(7)}`;
}

/**
 * Wait for a specific job status
 */
export async function waitForJobStatus(
  page: Page,
  jobId: string,
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled',
  timeoutMs: number = 30000
): Promise<void> {
  await page.goto(`/scraper/jobs/${jobId}`);

  // Poll for status
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    // Reload to get fresh status
    await page.reload();

    // Check for status badge
    const statusElement = await page.locator(`[data-testid="job-status"]`).textContent();
    if (statusElement?.toLowerCase().includes(status)) {
      return;
    }

    // Wait before next poll
    await page.waitForTimeout(2000);
  }

  throw new Error(`Job ${jobId} did not reach status ${status} within ${timeoutMs}ms`);
}
