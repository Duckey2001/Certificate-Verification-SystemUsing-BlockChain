import React, { useState, useEffect } from 'react';

const RecentActivity = ({ title = "Recent Activity", limit = 10 }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRealActivities = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/admin/system-logs?limit=10');
        
        // Check if response is OK
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Check content type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Received non-JSON response from server');
        }
        
        const data = await response.json();
        
        const formattedActivities = data.logs?.map(log => ({
          id: log.id,
          type: log.event_type,
          description: getEventDescription(log),
          timestamp: log.created_at,
          user: { username: log.actor_role || 'System' }
        })) || [];
        setActivities(formattedActivities);
      } catch (error) {
        console.error('Failed to fetch activities:', error);
        // Set fallback data or show error to user
        setActivities([]); // or some mock data
      } finally {
        setLoading(false);
      }
    };

    const getEventDescription = (log) => {
      switch (log.event_type) {
        case 'certificate_issued':
          return `New certificate issued for ${log.payload?.student_name || 'Student'}`;
        case 'certificate_verified':
          return 'Certificate verified';
        case 'payment_confirmed':
          return `Payment of M${log.payload?.amount || '0'} received`;
        case 'bulk_upload':
          return 'Bulk upload of certificates';
        case 'user_registered':
          return 'New user registered';
        case 'user_approved':
          return 'User approved';
        default:
          return 'System activity';
      }
    };

    fetchRealActivities();
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
