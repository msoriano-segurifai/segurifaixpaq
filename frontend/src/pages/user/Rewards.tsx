import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { elearningAPI, promoCodesAPI } from '../../services/api';
import {
  Trophy, Star, Target, Gift, Zap, Medal, Crown, Award,
  Lock, CheckCircle, TrendingUp, RefreshCw, Sparkles, BookOpen,
  ArrowRight, Percent, BadgeCheck, Clock, Ticket, Copy
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

interface PromoCode {
  id: number;
  code: string;
  description: string;
  discount_type: string;
  discount_value: number;
  valid_until: string;
  is_used: boolean;
  source: string;
}

export const Rewards: React.FC = () => {
  const [data, setData] = useState<RewardsData | null>(null);
  const [points, setPoints] = useState<any>(null);
  const [modules, setModules] = useState<any[]>([]);
  const [progress, setProgress] = useState<any[]>([]);
  const [promoCodes, setPromoCodes] = useState<PromoCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'achievements' | 'rewards' | 'codes' | 'leaderboard'>('achievements');
  const [redeeming, setRedeeming] = useState<number | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Fetch actual data from multiple endpoints
      const [pointsRes, progressRes, modulesRes, achievementsRes, leaderboardRes, promoCodesRes] = await Promise.all([
        elearningAPI.getMyPoints(),
        elearningAPI.getMyProgress(),
        elearningAPI.getModules(),
        elearningAPI.getMyAchievements().catch(() => ({ data: [] })),
        elearningAPI.getLeaderboard().catch(() => ({ data: [] })),
        promoCodesAPI.getAvailableCodes().catch(() => ({ data: [] }))
      ]);

      // Set promo codes (backend returns { codes: [...], count: N })
      const promoData = promoCodesRes.data?.codes || promoCodesRes.data?.codigos || promoCodesRes.data || [];
      setPromoCodes(Array.isArray(promoData) ? promoData : []);

      const pointsData = pointsRes.data?.puntos || pointsRes.data;
      const progressData = progressRes.data?.progress || progressRes.data || [];
      const modulesData = modulesRes.data?.modules || modulesRes.data || [];

      setPoints(pointsData);
      setProgress(Array.isArray(progressData) ? progressData : []);
      setModules(Array.isArray(modulesData) ? modulesData : []);

      // Calculate level based on points (20 points = 1 level increase)
      const totalPoints = pointsData?.puntos_totales || 0;
      const calculatedLevel = Math.floor(totalPoints / 100) + 1;
      const levelNames = ['Novato', 'Aprendiz', 'Intermedio', 'Avanzado', 'Experto', 'Maestro', 'Elite', 'Legendario'];

      setData({
        total_points: totalPoints,
        level: calculatedLevel,
        level_name: levelNames[Math.min(calculatedLevel - 1, levelNames.length - 1)],
        next_level_points: calculatedLevel * 100,
        achievements: achievementsRes.data?.length > 0 ? achievementsRes.data : generateAchievements(progressData, modulesData, totalPoints),
        available_rewards: mockRewards,
        redeemed_rewards: [],
        leaderboard: leaderboardRes.data?.length > 0 ? leaderboardRes.data : mockLeaderboard
      });
    } catch (error) {
      // Use mock data for demo
      setData({
        total_points: 250,
        level: 3,
        level_name: 'Intermedio',
        next_level_points: 300,
        achievements: mockAchievements,
        available_rewards: mockRewards,
        redeemed_rewards: [],
        leaderboard: mockLeaderboard
      });
    } finally {
      setLoading(false);
    }
  };

  // Generate achievements based on actual progress
  const generateAchievements = (progressData: any[], modulesData: any[], totalPoints: number): Achievement[] => {
    const completedModules = progressData.filter(p => p.estado === 'COMPLETADO').length;
    const perfectQuizzes = progressData.filter(p => p.porcentaje_quiz === 100).length;

    return [
      {
        id: 1,
        name: 'Primer Paso',
        description: 'Completa tu primer módulo de aprendizaje',
        icon: 'star',
        points: 50,
        is_unlocked: completedModules >= 1,
        progress: Math.min(completedModules, 1),
        max_progress: 1
      },
      {
        id: 2,
        name: 'Estudiante Dedicado',
        description: 'Completa 3 módulos de aprendizaje',
        icon: 'medal',
        points: 100,
        is_unlocked: completedModules >= 3,
        progress: Math.min(completedModules, 3),
        max_progress: 3
      },
      {
        id: 3,
        name: 'Experto en Seguridad',
        description: 'Completa todos los módulos disponibles',
        icon: 'trophy',
        points: 200,
        is_unlocked: completedModules >= modulesData.length,
        progress: completedModules,
        max_progress: modulesData.length || 5
      },
      {
        id: 4,
        name: 'Perfeccionista',
        description: 'Obtén 100% en 3 quizzes',
        icon: 'zap',
        points: 150,
        is_unlocked: perfectQuizzes >= 3,
        progress: Math.min(perfectQuizzes, 3),
        max_progress: 3
      },
      {
        id: 5,
        name: 'Acumulador de Puntos',
        description: 'Acumula 500 puntos totales',
        icon: 'crown',
        points: 200,
        is_unlocked: totalPoints >= 500,
        progress: Math.min(totalPoints, 500),
        max_progress: 500
      },
      {
        id: 6,
        name: 'Maestro del Conocimiento',
        description: 'Alcanza el nivel Elite (1000 puntos)',
        icon: 'award',
        points: 500,
        is_unlocked: totalPoints >= 1000,
        progress: Math.min(totalPoints, 1000),
        max_progress: 1000
      },
    ];
  };

  const handleRedeem = async (rewardId: number) => {
    setRedeeming(rewardId);
    try {
      await elearningAPI.redeemReward(rewardId);
      alert('Recompensa canjeada exitosamente! Revisa tu perfil para ver tu codigo promocional.');
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
  const creditsEarned = data ? (data.total_points * 0.05).toFixed(2) : '0.00';
  const completedModulesCount = progress.filter(p => p.estado === 'COMPLETADO').length;
  const unlockedAchievements = data?.achievements.filter(a => a.is_unlocked).length || 0;

  return (
    <Layout variant="user">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Hero Header */}
        <div className="bg-gradient-to-br from-yellow-500 via-orange-500 to-red-500 rounded-3xl p-8 text-white shadow-2xl">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-4 bg-white/20 rounded-2xl backdrop-blur-sm">
              <Trophy className="text-yellow-200" size={36} />
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold">Recompensas y Logros</h1>
              <p className="text-yellow-100">Aprende, gana puntos y canjea premios increíbles</p>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/20 rounded-xl p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-2">
                <Star className="text-yellow-200" size={24} />
                <TrendingUp className="text-green-300" size={16} />
              </div>
              <p className="text-3xl font-bold">{data?.total_points || 0}</p>
              <p className="text-sm text-yellow-100">Puntos Totales</p>
            </div>

            <div className="bg-white/20 rounded-xl p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-2">
                <Gift className="text-green-200" size={24} />
                <Sparkles className="text-yellow-200" size={16} />
              </div>
              <p className="text-3xl font-bold">Q{creditsEarned}</p>
              <p className="text-sm text-yellow-100">Créditos Ganados</p>
            </div>

            <div className="bg-white/20 rounded-xl p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-2">
                <BookOpen className="text-blue-200" size={24} />
                <CheckCircle className="text-green-300" size={16} />
              </div>
              <p className="text-3xl font-bold">{completedModulesCount}/{modules.length}</p>
              <p className="text-sm text-yellow-100">Módulos Completados</p>
            </div>

            <div className="bg-white/20 rounded-xl p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-2">
                <Award className="text-purple-200" size={24} />
                <BadgeCheck className="text-green-300" size={16} />
              </div>
              <p className="text-3xl font-bold">{unlockedAchievements}/{data?.achievements.length || 0}</p>
              <p className="text-sm text-yellow-100">Logros Desbloqueados</p>
            </div>
          </div>
        </div>

        {/* Level Progress Card */}
        <div className="card bg-gradient-to-r from-purple-600 to-pink-600 text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
                <Crown size={32} />
              </div>
              <div>
                <p className="text-purple-200 text-sm font-medium">Nivel {data?.level}</p>
                <p className="text-2xl font-bold">{data?.level_name}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-4xl font-bold">{data?.total_points}</p>
              <p className="text-purple-200 text-sm">puntos acumulados</p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Progreso al siguiente nivel</span>
              <span className="font-bold">{data?.total_points} / {data?.next_level_points} pts</span>
            </div>
            <div className="h-4 bg-white/20 rounded-full overflow-hidden shadow-inner">
              <div
                className="h-full bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full transition-all duration-500 shadow-lg"
                style={{ width: `${Math.min(progressPercent, 100)}%` }}
              />
            </div>
            <p className="text-sm text-purple-200 mt-2">
              Te faltan {Math.max(0, (data?.next_level_points || 0) - (data?.total_points || 0))} puntos para el siguiente nivel
            </p>
          </div>
        </div>

        {/* Credits Info Banner */}
        <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-100 rounded-xl">
              <Gift className="text-green-600" size={28} />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-green-900 text-lg mb-1">💰 Sistema de Créditos</h3>
              <p className="text-green-700 text-sm leading-relaxed">
                Por cada <strong>20 puntos</strong> que acumules, ganas <strong>Q1.00 en créditos</strong>.
                Actualmente tienes <strong className="text-green-900 text-lg">Q{creditsEarned}</strong> en créditos
                que se aplicarán automáticamente como descuento en tu próxima suscripción.
              </p>
              <a
                href="/user/elearning"
                className="inline-flex items-center gap-2 mt-3 text-green-700 hover:text-green-900 font-semibold transition-colors"
              >
                <BookOpen size={18} />
                Ir al Centro de Aprendizaje
                <ArrowRight size={16} />
              </a>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex bg-gray-100 p-1 rounded-xl">
          {[
            { id: 'achievements', label: 'Logros', icon: Trophy },
            { id: 'codes', label: 'Mis Códigos', icon: Ticket, badge: promoCodes.filter(c => c.source === 'E-Learning' && !c.is_used).length },
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
              {tab.badge && tab.badge > 0 && (
                <span className="ml-1 px-2 py-0.5 bg-green-500 text-white text-xs rounded-full font-bold">
                  {tab.badge}
                </span>
              )}
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

        {/* My Promo Codes Tab - Only E-Learning Earned Codes */}
        {activeTab === 'codes' && (() => {
          // Filter to only show e-learning earned codes
          const elearningCodes = promoCodes.filter(c => c.source === 'E-Learning');
          const totalPoints = data?.total_points || 0;
          return (
          <div className="space-y-4">
            {/* Progress info - how to unlock codes */}
            <div className="card bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-purple-100 rounded-xl">
                  <Target className="text-purple-600" size={28} />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-purple-900 text-lg mb-2">Desbloquea Codigos con E-Learning</h3>
                  <p className="text-purple-700 text-sm mb-3">
                    Completa modulos educativos y quizzes para ganar puntos. Al alcanzar ciertos niveles, desbloquearas codigos de descuento exclusivos.
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                    <div className={`p-2 rounded-lg text-center ${totalPoints >= 100 ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-gray-100 text-gray-500'}`}>
                      <strong>100 pts</strong><br/>2% OFF
                    </div>
                    <div className={`p-2 rounded-lg text-center ${totalPoints >= 250 ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-gray-100 text-gray-500'}`}>
                      <strong>250 pts</strong><br/>3% OFF
                    </div>
                    <div className={`p-2 rounded-lg text-center ${totalPoints >= 500 ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-gray-100 text-gray-500'}`}>
                      <strong>500 pts</strong><br/>5% OFF
                    </div>
                    <div className={`p-2 rounded-lg text-center ${totalPoints >= 1000 ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-gray-100 text-gray-500'}`}>
                      <strong>1000 pts</strong><br/>7% OFF
                    </div>
                  </div>
                  <p className="text-purple-600 text-xs mt-2">
                    Tus puntos actuales: <strong className="text-lg">{totalPoints}</strong>
                  </p>
                </div>
              </div>
            </div>

            {elearningCodes.length === 0 ? (
              <div className="card text-center py-12">
                <Ticket className="mx-auto text-gray-300 mb-4" size={64} />
                <h3 className="text-xl font-bold text-gray-700 mb-2">No tienes códigos promocionales</h3>
                <p className="text-gray-500 mb-4">
                  Completa módulos de aprendizaje y quizzes para ganar códigos de descuento
                </p>
                <a
                  href="/user/elearning"
                  className="inline-flex items-center gap-2 btn btn-primary"
                >
                  <BookOpen size={18} />
                  Ir al Centro de Aprendizaje
                  <ArrowRight size={16} />
                </a>
              </div>
            ) : (
              <>
                <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200">
                  <div className="flex items-center gap-3">
                    <Gift className="text-green-600" size={24} />
                    <div>
                      <h3 className="font-bold text-green-900">Tus Códigos de Descuento</h3>
                      <p className="text-sm text-green-700">
                        Usa estos códigos al momento de pagar para obtener descuentos
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {elearningCodes.map((promo) => {
                    const isExpired = promo.valid_until && new Date(promo.valid_until) < new Date();
                    return (
                      <div
                        key={promo.id}
                        className={`card ${
                          promo.is_used
                            ? 'bg-gray-100 opacity-60'
                            : isExpired
                            ? 'bg-red-50 border-red-200'
                            : 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className={`p-3 rounded-xl ${
                              promo.is_used ? 'bg-gray-200' : isExpired ? 'bg-red-100' : 'bg-green-100'
                            }`}>
                              <Ticket className={
                                promo.is_used ? 'text-gray-400' : isExpired ? 'text-red-500' : 'text-green-600'
                              } size={24} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`font-mono font-bold text-xl tracking-wider ${
                                  promo.is_used ? 'text-gray-400' : 'text-gray-900'
                                }`}>
                                  {promo.code}
                                </span>
                                {!promo.is_used && !isExpired && (
                                  <button
                                    onClick={() => {
                                      navigator.clipboard.writeText(promo.code);
                                      setCopiedCode(promo.code);
                                      setTimeout(() => setCopiedCode(null), 2000);
                                    }}
                                    className="p-1 hover:bg-green-100 rounded transition-colors"
                                    title="Copiar código"
                                  >
                                    {copiedCode === promo.code ? (
                                      <CheckCircle className="text-green-600" size={18} />
                                    ) : (
                                      <Copy className="text-gray-400" size={18} />
                                    )}
                                  </button>
                                )}
                              </div>
                              <p className="text-sm text-gray-600 mb-2">
                                {promo.description || 'Descuento especial por aprendizaje'}
                              </p>
                              <div className="flex items-center gap-2">
                                <span className={`inline-block px-2 py-1 rounded-full text-xs font-bold ${
                                  promo.is_used
                                    ? 'bg-gray-200 text-gray-500'
                                    : isExpired
                                    ? 'bg-red-100 text-red-600'
                                    : 'bg-green-100 text-green-700'
                                }`}>
                                  {promo.discount_type === 'percentage' || promo.discount_type === 'PORCENTAJE'
                                    ? `${promo.discount_value}% OFF`
                                    : `Q${promo.discount_value} OFF`
                                  }
                                </span>
                                {promo.source && (
                                  <span className="text-xs text-gray-500 flex items-center gap-1">
                                    <BookOpen size={12} />
                                    E-Learning
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            {promo.is_used ? (
                              <span className="inline-block px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded-full font-medium">
                                Usado
                              </span>
                            ) : isExpired ? (
                              <span className="inline-block px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full font-medium">
                                Expirado
                              </span>
                            ) : (
                              <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                Disponible
                              </span>
                            )}
                            {promo.valid_until && !promo.is_used && (
                              <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                <Clock size={12} />
                                {new Date(promo.valid_until).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
          );
        })()}

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

