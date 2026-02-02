import { chromium, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';

/**
 * Global Setup for E2E Tests
 *
 * Responsibilities:
 * 1. Set up dedicated test database
 * 2. Run migrations
 * 3. Seed baseline test data
 *
 * Per Phase 7.11 instructions:
 * - Uses separate test database (never dev/prod)
 * - Creates baseline data once at startup
 * - Tests create/cleanup additional data within each test
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment setup...');

  const baseURL = config.projects[0].use.baseURL || 'http://localhost:8000';

  // 1. Set up test database environment
  console.log('📦 Setting up test database...');
  process.env.DATABASE_URL = process.env.E2E_DATABASE_URL || 'file:test_e2e.db';
  process.env.APP_ENV = 'test';

  // 2. Run database migrations
  console.log('🔄 Running database migrations...');
  try {
    const projectRoot = path.resolve(__dirname, '../../..');
    execSync('python -m src.db.migrate', {
      cwd: projectRoot,
      env: { ...process.env },
      stdio: 'inherit',
    });
  } catch (error) {
    console.error('❌ Migration failed:', error);
    throw error;
  }

  // 3. Seed baseline test data
  console.log('🌱 Seeding baseline test data...');
  try {
    const projectRoot = path.resolve(__dirname, '../../..');
    execSync('python tests/e2e/setup/seed_data.py', {
      cwd: projectRoot,
      env: { ...process.env },
      stdio: 'inherit',
    });
  } catch (error) {
    console.error('❌ Data seeding failed:', error);
    throw error;
  }

  // 4. Verify server is running
  console.log('🔍 Verifying server availability...');
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    const response = await page.goto(`${baseURL}/health`, {
      waitUntil: 'networkidle',
      timeout: 10000,
    });

    if (!response || response.status() !== 200) {
      throw new Error(`Server not healthy. Status: ${response?.status()}`);
    }

    console.log('✅ Server is healthy and ready for testing');
  } catch (error) {
    console.error('❌ Server verification failed:', error);
    console.error('Please ensure the application is running on', baseURL);
    throw error;
  } finally {
    await page.close();
    await context.close();
    await browser.close();
  }

  console.log('✅ E2E test environment setup complete\n');
}

export default globalSetup;
