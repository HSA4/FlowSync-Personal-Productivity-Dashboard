/** Dashboard Component */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTasks, useEvents } from '../hooks';
import TaskList from './TaskList';
import { apiService } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    pendingTasks: 0,
    upcomingEvents: 0,
    overdueTasks: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch tasks and events with the new API
  const { data: tasksData, isLoading: tasksLoading, error: tasksError } = useTasks({ limit: 100 });
  const { data: eventsData, isLoading: eventsLoading } = useEvents({ limit: 100 });

  useEffect(() => {
    if (tasksData && eventsData) {
      const { tasks, total, completed, pending } = tasksData;

      // Calculate overdue tasks
      const overdue = tasks.filter((t) => {
        if (!t.due_date) return false;
        return new Date(t.due_date) < new Date() && !t.completed;
      }).length;

      setStats({
        totalTasks: total,
        completedTasks: completed,
        pendingTasks: pending,
        upcomingEvents: eventsData.total || 0,
        overdueTasks: overdue,
      });
      setIsLoading(false);
    }
  }, [tasksData, eventsData]);

  useEffect(() => {
    if (tasksError) {
      setError(tasksError.response?.data?.error?.message || 'Failed to load tasks');
      setIsLoading(false);
    }
  }, [tasksError]);

  const completionRate =
    stats.totalTasks > 0 ? Math.round((stats.completedTasks / stats.totalTasks) * 100) : 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Total Tasks</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.totalTasks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Completed</h3>
          <p className="mt-2 text-3xl font-bold text-green-600">{stats.completedTasks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Pending</h3>
          <p className="mt-2 text-3xl font-bold text-blue-600">{stats.pendingTasks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Completion Rate</h3>
          <p className="mt-2 text-3xl font-bold text-primary-600">{completionRate}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Overdue</h3>
          <p className="mt-2 text-3xl font-bold text-red-600">{stats.overdueTasks}</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Recent Tasks</h2>
            <Link
              to="/tasks"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              View all
            </Link>
          </div>
          {tasksLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <TaskList tasks={tasksData?.tasks?.slice(0, 5) || []} showActions={false} compact />
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <button className="p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors text-left">
              <svg
                className="w-6 h-6 text-primary-600 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className="font-medium text-primary-700">Add Task</span>
            </button>
            <button className="p-4 bg-secondary-50 rounded-lg hover:bg-secondary-100 transition-colors text-left">
              <svg
                className="w-6 h-6 text-secondary-600 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <span className="font-medium text-secondary-700">Add Event</span>
            </button>
            <button className="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors text-left">
              <svg
                className="w-6 h-6 text-green-600 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <span className="font-medium text-green-700">View Report</span>
            </button>
            <button className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors text-left">
              <svg
                className="w-6 h-6 text-purple-600 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span className="font-medium text-purple-700">AI Insights</span>
            </button>
          </div>
        </div>
      </div>

      {/* Upcoming Events */}
      {eventsData?.events && eventsData.events.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Upcoming Events</h2>
            <Link
              to="/calendar"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              View calendar
            </Link>
          </div>
          <div className="space-y-3">
            {eventsData.events.slice(0, 3).map((event) => (
              <div key={event.id} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-primary-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{event.title}</h4>
                  <p className="text-sm text-gray-600">
                    {new Date(event.start_time).toLocaleString()}
                    {event.all_day && ' (All day)'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
