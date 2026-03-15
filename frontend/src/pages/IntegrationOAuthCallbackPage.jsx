/** Integration OAuth Callback Page */
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';

const IntegrationOAuthCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState(null);

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    const code = searchParams.get('code');
    const provider = sessionStorage.getItem('pending_integration');
    const state = searchParams.get('state');

    if (!code) {
      setStatus('error');
      setError('No authorization code received from OAuth provider');
      return;
    }

    if (!provider) {
      setStatus('error');
      setError('No pending integration found. Please try connecting again.');
      return;
    }

    try {
      const providerMap = {
        todoist: 'todoist',
        'google-calendar': 'google-calendar',
      };

      const apiProvider = providerMap[provider];
      if (!apiProvider) {
        throw new Error(`Unknown provider: ${provider}`);
      }

      const redirectUri = `${window.location.origin}/integrations/callback`;

      await apiService.integrationOAuthCallback(apiProvider, code, redirectUri);

      setStatus('success');
      sessionStorage.removeItem('pending_integration');

      // Redirect to integrations page after a short delay
      setTimeout(() => {
        navigate('/integrations', { replace: true });
      }, 1500);
    } catch (err) {
      console.error('OAuth callback failed:', err);
      setStatus('error');
      setError(err.response?.data?.detail || 'Failed to complete integration. Please try again.');
      sessionStorage.removeItem('pending_integration');
    }
  };

  return (
    <div className="min-h-[400px] flex items-center justify-center">
      <div className="text-center">
        {status === 'loading' && (
          <div className="space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <h2 className="text-lg font-semibold text-gray-900">Connecting your integration...</h2>
            <p className="text-sm text-gray-600">Please wait while we complete the authorization.</p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto">
              <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Integration Connected!</h2>
            <p className="text-sm text-gray-600">Redirecting you to the integrations page...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto">
              <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Connection Failed</h2>
            <p className="text-sm text-red-600">{error}</p>
            <button
              onClick={() => navigate('/integrations')}
              className="mt-4 px-4 py-2 text-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors"
            >
              Back to Integrations
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegrationOAuthCallbackPage;
