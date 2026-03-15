/** Utility functions */

/**
 * Format a date for display
 */
export const formatDate = (date, options = {}) => {
  if (!date) return null;

  const defaultOptions = {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    ...options,
  };

  return new Date(date).toLocaleDateString('en-US', defaultOptions);
};

/**
 * Format a date and time for display
 */
export const formatDateTime = (date, options = {}) => {
  if (!date) return null;

  const defaultOptions = {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    ...options,
  };

  return new Date(date).toLocaleString('en-US', defaultOptions);
};

/**
 * Format a time for display
 */
export const formatTime = (date, options = {}) => {
  if (!date) return null;

  const defaultOptions = {
    hour: 'numeric',
    minute: '2-digit',
    ...options,
  };

  return new Date(date).toLocaleTimeString('en-US', defaultOptions);
};

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export const getRelativeTime = (date) => {
  if (!date) return null;

  const now = new Date();
  const past = new Date(date);
  const diffMs = now - past;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return formatDate(date);
};

/**
 * Check if a date is overdue
 */
export const isOverdue = (date, completed = false) => {
  if (!date || completed) return false;
  return new Date(date) < new Date();
};

/**
 * Get priority color class
 */
export const getPriorityColor = (priority) => {
  const colors = {
    1: 'text-gray-600 bg-gray-100', // Low
    2: 'text-blue-600 bg-blue-100', // Medium
    3: 'text-orange-600 bg-orange-100', // High
    4: 'text-red-600 bg-red-100', // Urgent
  };
  return colors[priority] || colors[2];
};

/**
 * Get priority label
 */
export const getPriorityLabel = (priority) => {
  const labels = {
    1: 'Low',
    2: 'Medium',
    3: 'High',
    4: 'Urgent',
  };
  return labels[priority] || 'Medium';
};

/**
 * Truncate text
 */
export const truncate = (text, length = 100) => {
  if (!text) return '';
  return text.length > length ? text.substring(0, length) + '...' : text;
};

/**
 * Debounce function
 */
export const debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
};

/**
 * Generate unique ID
 */
export const generateId = () => {
  return Math.random().toString(36).substring(2, 9);
};
