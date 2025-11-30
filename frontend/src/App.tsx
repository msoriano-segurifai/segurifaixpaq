import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import { Login } from './pages/Login';
import { UserDashboard } from './pages/user/UserDashboard';
import { Subscriptions } from './pages/user/Subscriptions';
import { ELearning } from './pages/user/ELearning';
import { RequestAssistance } from './pages/user/RequestAssistance';
import { MyRequests } from './pages/user/MyRequests';
import { Rewards } from './pages/user/Rewards';
import { UserProfile } from './pages/user/UserProfile';
import { EvidenceSubmission } from './pages/user/EvidenceSubmission';
import { HealthPortal } from './pages/user/HealthPortal';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; paqOnly?: boolean }> = ({ children, paqOnly = false }) => {
  const { isAuthenticated, isLoading, isPAQUser } = useAuth();

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

  // If route is PAQ-only and user is not a PAQ user, redirect to dashboard
  if (paqOnly && !isPAQUser) {
    return <Navigate to="/app" replace />;
  }

  return <>{children}</>;
};

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />

      {/* User App Routes */}
      <Route path="/app" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
      <Route path="/app/request" element={<ProtectedRoute><RequestAssistance /></ProtectedRoute>} />
      <Route path="/app/requests" element={<ProtectedRoute><MyRequests /></ProtectedRoute>} />
      <Route path="/app/requests/:requestId/evidence" element={<ProtectedRoute><EvidenceSubmission /></ProtectedRoute>} />
      <Route path="/app/subscriptions" element={<ProtectedRoute><Subscriptions /></ProtectedRoute>} />
      <Route path="/app/learning" element={<ProtectedRoute><ELearning /></ProtectedRoute>} />
      <Route path="/app/rewards" element={<ProtectedRoute><Rewards /></ProtectedRoute>} />
      <Route path="/app/profile" element={<ProtectedRoute><UserProfile /></ProtectedRoute>} />
      <Route path="/app/health" element={<ProtectedRoute><HealthPortal /></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to={isAuthenticated ? "/app" : "/login"} replace />} />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/app" : "/login"} replace />} />
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
