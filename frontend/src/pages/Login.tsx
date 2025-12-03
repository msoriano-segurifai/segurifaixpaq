import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Login: React.FC = () => {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPAQLogin, setShowPAQLogin] = useState(false);
  const [showSignUp, setShowSignUp] = useState(false);
  const [paqPhone, setPaqPhone] = useState('');
  const [paqName, setPaqName] = useState('');

  // Sign up form state
  const [signUpData, setSignUpData] = useState({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    gender: '',
    whatsapp: '',
    password: '',
    confirmPassword: ''
  });

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
      await login(phone, password);
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
        body: JSON.stringify({ phone: paqPhone, name: paqName })
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

  const handleSignUp = async () => {
    setError('');
    setSuccessMessage('');

    // Validate passwords match
    if (signUpData.password !== signUpData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    // Validate password length
    if (signUpData.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    // Validate required fields
    if (!signUpData.firstName || !signUpData.lastName || !signUpData.whatsapp || !signUpData.dateOfBirth || !signUpData.gender) {
      setError('Por favor complete todos los campos');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/users/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: signUpData.firstName,
          last_name: signUpData.lastName,
          phone_number: signUpData.whatsapp,
          email: `${signUpData.whatsapp.replace(/[^0-9]/g, '')}@segurifai.gt`,
          password: signUpData.password,
          password2: signUpData.confirmPassword,
          date_of_birth: signUpData.dateOfBirth,
          gender: signUpData.gender
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccessMessage('¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.');
        setShowSignUp(false);
        setPhone(signUpData.whatsapp);
        setSignUpData({
          firstName: '',
          lastName: '',
          dateOfBirth: '',
          gender: '',
          whatsapp: '',
          password: '',
          confirmPassword: ''
        });
      } else {
        setError(data.detail || data.error || 'Error al crear la cuenta');
      }
    } catch (err: any) {
      setError('Error de conexión');
    } finally {
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

          {successMessage && (
            <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg text-sm">
              {successMessage}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número de Teléfono
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="+502 1234 5678"
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

          {/* PAQ Wallet Login Option */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-600 mb-3 text-center">¿Eres usuario de PAQ Wallet?</p>
            <button
              type="button"
              onClick={() => setShowPAQLogin(true)}
              className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all"
            >
              Iniciar Sesión con PAQ Wallet
            </button>
          </div>

          {/* Sign Up Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              ¿No tienes cuenta?{' '}
              <button
                type="button"
                onClick={() => {
                  setShowSignUp(true);
                  setError('');
                  setSuccessMessage('');
                }}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Crear cuenta
              </button>
            </p>
          </div>
        </form>

        {/* PAQ Login Modal */}
        {showPAQLogin && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6">
              <h2 className="text-xl font-bold mb-4">Iniciar Sesión con PAQ Wallet</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <p className="text-sm text-gray-600 mb-4">
                Ingresa tus datos para acceder con PAQ Wallet
              </p>
              <div className="space-y-3 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre Completo
                  </label>
                  <input
                    type="text"
                    value={paqName}
                    onChange={(e) => setPaqName(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                    placeholder="Juan Pérez"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Número de Teléfono
                  </label>
                  <input
                    type="tel"
                    value={paqPhone}
                    onChange={(e) => setPaqPhone(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                    placeholder="+502 1234 5678"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowPAQLogin(false);
                    setError('');
                    setPaqPhone('');
                    setPaqName('');
                  }}
                  className="btn btn-outline flex-1"
                >
                  Cancelar
                </button>
                <button
                  onClick={handlePAQLogin}
                  disabled={loading || !paqPhone || !paqName}
                  className="btn btn-primary flex-1"
                >
                  {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Sign Up Modal */}
        {showSignUp && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 my-8">
              <h2 className="text-xl font-bold mb-4">Crear Cuenta en SegurifAI</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-3 mb-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nombre
                    </label>
                    <input
                      type="text"
                      value={signUpData.firstName}
                      onChange={(e) => setSignUpData({ ...signUpData, firstName: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                      placeholder="Juan"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Apellido
                    </label>
                    <input
                      type="text"
                      value={signUpData.lastName}
                      onChange={(e) => setSignUpData({ ...signUpData, lastName: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                      placeholder="Pérez"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fecha de Nacimiento
                  </label>
                  <input
                    type="date"
                    value={signUpData.dateOfBirth}
                    onChange={(e) => setSignUpData({ ...signUpData, dateOfBirth: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Género
                  </label>
                  <select
                    value={signUpData.gender}
                    onChange={(e) => setSignUpData({ ...signUpData, gender: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                  >
                    <option value="">Seleccionar...</option>
                    <option value="M">Masculino</option>
                    <option value="F">Femenino</option>
                    <option value="O">Otro</option>
                    <option value="N">Prefiero no decir</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Número de WhatsApp
                  </label>
                  <input
                    type="tel"
                    value={signUpData.whatsapp}
                    onChange={(e) => setSignUpData({ ...signUpData, whatsapp: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                    placeholder="+502 1234 5678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    value={signUpData.password}
                    onChange={(e) => setSignUpData({ ...signUpData, password: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                    placeholder="Mínimo 8 caracteres"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confirmar Contraseña
                  </label>
                  <input
                    type="password"
                    value={signUpData.confirmPassword}
                    onChange={(e) => setSignUpData({ ...signUpData, confirmPassword: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                    placeholder="Repetir contraseña"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowSignUp(false);
                    setError('');
                    setSignUpData({
                      firstName: '',
                      lastName: '',
                      dateOfBirth: '',
                      gender: '',
                      whatsapp: '',
                      password: '',
                      confirmPassword: ''
                    });
                  }}
                  className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSignUp}
                  disabled={loading}
                  className="flex-1 py-3 bg-blue-900 text-white rounded-lg font-medium hover:bg-blue-800 transition-all disabled:opacity-50"
                >
                  {loading ? 'Creando cuenta...' : 'Crear Cuenta'}
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
