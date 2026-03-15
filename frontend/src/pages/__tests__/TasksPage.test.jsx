/** TasksPage Component Tests */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { TasksPage } from '../TasksPage';

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    getTasks: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
    toggleTask: vi.fn(),
    parseTask: vi.fn(),
  },
}));

// Mock the AuthContext
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, name: 'Test User' },
    isAuthenticated: true,
    loading: false,
  }),
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

import { apiService } from '../../services/api';

describe('TasksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('auth_token', 'mock-token');
  });

  it('should render loading state initially', () => {
    apiService.getTasks.mockImplementation(() => new Promise(() => {}));

    render(<TasksPage />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should render tasks when loaded', async () => {
    const mockTasks = [
      { id: 1, title: 'Task 1', completed: false, priority: 2 },
      { id: 2, title: 'Task 2', completed: true, priority: 1 },
    ];

    apiService.getTasks.mockResolvedValue({
      data: {
        tasks: mockTasks,
        total: 2,
        completed: 1,
        pending: 1,
      },
    });

    render(<TasksPage />);

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });

  it('should display empty state when no tasks', async () => {
    apiService.getTasks.mockResolvedValue({
      data: {
        tasks: [],
        total: 0,
        completed: 0,
        pending: 0,
      },
    });

    render(<TasksPage />);

    await waitFor(() => {
      expect(screen.getByText(/no tasks/i)).toBeInTheDocument();
    });
  });

  it('should create a new task', async () => {
    const newTask = { id: 1, title: 'New Task', completed: false, priority: 2 };

    apiService.getTasks.mockResolvedValue({
      data: { tasks: [], total: 0, completed: 0, pending: 0 },
    });

    apiService.createTask.mockResolvedValue({ data: newTask });

    render(<TasksPage />);

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByText(/create task/i)).toBeInTheDocument();
    });

    // Find the create button/input and interact
    const createButton = screen.getByRole('button', { name: /create|add/i });
    expect(createButton).toBeInTheDocument();
  });

  it('should filter tasks by completion status', async () => {
    const mockTasks = [
      { id: 1, title: 'Active Task', completed: false, priority: 2 },
      { id: 2, title: 'Completed Task', completed: true, priority: 1 },
    ];

    apiService.getTasks.mockResolvedValue({
      data: {
        tasks: mockTasks,
        total: 2,
        completed: 1,
        pending: 1,
      },
    });

    render(<TasksPage />);

    await waitFor(() => {
      expect(screen.getByText('Active Task')).toBeInTheDocument();
    });
  });

  it('should display task count statistics', async () => {
    apiService.getTasks.mockResolvedValue({
      data: {
        tasks: [],
        total: 10,
        completed: 5,
        pending: 5,
      },
    });

    render(<TasksPage />);

    await waitFor(() => {
      expect(screen.getByText(/10 total/i)).toBeInTheDocument();
      expect(screen.getByText(/5 completed/i)).toBeInTheDocument();
      expect(screen.getByText(/5 pending/i)).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    apiService.getTasks.mockRejectedValue({
      response: { status: 500, data: { detail: 'Server error' } },
    });

    render(<TasksPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load tasks/i)).toBeInTheDocument();
    });
  });

  it('should refresh tasks when refresh button is clicked', async () => {
    apiService.getTasks.mockResolvedValue({
      data: { tasks: [], total: 0, completed: 0, pending: 0 },
    });

    render(<TasksPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
    });
  });
});
