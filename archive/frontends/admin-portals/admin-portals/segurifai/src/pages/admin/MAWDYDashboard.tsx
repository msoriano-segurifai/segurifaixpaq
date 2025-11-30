import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { adminAPI } from '../../services/api';
import { Truck, MapPin, Clock, Users, CheckCircle, AlertTriangle } from 'lucide-react';

export const MAWDYDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await adminAPI.getMAWDYOverview();
      setData(response.data);
    } catch (error) {
      console.error('Failed to load MAWDY dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout variant="mawdy-admin">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">MAWDY Dashboard</h1>
          <p className="text-gray-500">Manage field technicians and assistance jobs</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card bg-gradient-to-br from-red-500 to-red-600 text-white">
            <div className="flex items-center gap-4">
              <Users size={32} className="opacity-80" />
              <div>
                <p className="text-3xl font-bold">{data?.total_techs || 0}</p>
                <p className="text-red-100">Total Technicians</p>
              </div>
            </div>
          </div>
          <div className="card bg-gradient-to-br from-green-500 to-green-600 text-white">
            <div className="flex items-center gap-4">
              <CheckCircle size={32} className="opacity-80" />
              <div>
                <p className="text-3xl font-bold">{data?.online_techs || 0}</p>
                <p className="text-green-100">Online Now</p>
              </div>
            </div>
          </div>
          <div className="card bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <div className="flex items-center gap-4">
              <Truck size={32} className="opacity-80" />
              <div>
                <p className="text-3xl font-bold">{data?.active_jobs || 0}</p>
                <p className="text-orange-100">Active Jobs</p>
              </div>
            </div>
          </div>
          <div className="card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <div className="flex items-center gap-4">
              <Clock size={32} className="opacity-80" />
              <div>
                <p className="text-3xl font-bold">{data?.jobs_today || 0}</p>
                <p className="text-blue-100">Jobs Today</p>
              </div>
            </div>
          </div>
        </div>

        {/* Live Map Placeholder */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <MapPin className="text-red-500" />
            Live Technician Map
          </h3>
          <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center text-gray-500">
              <MapPin size={48} className="mx-auto mb-2 opacity-50" />
              <p>Live map will be displayed here</p>
              <p className="text-sm">Integration with Google Maps API</p>
            </div>
          </div>
        </div>

        {/* Active Jobs Table */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Active Jobs</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="table-header">Request #</th>
                  <th className="table-header">Type</th>
                  <th className="table-header">Technician</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Location</th>
                  <th className="table-header">ETA</th>
                </tr>
              </thead>
              <tbody>
                {data?.recent_jobs?.map((job: any) => (
                  <tr key={job.id} className="border-b hover:bg-gray-50">
                    <td className="table-cell font-medium">{job.request_number}</td>
                    <td className="table-cell">{job.service_type}</td>
                    <td className="table-cell">{job.tech_name}</td>
                    <td className="table-cell">
                      <span className={`badge ${
                        job.status === 'IN_PROGRESS' ? 'badge-warning' :
                        job.status === 'COMPLETED' ? 'badge-success' : 'badge-info'
                      }`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="table-cell">{job.location}</td>
                    <td className="table-cell">{job.eta || '-'}</td>
                  </tr>
                )) || (
                  <tr>
                    <td colSpan={6} className="table-cell text-center text-gray-500">
                      No active jobs
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};
