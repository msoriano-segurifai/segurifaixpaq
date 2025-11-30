import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import { Login } from './pages/Login';
import { PAQDashboard } from './pages/admin/PAQDashboard';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Placeholder components for routes not yet implemented
const ComingSoon: React.FC<{ title: string }> = ({ title }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-100">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">{title}</h1>
      <p className="text-gray-500">Esta pagina esta en desarrollo</p>
    </div>
  </div>
);

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />

      {/* PAQ Admin Routes */}
      <Route path="/paq-admin" element={<ProtectedRoute><PAQDashboard /></ProtectedRoute>} />
      <Route path="/paq-admin/wallets" element={<ProtectedRoute><ComingSoon title="Wallet Management" /></ProtectedRoute>} />
      <Route path="/paq-admin/transactions" element={<ProtectedRoute><ComingSoon title="Transaction History" /></ProtectedRoute>} />
      <Route path="/paq-admin/analytics" element={<ProtectedRoute><ComingSoon title="PAQ Analytics" /></ProtectedRoute>} />
      <Route path="/paq-admin/settings" element={<ProtectedRoute><ComingSoon title="PAQ Settings" /></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
