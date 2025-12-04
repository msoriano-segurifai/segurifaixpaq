import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { userAPI } from '../../services/api';
import {
  Shield, BookOpen, Award, Wallet, ShoppingCart,
  ChevronRight, Star, Gift, TrendingUp, AlertTriangle, Phone,
  Heart, Truck, CheckCircle, Loader2, Sparkles,
  FileText, Users, Zap, Sun, Moon, Sunrise,
  Lightbulb, Car, Activity, MapPin
} from 'lucide-react';

// Safety tips for the dashboard
const SAFETY_TIPS = [
  { icon: <Car size={18} />, tip: 'Revisa la presión de tus neumáticos cada 2 semanas para evitar emergencias viales.' },
  { icon: <Heart size={18} />, tip: 'Mantén a la mano los números de emergencia de tu familia y contacto de confianza.' },
  { icon: <Shield size={18} />, tip: 'Actualiza tu información de contacto para una respuesta de emergencia más rápida.' },
  { icon: <Truck size={18} />, tip: 'Lleva siempre cables de arranque y un triángulo reflectivo en tu vehículo.' },
  { icon: <Activity size={18} />, tip: 'Los primeros 10 minutos en una emergencia médica son cruciales. Actúa rápido.' },
  { icon: <MapPin size={18} />, tip: 'Activa el GPS de tu teléfono para que podamos localizarte más rápido en emergencias.' },
];

// Get greeting based on time of day
const getGreeting = (): { text: string; icon: React.ReactNode } => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) {
    return { text: 'Buenos días', icon: <Sunrise className="text-yellow-500" size={24} /> };
  } else if (hour >= 12 && hour < 18) {
    return { text: 'Buenas tardes', icon: <Sun className="text-orange-500" size={24} /> };
  } else {
    return { text: 'Buenas noches', icon: <Moon className="text-blue-400" size={24} /> };
  }
};

