import React from 'react';
import { Link } from 'react-router-dom';

const Demo = () => (
  <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
    <div className="max-w-2xl w-full bg-white rounded-xl shadow-lg p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">CertiVert Demo</h1>
      <p className="text-gray-600 mb-6">
        See CertiVert in action. Register for a free account to try certificate issuance and verification with blockchain.
      </p>
      <div className="space-y-4">
        <Link
          to="/register"
          className="block w-full py-3 px-4 bg-indigo-600 text-white text-center font-medium rounded-lg hover:bg-indigo-700"
        >
          Get Started Free
        </Link>
        <Link
          to="/"
          className="block w-full py-3 px-4 border border-gray-300 text-gray-700 text-center font-medium rounded-lg hover:bg-gray-50"
        >
          Back to Home
        </Link>
      </div>
      <p className="mt-6 text-sm text-gray-500">
        Already have an account? <Link to="/login" className="text-indigo-600 hover:underline">Sign in</Link>
      </p>
    </div>
  </div>
);

export default Demo;
