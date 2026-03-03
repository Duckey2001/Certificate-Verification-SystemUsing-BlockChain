import React, { useState, useEffect } from 'react';

const BlockchainStatus = () => {
  const [status, setStatus] = useState({
    connected: true,
    blockHeight: 1234567,
    peers: 12,
    network: 'testnet'
  });
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setStatus(prev => ({
        ...prev,
        blockHeight: prev.blockHeight + 1,
        peers: Math.floor(Math.random() * 5) + 10
      }));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={`flex items-center space-x-2 px-4 py-2 rounded-full shadow-lg ${
          status.connected 
            ? 'bg-gradient-to-r from-green-500 to-green-600 text-white' 
            : 'bg-gradient-to-r from-red-500 to-red-600 text-white'
        }`}
      >
        <span className={`w-2 h-2 rounded-full ${status.connected ? 'bg-white animate-pulse' : 'bg-white'}`}></span>
        <span className="text-sm font-medium">
          {status.connected ? 'Blockchain Connected' : 'Blockchain Disconnected'}
        </span>
        <span className="text-xs opacity-75">{showDetails ? '▼' : '▲'}</span>
      </button>

      {showDetails && (
        <div className="absolute bottom-12 right-0 w-64 bg-white rounded-xl shadow-2xl border border-gray-200 p-4 mb-2">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Blockchain Status</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Network:</span>
              <span className="text-xs font-medium">{status.network}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Block Height:</span>
              <span className="text-xs font-medium">{status.blockHeight.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Connected Peers:</span>
              <span className="text-xs font-medium">{status.peers}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">Last Sync:</span>
              <span className="text-xs font-medium">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center text-xs text-green-600">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1"></span>
              All systems operational
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BlockchainStatus;
