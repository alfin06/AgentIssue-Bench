import { test, expect, type Page, type Locator } from '@playwright/test';

// The entrypoint script will set this environment variable
const version = process.env.VERSION || 'buggy';

/**
 * Helper function to create a prerequisite chat session.
 * This establishes the initial state needed to reproduce the bug.
 */
const createPrerequisiteChat = async (page: Page): Promise<Locator> => {
  console.log('Setting up: Creating a prerequisite chat to establish initial state...');
  await page.goto('http://localhost:3000/');
  
  // Wait for the main goal input to be ready
  const goalTextarea = page.getByPlaceholder('Enter your goal here...');
  await expect(goalTextarea).toBeVisible({ timeout: 30000 });
  
  // Create a simple chat session
  await goalTextarea.fill('Write a simple hello world script in python');
  await page.getByRole('button', { name: 'Run' }).click();
  
  // Wait for the agent to finish, which ensures the chat is saved in the sidebar
  await expect(page.getByText('Done!', { exact: true })).toBeVisible({ timeout: 120000 });
  
  console.log('Setup complete: Prerequisite chat created.');
  // Return the locator for the newly created chat in the sidebar
  return page.locator('[data-chat-id]').first();
};

test.describe('Evo.Ninja Issue #652: Stale Workspace State', () => {
  let page: Page;
  let prerequisiteChatLocator: Locator;

  // Create one browser page and one prerequisite chat for all tests
  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    prerequisiteChatLocator = await createPrerequisiteChat(page);
  });

  test.afterAll(async () => {
    await page.close();
  });

  test(`should correctly apply workspace files from an example prompt (Version: ${version})`, async () => {
    // Step 1: Select the existing chat
    console.log('Step 1: Selecting the existing chat.');
    await prerequisiteChatLocator.click();
    await expect(page.locator('#goal-input')).toHaveValue('Write a simple hello world script in python');

    // Step 2: Navigate back to the root page
    console.log('Step 2: Navigating back to the root page.');
    // The "Evo" logo is the link back to the main page
    await page.getByRole('link', { name: 'Evo' }).click();
    await expect(page.getByText('Example Prompts')).toBeVisible();

    // Step 3: Click an example prompt that includes workspace files
    console.log('Step 3: Clicking the "Build a snake game" example prompt.');
    const snakeGamePrompt = page.getByText('Build a snake game');
    await expect(snakeGamePrompt).toBeVisible();
    await snakeGamePrompt.click();

    // Step 4: Verification - Check if the snake game files are loaded in the workspace
    console.log('Step 4: Verifying the workspace files...');
    const mainPyFile = page.locator('.file-tree').getByText('main.py');

    if (version === 'buggy') {
      console.log('Buggy Test: Expecting workspace files to BE MISSING due to stale state.');
      await expect(mainPyFile).not.toBeVisible({ timeout: 15000 });
    } else { // version === 'fixed'
      console.log('Fixed Test: Expecting workspace files to BE VISIBLE.');
      await expect(mainPyFile).toBeVisible({ timeout: 15000 });
    }
  });
});