import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { userAPI, servicesAPI, elearningAPI } from '../../services/api';
import {
  Shield, BookOpen, Award, Wallet, ShoppingCart, Clock,
  ChevronRight, Star, Gift, Zap, TrendingUp
} from 'lucide-react';

export const UserDashboard: React.FC = () => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
  const subscription = profile?.subscription;

  return (
    <Layout variant="user">
      <div className="space-y-6">
        {/* Welcome Banner */}
        <div className="card bg-gradient-to-r from-blue-900 via-blue-800 to-blue-700 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">
                Hola, {profile?.user?.first_name || 'Usuario'}!
              </h1>
              <p className="text-blue-200 mt-1">
                Bienvenido a SegurifAI - Tu asistencia segura
              </p>
            </div>
            <Shield size={48} className="opacity-50" />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link to="/app/request" className="card card-hover text-center group">
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-red-100 flex items-center justify-center group-hover:bg-red-200 transition-colors">
              <Shield className="text-red-600" size={24} />
            </div>
            <p className="font-medium">Solicitar Ayuda</p>
            <p className="text-xs text-gray-500 mt-1">Asistencia 24/7</p>
          </Link>
          <Link to="/app/learning" className="card card-hover text-center group">
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <BookOpen className="text-blue-600" size={24} />
            </div>
            <p className="font-medium">E-Learning</p>
            <p className="text-xs text-gray-500 mt-1">Gana puntos</p>
          </Link>
          <Link to="/app/subscriptions" className="card card-hover text-center group">
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <ShoppingCart className="text-purple-600" size={24} />
            </div>
            <p className="font-medium">Planes</p>
            <p className="text-xs text-gray-500 mt-1">Suscripciones</p>
          </Link>
          <Link to="/app/wallet" className="card card-hover text-center group">
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-green-100 flex items-center justify-center group-hover:bg-green-200 transition-colors">
              <Wallet className="text-green-600" size={24} />
            </div>
            <p className="font-medium">PAQ Wallet</p>
            <p className="text-xs text-gray-500 mt-1">Vincula tu cuenta</p>
          </Link>
        </div>

        {/* Subscription Status */}
        {subscription?.renewal_countdown && (
          <div className={`card border-l-4 ${
            subscription.renewal_countdown.urgency === 'critical' ? 'border-l-red-500 bg-red-50' :
            subscription.renewal_countdown.urgency === 'high' ? 'border-l-orange-500 bg-orange-50' :
            subscription.renewal_countdown.urgency === 'medium' ? 'border-l-yellow-500 bg-yellow-50' :
            'border-l-green-500 bg-green-50'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className={`${
                  subscription.renewal_countdown.urgency === 'critical' ? 'text-red-500' :
                  subscription.renewal_countdown.urgency === 'high' ? 'text-orange-500' :
                  'text-green-500'
                }`} />
                <div>
                  <p className="font-medium">{subscription.renewal_countdown.message}</p>
                  <p className="text-sm text-gray-600">{subscription.renewal_countdown.plan_name}</p>
                </div>
              </div>
              <Link to="/app/subscriptions" className="btn btn-primary btn-sm">
                Renovar
              </Link>
            </div>
          </div>
        )}

        {/* E-Learning Progress */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Award className="text-yellow-500" />
              Tu Progreso
            </h3>
            <Link to="/app/learning" className="text-blue-600 text-sm flex items-center gap-1">
              Ver todo <ChevronRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl">
              <Star className="mx-auto text-yellow-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-yellow-700">
                {elearning?.points?.total_points || 0}
              </p>
              <p className="text-sm text-yellow-600">Puntos</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
              <TrendingUp className="mx-auto text-blue-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-blue-700">
                {elearning?.points?.level_display || 'Novato'}
              </p>
              <p className="text-sm text-blue-600">Nivel</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
              <BookOpen className="mx-auto text-green-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-green-700">
                {elearning?.modules?.completed || 0}/{elearning?.modules?.total_available || 0}
              </p>
              <p className="text-sm text-green-600">Modulos</p>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
              <Gift className="mx-auto text-purple-500 mb-2" size={28} />
              <p className="text-2xl font-bold text-purple-700">
                Q{elearning?.credits?.available_balance || 0}
              </p>
              <p className="text-sm text-purple-600">Creditos</p>
            </div>
          </div>

          {/* Level Progress Bar */}
          {elearning?.points?.next_level && (
            <div className="mt-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Progreso al siguiente nivel</span>
                <span className="font-medium">{elearning.points.next_level.progress_percentage}%</span>
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all"
                  style={{ width: `${elearning.points.next_level.progress_percentage}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {elearning.points.next_level.points_remaining} puntos para {elearning.points.next_level.level}
              </p>
            </div>
          )}
        </div>

        {/* Recent Achievements */}
        {elearning?.achievements?.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Logros Recientes</h3>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {elearning.achievements.slice(0, 5).map((achievement: any) => (
                <div key={achievement.id} className="flex-shrink-0 w-24 text-center">
                  <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-white text-2xl">
                    {achievement.icon || '🏆'}
                  </div>
                  <p className="text-xs font-medium text-gray-700 truncate">{achievement.name}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
