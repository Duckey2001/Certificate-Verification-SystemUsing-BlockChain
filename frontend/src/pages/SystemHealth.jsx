// components/SystemHealth.jsx
import React from 'react';
import { motion } from 'framer-motion';
import { 
  FiServer, 
  FiCpu, 
  FiDatabase, 
  FiCloud,
  FiActivity,
  FiAlertCircle,
  FiCheck,
  FiX
} from 'react-icons/fi';

const SystemHealth = ({ health, alerts, loading }) => {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-100 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const metrics = [
    {
      label: 'Uptime',
      value: health?.uptime || '99.9%',
      icon: FiActivity,
      status: 'success',
      color: 'green'
    },
    {
      label: 'CPU Usage',
      value: health?.cpu_usage || '45%',
      icon: FiCpu,
      status: health?.cpu_usage > 80 ? 'warning' : 'success',
      color: health?.cpu_usage > 80 ? 'yellow' : 'green'
    },
    {
      label: 'Memory Usage',
      value: health?.memory_usage || '62%',
      icon: FiDatabase,
      status: health?.memory_usage > 85 ? 'error' : health?.memory_usage > 70 ? 'warning' : 'success',
      color: health?.memory_usage > 85 ? 'red' : health?.memory_usage > 70 ? 'yellow' : 'green'
    },
    {
      label: 'Storage',
      value: health?.storage_usage || '38%',
      icon: FiServer,
      status: health?.storage_usage > 90 ? 'error' : health?.storage_usage > 80 ? 'warning' : 'success',
      color: health?.storage_usage > 90 ? 'red' : health?.storage_usage > 80 ? 'yellow' : 'green'
    }
  ];

  const statusColors = {
    success: 'text-green-500 bg-green-100 dark:bg-green-900/20',
    warning: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/20',
    error: 'text-red-500 bg-red-100 dark:bg-red-900/20'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden"
    >
      <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <FiServer className="mr-2" />
          System Health
        </h3>
      </div>

      <div className="p-6">
        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          {metrics.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${statusColors[metric.status]} mb-3`}>
                  <Icon className="w-6 h-6" />
                </div>
                <p className="text-2xl font-bold text-gray-800 dark:text-white">
                  {metric.value}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {metric.label}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Service Status */}
        <div className="mb-8">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            Service Status
          </h4>
          <div className="space-y-3">
            {health?.services?.map((service, index) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {service.status === 'operational' ? (
                    <FiCheck className="w-5 h-5 text-green-500" />
                  ) : service.status === 'degraded' ? (
                    <FiAlertCircle className="w-5 h-5 text-yellow-500" />
                  ) : (
                    <FiX className="w-5 h-5 text-red-500" />
                  )}
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {service.name}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  service.status === 'operational' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                  service.status === 'degraded' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                  'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                }`}>
                  {service.status}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        {alerts?.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
              Recent Alerts
            </h4>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert, index) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-3 rounded-lg border-l-4 ${
                    alert.severity === 'high' ? 'border-red-500 bg-red-50 dark:bg-red-900/10' :
                    alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10' :
                    'border-blue-500 bg-blue-50 dark:bg-blue-900/10'
                  }`}
                >
                  <div className="flex items-start">
                    <FiAlertCircle className={`w-4 h-4 mr-2 mt-0.5 ${
                      alert.severity === 'high' ? 'text-red-500' :
                      alert.severity === 'medium' ? 'text-yellow-500' :
                      'text-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {alert.message}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default SystemHealth;