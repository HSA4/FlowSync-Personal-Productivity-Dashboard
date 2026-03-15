/** API Service Tests */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import { apiService } from '../api';

// Mock axios
vi.mock('axios');

describe('API Service', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();

    // Mock localStorage
    localStorage.getItem.mockReturnValue('mock-token');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Health Check', () => {
    it('should call health endpoint', async () => {
      const mockResponse = { data: { status: 'healthy' } };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.health();

      expect(axios.get).toHaveBeenCalledWith('/health');
      expect(response.data).toEqual({ status: 'healthy' });
    });
  });

  describe('Authentication', () => {
    it('should get Google OAuth URL', async () => {
      const mockResponse = { data: { url: 'https://accounts.google.com/oauth' } };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getGoogleOAuthUrl('http://localhost:5173/auth/callback');

      expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/oauth/google', {
        params: { redirect_uri: 'http://localhost:5173/auth/callback' },
      });
      expect(response.data.url).toBeTruthy();
    });

    it('should get current user', async () => {
      const mockResponse = {
        data: {
          id: 1,
          email: 'test@example.com',
          name: 'Test User',
        },
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getCurrentUser();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/me');
      expect(response.data).toHaveProperty('email');
    });

    it('should logout', async () => {
      const mockResponse = { data: { message: 'Logged out' } };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.logout();

      expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/logout');
    });
  });

  describe('Tasks', () => {
    it('should get tasks', async () => {
      const mockResponse = {
        data: {
          tasks: [
            { id: 1, title: 'Task 1', completed: false },
            { id: 2, title: 'Task 2', completed: true },
          ],
          total: 2,
          completed: 1,
          pending: 1,
        },
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getTasks({ completed: false });

      expect(axios.get).toHaveBeenCalledWith('/api/v1/tasks', {
        params: { completed: false },
      });
      expect(response.data.tasks).toHaveLength(2);
    });

    it('should create a task', async () => {
      const newTask = {
        title: 'New Task',
        description: 'Task description',
        priority: 2,
      };
      const mockResponse = {
        data: { id: 1, ...newTask },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.createTask(newTask);

      expect(axios.post).toHaveBeenCalledWith('/api/v1/tasks', newTask);
      expect(response.data.id).toBe(1);
    });

    it('should update a task', async () => {
      const updates = { title: 'Updated Task' };
      const mockResponse = {
        data: { id: 1, ...updates },
      };
      axios.put.mockResolvedValue(mockResponse);

      const response = await apiService.updateTask(1, updates);

      expect(axios.put).toHaveBeenCalledWith('/api/v1/tasks/1', updates);
      expect(response.data.title).toBe('Updated Task');
    });

    it('should delete a task', async () => {
      axios.delete.mockResolvedValue({ data: null });

      await apiService.deleteTask(1);

      expect(axios.delete).toHaveBeenCalledWith('/api/v1/tasks/1');
    });

    it('should toggle task completion', async () => {
      const mockResponse = {
        data: { id: 1, completed: true },
      };
      axios.patch.mockResolvedValue(mockResponse);

      const response = await apiService.toggleTask(1);

      expect(axios.patch).toHaveBeenCalledWith('/api/v1/tasks/1/toggle');
      expect(response.data.completed).toBe(true);
    });
  });

  describe('Events', () => {
    it('should get events', async () => {
      const mockResponse = {
        data: [
          { id: 1, title: 'Event 1' },
          { id: 2, title: 'Event 2' },
        ],
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getEvents();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/events');
      expect(response.data).toHaveLength(2);
    });

    it('should create an event', async () => {
      const newEvent = {
        title: 'New Event',
        start_time: '2025-01-15T10:00:00Z',
        end_time: '2025-01-15T11:00:00Z',
      };
      const mockResponse = {
        data: { id: 1, ...newEvent },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.createEvent(newEvent);

      expect(axios.post).toHaveBeenCalledWith('/api/v1/events', newEvent);
      expect(response.data.id).toBe(1);
    });
  });

  describe('Integrations', () => {
    it('should get available providers', async () => {
      const mockResponse = {
        data: [
          { id: 'todoist', name: 'Todoist' },
          { id: 'google-calendar', name: 'Google Calendar' },
        ],
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getAvailableProviders();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/integrations/providers/available');
      expect(response.data).toHaveLength(2);
    });

    it('should get user integrations', async () => {
      const mockResponse = {
        data: [
          { id: 1, name: 'Todoist', provider: 'todoist', enabled: true },
        ],
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getIntegrations();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/integrations');
      expect(response.data).toHaveLength(1);
    });

    it('should trigger sync for an integration', async () => {
      const mockResponse = {
        data: { status: 'queued', task_id: 'task-123' },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.syncIntegration(1);

      expect(axios.post).toHaveBeenCalledWith('/api/v1/integrations/1/sync', {}, {
        params: { sync_to_external: false },
      });
      expect(response.data.status).toBe('queued');
    });

    it('should get sync status', async () => {
      const mockResponse = {
        data: {
          integrations: [
            { id: 1, status: 'synced', webhook_registered: true },
          ],
          overall_status: 'synced',
        },
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getSyncStatus();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/integrations/sync/status');
      expect(response.data.overall_status).toBe('synced');
    });
  });

  describe('AI Features', () => {
    it('should parse task from natural language', async () => {
      const mockResponse = {
        data: {
          title: 'Complete project report',
          description: 'Write and submit quarterly report',
          priority: 3,
          due_date: '2025-01-20',
        },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.parseTask('I need to complete my project report by Friday');

      expect(axios.post).toHaveBeenCalledWith('/api/v1/ai/parse-task', {
        text: 'I need to complete my project report by Friday',
      });
      expect(response.data.title).toBeTruthy();
    });

    it('should get task suggestions', async () => {
      const mockResponse = {
        data: {
          suggestions: [
            { title: 'Review goals', description: 'Assess progress' },
            { title: 'Schedule meeting', description: 'Organize sync' },
          ],
        },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.suggestTasks(3);

      expect(axios.post).toHaveBeenCalledWith('/api/v1/ai/suggest-tasks', {
        max_suggestions: 3,
      });
      expect(response.data.suggestions).toHaveLength(2);
    });

    it('should prioritize tasks', async () => {
      const mockResponse = {
        data: {
          priorities: { 1: 4, 2: 3, 3: 2 },
        },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.prioritizeTasks([1, 2, 3]);

      expect(axios.post).toHaveBeenCalledWith('/api/v1/ai/prioritize-tasks', {
        task_ids: [1, 2, 3],
      });
      expect(response.data.priorities).toBeDefined();
    });
  });

  describe('Celery Tasks', () => {
    it('should get Celery status', async () => {
      const mockResponse = {
        data: {
          status: 'running',
          workers: ['worker1@host'],
          active_tasks: 2,
        },
      };
      axios.get.mockResolvedValue(mockResponse);

      const response = await apiService.get('/api/v1/tasks/status');

      expect(axios.get).toHaveBeenCalledWith('/api/v1/tasks/status');
      expect(response.data.status).toBe('running');
    });

    it('should trigger sync via Celery', async () => {
      const mockResponse = {
        data: { status: 'queued', task_id: 'celery-task-123' },
      };
      axios.post.mockResolvedValue(mockResponse);

      const response = await apiService.post('/api/v1/tasks/sync/1');

      expect(axios.post).toHaveBeenCalledWith('/api/v1/tasks/sync/1');
      expect(response.data.task_id).toBeTruthy();
    });
  });
});
