import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { adminAPI } from '../../services/api';
import {
  Users, DollarSign, FileText, TrendingUp, Activity,
  ArrowUpRight, ArrowDownRight, Clock, CheckCircle, AlertCircle
} from 'lucide-react';

interface DashboardData {
  users: { total: number; active: number; new_today: number };
  revenue: { total: number; today: number; trend: number };
  requests: { total: number; active: number; completed: number };
  providers: { total: number; online: number };
}

export const SegurifAIDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await adminAPI.getFullDashboard();
      setData(response.data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      title: 'Total Users',
      value: data?.users?.total || 0,
      change: `+${data?.users?.new_today || 0} today`,
      icon: <Users className="text-blue-600" />,
      color: 'bg-blue-50',
    },
    {
      title: 'Revenue (GTQ)',
      value: `Q${(data?.revenue?.total || 0).toLocaleString()}`,
      change: `${data?.revenue?.trend || 0 > 0 ? '+' : ''}${data?.revenue?.trend || 0}%`,
      icon: <DollarSign className="text-green-600" />,
      color: 'bg-green-50',
    },
    {
      title: 'Active Requests',
      value: data?.requests?.active || 0,
      change: `${data?.requests?.completed || 0} completed`,
      icon: <FileText className="text-purple-600" />,
      color: 'bg-purple-50',
    },
    {
      title: 'Online Providers',
      value: data?.providers?.online || 0,
      change: `of ${data?.providers?.total || 0} total`,
      icon: <Activity className="text-orange-600" />,
      color: 'bg-orange-50',
    },
  ];

  return (
    <Layout variant="segurifai-admin">
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">Welcome to SegurifAI Admin Panel</p>
          </div>
          <button className="btn btn-primary">
            Download Report
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div key={index} className="card">
              <div className="flex items-start justify-between">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  {stat.icon}
                </div>
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  {stat.change.includes('+') ? (
                    <ArrowUpRight size={14} className="text-green-500" />
                  ) : (
                    <ArrowDownRight size={14} className="text-gray-400" />
                  )}
                  {stat.change}
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-2xl font-bold text-gray-900">{stat.value}</h3>
                <p className="text-sm text-gray-500">{stat.title}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-4">
              {[
                { icon: <CheckCircle className="text-green-500" />, text: 'Request #REQ-001 completed', time: '5 min ago' },
                { icon: <Users className="text-blue-500" />, text: 'New user registered', time: '15 min ago' },
                { icon: <AlertCircle className="text-yellow-500" />, text: 'Request #REQ-002 pending review', time: '1 hour ago' },
                { icon: <DollarSign className="text-green-500" />, text: 'Payment received Q150.00', time: '2 hours ago' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  {item.icon}
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{item.text}</p>
                    <p className="text-xs text-gray-500">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Platform Overview</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Requests Today</span>
                <span className="font-bold text-lg">{data?.requests?.active || 0}</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full">
                <div className="h-2 bg-blue-600 rounded-full" style={{ width: '65%' }} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Provider Availability</span>
                <span className="font-bold text-lg">
                  {data?.providers?.online || 0}/{data?.providers?.total || 0}
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full">
                <div className="h-2 bg-green-600 rounded-full" style={{ width: `${((data?.providers?.online || 0) / (data?.providers?.total || 1)) * 100}%` }} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">System Health</span>
                <span className="badge badge-success">Healthy</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
