/** Settings Page */
import React from 'react';

const SettingsPage = () => {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Customize your FlowSync experience.</p>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Notifications</h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Email Notifications</p>
              <p className="text-sm text-gray-600">Receive daily summaries via email</p>
            </div>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition-colors">
              <span className="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Task Reminders</p>
              <p className="text-sm text-gray-600">Get reminded about upcoming deadlines</p>
            </div>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-600 transition-colors">
              <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* Appearance */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Appearance</h2>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
            <div className="flex gap-2">
              <button className="flex-1 px-4 py-2 border-2 border-primary-600 rounded-lg bg-primary-50 text-primary-700 font-medium">
                Light
              </button>
              <button className="flex-1 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 font-medium">
                Dark
              </button>
              <button className="flex-1 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 font-medium">
                System
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Privacy</h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Analytics</p>
              <p className="text-sm text-gray-600">Help improve FlowSync with anonymous usage data</p>
            </div>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-600 transition-colors">
              <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-lg border border-red-200">
        <div className="px-6 py-4 border-b border-red-200">
          <h2 className="font-semibold text-red-900">Danger Zone</h2>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-600 mb-4">
            Irreversible and destructive actions for your account.
          </p>
          <button className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors font-medium">
            Clear All Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
