'use client';

import { signIn, useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Sparkles, Zap, Target, TrendingUp, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function HomePage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session) {
      router.push('/dashboard');
    }
  }, [session, router]);

  const handleGoogleSignIn = () => {
    signIn('google', { callbackUrl: '/dashboard' });
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-teal-50/30 to-amber-50/30 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-400/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-amber-400/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 px-6 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-amber-600 bg-clip-text text-transparent">
              AutoApply
            </span>
          </motion.div>

          <motion.button
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => router.push('/auth/signin')}
            className="px-6 py-2.5 rounded-xl border-2 border-gray-900 dark:border-white text-sm font-semibold hover:bg-gray-900 hover:text-white dark:hover:bg-white dark:hover:text-gray-900 transition-all"
          >
            Sign In
          </motion.button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 px-6 pt-20 pb-32">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-center max-w-4xl mx-auto mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 text-sm font-medium mb-8">
              <Sparkles className="w-4 h-4" />
              AI-Powered Job Applications
            </div>

            <h1 className="text-6xl md:text-7xl font-bold mb-8 leading-tight">
              Land Your Dream Job
              <span className="block text-gradient mt-2">
                On Autopilot
              </span>
            </h1>

            <p className="text-xl text-gray-600 dark:text-gray-300 mb-12 leading-relaxed max-w-2xl mx-auto">
              AutoApply automates your job search. Upload your resume, set your preferences, 
              and let AI apply to hundreds of relevant positions while you focus on what matters.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleGoogleSignIn}
                className="group relative px-8 py-4 rounded-2xl bg-white dark:bg-gray-800 shadow-xl hover:shadow-2xl transition-all overflow-hidden border border-gray-200 dark:border-gray-700"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-teal-500 to-amber-500 opacity-0 group-hover:opacity-10 transition-opacity" />
                <div className="relative flex items-center justify-center gap-3">
                  <svg className="w-6 h-6" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">
                    Continue with Google
                  </span>
                </div>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => router.push('/auth/signin')}
                className="px-8 py-4 rounded-2xl bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold text-lg shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </motion.button>
            </div>
          </motion.div>

          {/* Features Grid */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto"
          >
            {[
              {
                icon: Target,
                title: 'Smart Matching',
                description: 'AI analyzes your profile and finds the perfect job matches automatically.',
                color: 'from-teal-500 to-cyan-500',
              },
              {
                icon: Zap,
                title: 'Auto-Apply',
                description: 'Apply to hundreds of jobs with a single click. Save hours every week.',
                color: 'from-amber-500 to-orange-500',
              },
              {
                icon: TrendingUp,
                title: 'Track Progress',
                description: 'Monitor your applications, interviews, and success rate in real-time.',
                color: 'from-purple-500 to-pink-500',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="group relative p-8 rounded-3xl bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all border border-gray-100 dark:border-gray-700"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="mt-24 grid grid-cols-3 gap-8 max-w-3xl mx-auto"
          >
            {[
              { value: '10k+', label: 'Applications Sent' },
              { value: '500+', label: 'Users Hired' },
              { value: '95%', label: 'Success Rate' },
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl font-bold text-gradient mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {stat.label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
