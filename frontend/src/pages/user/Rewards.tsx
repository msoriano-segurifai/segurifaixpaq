import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
  const [actualCredits, setActualCredits] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'achievements' | 'rewards' | 'codes' | 'leaderboard'>('achievements');
  const [redeeming, setRedeeming] = useState<number | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Fetch actual data from multiple endpoints including credits
      const [pointsRes, progressRes, modulesRes, achievementsRes, leaderboardRes, promoCodesRes, creditsRes] = await Promise.all([
        elearningAPI.getMyPoints(),
        elearningAPI.getMyProgress(),
        elearningAPI.getModules(),
        elearningAPI.getMyAchievements().catch(() => ({ data: [] })),
        elearningAPI.getLeaderboard().catch(() => ({ data: [] })),
        promoCodesAPI.getAvailableCodes().catch(() => ({ data: [] })),
        elearningAPI.getDiscountCredits().catch(() => ({ data: { saldo_disponible: 0 } }))
      ]);

      // Set actual credits from API (same as UserDashboard)
      setActualCredits(creditsRes.data?.saldo_disponible || 0);

      // Set promo codes (backend returns { codes: [...], count: N })
      const promoData = promoCodesRes.data?.codes || promoCodesRes.data?.codigos || promoCodesRes.data || [];
      setPromoCodes(Array.isArray(promoData) ? promoData : []);

      const pointsData = pointsRes.data?.puntos || pointsRes.data;
      // API returns 'progresos' not 'progress'
      const progressData = progressRes.data?.progresos || progressRes.data?.progress || progressRes.data || [];
      const modulesData = modulesRes.data?.modules || modulesRes.data || [];

      setPoints(pointsData);
      setProgress(Array.isArray(progressData) ? progressData : []);
      setModules(Array.isArray(modulesData) ? modulesData : []);

      // Use level from API (same as UserDashboard) instead of calculating locally
      const totalPoints = pointsData?.puntos_totales || 0;
      const apiLevel = pointsData?.nivel || 'NOVATO';
      // Level display mapping - matches backend UserPoints model
      const levelDisplayMap: Record<string, string> = {
        'NOVATO': 'Novato', 'PRINCIPIANTE': 'Novato',
        'APRENDIZ': 'Aprendiz',
        'CONOCEDOR': 'Conocedor', 'INTERMEDIO': 'Intermedio',
        'EXPERTO': 'Experto', 'AVANZADO': 'Avanzado',
        'MAESTRO': 'Maestro'
      };
      const levelName = levelDisplayMap[apiLevel] || 'Novato';
      // Level thresholds from backend
      const levelThresholds: Record<string, number> = {
        'NOVATO': 100, 'PRINCIPIANTE': 100,
        'APRENDIZ': 250,
        'CONOCEDOR': 500, 'INTERMEDIO': 500,
        'EXPERTO': 1000, 'AVANZADO': 1000,
        'MAESTRO': 2000
      };
      const nextLevelPoints = levelThresholds[apiLevel] || 100;

      setData({
        total_points: totalPoints,
        level: Object.keys(levelThresholds).indexOf(apiLevel) + 1,
        level_name: levelName,
        next_level_points: nextLevelPoints,
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
  const completedModulesCount = progress.filter(p => p.estado === 'COMPLETADO').length;
  // New rewards logic: Q1.50 per completed module
  const creditsEarned = (completedModulesCount * 1.50).toFixed(2);
  const unlockedAchievements = data?.achievements.filter(a => a.is_unlocked).length || 0;

  return (
    <Layout variant="user">
      <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 px-2 sm:px-0">
        {/* Hero Header - Ultra responsive */}
        <div className="bg-gradient-to-br from-yellow-500 via-orange-500 to-red-500 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 text-white shadow-2xl">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 mb-4 sm:mb-6">
            <div className="p-3 sm:p-4 bg-white/20 rounded-xl sm:rounded-2xl backdrop-blur-sm">
              <Trophy className="text-yellow-200" size={28} />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold leading-tight">Recompensas y Logros</h1>
              <p className="text-yellow-100 text-sm sm:text-base">Aprende, gana puntos y canjea premios</p>
            </div>
          </div>

          {/* Stats Cards - Mobile-first grid */}
          <div className="grid grid-cols-2 gap-2 sm:gap-3 md:gap-4">
            <div className="bg-white/20 rounded-lg sm:rounded-xl p-3 sm:p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <Star className="text-yellow-200" size={20} />
                <TrendingUp className="text-green-300 hidden sm:block" size={14} />
              </div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold">{data?.total_points || 0}</p>
              <p className="text-xs sm:text-sm text-yellow-100 truncate">Puntos</p>
            </div>

            <div className="bg-white/20 rounded-lg sm:rounded-xl p-3 sm:p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <Gift className="text-green-200" size={20} />
                <Sparkles className="text-yellow-200 hidden sm:block" size={14} />
              </div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold">Q{creditsEarned}</p>
              <p className="text-xs sm:text-sm text-yellow-100 truncate">Créditos</p>
            </div>

            <div className="bg-white/20 rounded-lg sm:rounded-xl p-3 sm:p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <BookOpen className="text-blue-200" size={20} />
                <CheckCircle className="text-green-300 hidden sm:block" size={14} />
              </div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold">{completedModulesCount}/{modules.length}</p>
              <p className="text-xs sm:text-sm text-yellow-100 truncate">Módulos</p>
            </div>

            <div className="bg-white/20 rounded-lg sm:rounded-xl p-3 sm:p-4 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <Award className="text-purple-200" size={20} />
                <BadgeCheck className="text-green-300 hidden sm:block" size={14} />
              </div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold">{unlockedAchievements}/{data?.achievements.length || 0}</p>
              <p className="text-xs sm:text-sm text-yellow-100 truncate">Logros</p>
            </div>
          </div>
        </div>

        {/* Level Progress Card - Mobile optimized */}
        <div className="card bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0 mb-4">
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-white/20 rounded-xl sm:rounded-2xl flex items-center justify-center">
                <Crown size={24} className="sm:hidden" />
                <Crown size={32} className="hidden sm:block" />
              </div>
              <div>
                <p className="text-purple-200 text-xs sm:text-sm font-medium">Nivel {data?.level}</p>
                <p className="text-lg sm:text-2xl font-bold">{data?.level_name}</p>
              </div>
            </div>
            <div className="text-left sm:text-right w-full sm:w-auto bg-white/10 rounded-lg p-2 sm:p-0 sm:bg-transparent">
              <p className="text-2xl sm:text-4xl font-bold">{data?.total_points} <span className="text-sm sm:text-base font-normal text-purple-200">pts</span></p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs sm:text-sm mb-2">
              <span>Siguiente nivel</span>
              <span className="font-bold">{data?.total_points} / {data?.next_level_points}</span>
            </div>
            <div className="h-3 sm:h-4 bg-white/20 rounded-full overflow-hidden shadow-inner">
              <div
                className="h-full bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full transition-all duration-500 shadow-lg"
                style={{ width: `${Math.min(progressPercent, 100)}%` }}
              />
            </div>
            <p className="text-xs sm:text-sm text-purple-200 mt-2">
              Faltan {Math.max(0, (data?.next_level_points || 0) - (data?.total_points || 0))} pts
            </p>
          </div>
        </div>

        {/* Credits Info Banner - Mobile optimized */}
        <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 p-3 sm:p-6">
          <div className="flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
            <div className="p-2 sm:p-3 bg-green-100 rounded-lg sm:rounded-xl">
              <Gift className="text-green-600" size={24} />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-green-900 text-base sm:text-lg mb-1">Sistema de Créditos</h3>
              <p className="text-green-700 text-xs sm:text-sm leading-relaxed">
                Por cada <strong>módulo completado</strong> ganas <strong>Q1.50</strong>.
                Tienes <strong className="text-green-900 text-base sm:text-lg">Q{creditsEarned}</strong> en créditos ({completedModulesCount} módulos).
              </p>
              <Link
                to="/app/learning"
                className="inline-flex items-center gap-2 mt-2 sm:mt-3 text-green-700 hover:text-green-900 font-semibold transition-colors text-sm"
              >
                <BookOpen size={16} />
                Centro de Aprendizaje
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>

        {/* Tabs - Scrollable on mobile */}
        <div className="overflow-x-auto -mx-2 px-2 sm:mx-0 sm:px-0">
          <div className="flex bg-gray-100 p-1 rounded-xl min-w-max sm:min-w-0">
            {[
              { id: 'achievements', label: 'Logros', shortLabel: 'Logros', icon: Trophy },
              { id: 'codes', label: 'Mis Códigos', shortLabel: 'Códigos', icon: Ticket, badge: promoCodes.filter(c => c.source === 'E-Learning' && !c.is_used).length },
              { id: 'rewards', label: 'Premios', shortLabel: 'Premios', icon: Gift },
              { id: 'leaderboard', label: 'Ranking', shortLabel: 'Rank', icon: TrendingUp }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex-1 py-2 sm:py-3 px-3 sm:px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-1 sm:gap-2 text-xs sm:text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-white shadow text-gray-900'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <tab.icon size={16} className="flex-shrink-0" />
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.shortLabel}</span>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span className="ml-0.5 sm:ml-1 px-1.5 sm:px-2 py-0.5 bg-green-500 text-white text-[10px] sm:text-xs rounded-full font-bold">
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Achievements Tab - Mobile optimized */}
        {activeTab === 'achievements' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            {data?.achievements.map((achievement) => (
              <div
                key={achievement.id}
                className={`card p-3 sm:p-4 ${
                  achievement.is_unlocked
                    ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200'
                    : 'opacity-60'
                }`}
              >
                <div className="flex items-start gap-3 sm:gap-4">
                  <div className={`w-11 h-11 sm:w-14 sm:h-14 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0 ${
                    achievement.is_unlocked ? 'bg-yellow-100' : 'bg-gray-100'
                  }`}>
                    {achievement.is_unlocked ? (
                      getAchievementIcon(achievement.icon)
                    ) : (
                      <Lock className="text-gray-400" size={20} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                      <h3 className="font-bold text-sm sm:text-base">{achievement.name}</h3>
                      {achievement.is_unlocked && (
                        <CheckCircle className="text-green-500" size={14} />
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-gray-500 mb-1 sm:mb-2 line-clamp-2">{achievement.description}</p>
                    <div className="flex items-center justify-between flex-wrap gap-1">
                      <span className="text-xs sm:text-sm font-medium text-yellow-600">
                        +{achievement.points} pts
                      </span>
                      {achievement.progress !== undefined && !achievement.is_unlocked && (
                        <span className="text-[10px] sm:text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
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
          return (
          <div className="space-y-3 sm:space-y-4">
            {/* Credits info - Q1.50 per module - Mobile optimized */}
            <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 p-3 sm:p-6">
              <div className="flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
                <div className="p-2 sm:p-3 bg-green-100 rounded-lg sm:rounded-xl">
                  <Gift className="text-green-600" size={24} />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-green-900 text-base sm:text-lg mb-1 sm:mb-2">Tus Créditos de Descuento</h3>
                  <p className="text-green-700 text-xs sm:text-sm mb-2 sm:mb-3">
                    Por cada <strong>módulo completado</strong> ganas <strong>Q1.50</strong> en créditos. Se aplican automáticamente como descuento en tu próxima suscripción.
                  </p>
                  <div className="grid grid-cols-2 gap-2 sm:gap-3">
                    <div className="p-3 sm:p-4 bg-white rounded-xl border border-green-200 text-center">
                      <p className="text-2xl sm:text-3xl font-bold text-green-700">{completedModulesCount}</p>
                      <p className="text-xs sm:text-sm text-green-600">Módulos Completados</p>
                    </div>
                    <div className="p-3 sm:p-4 bg-white rounded-xl border border-green-200 text-center">
                      <p className="text-2xl sm:text-3xl font-bold text-green-700">Q{creditsEarned}</p>
                      <p className="text-xs sm:text-sm text-green-600">Créditos Disponibles</p>
                    </div>
                  </div>
                  <Link
                    to="/app/learning"
                    className="inline-flex items-center gap-2 mt-3 text-green-700 hover:text-green-900 font-semibold transition-colors text-sm"
                  >
                    <BookOpen size={16} />
                    Completar más módulos
                    <ArrowRight size={14} />
                  </Link>
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
                <Link
                  to="/app/learning"
                  className="inline-flex items-center gap-2 btn btn-primary"
                >
                  <BookOpen size={18} />
                  Ir al Centro de Aprendizaje
                  <ArrowRight size={16} />
                </Link>
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
            {/* User's own stats */}
            <div className="mb-6">
              <h3 className="font-bold text-lg mb-3">Tu Posición</h3>
              <div className="flex items-center gap-4 p-4 rounded-xl bg-blue-50 border-2 border-blue-200">
                <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center">
                  <Star className="text-white" size={24} />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-lg">
                    {data?.total_points || 0} puntos
                  </p>
                  <p className="text-sm text-gray-600">
                    Nivel {data?.level || 1} • {data?.achievements?.filter((a: Achievement) => a.is_unlocked).length || 0} logros obtenidos
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-blue-600 font-medium">
                    Q{creditsEarned}
                  </p>
                  <p className="text-xs text-gray-500">en créditos</p>
                </div>
              </div>
            </div>

            {/* Ranking explanation */}
            <div className="bg-gray-50 rounded-xl p-6 text-center">
              <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="text-gray-400" size={32} />
              </div>
              <h4 className="font-bold text-gray-700 mb-2">Ranking Global Próximamente</h4>
              <p className="text-gray-500 text-sm max-w-md mx-auto">
                A medida que más usuarios completen módulos y acumulen puntos, podrás ver cómo te comparas con otros miembros de SegurifAI. ¡Sigue aprendiendo para subir en el ranking!
              </p>
              <div className="mt-4 flex justify-center gap-2">
                <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">🥇 Top 1</span>
                <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">🥈 Top 2</span>
                <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">🥉 Top 3</span>
              </div>
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

