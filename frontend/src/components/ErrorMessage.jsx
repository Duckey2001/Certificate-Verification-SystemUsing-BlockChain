import React from 'react';

const ErrorMessage = ({ message, onDismiss }) => {
  if (!message) return null;

  return (
    <div className="rounded-xl bg-red-50 border border-red-200 p-4 mb-4 animate-slideDown">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <span className="text-red-400 text-lg">⚠️</span>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm text-red-700">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-auto pl-3 text-red-400 hover:text-red-600"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;
