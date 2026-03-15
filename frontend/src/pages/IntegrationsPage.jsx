/** Integrations Page */
import React, { useState } from 'react';

const availableIntegrations = [
  {
    id: 'todoist',
    name: 'Todoist',
    description: 'Sync your tasks from Todoist',
    icon: '📋',
    color: 'red',
    connected: false,
  },
  {
    id: 'google-calendar',
    name: 'Google Calendar',
    description: 'Sync your events with Google Calendar',
    icon: '📅',
    color: 'blue',
    connected: false,
  },
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Get email summaries and task suggestions',
    icon: '📧',
    color: 'red',
    connected: false,
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Track issues and pull requests',
    icon: '🐙',
    color: 'gray',
    connected: false,
  },
];

const IntegrationsPage = () => {
  const [integrations, setIntegrations] = useState(availableIntegrations);

  const handleConnect = (integrationId) => {
    console.log('Connecting to', integrationId);
    // TODO: Implement OAuth flow for each integration
  };

  const handleDisconnect = (integrationId) => {
    console.log('Disconnecting', integrationId);
    setIntegrations((prev) =>
      prev.map((i) => (i.id === integrationId ? { ...i, connected: false } : i))
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-600 mt-1">
          Connect your favorite tools to FlowSync for a unified productivity experience.
        </p>
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrations.map((integration) => (
          <div
            key={integration.id}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className={`w-12 h-12 rounded-lg bg-${integration.color}-100 flex items-center justify-center text-2xl`}>
                {integration.icon}
              </div>

              {/* Content */}
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{integration.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{integration.description}</p>

                {integration.connected ? (
                  <div className="mt-4 flex items-center gap-2">
                    <span className="flex items-center gap-1 text-sm text-green-600">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Connected
                    </span>
                    <button
                      onClick={() => handleDisconnect(integration.id)}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Disconnect
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => handleConnect(integration.id)}
                    className="mt-4 px-4 py-2 text-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
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
