import React from 'react';
import { motion } from 'framer-motion';
import { FiUsers, FiFileText, FiCheckCircle, FiXCircle, FiTrendingUp, FiDollarSign, FiActivity, FiShield } from 'react-icons/fi';

const AdminStats = ({ stats, loading }) => {
  const statCards = [
    {
      title: 'Total Users',
      value: stats?.totalUsers || 0,
      icon: FiUsers,
      color: 'from-blue-500 to-blue-600',
      change: stats?.userGrowth || '+12%',
      changeType: 'positive'
    },
    {
      title: 'Total Certificates',
      value: stats?.totalCertificates || 0,
      icon: FiFileText,
      color: 'from-green-500 to-green-600',
      change: stats?.certificateGrowth || '+8%',
      changeType: 'positive'
    },
    {
      title: 'Verified Certificates',
      value: stats?.verifiedCertificates || 0,
      icon: FiCheckCircle,
      color: 'from-emerald-500 to-emerald-600',
      change: stats?.verificationRate || '95%',
      changeType: 'positive'
    },
    {
      title: 'Failed Verifications',
      value: stats?.failedVerifications || 0,
      icon: FiXCircle,
      color: 'from-red-500 to-red-600',
      change: stats?.failureRate || '5%',
      changeType: 'negative'
    },
    {
      title: 'Revenue',
      value: `M${stats?.revenue || 0}`,
      icon: FiDollarSign,
      color: 'from-yellow-500 to-yellow-600',
      change: stats?.revenueGrowth || '+15%',
      changeType: 'positive'
    },
    {
      title: 'System Health',
      value: `${stats?.systemHealth || 98}%`,
      icon: FiActivity,
      color: 'from-purple-500 to-purple-600',
      change: 'Optimal',
      changeType: 'positive'
    },
    {
      title: 'Security Score',
      value: `${stats?.securityScore || 92}/100`,
      icon: FiShield,
      color: 'from-indigo-500 to-indigo-600',
      change: 'High',
      changeType: 'positive'
    },
    {
      title: 'Growth Rate',
      value: `${stats?.growthRate || 23}%`,
      icon: FiTrendingUp,
      color: 'from-pink-500 to-pink-600',
      change: stats?.monthlyGrowth || '+3%',
      changeType: 'positive'
    }
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat, index) => (
        <motion.div
          key={stat.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 border-l-4 border-transparent hover:border-blue-500"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${stat.color} flex items-center justify-center text-white shadow-lg`}>
              <stat.icon className="w-6 h-6" />
            </div>
            <span className={`text-sm font-medium ${
              stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
            }`}>
              {stat.change}
            </span>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-1">
            {stat.value}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {stat.title}
          </p>
        </motion.div>
      ))}
    </div>
  );
};

export default AdminStats;
