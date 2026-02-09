'use client';

import { useSession } from 'next-auth/react';
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Upload,
  FileText,
  Save,
  Loader2,
  Plus,
  X,
  MapPin,
  Phone,
  Globe,
  Github,
  Linkedin,
  Sparkles,
  Key,
  Trash2,
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ProfilePage() {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [profile, setProfile] = useState({
    phone: '',
    location: '',
    linkedin_url: '',
    linkedin_cookies: '',
    github_url: '',
    portfolio_url: '',
    experience_years: 0,
    skills: [] as string[],
    resume_url: '',
    cover_letter_template: '',
  });
  const [newSkill, setNewSkill] = useState('');

  // New state for AI features
  const [resumes, setResumes] = useState<{ id: number, file_name: string }[]>([]);
  const [geminiKey, setGeminiKey] = useState('');

  // Fetch Profile and Resumes
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [profileRes, resumesRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/users/profile`, {
            headers: { Authorization: `Bearer ${session?.accessToken}` },
          }).catch(e => ({ data: {} })), // Handle 404 gracefully
          axios.get(`${API_URL}/api/v1/users/resumes`, {
            headers: { Authorization: `Bearer ${session?.accessToken}` },
          }).catch(e => ({ data: [] }))
        ]);

        if (profileRes.data) {
          setProfile(prev => ({
            ...prev,
            ...profileRes.data,
            skills: profileRes.data.skills || [],
          }));
          // If API key is returned in profile (it usually isn't for security, but if we stored it)
          // For now assuming we don't get it back or handled separately. 
          if (profileRes.data.gemini_api_key) setGeminiKey(profileRes.data.gemini_api_key);
        }

        if (resumesRes.data) {
          setResumes(resumesRes.data);
        }

      } catch (error: any) {
        console.error("Error fetching data", error);
        toast.error('Failed to load profile data');
      } finally {
        setLoading(false);
      }
    };

    if (session?.accessToken) {
      fetchData();
    }
  }, [session]);

  const handleGeminiKeySave = async () => {
    try {
      await axios.post(`${API_URL}/api/v1/users/gemini-key`,
        { api_key: geminiKey },
        { headers: { Authorization: `Bearer ${session?.accessToken}` } }
      );
      toast.success('Gemini API Key saved!');
    } catch (e) { toast.error('Failed to save API key'); }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    const toastId = toast.loading('Uploading and analyzing resume...');

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/users/upload-resume`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${session?.accessToken}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setProfile((prev) => ({ ...prev, resume_url: response.data.file_url }));

      // Refresh resumes list
      const resumesRes = await axios.get(`${API_URL}/api/v1/users/resumes`, {
        headers: { Authorization: `Bearer ${session?.accessToken}` },
      });
      setResumes(resumesRes.data);

      toast.success('Resume uploaded successfully!', { id: toastId });
    } catch (error) {
      toast.error('Failed to upload resume', { id: toastId });
    } finally {
      setUploading(false);
    }
  }, [session]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      // Try to create profile first, if it exists, update it
      try {
        await axios.post(
          `${API_URL}/api/v1/users/profile`,
          profile,
          {
            headers: { Authorization: `Bearer ${session?.accessToken}` },
          }
        );
      } catch (error: any) {
        if (error.response?.status === 400) {
          // Profile exists, update it
          await axios.put(
            `${API_URL}/api/v1/users/profile`,
            profile,
            {
              headers: { Authorization: `Bearer ${session?.accessToken}` },
            }
          );
        } else {
          throw error;
        }
      }

      toast.success('Profile saved successfully!');
    } catch (error) {
      toast.error('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const addSkill = () => {
    if (newSkill.trim() && !profile.skills.includes(newSkill.trim())) {
      setProfile((prev) => ({
        ...prev,
        skills: [...prev.skills, newSkill.trim()],
      }));
      setNewSkill('');
    }
  };

  const removeSkill = (skill: string) => {
    setProfile((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s !== skill),
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Profile Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your profile, resumes, and AI settings
        </p>
      </div>

      {/* AI & Resume Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          AI Resume Matching (Gemini)
        </h2>

        <div className="mb-8 p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-800/30">
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Google Gemini API Key
          </label>
          <div className="flex gap-2">
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="Enter your Gemini API key"
              className="flex-1 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={handleGeminiKeySave}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-sm"
            >
              Save
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Required for intelligent resume selection and automated form filling.
            <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:underline ml-1">
              Get a key here
            </a>
          </p>
        </div>

        <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Uploaded Resumes
        </h3>

        <div className="space-y-2 mb-4">
          {resumes.map(resume => (
            <div key={resume.id} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg shadow-sm">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{resume.file_name}</span>
              </div>
            </div>
          ))}
          {resumes.length === 0 && (
            <p className="text-sm text-gray-500 italic p-2">No resumes uploaded yet.</p>
          )}
        </div>

        <div
          {...getRootProps()}
          className={`
                border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                ${isDragActive
              ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
              : 'border-gray-300 dark:border-gray-700 hover:border-purple-500 hover:bg-gray-50 dark:hover:bg-gray-800/50'
            }
            `}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <Loader2 className="w-10 h-10 mx-auto mb-3 text-purple-600 animate-spin" />
          ) : (
            <Upload className="w-10 h-10 mx-auto mb-3 text-gray-400" />
          )}
          <p className="font-medium text-gray-900 dark:text-white">
            {isDragActive ? 'Drop your resume here' : 'Upload another resume'}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            PDF or DOCX (Max 10MB)
          </p>
        </div>
      </motion.div>

      {/* Personal Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
          Personal Information
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              <Phone className="w-4 h-4 inline mr-2" />
              Phone Number
            </label>
            <input
              type="tel"
              value={profile.phone || ''}
              onChange={(e) =>
                setProfile({ ...profile, phone: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
              placeholder="+1 (555) 123-4567"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              <MapPin className="w-4 h-4 inline mr-2" />
              Location
            </label>
            <input
              type="text"
              value={profile.location || ''}
              onChange={(e) =>
                setProfile({ ...profile, location: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
              placeholder="San Francisco, CA"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              <Linkedin className="w-4 h-4 inline mr-2" />
              LinkedIn URL
            </label>
            <input
              type="url"
              value={profile.linkedin_url || ''}
              onChange={(e) =>
                setProfile({ ...profile, linkedin_url: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
              placeholder="https://linkedin.com/in/yourprofile"
            />
          </div>

          {/* LinkedIn Login Section */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-xl p-4 bg-blue-50 dark:bg-blue-900/10 col-span-1 md:col-span-2">
            <label className="block text-sm font-medium mb-4 text-gray-700 dark:text-gray-300">
              <span className="flex items-center gap-2">
                <Linkedin className="w-4 h-4 text-blue-600" />
                Connect LinkedIn
              </span>
            </label>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="email"
                  placeholder="LinkedIn Email"
                  id="linkedin-email"
                  className="px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
                />
                <input
                  type="password"
                  placeholder="LinkedIn Password"
                  id="linkedin-password"
                  className="px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
                />
              </div>

              <button
                onClick={async () => {
                  const email = (document.getElementById('linkedin-email') as HTMLInputElement).value;
                  const password = (document.getElementById('linkedin-password') as HTMLInputElement).value;

                  if (!email || !password) {
                    toast.error('Please enter email and password');
                    return;
                  }

                  const btn = document.getElementById('connect-btn');
                  if (btn) btn.innerHTML = 'Connecting... (this may take up to 30s)';

                  try {
                    await axios.post(`${API_URL}/api/v1/users/connect-linkedin`, {
                      email,
                      password
                    }, {
                      headers: { Authorization: `Bearer ${session?.accessToken}` },
                    });
                    toast.success('Successfully connected to LinkedIn!');
                    window.location.reload();
                  } catch (error: any) {
                    toast.error(error.response?.data?.detail || 'Connection failed. Try manual cookie entry.');
                  } finally {
                    if (btn) btn.innerHTML = 'Connect';
                  }
                }}
                id="connect-btn"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Connect
              </button>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <details className="text-sm">
                <summary className="cursor-pointer text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 select-none font-medium">
                  Alternative: Enter Cookie Manually
                </summary>
                <div className="mt-3">
                  <label className="block text-xs text-gray-500 mb-1">
                    LinkedIn Session Cookie (li_at)
                  </label>
                  <input
                    type="password"
                    value={profile.linkedin_cookies || ''}
                    onChange={(e) =>
                      setProfile({ ...profile, linkedin_cookies: e.target.value })
                    }
                    className="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-teal-500 outline-none"
                    placeholder="Paste li_at cookie here"
                  />
                </div>
              </details>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              <Github className="w-4 h-4 inline mr-2" />
              GitHub URL
            </label>
            <input
              type="url"
              value={profile.github_url || ''}
              onChange={(e) =>
                setProfile({ ...profile, github_url: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
              placeholder="https://github.com/yourusername"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              <Globe className="w-4 h-4 inline mr-2" />
              Portfolio URL
            </label>
            <input
              type="url"
              value={profile.portfolio_url || ''}
              onChange={(e) =>
                setProfile({ ...profile, portfolio_url: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
              placeholder="https://yourportfolio.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              Years of Experience
            </label>
            <input
              type="number"
              value={profile.experience_years || 0}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  experience_years: parseInt(e.target.value) || 0,
                })
              }
              min="0"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
            />
          </div>
        </div>
      </motion.div>

      {/* Skills */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Skills
        </h2>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addSkill()}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none"
            placeholder="Add a skill (e.g., Python, React, AWS)"
          />
          <button
            onClick={addSkill}
            className="px-6 py-3 rounded-xl bg-teal-600 text-white hover:bg-teal-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {profile.skills.map((skill) => (
            <span
              key={skill}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 font-medium"
            >
              {skill}
              <button
                onClick={() => removeSkill(skill)}
                className="hover:text-teal-900 dark:hover:text-teal-100"
              >
                <X className="w-4 h-4" />
              </button>
            </span>
          ))}
          {profile.skills.length === 0 && (
            <p className="text-gray-500 dark:text-gray-400">
              No skills added yet. Start adding your skills!
            </p>
          )}
        </div>
      </motion.div>

      {/* Cover Letter Template */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Cover Letter Template
        </h2>
        <textarea
          value={profile.cover_letter_template || ''}
          onChange={(e) =>
            setProfile({ ...profile, cover_letter_template: e.target.value })
          }
          rows={8}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 outline-none resize-none"
          placeholder="Write a cover letter template that will be used for job applications..."
        />
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="pb-10"
      >
        <button
          onClick={handleSaveProfile}
          disabled={saving}
          className="w-full py-4 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Save Profile
            </>
          )}
        </button>
      </motion.div>
    </div>
  );
}
