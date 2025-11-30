import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { elearningAPI } from '../../services/api';
import {
  Trophy, Star, Target, Gift, Zap, Medal, Crown, Award,
  Lock, CheckCircle, TrendingUp, Calendar, RefreshCw
} from 'lucide-react';

interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  points: number;
  is_unlocked: boolean;
  unlocked_at?: string;
  progress?: number;
  max_progress?: number;
}

interface LeaderboardEntry {
  rank: number;
  user_name: string;
  points: number;
  level: number;
  is_current_user: boolean;
}

interface RewardsData {
  total_points: number;
  level: number;
  level_name: string;
  next_level_points: number;
  achievements: Achievement[];
  available_rewards: Reward[];
  redeemed_rewards: Reward[];
  leaderboard: LeaderboardEntry[];
}

interface Reward {
  id: number;
  name: string;
  description: string;
  points_cost: number;
  discount_percent?: number;
  is_available: boolean;
}

export const Rewards: React.FC = () => {
  const [data, setData] = useState<RewardsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'achievements' | 'rewards' | 'leaderboard'>('achievements');
  const [redeeming, setRedeeming] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await elearningAPI.getMyProgress();
      // Transform the data
      setData({
        total_points: response.data.total_points || 250,
        level: response.data.level || 3,
        level_name: response.data.level_name || 'Aprendiz Avanzado',
        next_level_points: response.data.next_level_points || 500,
        achievements: response.data.achievements || mockAchievements,
        available_rewards: response.data.available_rewards || mockRewards,
        redeemed_rewards: response.data.redeemed_rewards || [],
        leaderboard: response.data.leaderboard || mockLeaderboard
      });
    } catch (error) {
      // Use mock data for demo
      setData({
        total_points: 250,
        level: 3,
        level_name: 'Aprendiz Avanzado',
        next_level_points: 500,
        achievements: mockAchievements,
        available_rewards: mockRewards,
        redeemed_rewards: [],
        leaderboard: mockLeaderboard
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRedeem = async (rewardId: number) => {
    setRedeeming(rewardId);
    try {
      // await elearningAPI.redeemReward(rewardId);
      alert('Recompensa canjeada exitosamente!');
      await loadData();
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al canjear recompensa');
    } finally {
      setRedeeming(null);
    }
  };

  const getAchievementIcon = (icon: string) => {
    const icons: Record<string, React.ReactNode> = {
      'trophy': <Trophy className="text-yellow-500" size={24} />,
      'star': <Star className="text-yellow-500" size={24} />,
      'target': <Target className="text-red-500" size={24} />,
      'zap': <Zap className="text-blue-500" size={24} />,
      'medal': <Medal className="text-orange-500" size={24} />,
      'crown': <Crown className="text-purple-500" size={24} />,
      'award': <Award className="text-green-500" size={24} />,
    };
    return icons[icon] || <Star className="text-gray-400" size={24} />;
  };

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="animate-spin text-yellow-600" size={48} />
        </div>
      </Layout>
    );
  }

  const progressPercent = data ? (data.total_points / data.next_level_points) * 100 : 0;

  return (
    <Layout variant="user">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Recompensas y Logros</h1>
          <p className="text-gray-500">Gana puntos, desbloquea logros y canjea premios</p>
        </div>

        {/* Level Card */}
        <div className="card bg-gradient-to-r from-yellow-500 to-orange-500 text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center">
                <Crown size={28} />
              </div>
              <div>
                <p className="text-yellow-100 text-sm">Nivel {data?.level}</p>
                <p className="text-xl font-bold">{data?.level_name}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold">{data?.total_points}</p>
              <p className="text-yellow-100 text-sm">puntos</p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Progreso al siguiente nivel</span>
              <span>{data?.total_points} / {data?.next_level_points}</span>
            </div>
            <div className="h-3 bg-white/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-white rounded-full transition-all"
                style={{ width: `${Math.min(progressPercent, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex bg-gray-100 p-1 rounded-xl">
          {[
            { id: 'achievements', label: 'Logros', icon: Trophy },
            { id: 'rewards', label: 'Premios', icon: Gift },
            { id: 'leaderboard', label: 'Ranking', icon: TrendingUp }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-white shadow text-gray-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Achievements Tab */}
        {activeTab === 'achievements' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data?.achievements.map((achievement) => (
              <div
                key={achievement.id}
                className={`card ${
                  achievement.is_unlocked
                    ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200'
                    : 'opacity-60'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                    achievement.is_unlocked ? 'bg-yellow-100' : 'bg-gray-100'
                  }`}>
                    {achievement.is_unlocked ? (
                      getAchievementIcon(achievement.icon)
                    ) : (
                      <Lock className="text-gray-400" size={24} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold">{achievement.name}</h3>
                      {achievement.is_unlocked && (
                        <CheckCircle className="text-green-500" size={16} />
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mb-2">{achievement.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-yellow-600">
                        +{achievement.points} puntos
                      </span>
                      {achievement.progress !== undefined && !achievement.is_unlocked && (
                        <span className="text-xs text-gray-500">
                          {achievement.progress}/{achievement.max_progress}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Rewards Tab */}
        {activeTab === 'rewards' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data?.available_rewards.map((reward) => (
                <div key={reward.id} className="card">
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center">
                      <Gift className="text-purple-600" size={24} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold">{reward.name}</h3>
                      <p className="text-sm text-gray-500 mb-2">{reward.description}</p>
                      {reward.discount_percent && (
                        <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full mb-2">
                          {reward.discount_percent}% descuento
                        </span>
                      )}
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-purple-600">{reward.points_cost} puntos</span>
                        <button
                          onClick={() => handleRedeem(reward.id)}
                          disabled={redeeming === reward.id || (data?.total_points || 0) < reward.points_cost}
                          className="btn btn-primary btn-sm"
                        >
                          {redeeming === reward.id ? 'Canjeando...' : 'Canjear'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Leaderboard Tab */}
        {activeTab === 'leaderboard' && (
          <div className="card">
            <div className="space-y-3">
              {data?.leaderboard.map((entry) => (
                <div
                  key={entry.rank}
                  className={`flex items-center gap-4 p-4 rounded-xl ${
                    entry.is_current_user
                      ? 'bg-blue-50 border-2 border-blue-200'
                      : 'bg-gray-50'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                    entry.rank === 1 ? 'bg-yellow-400 text-yellow-900' :
                    entry.rank === 2 ? 'bg-gray-300 text-gray-700' :
                    entry.rank === 3 ? 'bg-orange-300 text-orange-800' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {entry.rank <= 3 ? (
                      <Crown size={20} />
                    ) : (
                      entry.rank
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">
                      {entry.user_name}
                      {entry.is_current_user && <span className="text-blue-600"> (Tu)</span>}
                    </p>
                    <p className="text-sm text-gray-500">Nivel {entry.level}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">{entry.points}</p>
                    <p className="text-xs text-gray-500">puntos</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

// Mock data
const mockAchievements: Achievement[] = [
  { id: 1, name: 'Primer Paso', description: 'Completa tu primer modulo', icon: 'star', points: 50, is_unlocked: true, unlocked_at: new Date().toISOString() },
  { id: 2, name: 'Estudiante Dedicado', description: 'Completa 5 modulos', icon: 'medal', points: 100, is_unlocked: true },
  { id: 3, name: 'Experto en Seguridad', description: 'Completa todos los modulos de seguridad vial', icon: 'trophy', points: 200, is_unlocked: false, progress: 3, max_progress: 5 },
  { id: 4, name: 'Velocista', description: 'Completa un quiz en menos de 2 minutos', icon: 'zap', points: 75, is_unlocked: false },
  { id: 5, name: 'Perfeccionista', description: 'Obtiene 100% en 3 quizzes', icon: 'crown', points: 150, is_unlocked: false, progress: 1, max_progress: 3 },
  { id: 6, name: 'Maestro del Conocimiento', description: 'Alcanza el nivel 10', icon: 'award', points: 500, is_unlocked: false },
];

const mockRewards: Reward[] = [
  { id: 1, name: '10% Descuento', description: 'En tu proxima asistencia', points_cost: 100, discount_percent: 10, is_available: true },
  { id: 2, name: '25% Descuento', description: 'En renovacion de suscripcion', points_cost: 250, discount_percent: 25, is_available: true },
  { id: 3, name: 'Mes Gratis', description: 'Un mes de suscripcion gratis', points_cost: 500, is_available: true },
  { id: 4, name: 'Kit de Emergencia', description: 'Kit basico de emergencia vehicular', points_cost: 750, is_available: true },
];

const mockLeaderboard: LeaderboardEntry[] = [
  { rank: 1, user_name: 'Maria G.', points: 1250, level: 8, is_current_user: false },
  { rank: 2, user_name: 'Carlos M.', points: 980, level: 7, is_current_user: false },
  { rank: 3, user_name: 'Ana L.', points: 875, level: 6, is_current_user: false },
  { rank: 4, user_name: 'Tu', points: 250, level: 3, is_current_user: true },
  { rank: 5, user_name: 'Pedro S.', points: 200, level: 2, is_current_user: false },
];
