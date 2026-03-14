import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TaskList from './TaskList';
import api from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    upcomingEvents: 0,
    overdueTasks: 0,
  });
  const [recentTasks, setRecentTasks] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [tasksResponse, eventsResponse] = await Promise.all([
        api.get('/tasks'),
        api.get('/events')
      ]);
      const tasks = tasksResponse.data;
      const events = eventsResponse.data;

      const completed = tasks.filter(t => t.completed).length;
      const overdue = tasks.filter(t => {
        if (!t.due_date) return false;
        return new Date(t.due_date) < new Date() && !t.completed;
      }).length;

      setStats({
        totalTasks: tasks.length,
        completedTasks: completed,
        upcomingEvents: events.length,
        overdueTasks: overdue,
      });
      setRecentTasks(tasks.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const completionRate = stats.totalTasks > 0
    ? Math.round((stats.completedTasks / stats.totalTasks) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Total Tasks</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.totalTasks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Completed</h3>
          <p className="mt-2 text-3xl font-bold text-green-600">{stats.completedTasks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Completion Rate</h3>
          <p className="mt-2 text-3xl font-bold text-primary-600">{completionRate}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Upcoming Events</h3>
          <p className="mt-2 text-3xl font-bold text-secondary-600">{stats.upcomingEvents}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Recent Tasks</h2>
            <Link to="/tasks" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View all
            </Link>
          </div>
          <TaskList tasks={recentTasks} showActions={false} compact />
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <button className="p-4 bg-primary-50 rounded-md hover:bg-primary-100 transition-colors">
              <span className="font-medium text-primary-700">Add Task</span>
            </button>
            <button className="p-4 bg-secondary-50 rounded-md hover:bg-secondary-100 transition-colors">
              <span className="font-medium text-secondary-700">Add Event</span>
            </button>
            <button className="p-4 bg-accent-50 rounded-md hover:bg-accent-100 transition-colors col-span-2">
              <span className="font-medium text-accent-700">Generate AI Report</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;