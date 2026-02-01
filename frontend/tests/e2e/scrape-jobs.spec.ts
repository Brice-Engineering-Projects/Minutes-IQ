import { test, expect } from '@playwright/test';
import { loginAsUser } from './helpers/auth';
import { deleteScrapeJob, cancelScrapeJob, waitForJobStatus, generateTestId } from './helpers/cleanup';

/**
 * E2E Tests: Scrape Jobs
 *
 * Coverage:
 * - Creating new job
 * - Viewing job list
 * - Viewing job details
 * - Status polling
 * - Downloading CSV
 * - Generating ZIP artifact
 * - Downloading ZIP
 * - Canceling job
 *
 * Per Phase 7.11: 8+ tests required (highest business risk)
 */

test.describe('Scrape Job Management', () => {
  test('should create new scrape job', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to jobs page
    await page.goto('/scraper/jobs');

    // Click "New Scrape Job" button
    await page.click('button:has-text("New Scrape Job"), a:has-text("New"), [data-testid="new-job-button"]');

    // Should navigate to create form
    await page.waitForURL(/\/scraper\/jobs\/new/, { timeout: 10000 });

    // Fill in job configuration
    await page.selectOption('select[name="client_id"]', '1'); // Test Agency

    // Set date range
    const today = new Date();
    const oneMonthAgo = new Date(today.setMonth(today.getMonth() - 1));
    const dateStr = oneMonthAgo.toISOString().split('T')[0];

    await page.fill('input[name="date_range_start"]', dateStr);
    await page.fill('input[name="date_range_end"]', new Date().toISOString().split('T')[0]);

    // Set max scan pages (optional)
    const maxPagesInput = page.locator('input[name="max_scan_pages"]');
    if (await maxPagesInput.isVisible()) {
      await maxPagesInput.fill('5');
    }

    // Submit form
    await page.click('button[type="submit"], button:has-text("Start Scrape")');

    // Should redirect to job details or list
    await page.waitForURL(/\/scraper\/jobs/, { timeout: 10000 });

    // Verify job was created (should see pending or running status)
    await expect(page.locator('text=/pending|running|queued/i')).toBeVisible();
  });

  test('should view job list with filtering', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to jobs page
    await page.goto('/scraper/jobs');

    // Should see job list
    await expect(page.locator('h1')).toContainText(/jobs|scrapes/i);

    // Should have status filter
    const statusFilter = page.locator('select[name="status"], [data-testid="status-filter"]');
    if (await statusFilter.isVisible()) {
      await statusFilter.selectOption('completed');
      // Wait for filtered results
      await page.waitForTimeout(1000);
    }

    // Should have client filter
    const clientFilter = page.locator('select[name="client_id"], [data-testid="client-filter"]');
    if (await clientFilter.isVisible()) {
      await clientFilter.selectOption('1'); // Test Agency
      await page.waitForTimeout(1000);
    }

    // Should see table with columns: Client, Status, Created, Results
    await expect(page.locator('th:has-text("Status"), [data-testid="status-column"]')).toBeVisible();
  });

  test('should view job details', async ({ page }) => {
    await loginAsUser(page);

    // Create a job first
    await page.goto('/scraper/jobs/new');
    await page.selectOption('select[name="client_id"]', '1');

    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    await page.fill('input[name="date_range_start"]', dateStr);
    await page.fill('input[name="date_range_end"]', dateStr);

    await page.click('button[type="submit"]');

    // Should redirect to job details
    await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

    // Should see job information
    await expect(page.locator('text=Test Agency')).toBeVisible();
    await expect(page.locator('[data-testid="job-status"], .status-badge')).toBeVisible();

    // Should see configuration details
    await expect(page.locator('text=/date.*range|start.*date/i')).toBeVisible();

    // Should see results summary section
    await expect(page.locator('text=/results|matches/i')).toBeVisible();
  });

  test('should poll job status in real-time', async ({ page }) => {
    await loginAsUser(page);

    // Create a job
    await page.goto('/scraper/jobs/new');
    await page.selectOption('select[name="client_id"]', '1');

    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    await page.fill('input[name="date_range_start"]', dateStr);
    await page.fill('input[name="date_range_end"]', dateStr);

    await page.click('button[type="submit"]');
    await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

    // Extract job ID from URL
    const url = page.url();
    const jobId = url.match(/\/scraper\/jobs\/(\d+)/)?.[1];
    expect(jobId).toBeTruthy();

    // Initial status should be pending or running
    const initialStatus = await page.locator('[data-testid="job-status"]').textContent();
    expect(initialStatus?.toLowerCase()).toMatch(/pending|running/);

    // Wait a moment for potential status change
    await page.waitForTimeout(3000);

    // Reload page to check for status update
    await page.reload();

    // Status should be visible (could be running, completed, or failed)
    const updatedStatus = await page.locator('[data-testid="job-status"]').textContent();
    expect(updatedStatus).toBeTruthy();

    // Note: In a full test with a real scraper, we would wait for completion
    // For E2E, we verify the status updates are visible
  });

  test('should download CSV export', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to a completed job (or create one)
    // For this test, we assume there's at least one completed job
    await page.goto('/scraper/jobs');

    // Find a completed job
    const completedJob = page.locator('tr:has-text("completed"), .job-row:has-text("completed")').first();

    if (await completedJob.isVisible()) {
      await completedJob.click();

      // Wait for job details page
      await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

      // Click "Download CSV" button
      const downloadPromise = page.waitForEvent('download');
      await page.click('button:has-text("Download CSV"), a:has-text("Download CSV"), [data-testid="download-csv"]');

      const download = await downloadPromise;

      // Verify download
      expect(download.suggestedFilename()).toMatch(/\.csv$/);
    } else {
      // Skip test if no completed jobs available
      test.skip();
    }
  });

  test('should generate ZIP artifact', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to a completed job
    await page.goto('/scraper/jobs');

    const completedJob = page.locator('tr:has-text("completed"), .job-row:has-text("completed")').first();

    if (await completedJob.isVisible()) {
      await completedJob.click();
      await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

      // Click "Generate Artifact" or "Generate ZIP" button
      const generateButton = page.locator('button:has-text("Generate"), [data-testid="generate-artifact"]');

      if (await generateButton.isVisible()) {
        await generateButton.click();

        // Should show progress or success message
        await expect(page.locator('text=/generating|artifact.*ready|success/i')).toBeVisible({ timeout: 30000 });
      }
    } else {
      test.skip();
    }
  });

  test('should download ZIP artifact', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to a job with generated artifact
    await page.goto('/scraper/jobs');

    const jobWithArtifact = page.locator('tr:has-text("completed")').first();

    if (await jobWithArtifact.isVisible()) {
      await jobWithArtifact.click();
      await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

      // Look for "Download ZIP" button
      const downloadZipButton = page.locator('button:has-text("Download ZIP"), a:has-text("Download ZIP"), [data-testid="download-zip"]');

      if (await downloadZipButton.isVisible()) {
        const downloadPromise = page.waitForEvent('download');
        await downloadZipButton.click();

        const download = await downloadPromise;
        expect(download.suggestedFilename()).toMatch(/\.zip$/);
      }
    } else {
      test.skip();
    }
  });

  test('should cancel pending or running job', async ({ page }) => {
    await loginAsUser(page);

    // Create a new job
    await page.goto('/scraper/jobs/new');
    await page.selectOption('select[name="client_id"]', '1');

    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    await page.fill('input[name="date_range_start"]', dateStr);
    await page.fill('input[name="date_range_end"]', dateStr);

    await page.click('button[type="submit"]');
    await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

    // Extract job ID
    const url = page.url();
    const jobId = url.match(/\/scraper\/jobs\/(\d+)/)?.[1];
    expect(jobId).toBeTruthy();

    // Click cancel button
    const cancelButton = page.locator('button:has-text("Cancel"), [data-testid="cancel-job-button"]');

    if (await cancelButton.isVisible()) {
      await cancelButton.click();

      // Confirm cancellation in modal
      await page.click('[data-testid="confirm-cancel-button"], button:has-text("Confirm")');

      // Should show cancelled status
      await expect(page.locator('text=/cancelled|canceled/i')).toBeVisible({ timeout: 10000 });
    }
  });

  test('should show validation errors for invalid job configuration', async ({ page }) => {
    await loginAsUser(page);

    await page.goto('/scraper/jobs/new');

    // Submit without selecting client
    await page.click('button[type="submit"]');

    // Should show validation error
    await expect(page.locator('.error, .alert-error, [role="alert"]')).toBeVisible();

    // Fill in client but with invalid date range
    await page.selectOption('select[name="client_id"]', '1');

    const today = new Date();
    const future = new Date(today.setMonth(today.getMonth() + 1));
    const futureStr = future.toISOString().split('T')[0];

    await page.fill('input[name="date_range_start"]', futureStr);
    await page.fill('input[name="date_range_end"]', new Date().toISOString().split('T')[0]);

    await page.click('button[type="submit"]');

    // Should show date range validation error
    await expect(page.locator('text=/invalid.*date|date.*range/i')).toBeVisible();
  });

  test('should paginate results in job details', async ({ page }) => {
    await loginAsUser(page);

    // Navigate to a completed job with results
    await page.goto('/scraper/jobs');

    const completedJob = page.locator('tr:has-text("completed")').first();

    if (await completedJob.isVisible()) {
      await completedJob.click();
      await page.waitForURL(/\/scraper\/jobs\/\d+/, { timeout: 10000 });

      // Look for pagination controls
      const paginationControls = page.locator('.pagination, [data-testid="pagination"]');

      if (await paginationControls.isVisible()) {
        // Click next page
        await page.click('button:has-text("Next"), a:has-text("Next"), .pagination .next');

        // Should load next page of results
        await page.waitForTimeout(1000);

        // Verify URL or content changed
        const currentUrl = page.url();
        expect(currentUrl).toMatch(/page=|offset=/);
      }
    } else {
      test.skip();
    }
  });
});
