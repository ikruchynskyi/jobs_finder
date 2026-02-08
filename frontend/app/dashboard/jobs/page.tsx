'use client';

import { useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  MapPin,
  Briefcase,
  DollarSign,
  ExternalLink,
  Check,
  Loader2,
  Filter,
  RefreshCw,
  Building,
  Calendar,
  Target,
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  salary_min?: number;
  salary_max?: number;
  remote: boolean;
  source: string;
  source_url: string;
  created_at: string;
  job_type?: string;
}

export default function JobsPage() {
  const { data: session } = useSession();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [crawling, setCrawling] = useState(false);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/v1/jobs/`, {
        headers: { Authorization: `Bearer ${session?.accessToken}` },
        params: {
          remote_only: remoteOnly,
        },
      });
      setJobs(response.data);
    } catch (error) {
      toast.error('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (session?.accessToken) {
      fetchJobs();
    }
  }, [session, remoteOnly]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/jobs/search`,
        {
          query: searchQuery,
          location: locationFilter || null,
          remote_only: remoteOnly,
        },
        {
          headers: { Authorization: `Bearer ${session?.accessToken}` },
        }
      );
      setJobs(response.data.results);
      toast.success(`Found ${response.data.count} jobs`);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCrawlJobs = async () => {
    if (!searchQuery.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setCrawling(true);
    try {
      await axios.post(
        `${API_URL}/api/v1/jobs/crawl`,
        {
          search_query: searchQuery,
          location: locationFilter || null,
          source: 'linkedin', // Default to LinkedIn
        },
        {
          headers: { Authorization: `Bearer ${session?.accessToken}` },
        }
      );
      toast.success('Job crawling started! New jobs will appear soon.');
      
      // Refresh jobs after a delay
      setTimeout(fetchJobs, 3000);
    } catch (error) {
      toast.error('Failed to start crawling');
    } finally {
      setCrawling(false);
    }
  };

  const handleApply = async (jobId: number) => {
    setApplying(jobId);
    try {
      await axios.post(
        `${API_URL}/api/v1/applications/apply`,
        { job_id: jobId },
        {
          headers: { Authorization: `Bearer ${session?.accessToken}` },
        }
      );
      toast.success('Application submitted! Processing in background.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to apply');
    } finally {
      setApplying(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Browse Jobs
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Search and apply to jobs across multiple platforms
        </p>
      </div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
                placeholder="Job title, keywords, or company"
              />
            </div>
          </div>

          <div className="relative">
            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
              placeholder="Location"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="w-5 h-5 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Remote only
            </span>
          </label>

          <div className="flex-1" />

          <button
            onClick={handleCrawlJobs}
            disabled={crawling}
            className="px-6 py-3 rounded-xl bg-amber-600 text-white hover:bg-amber-700 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {crawling ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Crawling...
              </>
            ) : (
              <>
                <Target className="w-5 h-5" />
                Crawl New Jobs
              </>
            )}
          </button>

          <button
            onClick={handleSearch}
            className="px-6 py-3 rounded-xl bg-teal-600 text-white hover:bg-teal-700 transition-colors flex items-center gap-2"
          >
            <Search className="w-5 h-5" />
            Search
          </button>

          <button
            onClick={fetchJobs}
            className="p-3 rounded-xl bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </motion.div>

      {/* Jobs List */}
      {loading ? (
        <div className="flex items-center justify-center h-96">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : jobs.length > 0 ? (
        <div className="space-y-4">
          {jobs.map((job, index) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800 hover:shadow-xl transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-start gap-4 mb-3">
                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
                      {job.company[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                        {job.title}
                      </h3>
                      <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Building className="w-4 h-4" />
                          {job.company}
                        </span>
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {job.location}
                          </span>
                        )}
                        {job.remote && (
                          <span className="px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium">
                            Remote
                          </span>
                        )}
                        {job.job_type && (
                          <span className="px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-medium">
                            {job.job_type}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {job.description && (
                    <p className="text-gray-700 dark:text-gray-300 mb-3 line-clamp-2">
                      {job.description}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-4 text-sm">
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                        <DollarSign className="w-4 h-4" />
                        {job.salary_min && job.salary_max
                          ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
                          : job.salary_min
                          ? `From $${job.salary_min.toLocaleString()}`
                          : `Up to $${job.salary_max?.toLocaleString()}`}
                      </span>
                    )}
                    <span className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(job.created_at), 'MMM dd, yyyy')}
                    </span>
                    <span className="px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs font-medium">
                      {job.source}
                    </span>
                  </div>
                </div>

                <div className="flex flex-col gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleApply(job.id)}
                    disabled={applying === job.id}
                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold hover:shadow-lg transition-all disabled:opacity-50 flex items-center gap-2 whitespace-nowrap"
                  >
                    {applying === job.id ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Applying...
                      </>
                    ) : (
                      <>
                        <Check className="w-5 h-5" />
                        Apply Now
                      </>
                    )}
                  </button>

                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-6 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-semibold hover:bg-gray-100 dark:hover:bg-gray-800 transition-all flex items-center gap-2 justify-center whitespace-nowrap"
                  >
                    <ExternalLink className="w-5 h-5" />
                    View Job
                  </a>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="glass rounded-2xl p-12 border border-gray-200 dark:border-gray-800 text-center">
          <Briefcase className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            No jobs found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Try searching for jobs or crawl new opportunities
          </p>
          <button
            onClick={handleCrawlJobs}
            disabled={crawling}
            className="px-6 py-3 rounded-xl bg-teal-600 text-white hover:bg-teal-700 transition-colors inline-flex items-center gap-2"
          >
            {crawling ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Crawling...
              </>
            ) : (
              <>
                <Target className="w-5 h-5" />
                Crawl Jobs
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
