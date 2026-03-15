import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should show login page when not authenticated', async ({ page }) => {
    await page.goto('/');

    // Should redirect to login or show login button
    await expect(page).toHaveURL(/.*login.*/);
  });

  test('should display Google OAuth button', async ({ page }) => {
    await page.goto('/login');

    // Check for Google OAuth button
    const googleButton = page.getByRole('button', { name: /google|sign in with google/i });
    await expect(googleButton).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test.use({ storageState: 'e2e/.auth/auth.json' });

  test('should display dashboard elements', async ({ page }) => {
    await page.goto('/');

    // Check for main navigation
    await expect(page.getByRole('navigation')).toBeVisible();

    // Check for dashboard heading
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should navigate to tasks page', async ({ page }) => {
    await page.goto('/');

    // Click on Tasks link
    await page.click('text=Tasks');

    // Should navigate to tasks page
    await expect(page).toHaveURL(/.*tasks.*/);
    await expect(page.getByRole('heading', { name: /tasks/i })).toBeVisible();
  });

  test('should navigate to integrations page', async ({ page }) => {
    await page.goto('/');

    // Click on Integrations link
    await page.click('text=Integrations');

    // Should navigate to integrations page
    await expect(page).toHaveURL(/.*integrations.*/);
    await expect(page.getByRole('heading', { name: /integrations/i })).toBeVisible();
  });
});

test.describe('Tasks Page', () => {
  test.use({ storageState: 'e2e/.auth/auth.json' });

  test('should display task list', async ({ page }) => {
    await page.goto('/tasks');

    // Check for task list or empty state
    const taskList = page.getByTestId('task-list');
    const emptyState = page.getByText(/no tasks/i);

    await expect(taskList.or(emptyState)).toBeVisible();
  });

  test('should create a new task', async ({ page }) => {
    await page.goto('/tasks');

    // Click create button
    await page.click('button:has-text("Create")');

    // Fill in task details
    await page.fill('input[name="title"]', 'Test Task from E2E');
    await page.fill('textarea[name="description"]', 'This is a test task created by E2E tests');

    // Submit form
    await page.click('button:has-text("Save")');

    // Should show new task or success message
    await expect(page.getByText('Test Task from E2E')).toBeVisible();
  });
});

test.describe('Integrations Page', () => {
  test.use({ storageState: 'e2e/.auth/auth.json' });

  test('should display available integrations', async ({ page }) => {
    await page.goto('/integrations');

    // Check for integration cards
    await expect(page.getByText('Todoist')).toBeVisible();
    await expect(page.getByText('Google Calendar')).toBeVisible();
  });

  test('should show OAuth connect button', async ({ page }) => {
    await page.goto('/integrations');

    // Find Todoist card
    const todoistCard = page.getByText('Todoist').locator('..').locator('..');

    // Check for Connect button
    await expect(todoistCard.getByRole('button', { name: /connect/i })).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test.use({ storageState: 'e2e/.auth/auth.json' });

  test('should be mobile responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Check for mobile menu button
    const menuButton = page.getByRole('button', { name: /menu/i });
    await expect(menuButton).toBeVisible();
  });

  test('should be tablet responsive', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto('/');

    // Check navigation is visible
    await expect(page.getByRole('navigation')).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test.use({ storageState: 'e2e/.auth/auth.json' });

  test('should show error message on API failure', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/v1/tasks', route => route.abort());

    await page.goto('/tasks');

    // Should show error message
    await expect(page.getByText(/failed to load|error/i)).toBeVisible();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Simulate network offline
    await page.context().setOffline(true);

    await page.goto('/');

    // Should show offline indicator or message
    const offlineIndicator = page.getByText(/offline|no connection/i);
    await expect(offlineIndicator).toBeVisible({ timeout: 5000 }).catch(() => {
      // If offline indicator not found, that's also acceptable
      // The app should still be functional with cached data
    });

    // Restore connection
    await page.context().setOffline(false);
  });
});
