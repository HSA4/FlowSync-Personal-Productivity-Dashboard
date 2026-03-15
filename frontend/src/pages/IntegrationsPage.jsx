/** Integrations Page */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { apiService } from '../services/api';
import { useNavigate } from 'react-router-dom';

const SYNC_STATUS_CONFIG = {
  idle: {
    label: 'Idle',
    color: 'gray',
    icon: '●',
  },
  synced: {
    label: 'Synced',
    color: 'green',
    icon: '✓',
  },
  syncing: {
    label: 'Syncing',
    color: 'blue',
    icon: '⟳',
    animate: true,
  },
  pending_sync: {
    label: 'Pending',
    color: 'yellow',
    icon: '⏳',
  },
  disabled: {
    label: 'Disabled',
    color: 'gray',
    icon: '○',
  },
};

const PROVIDER_CONFIG = {
  todoist: {
    id: 'todoist',
    name: 'Todoist',
    description: 'Sync your tasks from Todoist',
    icon: '📋',
    color: 'red',
  },
  'google-calendar': {
    id: 'google-calendar',
    name: 'Google Calendar',
    description: 'Sync your events with Google Calendar',
    icon: '📅',
    color: 'blue',
  },
  gmail: {
    id: 'gmail',
    name: 'Gmail',
    description: 'Get email summaries and task suggestions',
    icon: '📧',
    color: 'red',
  },
  github: {
    id: 'github',
    name: 'GitHub',
    description: 'Track issues and pull requests',
    icon: '🐙',
    color: 'gray',
  },
};

