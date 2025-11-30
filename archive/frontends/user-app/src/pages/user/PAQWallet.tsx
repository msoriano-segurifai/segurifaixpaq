import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { userAPI } from '../../services/api';
import {
  Wallet, CreditCard, ArrowUpRight, ArrowDownLeft, Plus,
  RefreshCw, Clock, CheckCircle, AlertCircle, Link2, DollarSign
} from 'lucide-react';

interface WalletData {
  balance: number;
  pending_balance: number;
  linked_account?: {
    bank_name: string;
    account_last4: string;
    is_verified: boolean;
  };
  transactions: Transaction[];
}

interface Transaction {
  id: number;
  type: 'CREDIT' | 'DEBIT' | 'REWARD' | 'REFUND';
  amount: number;
  description: string;
  status: string;
  created_at: string;
}

export const PAQWallet: React.FC = () => {
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWallet();
  }, []);

  const loadWallet = async () => {
    try {
      // Fetch balance and history in parallel
      const [balanceRes, historyRes] = await Promise.all([
        userAPI.getWalletBalance().catch(e => {
          console.log('Balance API error:', e.response?.data);
          return { data: { balance: 0, pending_balance: 0 } };
        }),
        userAPI.getWalletHistory().catch(e => {
          console.log('History API error:', e.response?.data);
          return { data: { transactions: [] } };
        })
      ]);
      setWallet({
        balance: balanceRes.data.balance || balanceRes.data.saldo || 0,
        pending_balance: balanceRes.data.pending_balance || balanceRes.data.saldo_pendiente || 0,
        linked_account: balanceRes.data.linked_account,
        transactions: historyRes.data.transactions || historyRes.data.transacciones || []
      });
    } catch (error) {
      console.error('Error cargando wallet:', error);
      // Show empty wallet state - user needs to link PAQ account
      setWallet({
        balance: 0,
        pending_balance: 0,
        transactions: []
      });
    } finally {
      setLoading(false);
    }
  };


  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'CREDIT':
      case 'REWARD':
        return <ArrowDownLeft className="text-green-500" size={20} />;
      case 'DEBIT':
        return <ArrowUpRight className="text-red-500" size={20} />;
      case 'REFUND':
        return <RefreshCw className="text-blue-500" size={20} />;
      default:
        return <DollarSign className="text-gray-500" size={20} />;
    }
  };

  const getTransactionColor = (type: string) => {
    switch (type) {
      case 'CREDIT':
      case 'REWARD':
      case 'REFUND':
        return 'text-green-600';
      case 'DEBIT':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="animate-spin text-purple-600" size={48} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="user">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Mi Billetera PAQ</h1>
          <p className="text-gray-500">Administra tu saldo y transacciones</p>
        </div>

        {/* Balance Card */}
        <div className="card bg-gradient-to-r from-purple-600 to-purple-700 text-white">
          <div className="flex items-center justify-between mb-6">
            <Wallet size={32} />
            <span className="px-3 py-1 bg-white/20 rounded-full text-sm">PAQ Wallet</span>
          </div>
          <div>
            <p className="text-purple-200 text-sm">Saldo Disponible</p>
            <p className="text-4xl font-bold">Q{wallet?.balance?.toFixed(2) || '0.00'}</p>
          </div>
          {wallet?.pending_balance && wallet.pending_balance > 0 && (
            <div className="mt-4 pt-4 border-t border-white/20">
              <div className="flex items-center justify-between text-sm">
                <span className="text-purple-200">Saldo Pendiente</span>
                <span className="font-medium">Q{wallet.pending_balance.toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 gap-4">
          <button className="card hover:shadow-lg transition-shadow flex flex-col items-center py-6">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-3">
              <Plus className="text-green-600" size={24} />
            </div>
            <span className="font-medium">Recargar Saldo</span>
          </button>
          {/* Link Account button hidden - PAQ users are already linked */}
        </div>

        {/* PAQ Account Status - Always linked for PAQ users */}
        <div className="card bg-green-50 border-green-200">
          <h3 className="font-bold mb-4 flex items-center gap-2 text-green-800">
            <CheckCircle size={18} />
            Cuenta PAQ Vinculada
          </h3>
          <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-green-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <CreditCard className="text-purple-600" size={20} />
              </div>
              <div>
                <p className="font-medium">PAQ Wallet</p>
                <p className="text-sm text-gray-500">Cuenta verificada</p>
              </div>
            </div>
            <span className="flex items-center gap-1 text-green-600 text-sm font-medium">
              <CheckCircle size={16} />
              Activa
            </span>
          </div>
          <p className="mt-3 text-sm text-green-700">
            Tu cuenta PAQ esta vinculada automaticamente. Puedes usar tu saldo para pagos y recibir recompensas.
          </p>
        </div>

        {/* Transaction History */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <Clock size={18} />
            Historial de Transacciones
          </h3>
          {wallet?.transactions && wallet.transactions.length > 0 ? (
            <div className="space-y-3">
              {wallet.transactions.map((tx) => (
                <div key={tx.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                      {getTransactionIcon(tx.type)}
                    </div>
                    <div>
                      <p className="font-medium">{tx.description}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(tx.created_at).toLocaleDateString('es-GT')}
                      </p>
                    </div>
                  </div>
                  <span className={`font-bold ${getTransactionColor(tx.type)}`}>
                    {tx.type === 'DEBIT' ? '-' : '+'}Q{tx.amount.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="mx-auto mb-2" size={32} />
              <p>No hay transacciones aun</p>
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
};
