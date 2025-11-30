import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { adminAPI } from '../../services/api';
import { Wallet, CreditCard, TrendingUp, Users, ArrowUpRight } from 'lucide-react';

export const PAQDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await adminAPI.getPAQDashboard();
      setData(response.data);
    } catch (error) {
      console.error('Failed to load PAQ dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout variant="paq-admin">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">PAQ Dashboard</h1>
          <p className="text-gray-500">Payment & Wallet Management</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <Wallet size={24} className="opacity-80 mb-2" />
            <p className="text-3xl font-bold">{data?.total_wallets || 0}</p>
            <p className="text-purple-100">Total Wallets</p>
          </div>
          <div className="card bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CreditCard size={24} className="opacity-80 mb-2" />
            <p className="text-3xl font-bold">Q{(data?.total_balance || 0).toLocaleString()}</p>
            <p className="text-green-100">Total Balance</p>
          </div>
          <div className="card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <TrendingUp size={24} className="opacity-80 mb-2" />
            <p className="text-3xl font-bold">{data?.transactions_today || 0}</p>
            <p className="text-blue-100">Transactions Today</p>
          </div>
          <div className="card bg-gradient-to-br from-amber-500 to-amber-600 text-white">
            <Users size={24} className="opacity-80 mb-2" />
            <p className="text-3xl font-bold">{data?.linked_accounts || 0}</p>
            <p className="text-amber-100">Linked Accounts</p>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Transactions</h3>
          <div className="space-y-3">
            {data?.recent_transactions?.map((tx: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${tx.type === 'credit' ? 'bg-green-100' : 'bg-red-100'}`}>
                    <ArrowUpRight className={tx.type === 'credit' ? 'text-green-600' : 'text-red-600 rotate-180'} size={16} />
                  </div>
                  <div>
                    <p className="font-medium">{tx.description}</p>
                    <p className="text-sm text-gray-500">{tx.wallet_id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${tx.type === 'credit' ? 'text-green-600' : 'text-red-600'}`}>
                    {tx.type === 'credit' ? '+' : '-'}Q{tx.amount}
                  </p>
                  <p className="text-xs text-gray-500">{tx.time}</p>
                </div>
              </div>
            )) || (
              <p className="text-center text-gray-500 py-8">No recent transactions</p>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};
