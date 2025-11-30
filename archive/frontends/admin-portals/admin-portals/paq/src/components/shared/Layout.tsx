import React, { ReactNode, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Home, Users, FileText, CreditCard, Settings, LogOut, Menu, X,
  Truck, MapPin, Clock, DollarSign, Award, BookOpen, ShoppingCart,
  Activity, PieChart, Bell, Shield, Wallet, BarChart3, Building2
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
        { label: 'Home', path: '/app', icon: <Home size={20} /> },
        { label: 'Request Help', path: '/app/request', icon: <Shield size={20} /> },
        { label: 'My Requests', path: '/app/requests', icon: <FileText size={20} /> },
        { label: 'Subscriptions', path: '/app/subscriptions', icon: <ShoppingCart size={20} /> },
        { label: 'E-Learning', path: '/app/learning', icon: <BookOpen size={20} /> },
        { label: 'Rewards', path: '/app/rewards', icon: <Award size={20} /> },
        { label: 'PAQ Wallet', path: '/app/wallet', icon: <Wallet size={20} /> },
        { label: 'Profile', path: '/app/profile', icon: <Users size={20} /> },
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
      return { bg: 'bg-red-700', hover: 'hover:bg-red-600', text: 'MAWDY Admin' };
    case 'field-tech':
      return { bg: 'bg-red-600', hover: 'hover:bg-red-500', text: 'MAWDY Tech' };
    case 'user':
      return { bg: 'bg-blue-900', hover: 'hover:bg-blue-800', text: 'SegurifAI' };
  }
};

export const Layout: React.FC<LayoutProps> = ({ children, variant }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const navItems = getNavItems(variant);
  const styles = getVariantStyles(variant);

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
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 ${styles.bg} text-white transform transition-transform lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-white/10">
            <h1 className="text-xl font-bold">{styles.text}</h1>
            <p className="text-sm text-white/60 mt-1">{user?.email}</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-white/20 text-white'
                    : `text-white/70 ${styles.hover}`
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-white/10">
            <button
              onClick={logout}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg w-full text-white/70 ${styles.hover} transition-colors`}
            >
              <LogOut size={20} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            <div className="flex items-center gap-4">
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
        <main className="flex-1 p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
};
