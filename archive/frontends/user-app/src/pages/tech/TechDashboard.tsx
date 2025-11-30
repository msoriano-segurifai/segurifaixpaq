import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { dispatchAPI } from '../../services/api';
import { Truck, DollarSign, Star, Clock, MapPin, CheckCircle, Play, Navigation } from 'lucide-react';

export const TechDashboard: React.FC = () => {
  const [profile, setProfile] = useState<any>(null);
  const [activeJob, setActiveJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await dispatchAPI.getMyProfile();
      setProfile(response.data);
      setActiveJob(response.data.active_job);
      setIsOnline(response.data.profile?.is_online);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleOnline = async () => {
    try {
      if (isOnline) {
        await dispatchAPI.goOffline();
      } else {
        // Get current location
        navigator.geolocation.getCurrentPosition(async (pos) => {
          await dispatchAPI.goOnline(pos.coords.latitude, pos.coords.longitude);
          setIsOnline(true);
        });
        return;
      }
      setIsOnline(!isOnline);
    } catch (error) {
      console.error('Failed to toggle online status:', error);
    }
  };

  return (
    <Layout variant="field-tech">
      <div className="space-y-6">
        {/* Online Toggle */}
        <div className="card bg-gradient-to-r from-red-600 to-red-700 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">
                {profile?.profile?.user?.first_name || 'Tech'}'s Dashboard
              </h2>
              <p className="text-red-100">
                {isOnline ? 'You are online and receiving jobs' : 'You are offline'}
              </p>
            </div>
            <button
              onClick={toggleOnline}
              className={`px-6 py-3 rounded-xl font-bold transition-all ${
                isOnline
                  ? 'bg-white text-red-600 hover:bg-red-50'
                  : 'bg-green-500 text-white hover:bg-green-400'
              }`}
            >
              {isOnline ? 'Go Offline' : 'Go Online'}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <Star className="mx-auto text-yellow-500 mb-2" size={28} />
            <p className="text-2xl font-bold">{profile?.performance?.rating || '5.0'}</p>
            <p className="text-sm text-gray-500">Rating</p>
          </div>
          <div className="card text-center">
            <CheckCircle className="mx-auto text-green-500 mb-2" size={28} />
            <p className="text-2xl font-bold">{profile?.performance?.total_jobs_completed || 0}</p>
            <p className="text-sm text-gray-500">Jobs Done</p>
          </div>
          <div className="card text-center">
            <DollarSign className="mx-auto text-green-600 mb-2" size={28} />
            <p className="text-2xl font-bold">Q{profile?.earnings?.daily || 0}</p>
            <p className="text-sm text-gray-500">Today</p>
          </div>
          <div className="card text-center">
            <Clock className="mx-auto text-blue-500 mb-2" size={28} />
            <p className="text-2xl font-bold">{profile?.summary?.jobs_today || 0}</p>
            <p className="text-sm text-gray-500">Jobs Today</p>
          </div>
        </div>

        {/* Active Job */}
        {activeJob && (
          <div className="card border-2 border-red-500">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <h3 className="text-lg font-bold text-red-600">Active Job</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Request #</span>
                <span className="font-bold">{activeJob.request_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Service</span>
                <span className="font-medium">{activeJob.title}</span>
              </div>
              <div className="flex items-start gap-2">
                <MapPin className="text-red-500 mt-1" size={16} />
                <div>
                  <p className="font-medium">{activeJob.location?.address}</p>
                  <p className="text-sm text-gray-500">{activeJob.location?.city}</p>
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button className="btn btn-mawdy flex-1 flex items-center justify-center gap-2">
                  <Navigation size={18} />
                  Navigate
                </button>
                <button className="btn btn-success flex-1 flex items-center justify-center gap-2">
                  <Play size={18} />
                  {activeJob.status === 'ASSIGNED' ? 'Start' : 'Complete'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Work History */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Work History</h3>
          <div className="space-y-3">
            {profile?.work_history?.length > 0 ? (
              profile.work_history.map((job: any) => (
                <div key={job.job_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{job.title}</p>
                    <p className="text-sm text-gray-500">{job.request_number}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-600">Q{job.earnings}</p>
                    <p className="text-xs text-gray-500">{job.distance_km} km</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-gray-500 py-8">No work history yet</p>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};
