/** Task List Component */
import React from 'react';
import { getRelativeTime, getPriorityColor, getPriorityLabel, isOverdue } from '../utils/format';

const TaskList = ({ tasks = [], showActions = true, compact = false, onToggle, onDelete }) => {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
          />
        </svg>
        <p className="mt-2">No tasks found</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => {
        const overdue = isOverdue(task.due_date, task.completed);

        return (
          <div
            key={task.id}
            className={`group flex items-start gap-3 p-3 rounded-lg border transition-all ${
              task.completed
                ? 'bg-gray-50 border-gray-200 opacity-60'
                : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
            }`}
          >
            {/* Checkbox */}
            {showActions && (
              <button
                onClick={() => onToggle?.(task.id)}
                className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                  task.completed
                    ? 'bg-green-500 border-green-500 text-white'
                    : 'border-gray-300 hover:border-green-500'
                }`}
              >
                {task.completed && (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            )}

            {/* Task content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h4
                  className={`font-medium ${
                    task.completed ? 'line-through text-gray-500' : 'text-gray-900'
                  }`}
                >
                  {task.title}
                </h4>
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded-full ${getPriorityColor(
                    task.priority
                  )}`}
                >
                  {getPriorityLabel(task.priority)}
                </span>
                {overdue && (
                  <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700">
                    Overdue
                  </span>
                )}
              </div>

              {!compact && task.description && (
                <p className="mt-1 text-sm text-gray-600 line-clamp-2">{task.description}</p>
              )}

              <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                {task.due_date && (
                  <span className={overdue ? 'text-red-600 font-medium' : ''}>
                    Due: {new Date(task.due_date).toLocaleDateString()}
                  </span>
                )}
                <span>Created {getRelativeTime(task.created_at)}</span>
              </div>
            </div>

            {/* Actions */}
            {showActions && (
              <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => onDelete?.(task.id)}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Delete task"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default TaskList;
