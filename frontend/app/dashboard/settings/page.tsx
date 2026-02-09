'use client';

import Link from 'next/link';
import { User, Shield, Key } from 'lucide-react';

export default function SettingsPage() {
    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                    Settings
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Manage your account settings and preferences
                </p>
            </div>

            <div className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Key className="w-5 h-5" />
                    Authentication & Connections
                </h2>

                <div className="p-4 bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800 rounded-xl">
                    <h3 className="font-medium text-teal-900 dark:text-teal-100 mb-2">
                        Looking for LinkedIn Authentication?
                    </h3>
                    <p className="text-teal-700 dark:text-teal-300 mb-4 text-sm">
                        You can configure your LinkedIn session cookie (li_at) in your Profile settings.
                    </p>
                    <Link
                        href="/dashboard/profile"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
                    >
                        <User className="w-4 h-4" />
                        Go to Profile Settings
                    </Link>
                </div>
            </div>

            <div className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800 opacity-50 cursor-not-allowed">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Security (Coming Soon)
                </h2>
                <p className="text-gray-500">
                    Password change and 2FA settings will be available here.
                </p>
            </div>
        </div>
    );
}
