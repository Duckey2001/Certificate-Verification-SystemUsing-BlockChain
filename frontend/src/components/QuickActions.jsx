import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FiPlus, FiDownload, FiRefreshCw, FiSettings, FiUsers, FiFileText, FiShield, FiActivity } from 'react-icons/fi';

const QuickActions = ({ actions = [], className = "" }) => {
  const [loading, setLoading] = useState({});

  const defaultActions = [
    {
      id: 'add-user',
      label: 'Add User',
      icon: FiUsers,
      color: 'from-blue-500 to-blue-600',
      onClick: () => console.log('Add user clicked')
    },
    {
      id: 'issue-certificate',
      label: 'Issue Certificate',
      icon: FiFileText,
      color: 'from-green-500 to-green-600',
      onClick: () => console.log('Issue certificate clicked')
    },
    {
      id: 'system-scan',
      label: 'System Scan',
      icon: FiShield,
      color: 'from-purple-500 to-purple-600',
      onClick: () => console.log('System scan clicked')
    },
    {
      id: 'export-data',
      label: 'Export Data',
      icon: FiDownload,
      color: 'from-yellow-500 to-yellow-600',
      onClick: () => console.log('Export data clicked')
    }
  ];

  const allActions = actions.length > 0 ? actions : defaultActions;

  const handleActionClick = async (action) => {
    setLoading(prev => ({ ...prev, [action.id]: true }));
    
    try {
      await action.onClick();
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setLoading(prev => ({ ...prev, [action.id]: false }));
    }
  };

  return (
    <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${className}`}>
      {allActions.map((action, index) => (
        <motion.button
          key={action.id}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleActionClick(action)}
          disabled={loading[action.id]}
          className="relative p-4 bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 group overflow-hidden"
        >
          {/* Background gradient */}
          <div className={`absolute inset-0 bg-gradient-to-r ${action.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
          
          {/* Loading overlay */}
          {loading[action.id] && (
            <div className="absolute inset-0 bg-white/50 dark:bg-gray-800/50 flex items-center justify-center rounded-2xl">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="w-6 h-6 border-2 border-current border-t-transparent rounded-full"
              />
            </div>
          )}

          {/* Content */}
          <div className="relative z-10">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${action.color} flex items-center justify-center text-white mb-3 mx-auto group-hover:scale-110 transition-transform duration-300`}>
              <action.icon className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-1">
              {action.label}
            </h4>
            {action.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                {action.description}
              </p>
            )}
          </div>

          {/* Hover effect */}
          <motion.div
            className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{ background: `linear-gradient(to right, ${action.color.split(' ')[1]}, ${action.color.split(' ')[3]})` }}
          />
        </motion.button>
      ))}
    </div>
  );
};

export default QuickActions;
