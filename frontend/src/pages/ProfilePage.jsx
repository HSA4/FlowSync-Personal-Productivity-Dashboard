/** Profile Page */
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const ProfilePage = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600 mt-1">Manage your account settings and preferences.</p>
      </div>

      {/* Profile Card */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {/* Avatar Section */}
        <div className="bg-gradient-to-r from-primary-500 to-secondary-500 px-6 py-8">
          <div className="flex items-end gap-4">
            <div className="w-20 h-20 rounded-full bg-white flex items-center justify-center text-3xl shadow-lg">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <span className="text-primary-600">{user.name.charAt(0).toUpperCase()}</span>
              )}
            </div>
            <div className="pb-2">
              <h2 className="text-xl font-semibold text-white">{user.name}</h2>
              <p className="text-white/80 text-sm">{user.email}</p>
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Account Provider</label>
              <p className="mt-1 text-gray-900 capitalize">{user.provider}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Member Since</label>
              <p className="mt-1 text-gray-900">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
            {user.last_login && (
              <div>
                <label className="text-sm font-medium text-gray-500">Last Login</label>
                <p className="mt-1 text-gray-900">
                  {new Date(user.last_login).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Account Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Account Actions</h3>
        <div className="space-y-3">
          <button className="w-full flex items-center justify-between px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <span className="text-gray-700">Export my data</span>
            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button className="w-full flex items-center justify-between px-4 py-3 border border-red-200 rounded-lg hover:bg-red-50 transition-colors text-red-600">
            <span>Delete account</span>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
