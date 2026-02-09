'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  Zap,
  Clock,
  Hash,
  ArrowDownToLine,
  ArrowUpFromLine,
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ByService {
  service_type: string;
  request_count: number;
  total_tokens: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

interface AIUsageStats {
  total_requests: number;
  total_tokens: number;
  total_input_tokens: number;
  total_output_tokens: number;
  requests_today: number;
  tokens_today: number;
  by_service: ByService[];
}

const SERVICE_LABELS: Record<string, string> = {
  job_match: 'Job Matching',
  form_questions: 'Form Questions',
  data_extraction: 'Data Extraction',
};

export default function AIUsagePage() {
  const { data: session } = useSession();
  const [stats, setStats] = useState<AIUsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/users/ai-usage/stats`, {
          headers: { Authorization: `Bearer ${session?.accessToken}` },
        });
        setStats(res.data);
      } catch (error) {
        toast.error('Failed to load AI usage data');
      } finally {
        setLoading(false);
      }
    };

    if (session?.accessToken) {
      fetchStats();
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
      title: 'Total Requests',
      value: stats?.total_requests || 0,
      icon: Hash,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      title: 'Total Tokens',
      value: (stats?.total_tokens || 0).toLocaleString(),
      icon: Zap,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
    {
      title: 'Requests Today',
      value: stats?.requests_today || 0,
      icon: Clock,
      color: 'from-teal-500 to-teal-600',
      bgColor: 'bg-teal-100 dark:bg-teal-900/30',
    },
    {
      title: 'Tokens Today',
      value: (stats?.tokens_today || 0).toLocaleString(),
      icon: BarChart3,
      color: 'from-amber-500 to-amber-600',
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          AI Usage
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitor your Gemini AI token consumption and request history
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

      {/* Token Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Token Breakdown
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50">
            <div className="p-3 rounded-xl bg-green-100 dark:bg-green-900/30">
              <ArrowDownToLine className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {(stats?.total_input_tokens || 0).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Input Tokens</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50">
            <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/30">
              <ArrowUpFromLine className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {(stats?.total_output_tokens || 0).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Output Tokens</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Usage by Service */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Usage by Service
        </h3>
        {stats?.by_service && stats.by_service.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                  <th className="pb-3 font-medium">Service</th>
                  <th className="pb-3 font-medium">Requests</th>
                  <th className="pb-3 font-medium">Input Tokens</th>
                  <th className="pb-3 font-medium">Output Tokens</th>
                  <th className="pb-3 font-medium">Total Tokens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {stats.by_service.map((svc) => (
                  <tr key={svc.service_type} className="text-gray-900 dark:text-white">
                    <td className="py-3 font-medium">
                      {SERVICE_LABELS[svc.service_type] || svc.service_type}
                    </td>
                    <td className="py-3">{svc.request_count}</td>
                    <td className="py-3">{svc.total_input_tokens.toLocaleString()}</td>
                    <td className="py-3">{svc.total_output_tokens.toLocaleString()}</td>
                    <td className="py-3 font-semibold">{svc.total_tokens.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No AI usage data yet. Usage will appear here after AI-powered applications.</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
