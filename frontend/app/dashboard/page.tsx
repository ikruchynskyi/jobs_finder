'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Briefcase,
  CheckCircle,
  Clock,
  TrendingUp,
  Calendar,
  Target,
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Stats {
  total: number;
  pending: number;
  applied: number;
  interviews: number;
  failed: number;
  success_rate: number;
}

export default function DashboardPage() {
  const { data: session } = useSession();
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentApplications, setRecentApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, appsRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/applications/stats/summary`, {
            headers: { Authorization: `Bearer ${session?.accessToken}` },
          }),
          axios.get(`${API_URL}/api/v1/applications/?limit=5`, {
            headers: { Authorization: `Bearer ${session?.accessToken}` },
          }),
        ]);

        setStats(statsRes.data);
        setRecentApplications(appsRes.data);
      } catch (error) {
        toast.error('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    if (session?.accessToken) {
      fetchData();
    }
  }, [session]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Applications',
      value: stats?.total || 0,
      icon: Briefcase,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      title: 'Applied',
      value: stats?.applied || 0,
      icon: CheckCircle,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      title: 'Pending',
      value: stats?.pending || 0,
      icon: Clock,
      color: 'from-amber-500 to-amber-600',
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
    },
    {
      title: 'Interviews',
      value: stats?.interviews || 0,
      icon: Target,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome back, {session?.user?.name?.split(' ')[0] || 'there'}! 👋
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Here's an overview of your job search progress
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`} />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
              {stat.value}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {stat.title}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Success Rate */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              Success Rate
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Applications successfully submitted
            </p>
          </div>
          <TrendingUp className="w-6 h-6 text-green-500" />
        </div>
        <div className="relative h-4 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${stats?.success_rate || 0}%` }}
            transition={{ duration: 1, delay: 0.5 }}
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-teal-500 to-green-500 rounded-full"
          />
        </div>
        <p className="mt-2 text-right text-2xl font-bold text-gradient">
          {(stats?.success_rate || 0).toFixed(1)}%
        </p>
      </motion.div>

      {/* Recent Applications */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent Applications
        </h3>
        {recentApplications.length > 0 ? (
          <div className="space-y-3">
            {recentApplications.map((app: any) => (
              <div
                key={app.id}
                className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white font-bold">
                    {app.job?.company?.[0] || 'J'}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {app.job?.title || 'Job Position'}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {app.job?.company || 'Company'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      app.status === 'APPLIED'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : app.status === 'PENDING'
                        ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                    }`}
                  >
                    {app.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No applications yet. Start applying to jobs!</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
