import React, { ReactNode, useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Home, Users, FileText, CreditCard, Settings, LogOut, Menu, X,
  Truck, MapPin, Clock, DollarSign, Award, BookOpen, ShoppingCart,
  Activity, PieChart, Bell, Shield, Wallet, BarChart3, Building2,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface LayoutProps {
  children: ReactNode;
  variant: 'segurifai-admin' | 'paq-admin' | 'mawdy-admin' | 'field-tech' | 'user';
}

interface NavItem {
  label: string;
  path: string;
  icon: ReactNode;
}

const getNavItems = (variant: LayoutProps['variant']): NavItem[] => {
  switch (variant) {
    case 'segurifai-admin':
      return [
        { label: 'Dashboard', path: '/admin', icon: <Home size={20} /> },
        { label: 'Users', path: '/admin/users', icon: <Users size={20} /> },
        { label: 'Providers', path: '/admin/providers', icon: <Building2 size={20} /> },
        { label: 'Requests', path: '/admin/requests', icon: <FileText size={20} /> },
        { label: 'Revenue', path: '/admin/revenue', icon: <DollarSign size={20} /> },
        { label: 'Analytics', path: '/admin/analytics', icon: <BarChart3 size={20} /> },
        { label: 'Settings', path: '/admin/settings', icon: <Settings size={20} /> },
      ];
    case 'paq-admin':
      return [
        { label: 'Dashboard', path: '/paq-admin', icon: <Home size={20} /> },
        { label: 'Wallets', path: '/paq-admin/wallets', icon: <Wallet size={20} /> },
        { label: 'Transactions', path: '/paq-admin/transactions', icon: <CreditCard size={20} /> },
        { label: 'Analytics', path: '/paq-admin/analytics', icon: <PieChart size={20} /> },
        { label: 'Settings', path: '/paq-admin/settings', icon: <Settings size={20} /> },
      ];
    case 'mawdy-admin':
      return [
        { label: 'Dashboard', path: '/mawdy-admin', icon: <Home size={20} /> },
        { label: 'Field Techs', path: '/mawdy-admin/techs', icon: <Users size={20} /> },
        { label: 'Live Map', path: '/mawdy-admin/map', icon: <MapPin size={20} /> },
        { label: 'Jobs', path: '/mawdy-admin/jobs', icon: <Truck size={20} /> },
        { label: 'Analytics', path: '/mawdy-admin/analytics', icon: <Activity size={20} /> },
        { label: 'Settings', path: '/mawdy-admin/settings', icon: <Settings size={20} /> },
      ];
    case 'field-tech':
      return [
        { label: 'Dashboard', path: '/tech', icon: <Home size={20} /> },
        { label: 'Available Jobs', path: '/tech/jobs', icon: <Truck size={20} /> },
        { label: 'My Jobs', path: '/tech/my-jobs', icon: <Clock size={20} /> },
        { label: 'Earnings', path: '/tech/earnings', icon: <DollarSign size={20} /> },
        { label: 'Profile', path: '/tech/profile', icon: <Users size={20} /> },
      ];
    case 'user':
      return [
        { label: 'Inicio', path: '/app', icon: <Home size={20} /> },
        { label: 'Solicitar Ayuda', path: '/app/request', icon: <Shield size={20} /> },
        { label: 'Mis Solicitudes', path: '/app/requests', icon: <FileText size={20} /> },
        { label: 'Planes', path: '/app/subscriptions', icon: <ShoppingCart size={20} /> },
        { label: 'Aprendizaje', path: '/app/learning', icon: <BookOpen size={20} /> },
        { label: 'Recompensas', path: '/app/rewards', icon: <Award size={20} /> },
        { label: 'Perfil', path: '/app/profile', icon: <Users size={20} /> },
      ];
    default:
      return [];
  }
};

const getVariantStyles = (variant: LayoutProps['variant']) => {
  switch (variant) {
    case 'segurifai-admin':
      return { bg: 'bg-blue-900', hover: 'hover:bg-blue-800', text: 'SegurifAI Admin' };
    case 'paq-admin':
      return { bg: 'bg-green-700', hover: 'hover:bg-green-600', text: 'PAQ Admin' };
    case 'mawdy-admin':
      return { bg: 'bg-red-700', hover: 'hover:bg-red-600', text: 'SegurifAI Admin' };
    case 'field-tech':
      return { bg: 'bg-red-600', hover: 'hover:bg-red-500', text: 'SegurifAI Tech' };
    case 'user':
      return { bg: 'bg-blue-900', hover: 'hover:bg-blue-800', text: 'SegurifAI' };
  }
};

export const Layout: React.FC<LayoutProps> = ({ children, variant }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const navItems = getNavItems(variant);
  const styles = getVariantStyles(variant);

  // Load collapsed state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    if (saved !== null) {
      setSidebarCollapsed(JSON.parse(saved));
    }
  }, []);

  // Save collapsed state to localStorage
  const toggleSidebarCollapse = () => {
    const newState = !sidebarCollapsed;
    setSidebarCollapsed(newState);
    localStorage.setItem('sidebarCollapsed', JSON.stringify(newState));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 ${sidebarCollapsed ? 'lg:w-20' : 'lg:w-64'} w-64 ${styles.bg} text-white transform transition-all duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={`p-4 lg:p-6 border-b border-white/10 ${sidebarCollapsed ? 'lg:px-3' : ''}`}>
            <div className="flex items-center justify-between">
              <div className={`${sidebarCollapsed ? 'lg:hidden' : ''}`}>
                <h1 className="text-xl font-bold">{styles.text}</h1>
                <p className="text-sm text-white/60 mt-1 truncate max-w-[180px]">{user?.email}</p>
              </div>
              {/* Collapsed state - show icon */}
              <div className={`hidden ${sidebarCollapsed ? 'lg:flex' : ''} items-center justify-center w-full`}>
                <Shield size={28} className="text-white" />
              </div>
              {/* Desktop collapse button */}
              <button
                onClick={toggleSidebarCollapse}
                className={`hidden lg:flex items-center justify-center p-2 rounded-lg hover:bg-white/10 transition-colors ${sidebarCollapsed ? 'absolute right-2 top-4' : ''}`}
                title={sidebarCollapsed ? 'Expandir menú' : 'Colapsar menú'}
              >
                {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
              </button>
              {/* Mobile close button */}
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className={`flex-1 p-2 lg:p-4 space-y-1 overflow-y-auto ${sidebarCollapsed ? 'lg:px-2' : ''}`}>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''} ${
                  location.pathname === item.path
                    ? 'bg-white/20 text-white'
                    : `text-white/70 ${styles.hover}`
                }`}
                onClick={() => setSidebarOpen(false)}
                title={sidebarCollapsed ? item.label : ''}
              >
                <span className="flex-shrink-0">{item.icon}</span>
                <span className={`${sidebarCollapsed ? 'lg:hidden' : ''}`}>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Logout */}
          <div className={`p-2 lg:p-4 border-t border-white/10 ${sidebarCollapsed ? 'lg:px-2' : ''}`}>
            <button
              onClick={logout}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg w-full text-white/70 ${styles.hover} transition-colors ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''}`}
              title={sidebarCollapsed ? 'Cerrar Sesión' : ''}
            >
              <LogOut size={20} className="flex-shrink-0" />
              <span className={`${sidebarCollapsed ? 'lg:hidden' : ''}`}>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen min-w-0">
        {/* Top header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu size={24} />
            </button>

            <div className="flex items-center gap-4 ml-auto">
              <button className="p-2 rounded-lg hover:bg-gray-100 relative">
                <Bell size={20} />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium">
                    {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
};
