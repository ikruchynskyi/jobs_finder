'use client';

import { useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Building,
  MapPin,
  Calendar,
  ExternalLink,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Application {
  id: number;
  status: string;
  created_at: string;
  applied_at?: string;
  error_message?: string;
  screenshot_url?: string;
  job: {
    id: number;
    title: string;
    company: string;
    location: string;
    source_url: string;
    source: string;
  };
}

const statusColors: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  applied: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  rejected: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  interview: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  accepted: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
};

export default function ApplicationsPage() {
  const { data: session } = useSession();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/v1/applications/`, {
        headers: { Authorization: `Bearer ${session?.accessToken}` },
        params: {
          status: filter !== 'all' ? filter : undefined,
        },
      });
      setApplications(response.data);
    } catch (error) {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (session?.accessToken) {
      fetchApplications();
    }
  }, [session, filter]);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this application?')) return;

    try {
      await axios.delete(`${API_URL}/api/v1/applications/${id}`, {
        headers: { Authorization: `Bearer ${session?.accessToken}` },
      });
      toast.success('Application deleted');
      fetchApplications();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  const handleRetry = async (jobId: number) => {
    try {
      await axios.post(
        `${API_URL}/api/v1/applications/apply`,
        { job_id: jobId },
        {
          headers: { Authorization: `Bearer ${session?.accessToken}` },
        }
      );
      toast.success('Retrying application...');
      fetchApplications();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to retry application');
    }
  };

  const filters = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'applied', label: 'Applied' },
    { value: 'interview', label: 'Interview' },
    { value: 'rejected', label: 'Rejected' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            My Applications
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Track and manage your job applications
          </p>
        </div>
        <button
          onClick={fetchApplications}
          className="p-3 rounded-xl bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex gap-2 overflow-x-auto pb-2"
      >
        {filters.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`
              px-6 py-3 rounded-xl font-medium whitespace-nowrap transition-all
              ${filter === f.value
                ? 'bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg'
                : 'bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-700'
              }
            `}
          >
            {f.label}
          </button>
        ))}
      </motion.div>

      {/* Applications List */}
      {loading ? (
        <div className="flex items-center justify-center h-96">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : applications.length > 0 ? (
        <div className="space-y-4">
          {applications.map((app, index) => (
            <motion.div
              key={app.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
                    {app.job.company[0]}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-3 mb-2">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                        {app.job.title}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${statusColors[app.status] || statusColors.pending
                          }`}
                      >
                        {app.status.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400 mb-3">
                      <span className="flex items-center gap-1">
                        <Building className="w-4 h-4" />
                        {app.job.company}
                      </span>
                      {app.job.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {app.job.location}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        Applied: {format(new Date(app.created_at), 'MMM dd, yyyy')}
                      </span>
                      <span className="px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-xs">
                        {app.job.source}
                      </span>
                    </div>

                    {app.error_message && (
                      <div className="mt-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                        <p className="text-sm text-red-700 dark:text-red-400">
                          <strong>Error:</strong> {app.error_message}
                        </p>
                      </div>
                    )}

                    {app.applied_at && (
                      <p className="text-sm text-green-600 dark:text-green-400">
                        ✓ Successfully applied on {format(new Date(app.applied_at), 'MMM dd, yyyy HH:mm')}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-2 flex-shrink-0">
                  <a
                    href={app.job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 rounded-xl border-2 border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all flex items-center gap-2 text-sm whitespace-nowrap justify-center"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Job
                  </a>

                  {app.status === 'failed' && (
                    <button
                      onClick={() => handleRetry(app.job.id)}
                      className="px-4 py-2 rounded-xl bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50 transition-all flex items-center gap-2 text-sm whitespace-nowrap justify-center"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Retry
                    </button>
                  )}

                  {app.screenshot_url && (
                    <a
                      href={`${API_URL}${app.screenshot_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 rounded-xl bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-all flex items-center gap-2 text-sm whitespace-nowrap justify-center border border-red-200 dark:border-red-900/50"
                    >
                      <FileText className="w-4 h-4" />
                      View Error
                    </a>
                  )}

                  {(app.status === 'pending' || app.status === 'failed') && (
                    <button
                      onClick={() => handleDelete(app.id)}
                      className="px-4 py-2 rounded-xl bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-all flex items-center gap-2 text-sm whitespace-nowrap justify-center"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="glass rounded-2xl p-12 border border-gray-200 dark:border-gray-800 text-center">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            No applications yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Start applying to jobs to see them here
          </p>
          <a
            href="/dashboard/jobs"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold hover:shadow-lg transition-all"
          >
            Browse Jobs
          </a>
        </div>
      )}
    </div>
  );
}
