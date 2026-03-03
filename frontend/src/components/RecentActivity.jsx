import React, { useState, useEffect } from 'react';

const RecentActivity = ({ title = "Recent Activity", limit = 10 }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching activities
    const mockActivities = [
      { id: 1, type: 'certificate_issued', description: 'New certificate issued for John Doe', timestamp: new Date(), user: { username: 'Issuer' } },
      { id: 2, type: 'certificate_verified', description: 'Certificate verified by Verifier', timestamp: new Date(Date.now() - 3600000), user: { username: 'Verifier' } },
      { id: 3, type: 'payment_received', description: 'Payment of M300 received', timestamp: new Date(Date.now() - 7200000), user: { username: 'System' } },
      { id: 4, type: 'bulk_upload', description: 'Bulk upload of 5 certificates', timestamp: new Date(Date.now() - 86400000), user: { username: 'Issuer' } },
    ];
    
    setActivities(mockActivities.slice(0, limit));
    setLoading(false);
  }, [limit]);

  const getActivityIcon = (type) => {
    switch(type) {
      case 'certificate_issued': return '📜';
      case 'certificate_verified': return '✓';
      case 'certificate_revoked': return '🚫';
      case 'payment_received': return '💰';
      case 'user_registered': return '👤';
      case 'bulk_upload': return '📤';
      default: return '📋';
    }
  };

  const getActivityColor = (type) => {
    switch(type) {
      case 'certificate_issued': return 'bg-green-100 text-green-800';
      case 'certificate_verified': return 'bg-blue-100 text-blue-800';
      case 'certificate_revoked': return 'bg-red-100 text-red-800';
      case 'payment_received': return 'bg-purple-100 text-purple-800';
      case 'user_registered': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const activityDate = new Date(timestamp);
    const diffInSeconds = Math.floor((now - activityDate) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex items-center space-x-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      
      <div className="p-6">
        {activities.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">📊</div>
            <p className="text-gray-500">No recent activity</p>
          </div>
        ) : (
          <div className="space-y-4">
            {activities.map((activity, index) => (
              <div
                key={activity.id || index}
                className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-xl transition-colors animate-fadeIn"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${getActivityColor(activity.type)}`}>
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {activity.description}
                    </p>
                    <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                      {formatTimeAgo(activity.timestamp)}
                    </span>
                  </div>
                  <div className="flex items-center mt-1">
                    <span className="text-xs text-gray-500">
                      {activity.user?.username || 'System'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentActivity;
