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
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkingAccount, setLinkingAccount] = useState(false);
  const [linkForm, setLinkForm] = useState({
    bank_name: '',
    account_number: '',
    account_type: 'SAVINGS'
  });

  useEffect(() => {
    loadWallet();
  }, []);

  const loadWallet = async () => {
    try {
      const response = await userAPI.getWallet();
      setWallet(response.data);
    } catch (error) {
      console.error('Error cargando wallet:', error);
      // Mock data for demo
      setWallet({
        balance: 150.00,
        pending_balance: 25.00,
        transactions: [
          { id: 1, type: 'REWARD', amount: 50, description: 'Recompensa por completar modulo', status: 'COMPLETED', created_at: new Date().toISOString() },
          { id: 2, type: 'CREDIT', amount: 100, description: 'Recarga de saldo', status: 'COMPLETED', created_at: new Date().toISOString() },
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLinkAccount = async () => {
    setLinkingAccount(true);
    try {
      await userAPI.linkPAQAccount(linkForm);
      await loadWallet();
      setShowLinkModal(false);
      alert('Cuenta vinculada exitosamente!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al vincular cuenta');
    } finally {
      setLinkingAccount(false);
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
        <div className="grid grid-cols-2 gap-4">
          <button className="card hover:shadow-lg transition-shadow flex flex-col items-center py-6">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-3">
              <Plus className="text-green-600" size={24} />
            </div>
            <span className="font-medium">Recargar Saldo</span>
          </button>
          <button
            onClick={() => setShowLinkModal(true)}
            className="card hover:shadow-lg transition-shadow flex flex-col items-center py-6"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-3">
              <Link2 className="text-blue-600" size={24} />
            </div>
            <span className="font-medium">Vincular Cuenta</span>
          </button>
        </div>

        {/* Linked Account */}
        {wallet?.linked_account ? (
          <div className="card">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <CreditCard size={18} />
              Cuenta Vinculada
            </h3>
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <CreditCard className="text-purple-600" size={20} />
                </div>
                <div>
                  <p className="font-medium">{wallet.linked_account.bank_name}</p>
                  <p className="text-sm text-gray-500">**** {wallet.linked_account.account_last4}</p>
                </div>
              </div>
              {wallet.linked_account.is_verified ? (
                <span className="flex items-center gap-1 text-green-600 text-sm">
                  <CheckCircle size={16} />
                  Verificada
                </span>
              ) : (
                <span className="flex items-center gap-1 text-yellow-600 text-sm">
                  <Clock size={16} />
                  Pendiente
                </span>
              )}
            </div>
          </div>
        ) : (
          <div className="card bg-yellow-50 border-yellow-200">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-yellow-600 flex-shrink-0" size={20} />
              <div>
                <p className="font-medium text-yellow-800">Sin cuenta vinculada</p>
                <p className="text-sm text-yellow-700">
                  Vincula tu cuenta bancaria PAQ para recibir recompensas y hacer retiros.
                </p>
              </div>
            </div>
          </div>
        )}

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

        {/* Link Account Modal */}
        {showLinkModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl w-full max-w-md p-6">
              <h3 className="text-xl font-bold mb-4">Vincular Cuenta PAQ</h3>

              <div className="space-y-4">
                <div>
                  <label className="label">Nombre del Banco</label>
                  <select
                    value={linkForm.bank_name}
                    onChange={(e) => setLinkForm({ ...linkForm, bank_name: e.target.value })}
                    className="input"
                  >
                    <option value="">Seleccionar banco</option>
                    <option value="Banco Industrial">Banco Industrial</option>
                    <option value="Banrural">Banrural</option>
                    <option value="BAM">BAM</option>
                    <option value="G&T Continental">G&T Continental</option>
                  </select>
                </div>

                <div>
                  <label className="label">Numero de Cuenta</label>
                  <input
                    type="text"
                    value={linkForm.account_number}
                    onChange={(e) => setLinkForm({ ...linkForm, account_number: e.target.value })}
                    className="input"
                    placeholder="Ej: 1234567890"
                  />
                </div>

                <div>
                  <label className="label">Tipo de Cuenta</label>
                  <div className="flex gap-2">
                    {['SAVINGS', 'CHECKING'].map((type) => (
                      <button
                        key={type}
                        onClick={() => setLinkForm({ ...linkForm, account_type: type })}
                        className={`flex-1 py-2 px-4 rounded-lg border-2 font-medium transition-all ${
                          linkForm.account_type === type
                            ? 'border-purple-500 bg-purple-50 text-purple-700'
                            : 'border-gray-200 text-gray-600'
                        }`}
                      >
                        {type === 'SAVINGS' ? 'Ahorro' : 'Monetaria'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowLinkModal(false)}
                  className="btn btn-outline flex-1"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleLinkAccount}
                  disabled={linkingAccount || !linkForm.bank_name || !linkForm.account_number}
                  className="btn btn-primary flex-1"
                >
                  {linkingAccount ? 'Vinculando...' : 'Vincular'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