export const UserDashboard: React.FC = () => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dailyTip] = useState(() => SAFETY_TIPS[Math.floor(Math.random() * SAFETY_TIPS.length)]);
  const greeting = getGreeting();

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await userAPI.getFullProfile();
      setProfile(response.data);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const elearning = profile?.e_learning;
  const wallet = profile?.wallet;

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className="animate-spin mx-auto text-blue-600 mb-4" size={48} />
            <p className="text-gray-500">Cargando tu dashboard...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="user">
      <div className="space-y-6">
        {/* Welcome Banner with Emergency CTA */}
        <div className="card bg-gradient-to-r from-blue-900 via-blue-800 to-purple-800 text-white overflow-hidden relative">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
          <div className="relative z-10">
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="flex items-center gap-2 text-blue-200 text-sm mb-1">
                  {greeting.icon}
                  <span>{greeting.text}</span>
                </div>
                <h1 className="text-3xl font-bold">
                  {profile?.user?.first_name
                    ? `${profile.user.first_name}${profile.user.last_name ? ' ' + profile.user.last_name : ''}`
                    : 'Usuario'}!
                </h1>
                <p className="text-blue-200 mt-2 max-w-md">
                  Tu asistencia SegurifAI está activa las 24 horas del día, los 7 días de la semana.
                </p>
              </div>
              <div className="hidden md:flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full">
                <CheckCircle size={16} className="text-green-400" />
                <span className="text-sm">Cuenta Verificada</span>
              </div>
            </div>

            {/* Emergency Button */}
            <Link
              to="/app/request"
              className="inline-flex items-center gap-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-6 py-4 rounded-2xl font-bold shadow-lg hover:shadow-xl transition-all group"
            >
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <Phone size={24} />
              </div>
              <div className="text-left">
                <p className="text-lg">Solicitar Asistencia</p>
                <p className="text-sm text-red-200 font-normal">Emergencia 24/7</p>
              </div>
              <ChevronRight size={24} className="ml-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Quick Stats Row - 3 cards centered on all screen sizes */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Points */}
          <div className="card bg-gradient-to-br from-yellow-400 to-orange-500 text-white">
            <div className="flex items-center justify-between mb-3">
              <Star size={24} className="opacity-80" />
              <span className="text-xs bg-white/20 px-2 py-1 rounded-full">Puntos</span>
            </div>
            <p className="text-3xl font-bold">{elearning?.points?.total_points || 0}</p>
            <p className="text-yellow-100 text-sm">{elearning?.points?.level_display || 'Novato'}</p>
            <Link to="/app/rewards" className="mt-3 text-xs text-white/80 hover:text-white flex items-center gap-1">
              Canjear <ChevronRight size={14} />
            </Link>
          </div>

          {/* E-Learning Credits */}
          <div className="card bg-gradient-to-br from-green-500 to-emerald-600 text-white">
            <div className="flex items-center justify-between mb-3">
              <Gift size={24} className="opacity-80" />
              <span className="text-xs bg-white/20 px-2 py-1 rounded-full">Créditos</span>
            </div>
            <p className="text-3xl font-bold">Q{elearning?.credits?.available_balance || 0}</p>
            <p className="text-green-100 text-sm">Por aprendizaje</p>
            <Link to="/app/learning" className="mt-3 text-xs text-white/80 hover:text-white flex items-center gap-1">
              Aprender más <ChevronRight size={14} />
            </Link>
          </div>

          {/* PAQ Wallet Balance */}
          <div className="card bg-gradient-to-br from-[#00A86B] to-[#006644] text-white">
            <div className="flex items-center justify-between mb-3">
              <Wallet size={24} className="opacity-80" />
              <span className="text-xs bg-white/20 px-2 py-1 rounded-full">PAQ Wallet</span>
            </div>
            <p className="text-3xl font-bold">Q{wallet?.balance || 0}</p>
            <p className="text-green-100 text-sm">Saldo disponible</p>
            <Link to="/app/subscriptions" className="mt-3 text-xs text-white/80 hover:text-white flex items-center gap-1">
              Suscribirme <ChevronRight size={14} />
            </Link>
          </div>
        </div>

        {/* Daily Safety Tip */}
        <div className="card bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center text-amber-600 flex-shrink-0">
              <Lightbulb size={24} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-amber-700 bg-amber-200 px-2 py-0.5 rounded-full">
                  Tip del Día
                </span>
              </div>
              <p className="text-gray-700 text-sm flex items-center gap-2">
                <span className="text-amber-600">{dailyTip.icon}</span>
                {dailyTip.tip}
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions Grid */}
        <div>
          <h3 className="text-lg font-bold text-gray-900 mb-4">Acciones Rápidas</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link to="/app/request" className="card card-hover text-center group p-6">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-red-100 flex items-center justify-center group-hover:bg-red-200 group-hover:scale-110 transition-all">
                <AlertTriangle className="text-red-600" size={28} />
              </div>
              <p className="font-bold text-gray-900">Emergencia</p>
              <p className="text-xs text-gray-500 mt-1">Asistencia inmediata</p>
            </Link>
            <Link to="/app/learning" className="card card-hover text-center group p-6">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 group-hover:scale-110 transition-all">
                <BookOpen className="text-blue-600" size={28} />
              </div>
              <p className="font-bold text-gray-900">E-Learning</p>
              <p className="text-xs text-gray-500 mt-1">Gana puntos y créditos</p>
            </Link>
            <Link to="/app/subscriptions" className="card card-hover text-center group p-6">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 group-hover:scale-110 transition-all">
                <ShoppingCart className="text-purple-600" size={28} />
              </div>
              <p className="font-bold text-gray-900">Planes</p>
              <p className="text-xs text-gray-500 mt-1">SegurifAI Drive & Health</p>
            </Link>
            <Link to="/app/requests" className="card card-hover text-center group p-6">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-green-100 flex items-center justify-center group-hover:bg-green-200 group-hover:scale-110 transition-all">
                <FileText className="text-green-600" size={28} />
              </div>
              <p className="font-bold text-gray-900">Mis Solicitudes</p>
              <p className="text-xs text-gray-500 mt-1">Historial y seguimiento</p>
            </Link>
          </div>
        </div>

        {/* E-Learning Progress - Full Width */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Sparkles className="text-yellow-500" />
              Tu Progreso de Aprendizaje
            </h3>
            <Link to="/app/learning" className="text-blue-600 text-sm flex items-center gap-1 hover:underline">
              Ver módulos <ChevronRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
              <TrendingUp className="mx-auto text-blue-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-blue-700">
                {elearning?.points?.level_display || 'Novato'}
              </p>
              <p className="text-sm text-blue-600">Tu nivel actual</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
              <BookOpen className="mx-auto text-green-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-green-700">
                {elearning?.modules?.completed || 0}/{elearning?.modules?.total_available || 0}
              </p>
              <p className="text-sm text-green-600">Módulos completados</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-orange-100 rounded-xl">
              <Star className="mx-auto text-yellow-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-yellow-700">
                {elearning?.points?.total_points || 0}
              </p>
              <p className="text-sm text-yellow-600">Puntos totales</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
              <Gift className="mx-auto text-purple-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-purple-700">
                Q{elearning?.credits?.available_balance || 0}
              </p>
              <p className="text-sm text-purple-600">Créditos disponibles</p>
            </div>
          </div>

          {/* E-Learning Module Progress Bar */}
          {elearning?.modules && (
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600 font-medium">Progreso E-Learning</span>
                <span className="font-bold text-blue-600">
                  {elearning.modules.total_available > 0
                    ? Math.round((elearning.modules.completed / elearning.modules.total_available) * 100)
                    : 0}%
                </span>
              </div>
              <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${elearning.modules.total_available > 0
                    ? (elearning.modules.completed / elearning.modules.total_available) * 100
                    : 0}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                <span className="font-medium text-purple-600">{elearning.modules.completed}</span> de <span className="font-medium">{elearning.modules.total_available}</span> módulos completados
              </p>
            </div>
          )}

          {/* CTA Button */}
          <Link
            to="/app/learning"
            className="w-full btn btn-primary flex items-center justify-center gap-2"
          >
            <Zap size={18} />
            Continuar Aprendiendo
          </Link>
        </div>

        {/* Recent Achievements */}
        {elearning?.achievements?.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Award className="text-yellow-500" />
              Logros Recientes
            </h3>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {elearning.achievements.slice(0, 6).map((achievement: any) => (
                <div key={achievement.id} className="flex-shrink-0 w-24 text-center group cursor-pointer">
                  <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-white text-2xl shadow-lg group-hover:scale-110 transition-transform">
                    {achievement.icon || '🏆'}
                  </div>
                  <p className="text-xs font-medium text-gray-700 truncate">{achievement.name}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Help Footer */}
        <div className="card bg-gray-50 text-center">
          <p className="text-gray-600 mb-2">¿Necesitas ayuda?</p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/app/request" className="flex items-center gap-2 text-blue-600 hover:underline">
              <Phone size={16} /> Solicitar Asistencia
            </Link>
            <span className="text-gray-300">|</span>
            <Link to="/app/profile" className="flex items-center gap-2 text-blue-600 hover:underline">
              <Users size={16} /> Mi Perfil
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
};
