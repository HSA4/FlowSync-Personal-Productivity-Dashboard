/** Dashboard Component - Simplified for debugging */
import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [message, setMessage] = useState('Loading...');
  const [stats, setStats] = useState({ tasks: 0, events: 0 });

  useEffect(() => {
    // Simple data fetch without AuthContext for now
    const checkHealth = async () => {
      try {
        const response = await fetch('/health');
        const data = await response.json();
        setMessage('Connected to backend ✓');
        setStats({
          backend: data.status,
          database: data.database,
        });
      } catch (error) {
        setMessage(`Error: ${error.message}`);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          FlowSync Dashboard
        </h1>
        
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
          <p className="text-lg">{message}</p>
          
          {stats.backend && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-green-600 font-semibold">●</span>
                <span className="text-gray-700">Backend: {stats.backend}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600 font-semibold">●</span>
                <span className="text-gray-700">Database: {stats.database}</span>
              </div>
            </div>
          )}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Debug Information</h2>
          <p className="text-gray-600 mb-2">
            <strong>Frontend:</strong> React app served by Nginx
          </p>
          <p className="text-gray-600 mb-2">
            <strong>Backend API:</strong> Available at http://5.189.181.109:8000
          </p>
          <p className="text-gray-600 mb-2">
            <strong>API Docs:</strong> <a href="http://5.189.181.109:8000/docs" className="text-blue-600 hover:underline">Open Swagger UI</a>
          </p>
          <p className="text-gray-600">
            <strong>Monitor Dashboard:</strong> <a href="http://5.189.181.109:8080" className="text-blue-600 hover:underline">Open System Monitor</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
