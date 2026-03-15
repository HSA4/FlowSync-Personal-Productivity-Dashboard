/** AI Task Input Component - Natural Language Task Creation */
import React, { useState } from 'react';
import { apiService } from '../services/api';

const AITaskInput = ({ onTaskCreated }) => {
  const [text, setText] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewTask, setPreviewTask] = useState(null);

  const handleParse = async () => {
    if (!text.trim()) return;

    setIsParsing(true);
    setError(null);

    try {
      const response = await apiService.parseTask(text);
      const parsed = response.data;

      setPreviewTask({
        title: parsed.title,
        description: parsed.description,
        due_date: parsed.due_date,
        priority: parsed.priority,
        estimated_duration: parsed.estimated_duration,
      });
      setShowPreview(true);
    } catch (err) {
      console.error('Failed to parse task:', err);
      setError(err.response?.data?.detail || 'Failed to parse task. Please try again.');
    } finally {
      setIsParsing(false);
    }
  };

  const handleCreateTask = async () => {
    if (!previewTask) return;

    try {
      const taskData = {
        title: previewTask.title,
        description: previewTask.description,
        due_date: previewTask.due_date,
        priority: previewTask.priority,
      };

      await apiService.createTask(taskData);

      // Reset and notify parent
      setText('');
      setShowPreview(false);
      setPreviewTask(null);

      if (onTaskCreated) {
        onTaskCreated();
      }
    } catch (err) {
      console.error('Failed to create task:', err);
      setError('Failed to create task. Please try again.');
    }
  };

  const handleCancelPreview = () => {
    setShowPreview(false);
    setPreviewTask(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleParse();
    }
  };

  const priorityLabels = {
    1: 'Low',
    2: 'Medium',
    3: 'High',
    4: 'Urgent',
  };

  const priorityColors = {
    1: 'bg-gray-100 text-gray-700',
    2: 'bg-blue-100 text-blue-700',
    3: 'bg-orange-100 text-orange-700',
    4: 'bg-red-100 text-red-700',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h3 className="font-semibold text-gray-900">AI Task Assistant</h3>
        <span className="text-xs text-gray-500 ml-auto">Powered by OpenRouter</span>
      </div>

      {/* Input */}
      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your task naturally... (e.g., 'Schedule team meeting tomorrow at 2pm')"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
          rows={2}
          disabled={isParsing}
        />
        <div className="absolute bottom-2 right-2 flex items-center gap-2">
          <span className="text-xs text-gray-400">Press Enter to parse</span>
          <button
            onClick={handleParse}
            disabled={!text.trim() || isParsing}
            className="px-3 py-1 text-sm font-medium text-purple-600 border border-purple-600 rounded hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isParsing ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 inline" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Parsing...
              </>
            ) : (
              'Parse'
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-700 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Preview */}
      {showPreview && previewTask && (
        <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">Parsed Task Preview</h4>

          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-gray-700">Title:</span>
              <span className="ml-2 text-gray-900">{previewTask.title}</span>
            </div>

            {previewTask.description && (
              <div>
                <span className="font-medium text-gray-700">Description:</span>
                <span className="ml-2 text-gray-600">{previewTask.description}</span>
              </div>
            )}

            <div className="flex gap-4">
              {previewTask.due_date && (
                <div>
                  <span className="font-medium text-gray-700">Due:</span>
                  <span className="ml-2 text-gray-600">
                    {new Date(previewTask.due_date).toLocaleString()}
                  </span>
                </div>
              )}

              <div>
                <span className="font-medium text-gray-700">Priority:</span>
                <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${priorityColors[previewTask.priority]}`}>
                  {priorityLabels[previewTask.priority]}
                </span>
              </div>

              {previewTask.estimated_duration && (
                <div>
                  <span className="font-medium text-gray-700">Duration:</span>
                  <span className="ml-2 text-gray-600">{previewTask.estimated_duration} min</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={handleCreateTask}
              className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded hover:bg-purple-700 transition-colors"
            >
              Create Task
            </button>
            <button
              onClick={handleCancelPreview}
              className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                handleCancelPreview();
                setText(previewTask.title);
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
            >
              Edit Manually
            </button>
          </div>
        </div>
      )}

      {/* Examples */}
      {!showPreview && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 mb-2">Try examples:</p>
          <div className="flex flex-wrap gap-2">
            {[
              'Finish project report by Friday 5pm',
              'Call dentist to schedule appointment',
              'Urgent: Submit tax documents before midnight',
              'Weekly team sync every Monday 10am',
            ].map((example) => (
              <button
                key={example}
                onClick={() => setText(example)}
                className="px-2 py-1 text-xs text-purple-600 bg-purple-50 rounded hover:bg-purple-100 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AITaskInput;
