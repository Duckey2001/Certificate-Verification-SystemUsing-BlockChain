import React, { useState, useEffect } from 'react';
import { blockchainApi } from '../api';

const BlockchainVisualization = () => {
  const [blocks, setBlocks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [networkStats, setNetworkStats] = useState(null);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [loading, setLoading] = useState(true);
  const [animationSpeed, setAnimationSpeed] = useState(2000);

  useEffect(() => {
    fetchBlockchainData();
    const interval = setInterval(fetchBlockchainData, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchBlockchainData = async () => {
    try {
      setLoading(true);
      const [statsRes, blocksRes] = await Promise.all([
        blockchainApi.getNetworkStats(),
        fetch('/api/blockchain/blocks').then(res => res.json()).catch(() => ({ blocks: [] }))
      ]);
      
      setNetworkStats(statsRes);
      setBlocks(blocksRes.blocks || []);
      
      // Get recent transactions
      const recentTxs = [];
      blocksRes.blocks?.forEach(block => {
        block.transactions?.forEach(tx => {
          recentTxs.push({
            hash: tx.hash,
            blockNumber: block.number,
            timestamp: block.timestamp,
            type: tx.type || 'certificate',
            from: tx.from || 'system',
            to: tx.to || 'network'
          });
        });
      });
      setTransactions(recentTxs.slice(0, 10));
    } catch (error) {
      console.error('Failed to fetch blockchain data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBlockColor = (block) => {
    if (block.verified) return 'bg-green-500';
    if (block.pending) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'certificate': return '📜';
      case 'verification': return '✅';
      case 'tamper': return '⚠️';
      default: return '🔗';
    }
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
        <h2 className="text-2xl font-bold mb-2">Blockchain Network Visualization</h2>
        <p className="text-purple-100">Real-time view of certificate transactions on the blockchain</p>
      </div>

      {/* Network Stats */}
      {networkStats && (
        <div className="p-6 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-purple-50 rounded-xl p-4">
              <div className="text-purple-600 text-sm font-medium">Total Blocks</div>
              <div className="text-2xl font-bold text-purple-800">{networkStats.totalBlocks || 0}</div>
            </div>
            <div className="bg-blue-50 rounded-xl p-4">
              <div className="text-blue-600 text-sm font-medium">Total Transactions</div>
              <div className="text-2xl font-bold text-blue-800">{networkStats.totalTransactions || 0}</div>
            </div>
            <div className="bg-green-50 rounded-xl p-4">
              <div className="text-green-600 text-sm font-medium">Certificates Stored</div>
              <div className="text-2xl font-bold text-green-800">{networkStats.certificatesStored || 0}</div>
            </div>
            <div className="bg-yellow-50 rounded-xl p-4">
              <div className="text-yellow-600 text-sm font-medium">Network Status</div>
              <div className="text-2xl font-bold text-green-800">Active</div>
            </div>
          </div>
        </div>
      )}

      {/* Blockchain Chain Visualization */}
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
          Live Blockchain Chain
        </h3>
        
        <div className="overflow-x-auto">
          <div className="flex space-x-4 pb-4">
            {blocks.length === 0 ? (
              <div className="text-center py-8 w-full">
                <div className="text-6xl mb-4">⛓️</div>
                <p className="text-gray-500">No blocks on the chain yet</p>
                <p className="text-sm text-gray-400 mt-2">Certificate issuances will appear here as blocks</p>
              </div>
            ) : (
              blocks.map((block, index) => (
                <div
                  key={block.number || index}
                  className={`flex-shrink-0 w-32 h-40 ${getBlockColor(block)} rounded-xl p-3 text-white cursor-pointer transform transition-all duration-200 hover:scale-105 relative`}
                  onClick={() => setSelectedBlock(block)}
                >
                  <div className="text-xs opacity-75">Block #{block.number || index}</div>
                  <div className="text-xs mt-1 opacity-90">
                    {block.transactions?.length || 0} txs
                  </div>
                  <div className="text-xs mt-2 opacity-75">
                    {formatTimeAgo(block.timestamp)}
                  </div>
                  {block.verified && (
                    <div className="absolute top-2 right-2">
                      <span className="text-xs">✓</span>
                    </div>
                  )}
                  <div className="absolute bottom-2 left-2 right-2">
                    <div className="text-xs opacity-75 truncate">
                      {block.hash ? `${block.hash.slice(0, 8)}...` : 'Pending'}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="p-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Recent Transactions</h3>
        
        {transactions.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-gray-500">No transactions yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transactions.map((tx, index) => (
              <div
                key={`${tx.hash}-${index}`}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getTransactionIcon(tx.type)}</span>
                  <div>
                    <div className="font-medium text-gray-900">
                      {tx.type === 'certificate' ? 'Certificate Issued' : 
                       tx.type === 'verification' ? 'Certificate Verified' : 
                       'Transaction'}
                    </div>
                    <div className="text-sm text-gray-500">
                      From: {tx.from} • Block: #{tx.blockNumber}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono text-gray-600">
                    {tx.hash ? `${tx.hash.slice(0, 8)}...` : 'Processing'}
                  </div>
                  <div className="text-xs text-gray-400">
                    {formatTimeAgo(tx.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Educational Info */}
      <div className="p-6 bg-gradient-to-r from-purple-50 to-blue-50 border-t border-purple-200">
        <h3 className="text-lg font-semibold mb-3 text-purple-800">Understanding the Blockchain</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">📦</div>
            <h4 className="font-semibold text-gray-800 mb-1">Blocks</h4>
            <p className="text-gray-600">Each block contains certificate transactions. Once added, they cannot be changed.</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">🔗</div>
            <h4 className="font-semibold text-gray-800 mb-1">Chain</h4>
            <p className="text-gray-600">Blocks are linked together using cryptography, creating a secure and unbreakable chain.</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">✅</div>
            <h4 className="font-semibold text-gray-800 mb-1">Verification</h4>
            <p className="text-gray-600">Anyone can verify certificate authenticity by checking the blockchain.</p>
          </div>
        </div>
      </div>

      {/* Block Detail Modal */}
      {selectedBlock && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Block #{selectedBlock.number || 'Unknown'}</h3>
              <button
                onClick={() => setSelectedBlock(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Block Hash</label>
                <div className="font-mono text-sm bg-gray-100 p-2 rounded">
                  {selectedBlock.hash || 'Pending...'}
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Timestamp</label>
                <div className="text-sm">
                  {selectedBlock.timestamp ? new Date(selectedBlock.timestamp).toLocaleString() : 'Pending...'}
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Transactions ({selectedBlock.transactions?.length || 0})</label>
                <div className="space-y-2 mt-2">
                  {selectedBlock.transactions?.map((tx, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-lg">
                      <div className="font-medium">{tx.type || 'Certificate Transaction'}</div>
                      <div className="text-sm text-gray-600 font-mono">
                        {tx.hash || 'Processing...'}
                      </div>
                    </div>
                  )) || <p className="text-gray-500">No transactions</p>}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BlockchainVisualization;
