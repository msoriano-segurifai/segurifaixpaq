import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPAQLogin, setShowPAQLogin] = useState(false);
  const [paqPhone, setPaqPhone] = useState('');

  const { login, loginWithPAQToken, isAuthenticated, isPAQUser } = useAuth();
  const navigate = useNavigate();

  // Auto-redirect if already authenticated (PAQ users come here with token)
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/app');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Credenciales invalidas');
    } finally {
      setLoading(false);
    }
  };

  const handlePAQLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/users/auth/paq/phone-login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: paqPhone })
      });
      const data = await response.json();
      if (response.ok && data.success) {
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        localStorage.setItem('is_paq_user', 'true');
        // Force full page reload to trigger AuthContext
        window.location.href = '/app';
      } else {
        setError(data.error || 'Error al iniciar sesión con PAQ');
        setLoading(false);
      }
    } catch (err: any) {
      setError('Error de conexión');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-blue-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-900 rounded-2xl mb-4 text-white shadow-lg">
            <Shield size={32} />
          </div>
          <h1 className="text-3xl font-bold text-white">SegurifAI - Usuario</h1>
          <p className="text-blue-200 mt-2">Portal de Usuario</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">
            Iniciar Sesión
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ingrese su email"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contraseña
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ingrese su contraseña"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-900 text-white rounded-lg font-medium hover:opacity-90 transition-all disabled:opacity-50"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </button>
          </div>

          {/* Quick login buttons for testing */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-3">Acceso Rápido (Pruebas):</p>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => { setEmail('user20@test.gt'); setPassword('TestPass123!'); }}
                className="w-full px-3 py-2 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Usuario de Prueba (No-PAQ)
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowPAQLogin(true);
                  setPaqPhone('+50230082653');
                }}
                className="w-full px-3 py-2 text-xs bg-green-100 hover:bg-green-200 text-green-800 rounded-lg"
              >
                Usuario PAQ (+502 3008 2653)
              </button>
            </div>
          </div>
        </form>

        {/* PAQ Login Modal */}
        {showPAQLogin && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6">
              <h2 className="text-xl font-bold mb-4">Login con PAQ Wallet</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <p className="text-sm text-gray-600 mb-4">
                Ingresa tu número de teléfono registrado en PAQ Wallet
              </p>
              <input
                type="tel"
                value={paqPhone}
                onChange={(e) => setPaqPhone(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg mb-4"
                placeholder="+502 3008 2653"
              />
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowPAQLogin(false);
                    setError('');
                    setPaqPhone('');
                  }}
                  className="btn btn-outline flex-1"
                >
                  Cancelar
                </button>
                <button
                  onClick={handlePAQLogin}
                  disabled={loading || !paqPhone}
                  className="btn btn-primary flex-1"
                >
                  {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
                </button>
              </div>
            </div>
          </div>
        )}

        <p className="text-center text-blue-200 text-sm mt-6">
          © 2025 SegurifAI. Todos los derechos reservados.
        </p>
      </div>
    </div>
  );
};
