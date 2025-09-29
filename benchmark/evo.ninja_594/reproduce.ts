import { test, expect, type Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// The entrypoint script will set this environment variable to 'buggy' or 'fixed'.
const version = process.env.VERSION || 'buggy';

const UPLOAD_FILE_NAME = 'test-file.txt';
const UPLOAD_FILE_CONTENT = 'hello world from the test file';
// Create the file in the test's directory. Playwright knows how to find it.
const UPLOAD_FILE_PATH = path.join(__dirname, UPLOAD_FILE_NAME);

test.describe('Evo.Ninja Issue #594: Anonymous Session File Uploads', () => {
  // Create the dummy file before the tests start.
  test.beforeAll(() => {
    fs.writeFileSync(UPLOAD_FILE_PATH, UPLOAD_FILE_CONTENT);
  });

  // Clean up by deleting the dummy file after the tests finish.
  test.afterAll(() => {
    fs.unlinkSync(UPLOAD_FILE_PATH);
  });

  test(`should transfer uploaded files from anonymous to new chat (Version: ${version})`, async ({ page }) => {
    // Step 1: Navigate to the app and wait for it to be ready.
    console.log('Step 1: Navigating to the application.');
    await page.goto('http://localhost:3000/');
    const goalTextarea = page.getByPlaceholder('Enter your goal here...');
    await expect(goalTextarea).toBeVisible({ timeout: 30000 });

    // Step 2: Upload a file to the initial "anonymous" workspace.
    console.log(`Step 2: Uploading file "${UPLOAD_FILE_NAME}".`);
    // The <input type="file"> is hidden, so we target it directly to set its files.
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(UPLOAD_FILE_PATH);
    
    // Verify the file appeared in the initial file explorer.
    const initialFile = page.locator('.file-tree').getByText(UPLOAD_FILE_NAME);
    await expect(initialFile).toBeVisible({ timeout: 10000 });
    console.log('File successfully appeared in the anonymous workspace.');

    // Step 3: Start a new chat session by submitting a goal.
    console.log('Step 3: Starting a new chat session.');
    await goalTextarea.fill(`Read the content of ${UPLOAD_FILE_NAME}`);
    await page.getByRole('button', { name: 'Run' }).click();

    // Wait for the new chat view to initialize.
    await expect(page.getByText('Thinking...')).toBeVisible({ timeout: 20000 });

    // Step 4: Verification.
    console.log('Step 4: Verifying if the file exists in the new chat workspace.');
    const newChatFile = page.locator('.file-tree').getByText(UPLOAD_FILE_NAME);

    if (version === 'buggy') {
      console.log('Buggy Test: Expecting the uploaded file to BE MISSING.');
      // In the buggy version, the file is NOT transferred to the new session's workspace.
      await expect(newChatFile).not.toBeVisible({ timeout: 15000 });
    } else { // version === 'fixed'
      console.log('Fixed Test: Expecting the uploaded file to BE VISIBLE.');
      // In the fixed version, the file is correctly transferred.
      await expect(newChatFile).toBeVisible({ timeout: 15000 });
    }
  });
});