import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-primary-600">FlowSync</h1>
          </div>
          <div className="flex space-x-4">
            <Link to="/" className="text-gray-600 hover:text-primary-600 px-3 py-2 text-sm font-medium">
              Dashboard
            </Link>
            <Link to="/tasks" className="text-gray-600 hover:text-primary-600 px-3 py-2 text-sm font-medium">
              Tasks
            </Link>
            <Link to="/calendar" className="text-gray-600 hover:text-primary-600 px-3 py-2 text-sm font-medium">
              Calendar
            </Link>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;