const IntegrationsPage = () => {
  const navigate = useNavigate();
  const [providers, setProviders] = useState([]);
  const [userIntegrations, setUserIntegrations] = useState([]);
  const [syncStatus, setSyncStatus] = useState({ overall: 'idle', integrations: [] });
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState({});
  const [error, setError] = useState(null);
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    fetchProviders();
    fetchIntegrations();
    startPolling();

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const startPolling = useCallback(() => {
    // Poll sync status every 10 seconds
    fetchSyncStatus();
    pollIntervalRef.current = setInterval(() => {
      fetchSyncStatus();
    }, 10000);
  }, []);

  const fetchSyncStatus = async () => {
    try {
      const response = await apiService.getSyncStatus();
      setSyncStatus(response.data);
    } catch (err) {
      // Silently fail for status updates
      console.debug('Failed to fetch sync status:', err);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await apiService.getAvailableProviders();
      setProviders(response.data);
    } catch (err) {
      console.error('Failed to fetch providers:', err);
      setError('Failed to load available integrations');
    }
  };

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      const response = await apiService.getIntegrations();
      setUserIntegrations(response.data);
    } catch (err) {
      console.error('Failed to fetch integrations:', err);
      if (err.response?.status !== 401) {
        setError('Failed to load your integrations');
      }
    } finally {
      setLoading(false);
    }
  };

  const getIntegrationForProvider = (providerId) => {
    return userIntegrations.find((i) => i.provider === providerId && i.enabled);
  };

  const handleConnect = async (providerId) => {
    try {
      // Store the intended action for callback handling
      sessionStorage.setItem('pending_integration', providerId);

      // Get OAuth URL
      const endpoint =
        providerId === 'todoist'
          ? apiService.getTodoistOAuthUrl
          : apiService.getGoogleCalendarOAuthUrl;

      const response = await endpoint(window.location.origin + '/integrations/callback');

      // Redirect to OAuth provider
      window.location.href = response.data.url;
    } catch (err) {
      console.error('Failed to initiate OAuth flow:', err);
      setError('Failed to connect integration. Please try again.');
    }
  };

  const handleDisconnect = async (integration) => {
    try {
      await apiService.deleteIntegration(integration.id);
      setUserIntegrations((prev) => prev.filter((i) => i.id !== integration.id));
    } catch (err) {
      console.error('Failed to disconnect integration:', err);
      setError('Failed to disconnect integration. Please try again.');
    }
  };

  const handleSync = async (integration) => {
    try {
      setSyncing((prev) => ({ ...prev, [integration.id]: true }));

      const response = await apiService.syncIntegration(integration.id);

      if (response.data.status === 'error') {
        setError('Sync failed: ' + (response.data.error_message || 'Unknown error'));
      } else {
        // Refresh integrations to get updated last_sync time
        await fetchIntegrations();
      }
    } catch (err) {
      console.error('Failed to sync integration:', err);
      setError('Failed to sync integration. Please try again.');
    } finally {
      setSyncing((prev) => ({ ...prev, [integration.id]: false }));
    }
  };

  const toggleEnabled = async (integration) => {
    try {
      const newEnabled = !integration.enabled;
      await apiService.updateIntegration(integration.id, newEnabled);
      setUserIntegrations((prev) =>
        prev.map((i) => (i.id === integration.id ? { ...i, enabled: newEnabled } : i))
      );
    } catch (err) {
      console.error('Failed to toggle integration:', err);
      setError('Failed to update integration. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-600 mt-1">
          Connect your favorite tools to FlowSync for a unified productivity experience.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-600">{error}</p>
          <button
            onClick={() => setError(null)}
            className="mt-2 text-sm text-red-700 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Integration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {providers.map((provider) => {
          const config = PROVIDER_CONFIG[provider.id] || {
            id: provider.id,
            name: provider.name,
            description: provider.description,
            icon: '🔌',
            color: 'gray',
          };

          const integration = getIntegrationForProvider(provider.id);
          const isConnected = !!integration;

          // Get sync status for this integration
          const integrationStatus = syncStatus.integrations.find(
            (s) => s.id === integration?.id
          );
          const statusConfig = integrationStatus
            ? SYNC_STATUS_CONFIG[integrationStatus.status] || SYNC_STATUS_CONFIG.idle
            : SYNC_STATUS_CONFIG.idle;

          return (
            <div
              key={provider.id}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center text-2xl">
                  {config.icon}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">{config.name}</h3>
                    <div className="flex items-center gap-2">
                      {isConnected && (
                        <>
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              integration.enabled
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {integration.enabled ? 'Connected' : 'Disabled'}
                          </span>
                          {/* Sync Status Indicator */}
                          {integration.enabled && integrationStatus && (
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-${statusConfig.color}-100 text-${statusConfig.color}-800 ${
                                statusConfig.animate ? 'animate-pulse' : ''
                              }`}
                            >
                              <span>{statusConfig.icon}</span>
                              {statusConfig.label}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{config.description}</p>

                  {isConnected ? (
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center justify-between">
                        {integrationStatus?.last_sync && (
                          <p className="text-xs text-gray-500">
                            Last synced: {new Date(integrationStatus.last_sync).toLocaleString()}
                          </p>
                        )}
                        {integrationStatus?.webhook_registered && (
                          <span className="text-xs text-green-600 flex items-center gap-1">
                            <span>🔔</span> Webhook active
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleSync(integration)}
                          disabled={syncing[integration.id]}
                          className="px-3 py-1.5 text-sm font-medium text-primary-600 border border-primary-600 rounded hover:bg-primary-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {syncing[integration.id] ? 'Syncing...' : 'Sync Now'}
                        </button>
                        <button
                          onClick={() => toggleEnabled(integration)}
                          className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                            integration.enabled
                              ? 'text-gray-600 border border-gray-300 hover:bg-gray-50'
                              : 'text-yellow-600 border border-yellow-300 hover:bg-yellow-50'
                          }`}
                        >
                          {integration.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleDisconnect(integration)}
                          className="text-sm text-red-600 hover:text-red-700"
                        >
                          Disconnect
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleConnect(provider.id)}
                      className="mt-4 px-4 py-2 text-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors"
                    >
                      Connect
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Coming Soon Banner */}
      <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-lg p-6 border border-primary-100">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">More integrations coming soon!</h3>
            <p className="text-sm text-gray-600 mt-1">
              We're working on adding support for more tools. Stay tuned for updates.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationsPage;
