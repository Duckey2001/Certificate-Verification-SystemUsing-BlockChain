import React from 'react';
import { motion } from 'framer-motion';
import { Line, Bar, Doughnut, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AdminCharts = ({ data, period, onPeriodChange }) => {
  const userGrowthData = {
    labels: data?.userGrowth?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'New Users',
        data: data?.userGrowth?.values || [12, 19, 23, 25, 32, 38],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Active Users',
        data: data?.activeUsers?.values || [45, 52, 58, 65, 72, 78],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  const certificateStatsData = {
    labels: data?.certificateStats?.labels || ['Issued', 'Verified', 'Pending', 'Revoked'],
    datasets: [
      {
        data: data?.certificateStats?.values || [1250, 1180, 45, 25],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)'
        ],
        borderWidth: 0
      }
    ]
  };

  const revenueData = {
    labels: data?.revenue?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Revenue',
        data: data?.revenue?.values || [12000, 15000, 18000, 22000, 25000, 28000],
        backgroundColor: 'rgba(251, 191, 36, 0.8)',
        borderColor: 'rgb(251, 191, 36)',
        borderWidth: 2,
        borderRadius: 8
      }
    ]
  };

  const verificationTrendsData = {
    labels: data?.verificationTrends?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Successful',
        data: data?.verificationTrends?.successful || [65, 72, 68, 81, 79, 62, 55],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        tension: 0.4
      },
      {
        label: 'Failed',
        data: data?.verificationTrends?.failed || [5, 8, 6, 4, 7, 9, 6],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        tension: 0.4
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Analytics Overview</h3>
        <select
          value={period}
          onChange={(e) => onPeriodChange(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="1y">Last year</option>
        </select>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6"
        >
          <h4 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">User Growth</h4>
          <div className="h-64">
            <Line data={userGrowthData} options={chartOptions} />
          </div>
        </motion.div>

        {/* Certificate Statistics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6"
        >
          <h4 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Certificate Status</h4>
          <div className="h-64">
            <Doughnut data={certificateStatsData} options={pieOptions} />
          </div>
        </motion.div>

        {/* Revenue Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6"
        >
          <h4 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Revenue Trends</h4>
          <div className="h-64">
            <Bar data={revenueData} options={chartOptions} />
          </div>
        </motion.div>

        {/* Verification Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6"
        >
          <h4 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Verification Trends</h4>
          <div className="h-64">
            <Line data={verificationTrendsData} options={chartOptions} />
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AdminCharts;
