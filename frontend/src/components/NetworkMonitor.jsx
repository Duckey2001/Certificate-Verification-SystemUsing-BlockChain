import React, { useState, useEffect } from 'react';
import { adminApi } from '../api';

const NetworkMonitor = () => {
  const [networkHealth, setNetworkHealth] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [institutionSummaries, setInstitutionSummaries] = useState([]);
  const [selectedInstitution, setSelectedInstitution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  useEffect(() => {
    fetchNetworkData();
    if (autoRefresh) {
      const interval = setInterval(fetchNetworkData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const fetchNetworkData = async () => {
    try {
      setLoading(true);
      
      // Fetch network health
      try {
        const healthResponse = await fetch('/api/blockchain/network-health');
        if (healthResponse.ok) {
          const health = await healthResponse.json();
          setNetworkHealth(health);
        }
      } catch (healthError) {
        console.warn('Network health endpoint not available:', healthError);
      }
      
      // Fetch recent activity - handle 404 gracefully
      try {
        const activityResponse = await fetch('/api/admin/system-logs?limit=20');
        if (activityResponse.ok) {
          const activityData = await activityResponse.json();
          setRecentActivity(activityData.logs || []);
        } else if (activityResponse.status === 404) {
          // Endpoint not found, use empty array
          setRecentActivity([]);
        }
      } catch (activityError) {
        console.warn('System logs endpoint not available:', activityError);
        setRecentActivity([]);
      }
      
      // Fetch institution summaries - handle 404 gracefully
      try {
        const institutionsResponse = await fetch('/api/admin/institutions');
        if (institutionsResponse.ok) {
          const institutions = await institutionsResponse.json();
          
          // Get detailed summaries for each institution
          const summaries = await Promise.all(
            institutions.slice(0, 5).map(async (inst) => {
              try {
                const summaryResponse = await fetch(`/api/blockchain/institution-activity?institution_code=${inst.code}`);
                if (summaryResponse.ok) {
                  return await summaryResponse.json();
                }
              } catch (summaryError) {
                console.warn(`Failed to fetch summary for ${inst.code}:`, summaryError);
              }
              return null;
            })
          );
          setInstitutionSummaries(summaries.filter(Boolean));
        } else if (institutionsResponse.status === 404) {
          setInstitutionSummaries([]);
        }
      } catch (institutionsError) {
        console.warn('Institutions endpoint not available:', institutionsError);
        setInstitutionSummaries([]);
      }
      
    } catch (error) {
      console.error('Failed to fetch network data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthIcon = (score) => {
    if (score >= 80) return '✅';
    if (score >= 60) return '⚠️';
    return '❌';
  };

  const getEventIcon = (eventType) => {
    if (eventType.includes('login')) return '👤';
    if (eventType.includes('certificate')) return '📜';
    if (eventType.includes('blockchain')) return '⛓️';
    if (eventType.includes('payment')) return '💰';
    if (eventType.includes('verification')) return '✅';
    if (eventType.includes('error') || eventType.includes('failed')) return '❌';
    return '📋';
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

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Network Monitor</h2>
            <p className="text-indigo-100">Real-time monitoring of all network activity</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="autoRefresh" className="text-sm">Auto-refresh</label>
            </div>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              className="bg-indigo-700 text-white rounded px-3 py-1 text-sm"
            >
              <option value={10000}>10s</option>
              <option value={30000}>30s</option>
              <option value={60000}>1m</option>
            </select>
            <button
              onClick={fetchNetworkData}
              className="bg-white text-indigo-600 px-4 py-2 rounded-lg hover:bg-indigo-50 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Network Health Overview */}
      {networkHealth && (
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Network Health</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-green-600 text-sm font-medium">Status</div>
                  <div className="text-xl font-bold text-green-800 capitalize">
                    {networkHealth.status || 'healthy'}
                  </div>
                </div>
                <div className="text-3xl">
                  {getHealthIcon(networkHealth.health_score || 100)}
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="text-blue-600 text-sm font-medium">Active Users</div>
              <div className="text-xl font-bold text-blue-800">
                {networkHealth.users?.active || 0}
              </div>
              <div className="text-xs text-blue-600">
                of {networkHealth.users?.total || 0} total
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="text-purple-600 text-sm font-medium">Certificates</div>
              <div className="text-xl font-bold text-purple-800">
                {networkHealth.certificates?.on_blockchain || 0}
              </div>
              <div className="text-xs text-purple-600">
                on blockchain
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl p-4 border border-yellow-200">
              <div className="text-yellow-600 text-sm font-medium">Activity (1h)</div>
              <div className="text-xl font-bold text-yellow-800">
                {networkHealth.activity?.recent_1h || 0}
              </div>
              <div className="text-xs text-yellow-600">
                events
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Institution Activity */}
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Institution Activity</h3>
        {institutionSummaries.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">🏫</div>
            <p className="text-gray-500">No institution activity yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {institutionSummaries.map((summary, index) => (
              <div
                key={summary.institution?.code || index}
                className="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => setSelectedInstitution(summary)}
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-800">
                    {summary.institution?.name || 'Unknown Institution'}
                  </h4>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {summary.institution?.code || 'N/A'}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Active Users:</span>
                    <span className="font-medium">{summary.users?.active || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Certificates:</span>
                    <span className="font-medium">{summary.certificates?.total || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">On Blockchain:</span>
                    <span className="font-medium">{summary.certificates?.on_blockchain || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Recent Activity:</span>
                    <span className="font-medium">{summary.activity?.recent_events_24h || 0}</span>
                  </div>
                </div>
                
                {summary.health_score && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Health Score:</span>
                      <span className={`font-bold ${getHealthColor(summary.health_score)}`}>
                        {summary.health_score}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Activity Feed */}
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Recent Network Activity</h3>
          <span className="text-sm text-gray-500">
            Last {recentActivity.length} events
          </span>
        </div>
        
        {recentActivity.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-gray-500">No recent activity</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recentActivity.map((event, index) => (
              <div
                key={`${event.id}-${index}`}
                className={`flex items-start space-x-3 p-3 rounded-lg border ${getSeverityColor(event.severity || 'low')}`}
              >
                <span className="text-xl flex-shrink-0 mt-1">
                  {getEventIcon(event.event_type)}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900 truncate">
                      {event.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                      {formatTimeAgo(event.created_at)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    by {event.actor_username || 'Unknown'} 
                    {event.institution_code && (
                      <span className="ml-1">
                        from <span className="font-medium">{event.institution_code}</span>
                      </span>
                    )}
                  </div>
                  {event.certificate_hash && (
                    <div className="text-xs text-gray-500 mt-1 font-mono">
                      Cert: {event.certificate_hash.slice(0, 12)}...
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Institution Detail Modal */}
      {selectedInstitution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">
                {selectedInstitution.institution?.name || 'Institution Details'}
              </h3>
              <button
                onClick={() => setSelectedInstitution(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              {/* User Stats */}
              <div>
                <h4 className="font-semibold text-gray-800 mb-3">Users</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedInstitution.users?.total || 0}
                    </div>
                    <div className="text-sm text-blue-600">Total</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {selectedInstitution.users?.active || 0}
                    </div>
                    <div className="text-sm text-green-600">Active</div>
                  </div>
                  <div className="bg-red-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {selectedInstitution.users?.inactive || 0}
                    </div>
                    <div className="text-sm text-red-600">Inactive</div>
                  </div>
                </div>
              </div>
              
              {/* Certificate Stats */}
              <div>
                <h4 className="font-semibold text-gray-800 mb-3">Certificates</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-purple-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedInstitution.certificates?.total || 0}
                    </div>
                    <div className="text-sm text-purple-600">Total</div>
                  </div>
                  <div className="bg-indigo-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-indigo-600">
                      {selectedInstitution.certificates?.on_blockchain || 0}
                    </div>
                    <div className="text-sm text-indigo-600">On Blockchain</div>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {selectedInstitution.certificates?.pending || 0}
                    </div>
                    <div className="text-sm text-yellow-600">Pending</div>
                  </div>
                </div>
              </div>
              
              {/* Activity Breakdown */}
              {selectedInstitution.activity?.breakdown_7d && (
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">7-Day Activity Breakdown</h4>
                  <div className="space-y-2">
                    {selectedInstitution.activity.breakdown_7d.map((activity, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 capitalize">
                          {activity.event_type.replace(/_/g, ' ')}
                        </span>
                        <span className="font-medium">{activity.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkMonitor;
