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
    github_url: '',
    portfolio_url: '',
    experience_years: 0,
    skills: [] as string[],
    resume_url: '',
    cover_letter_template: '',
  });
  const [newSkill, setNewSkill] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/users/profile`, {
          headers: { Authorization: `Bearer ${session?.accessToken}` },
        });
        setProfile({
          ...response.data,
          skills: response.data.skills || [],
        });
      } catch (error: any) {
        if (error.response?.status !== 404) {
          toast.error('Failed to load profile');
        }
      } finally {
        setLoading(false);
      }
    };

    if (session?.accessToken) {
      fetchProfile();
    }
  }, [session]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
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
      toast.success('Resume uploaded successfully!');
    } catch (error) {
      toast.error('Failed to upload resume');
    } finally {
      setUploading(false);
    }
  }, [session]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
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
          Manage your profile and upload your resume
        </p>
      </div>

      {/* Resume Upload */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Resume
        </h2>

        {profile.resume_url ? (
          <div className="flex items-center justify-between p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-3">
              <FileText className="w-6 h-6 text-green-600 dark:text-green-400" />
              <div>
                <p className="font-medium text-green-900 dark:text-green-100">
                  Resume uploaded
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  {profile.resume_url.split('/').pop()}
                </p>
              </div>
            </div>
            <button
              onClick={() =>
                setProfile((prev) => ({ ...prev, resume_url: '' }))
              }
              className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
            >
              Replace
            </button>
          </div>
        ) : (
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
              ${
                isDragActive
                  ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20'
                  : 'border-gray-300 dark:border-gray-700 hover:border-teal-500 hover:bg-gray-50 dark:hover:bg-gray-800/50'
              }
            `}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <Loader2 className="w-12 h-12 mx-auto mb-4 text-teal-600 animate-spin" />
            ) : (
              <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            )}
            <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {isDragActive ? 'Drop your resume here' : 'Upload your resume'}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Drag and drop or click to browse (PDF, DOC, DOCX - Max 10MB)
            </p>
          </div>
        )}
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
              value={profile.phone}
              onChange={(e) =>
                setProfile({ ...profile, phone: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
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
              value={profile.location}
              onChange={(e) =>
                setProfile({ ...profile, location: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
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
              value={profile.linkedin_url}
              onChange={(e) =>
                setProfile({ ...profile, linkedin_url: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
              placeholder="https://linkedin.com/in/yourprofile"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              <Github className="w-4 h-4 inline mr-2" />
              GitHub URL
            </label>
            <input
              type="url"
              value={profile.github_url}
              onChange={(e) =>
                setProfile({ ...profile, github_url: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
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
              value={profile.portfolio_url}
              onChange={(e) =>
                setProfile({ ...profile, portfolio_url: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
              placeholder="https://yourportfolio.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              Years of Experience
            </label>
            <input
              type="number"
              value={profile.experience_years}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  experience_years: parseInt(e.target.value) || 0,
                })
              }
              min="0"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
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
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all"
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
          value={profile.cover_letter_template}
          onChange={(e) =>
            setProfile({ ...profile, cover_letter_template: e.target.value })
          }
          rows={8}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition-all resize-none"
          placeholder="Write a cover letter template that will be used for job applications..."
        />
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
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
