/** Test Utilities */
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../contexts/AuthContext';

/**
 * Custom render function that includes providers
 */
export function renderWithProviders(ui, options = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const AllProviders = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>{children}</AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );

  return render(ui, { wrapper: AllProviders, ...options });
}

/**
 * Mock authenticated user
 */
export const mockUser = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User',
  avatar_url: 'https://example.com/avatar.jpg',
};

/**
 * Mock auth token
 */
export const mockAuthToken = 'mock-jwt-token-12345';

/**
 * Create a mock task
 */
export function createMockTask(overrides = {}) {
  return {
    id: 1,
    title: 'Test Task',
    description: 'Test task description',
    completed: false,
    priority: 2,
    status: 'pending',
    due_date: null,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/**
 * Create a mock event
 */
export function createMockEvent(overrides = {}) {
  return {
    id: 1,
    title: 'Test Event',
    description: 'Test event description',
    start_time: '2025-01-15T10:00:00Z',
    end_time: '2025-01-15T11:00:00Z',
    created_at: '2025-01-15T09:00:00Z',
    ...overrides,
  };
}

/**
 * Create a mock integration
 */
export function createMockIntegration(overrides = {}) {
  return {
    id: 1,
    name: 'Todoist',
    provider: 'todoist',
    enabled: true,
    last_sync: null,
    ...overrides,
  };
}

/**
 * Mock API response
 */
export function mockApiResponse(data, status = 200) {
  return {
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {},
  };
}

/**
 * Wait for async operations
 */
export function waitFor(ms = 0) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Re-export testing library utilities
export * from '@testing-library/react';
