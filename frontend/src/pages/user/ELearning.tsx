import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { elearningAPI } from '../../services/api';
import {
  BookOpen, Award, Star, CheckCircle, Play, Trophy, Gift,
  Brain, Heart, Car, Shield, XCircle, Lock,
  Zap, ArrowRight, Target, TrendingUp, Sparkles, ChevronRight, ChevronLeft,
  Lightbulb, AlertTriangle, Info, HelpCircle
} from 'lucide-react';

interface Module {
  id: number;
  titulo: string;
  descripcion: string;
  categoria: string;
  dificultad: string;
  duracion_minutos: number;
  puntos_completar: number;
  puntos_quiz_perfecto?: number;
  total_preguntas: number;
  completado: boolean;
  orden: number;
}

interface ModuleDetail extends Module {
  contenido: string;
  preguntas: QuizQuestion[];
  progreso_usuario?: {
    estado: string;
    quiz_completado: boolean;
    puntos_obtenidos: number;
    porcentaje_quiz: number;
  };
}

interface QuizQuestion {
  id: number;
  pregunta: string;
  opcion_a: string;
  opcion_b: string;
  opcion_c: string;
  opcion_d: string;
  orden: number;
}

interface Progress {
  modulo?: { id: number };
  estado: string;
  puntos_obtenidos?: number;
}

export const ELearning: React.FC = () => {
  const [modules, setModules] = useState<Module[]>([]);
  const [selectedModule, setSelectedModule] = useState<ModuleDetail | null>(null);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [points, setPoints] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadingModule, setLoadingModule] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState<{ [key: number]: string }>({});
  const [quizResult, setQuizResult] = useState<any>(null);
  const [contentSlide, setContentSlide] = useState(0);
  const [contentSlides, setContentSlides] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [modulesRes, progressRes, pointsRes] = await Promise.all([
        elearningAPI.getModules(),
        elearningAPI.getMyProgress(),
        elearningAPI.getMyPoints()
      ]);
      const modulesData = modulesRes.data.modules || modulesRes.data;
      const progressData = progressRes.data.progress || progressRes.data;
      setModules(Array.isArray(modulesData) ? modulesData : []);
      setProgress(Array.isArray(progressData) ? progressData : []);
      setPoints(pointsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
      setModules([]);
      setProgress([]);
    } finally {
      setLoading(false);
    }
  };

  const getModuleStatus = (moduleId: number) => {
    const p = progress.find(pr => pr.modulo?.id === moduleId);
    return p?.estado || 'NOT_STARTED';
  };

  const startModule = async (module: Module) => {
    setLoadingModule(true);
    try {
      const response = await elearningAPI.getModule(module.id);
      setSelectedModule(response.data);
      setShowQuiz(false);
      setQuizAnswers({});
      setQuizResult(null);
      setContentSlide(0);

      // Parse content into carousel slides
      const content = response.data.contenido || '';
      const slides = parseContentIntoSlides(content);
      setContentSlides(slides);

      try {
        await elearningAPI.startModule(module.id);
      } catch (err) {
        console.log('Module already started');
      }
    } catch (error) {
      console.error('Failed to load module:', error);
      alert('Error al cargar el módulo');
    } finally {
      setLoadingModule(false);
    }
  };

  // Parse module content into carousel slides
  const parseContentIntoSlides = (content: string): string[] => {
    if (!content) return [''];

    // Split by double line breaks or headings
    const sections = content.split(/\n\n+/);
    const slides: string[] = [];
    let currentSlide = '';

    for (const section of sections) {
      // If section is a heading, start a new slide
      if (section.startsWith('#') || section.startsWith('##')) {
        if (currentSlide.trim()) {
          slides.push(currentSlide.trim());
        }
        currentSlide = section;
      }
      // If current slide would be too long, start new slide
      else if (currentSlide.length + section.length > 800) {
        if (currentSlide.trim()) {
          slides.push(currentSlide.trim());
        }
        currentSlide = section;
      } else {
        currentSlide += '\n\n' + section;
      }
    }

    if (currentSlide.trim()) {
      slides.push(currentSlide.trim());
    }

    // Ensure at least 2 slides for carousel effect
    if (slides.length === 0) return [content];
    if (slides.length === 1) {
      const mid = Math.floor(slides[0].length / 2);
      const breakPoint = slides[0].indexOf('\n\n', mid);
      if (breakPoint > 0) {
        return [slides[0].slice(0, breakPoint).trim(), slides[0].slice(breakPoint).trim()];
      }
    }

    return slides;
  };

  const handleQuizAnswer = (questionId: number, answer: string) => {
    setQuizAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const submitQuiz = async () => {
    if (!selectedModule) return;

    const allAnswered = selectedModule.preguntas.every(q => quizAnswers[q.id]);
    if (!allAnswered) {
      alert('Por favor responde todas las preguntas antes de enviar.');
      return;
    }

    setCompleting(true);
    try {
      const answers = selectedModule.preguntas.map(q => ({
        pregunta_id: q.id,
        respuesta: quizAnswers[q.id]
      }));

      const response = await elearningAPI.submitQuiz(selectedModule.id, { respuestas: answers });

      if (response.data.success && response.data.resultado) {
        setQuizResult(response.data.resultado);
        await loadData();
      } else if (response.data.resultado) {
        // Backend returned resultado without success flag (backward compatibility)
        setQuizResult(response.data.resultado);
        await loadData();
      } else {
        alert(response.data.error || 'Error al procesar el quiz. Intenta de nuevo.');
      }
    } catch (error: any) {
      console.error('Failed to submit quiz:', error);
      alert(error.response?.data?.error || 'Error al enviar el quiz');
    } finally {
      setCompleting(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    const cat = category?.toUpperCase();
    if (cat?.includes('SEGURIDAD') || cat?.includes('VIAL')) return <Car className="text-red-500" size={28} />;
    if (cat?.includes('SALUD')) return <Heart className="text-pink-500" size={28} />;
    if (cat?.includes('PREVENCION')) return <Shield className="text-blue-500" size={28} />;
    if (cat?.includes('AHORRO') || cat?.includes('FINANZAS')) return <Gift className="text-green-500" size={28} />;
    if (cat?.includes('SEGURIFAI')) return <Car className="text-orange-500" size={28} />;
    return <BookOpen className="text-gray-500" size={28} />;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toUpperCase()) {
      case 'PRINCIPIANTE': return 'bg-green-100 text-green-700 border-green-300';
      case 'INTERMEDIO': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'AVANZADO': return 'bg-red-100 text-red-700 border-red-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-lg text-gray-600 font-medium">Cargando módulos educativos...</p>
          </div>
        </div>
      </Layout>
    );
  }

  const completedCount = progress.filter(p => p.estado === 'COMPLETADO').length;
  const totalPoints = points?.puntos?.puntos_totales || 0;
  const estimatedCredits = totalPoints * 0.05;
  const progressPercentage = modules.length > 0 ? (completedCount / modules.length) * 100 : 0;

  return (
    <Layout variant="user">
      <div className="space-y-8">
        {/* Enhanced Header with Progress */}
        <div className="bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-10 text-white shadow-2xl">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-start sm:items-center gap-3 mb-3">
              <div className="p-2 sm:p-3 bg-white/20 rounded-xl sm:rounded-2xl backdrop-blur-sm flex-shrink-0">
                <Sparkles className="text-yellow-300" size={24} />
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold leading-tight">Centro de Aprendizaje</h1>
                <p className="text-blue-100 text-sm sm:text-base md:text-lg mt-1">Aprende y gana descuentos en tus suscripciones</p>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4 mt-4 sm:mt-8">
              <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-1 sm:mb-2">
                  <Trophy className="text-yellow-300" size={20} />
                  <TrendingUp className="text-green-300 hidden sm:block" size={16} />
                </div>
                <p className="text-xl sm:text-2xl md:text-3xl font-bold mb-0.5 sm:mb-1">{totalPoints}</p>
                <p className="text-xs sm:text-sm text-blue-100">Puntos</p>
              </div>

              <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-1 sm:mb-2">
                  <Gift className="text-green-300" size={20} />
                  <Sparkles className="text-yellow-300 hidden sm:block" size={16} />
                </div>
                <p className="text-xl sm:text-2xl md:text-3xl font-bold mb-0.5 sm:mb-1">Q{estimatedCredits.toFixed(2)}</p>
                <p className="text-xs sm:text-sm text-blue-100">Créditos</p>
              </div>

              <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-1 sm:mb-2">
                  <CheckCircle className="text-green-300" size={20} />
                  <Target className="text-orange-300 hidden sm:block" size={16} />
                </div>
                <p className="text-xl sm:text-2xl md:text-3xl font-bold mb-0.5 sm:mb-1">{completedCount}/{modules.length}</p>
                <p className="text-xs sm:text-sm text-blue-100">Módulos</p>
              </div>

              <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-1 sm:mb-2">
                  <Brain className="text-purple-300" size={20} />
                  <Award className="text-pink-300 hidden sm:block" size={16} />
                </div>
                <p className="text-lg sm:text-2xl md:text-3xl font-bold mb-0.5 sm:mb-1 truncate">{points?.puntos?.nivel || 'NOVATO'}</p>
                <p className="text-xs sm:text-sm text-blue-100">Nivel</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-4 sm:mt-6 bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-5 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-2 sm:mb-3">
                <span className="font-semibold text-sm sm:text-lg">Progreso General</span>
                <span className="font-bold text-lg sm:text-xl">{progressPercentage.toFixed(0)}%</span>
              </div>
              <div className="h-3 sm:h-4 bg-white/30 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-500 rounded-full shadow-lg"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <p className="text-xs sm:text-sm text-blue-100 mt-2">
                {completedCount === modules.length
                  ? '🎉 ¡Has completado todos los módulos!'
                  : `Te faltan ${modules.length - completedCount} módulo${modules.length - completedCount !== 1 ? 's' : ''}`}
              </p>
            </div>

            {/* Credits Explanation */}
            <div className="mt-4 sm:mt-6 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-xl sm:rounded-2xl p-3 sm:p-5 backdrop-blur-sm border-2 border-yellow-400/50">
              <div className="flex items-start gap-3 sm:gap-4">
                <div className="p-2 sm:p-3 bg-yellow-400/30 rounded-lg sm:rounded-xl flex-shrink-0">
                  <Gift className="text-yellow-200" size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-sm sm:text-lg mb-1 sm:mb-2">💰 Sistema de Recompensas</h3>
                  <p className="text-xs sm:text-sm text-blue-100 leading-relaxed">
                    Por cada <strong>20 puntos</strong> ganas <strong>Q1.00</strong>.
                    <span className="hidden sm:inline"> Estos créditos se aplican automáticamente como descuento en tu próxima suscripción.</span>
                    <span className="sm:hidden"> ¡Se aplican automáticamente!</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modules Section */}
        <div>
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <div>
              <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900">Módulos Educativos</h2>
              <p className="text-sm sm:text-base text-gray-600 mt-1">Selecciona un módulo para comenzar</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {modules.map((module, index) => {
              const status = getModuleStatus(module.id);
              const isCompleted = status === 'COMPLETADO';
              const isInProgress = status === 'EN_PROGRESO';
              const isLocked = index > 0 && getModuleStatus(modules[index - 1].id) !== 'COMPLETADO';

              return (
                <div
                  key={module.id}
                  className={`group relative card overflow-hidden transition-all duration-300 hover:shadow-2xl ${
                    isCompleted ? 'border-2 border-green-400 bg-gradient-to-br from-green-50 to-emerald-50' :
                    isInProgress ? 'border-2 border-blue-400 bg-gradient-to-br from-blue-50 to-purple-50' :
                    'hover:border-blue-300'
                  } ${isLocked ? 'opacity-60' : ''}`}
                >
                  {/* Status Badge */}
                  {isCompleted && (
                    <div className="absolute top-0 right-0 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-[10px] sm:text-xs font-bold px-2 sm:px-4 py-1.5 sm:py-2 rounded-bl-xl sm:rounded-bl-2xl flex items-center gap-1 sm:gap-2 shadow-lg">
                      <CheckCircle size={12} className="sm:w-4 sm:h-4" />
                      <span className="hidden sm:inline">COMPLETADO</span>
                      <span className="sm:hidden">✓</span>
                    </div>
                  )}
                  {isInProgress && !isCompleted && (
                    <div className="absolute top-0 right-0 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-[10px] sm:text-xs font-bold px-2 sm:px-4 py-1.5 sm:py-2 rounded-bl-xl sm:rounded-bl-2xl flex items-center gap-1 sm:gap-2 shadow-lg">
                      <Zap size={12} className="sm:w-4 sm:h-4" />
                      <span className="hidden sm:inline">EN PROGRESO</span>
                      <span className="sm:hidden">...</span>
                    </div>
                  )}

                  <div className="p-4 sm:p-6">
                    {/* Module Header */}
                    <div className="flex items-start gap-3 sm:gap-4 mb-3 sm:mb-4">
                      <div className={`p-3 sm:p-4 rounded-xl sm:rounded-2xl transition-all flex-shrink-0 ${
                        isCompleted ? 'bg-green-100' :
                        isInProgress ? 'bg-blue-100' :
                        'bg-gray-100 group-hover:bg-blue-50'
                      }`}>
                        {getCategoryIcon(module.categoria)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 sm:mb-2">
                          <span className="text-[10px] sm:text-xs font-bold text-gray-500">MÓDULO {module.orden}</span>
                          {isLocked && (
                            <span className="text-[10px] sm:text-xs bg-gray-200 text-gray-600 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">🔒</span>
                          )}
                        </div>
                        <h3 className="font-bold text-base sm:text-lg md:text-xl mb-1 sm:mb-2 text-gray-900 leading-tight">{module.titulo}</h3>
                        <p className="text-xs sm:text-sm text-gray-600 line-clamp-2">{module.descripcion}</p>
                      </div>
                    </div>

                    {/* Module Meta */}
                    <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3 sm:mb-5">
                      <span className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1 sm:py-1.5 rounded-full font-semibold border ${getDifficultyColor(module.dificultad)}`}>
                        {module.dificultad}
                      </span>
                      <span className="text-[10px] sm:text-xs px-2 sm:px-3 py-1 sm:py-1.5 rounded-full bg-purple-100 text-purple-700 font-semibold border border-purple-300">
                        ~{module.duracion_minutos} min de lectura
                      </span>
                    </div>

                    {/* Quiz Info */}
                    {module.total_preguntas > 0 && (
                      <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-3 sm:p-4 rounded-lg sm:rounded-xl mb-3 sm:mb-5 border-2 border-yellow-300">
                        <div className="flex items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
                          <Brain className="text-orange-600 flex-shrink-0" size={18} />
                          <span className="font-bold text-orange-900 text-sm sm:text-base">{module.total_preguntas} Preguntas</span>
                        </div>
                        {module.puntos_quiz_perfecto ? (
                          <div className="flex items-start gap-2 text-xs sm:text-sm">
                            <Trophy className="text-yellow-600 flex-shrink-0 mt-0.5" size={14} />
                            <p className="text-yellow-800">
                              <span className="hidden sm:inline"><strong>Bonus perfecto:</strong> +{module.puntos_quiz_perfecto} pts = </span>
                              <strong className="text-green-700">Q{((module.puntos_completar + module.puntos_quiz_perfecto) * 0.05).toFixed(2)}</strong>
                              <span className="sm:hidden"> máx</span>
                            </p>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-xs sm:text-sm">
                            <Gift className="text-green-600 flex-shrink-0 mt-0.5" size={14} />
                            <p className="text-yellow-800">
                              <span className="hidden sm:inline">Gana hasta </span><strong className="text-green-700">Q{(module.puntos_completar * 0.05).toFixed(2)}</strong>
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action Button */}
                    <button
                      onClick={() => !isLocked && startModule(module)}
                      disabled={loadingModule || isLocked}
                      className={`w-full btn flex items-center justify-center gap-1.5 sm:gap-2 font-semibold transition-all py-2.5 sm:py-3 px-3 sm:px-4 text-xs sm:text-sm md:text-base min-h-[44px] sm:min-h-[48px] rounded-xl ${
                        isCompleted
                          ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600'
                          : isInProgress
                          ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600'
                          : isLocked
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'btn-primary'
                      }`}
                    >
                      {loadingModule ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-white"></div>
                          <span className="hidden sm:inline">Cargando...</span>
                        </>
                      ) : isLocked ? (
                        <>
                          <Lock size={16} className="flex-shrink-0" />
                          <span className="hidden sm:inline">Completar Anterior</span>
                          <span className="sm:hidden">Bloqueado</span>
                        </>
                      ) : isCompleted ? (
                        <>
                          <CheckCircle size={16} className="sm:w-5 sm:h-5 flex-shrink-0" />
                          <span className="hidden sm:inline">Revisar Módulo</span>
                          <span className="sm:hidden">Revisar</span>
                          <ArrowRight size={16} className="flex-shrink-0" />
                        </>
                      ) : isInProgress ? (
                        <>
                          <Play size={16} className="sm:w-5 sm:h-5 flex-shrink-0" />
                          <span className="hidden sm:inline">Continuar Módulo</span>
                          <span className="sm:hidden">Continuar</span>
                          <ArrowRight size={16} className="flex-shrink-0" />
                        </>
                      ) : (
                        <>
                          <Play size={16} className="sm:w-5 sm:h-5 flex-shrink-0" />
                          <span className="hidden sm:inline">Comenzar Módulo</span>
                          <span className="sm:hidden">Comenzar</span>
                          <ArrowRight size={16} className="flex-shrink-0" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Module Detail Modal */}
        {selectedModule && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center sm:p-4 overflow-hidden">
            <div className="bg-white rounded-t-2xl sm:rounded-3xl w-full sm:max-w-5xl max-h-[95vh] sm:max-h-[90vh] sm:my-8 shadow-2xl flex flex-col">
              {/* Modal Header */}
              <div className="p-4 sm:p-6 md:p-8 border-b bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 flex-shrink-0">
                <div className="flex items-start sm:items-center gap-3 sm:gap-4">
                  <div className="p-3 sm:p-4 bg-white rounded-xl sm:rounded-2xl shadow-lg flex-shrink-0">
                    {getCategoryIcon(selectedModule.categoria)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                      <span className="text-[10px] sm:text-xs font-bold text-gray-500 bg-white px-2 sm:px-3 py-0.5 sm:py-1 rounded-full">
                        MÓDULO {selectedModule.orden}
                      </span>
                      <span className={`text-[10px] sm:text-xs px-2 sm:px-3 py-0.5 sm:py-1 rounded-full font-semibold ${getDifficultyColor(selectedModule.dificultad)}`}>
                        {selectedModule.dificultad}
                      </span>
                    </div>
                    <h2 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-gray-900 mb-0.5 sm:mb-1 leading-tight">{selectedModule.titulo}</h2>
                    <p className="text-gray-600 text-xs sm:text-sm md:text-base lg:text-lg line-clamp-2 sm:line-clamp-none">{selectedModule.descripcion}</p>
                  </div>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-4 sm:p-6 md:p-8 flex-1 overflow-y-auto">
                {!showQuiz && !quizResult && (
                  <>
                    {/* Module Content - Carousel UI */}
                    <div className="mb-4 sm:mb-8">
                      {/* Progress Header */}
                      <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm py-2 sm:py-3 px-3 sm:px-4 -mx-4 sm:-mx-4 mb-4 sm:mb-6 border-b shadow-sm">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-xs sm:text-sm font-medium text-gray-600 whitespace-nowrap">
                            Tarjeta {contentSlide + 1} de {contentSlides.length}
                          </span>
                          <div className="flex-1 max-w-[200px] sm:max-w-xs">
                            <div className="h-2 sm:h-2.5 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300 rounded-full"
                                style={{ width: `${((contentSlide + 1) / contentSlides.length) * 100}%` }}
                              />
                            </div>
                          </div>
                          <span className="text-xs sm:text-sm font-bold text-blue-600 whitespace-nowrap">
                            {Math.round(((contentSlide + 1) / contentSlides.length) * 100)}%
                          </span>
                        </div>
                      </div>

                      {/* Carousel Card */}
                      <div className="relative">
                        <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-4 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl border-2 border-blue-200 min-h-[250px] sm:min-h-[350px] md:min-h-[400px] shadow-lg">
                          {/* Slide Counter */}
                          <div className="flex items-start sm:items-center justify-between mb-4 sm:mb-6 gap-2">
                            <div className="flex items-center gap-2 sm:gap-3">
                              <div className="p-1.5 sm:p-2 bg-white/80 rounded-lg sm:rounded-xl shadow flex-shrink-0">
                                <BookOpen className="text-blue-600" size={18} />
                              </div>
                              <div>
                                <h3 className="text-sm sm:text-lg md:text-xl font-bold text-blue-900">
                                  Tarjeta {contentSlide + 1}/{contentSlides.length}
                                </h3>
                                <p className="text-xs sm:text-sm text-blue-700 hidden sm:block">Lee cada tarjeta para continuar</p>
                              </div>
                            </div>
                            <div className="text-[10px] sm:text-xs md:text-sm font-bold text-blue-600 bg-white px-2 sm:px-3 py-0.5 sm:py-1 rounded-full shadow whitespace-nowrap">
                              {Math.round(((contentSlide + 1) / contentSlides.length) * 100)}%
                            </div>
                          </div>

                          {/* Carousel Content */}
                          <div className="prose max-w-none">
                            <div className="text-gray-800 leading-relaxed text-sm sm:text-base md:text-lg space-y-3 sm:space-y-4 bg-white/70 p-3 sm:p-4 md:p-6 rounded-lg sm:rounded-xl">
                              {(contentSlides[contentSlide] || '').split('\n\n').map((paragraph, index) => {
                            // TIP/NOTA Box
                            if (paragraph.toLowerCase().startsWith('tip:') || paragraph.toLowerCase().startsWith('💡')) {
                              const content = paragraph.replace(/^(tip:|💡)/i, '').trim();
                              return (
                                <div key={index} className="bg-gradient-to-r from-yellow-50 to-amber-50 border-l-4 border-yellow-500 p-5 rounded-r-xl my-4 shadow-sm">
                                  <div className="flex items-start gap-3">
                                    <Lightbulb className="text-yellow-600 flex-shrink-0 mt-0.5" size={22} />
                                    <div>
                                      <p className="font-bold text-yellow-800 mb-1">💡 Consejo</p>
                                      <p className="text-yellow-900" dangerouslySetInnerHTML={{ __html: content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </div>
                                  </div>
                                </div>
                              );
                            }
                            // WARNING Box
                            if (paragraph.toLowerCase().startsWith('advertencia:') || paragraph.toLowerCase().startsWith('⚠️')) {
                              const content = paragraph.replace(/^(advertencia:|⚠️)/i, '').trim();
                              return (
                                <div key={index} className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 p-5 rounded-r-xl my-4 shadow-sm">
                                  <div className="flex items-start gap-3">
                                    <AlertTriangle className="text-red-600 flex-shrink-0 mt-0.5" size={22} />
                                    <div>
                                      <p className="font-bold text-red-800 mb-1">⚠️ Advertencia</p>
                                      <p className="text-red-900" dangerouslySetInnerHTML={{ __html: content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </div>
                                  </div>
                                </div>
                              );
                            }
                            // INFO Box
                            if (paragraph.toLowerCase().startsWith('nota:') || paragraph.toLowerCase().startsWith('ℹ️')) {
                              const content = paragraph.replace(/^(nota:|ℹ️)/i, '').trim();
                              return (
                                <div key={index} className="bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-blue-500 p-5 rounded-r-xl my-4 shadow-sm">
                                  <div className="flex items-start gap-3">
                                    <Info className="text-blue-600 flex-shrink-0 mt-0.5" size={22} />
                                    <div>
                                      <p className="font-bold text-blue-800 mb-1">ℹ️ Información</p>
                                      <p className="text-blue-900" dangerouslySetInnerHTML={{ __html: content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </div>
                                  </div>
                                </div>
                              );
                            }
                            // FAQ/Question Box
                            if (paragraph.toLowerCase().startsWith('pregunta:') || paragraph.toLowerCase().startsWith('❓')) {
                              const content = paragraph.replace(/^(pregunta:|❓)/i, '').trim();
                              return (
                                <div key={index} className="bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-purple-500 p-5 rounded-r-xl my-4 shadow-sm">
                                  <div className="flex items-start gap-3">
                                    <HelpCircle className="text-purple-600 flex-shrink-0 mt-0.5" size={22} />
                                    <div>
                                      <p className="font-bold text-purple-800 mb-1">❓ Pregunta Frecuente</p>
                                      <p className="text-purple-900" dangerouslySetInnerHTML={{ __html: content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </div>
                                  </div>
                                </div>
                              );
                            }
                            // Check if it's a heading
                            if (paragraph.startsWith('# ')) {
                              return (
                                <div key={index} className="mt-8 mb-4">
                                  <h1 className="text-3xl font-bold text-blue-900 flex items-center gap-3">
                                    <div className="w-2 h-10 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                                    {paragraph.replace('# ', '')}
                                  </h1>
                                </div>
                              );
                            } else if (paragraph.startsWith('## ')) {
                              return (
                                <div key={index} className="mt-6 mb-3">
                                  <h2 className="text-2xl font-bold text-blue-800 flex items-center gap-2">
                                    <div className="w-1.5 h-8 bg-blue-400 rounded-full"></div>
                                    {paragraph.replace('## ', '')}
                                  </h2>
                                </div>
                              );
                            } else if (paragraph.startsWith('### ')) {
                              return (
                                <h3 key={index} className="text-xl font-bold text-blue-700 mt-4 mb-2 flex items-center gap-2">
                                  <div className="w-1 h-6 bg-blue-300 rounded-full"></div>
                                  {paragraph.replace('### ', '')}
                                </h3>
                              );
                            }
                            // Check if it's a numbered list
                            else if (/^\d+\.\s/.test(paragraph) || paragraph.includes('\n1.')) {
                              const items = paragraph.split('\n').filter(line => /^\d+\.\s/.test(line.trim()));
                              return (
                                <ol key={index} className="space-y-3 ml-2 my-4">
                                  {items.map((item, i) => {
                                    const cleanItem = item.replace(/^\d+\.\s*/, '');
                                    const processedItem = cleanItem
                                      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>')
                                      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
                                    return (
                                      <li key={i} className="flex items-start gap-4 bg-white/50 p-4 rounded-xl border border-gray-100">
                                        <span className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 text-white rounded-full flex items-center justify-center font-bold text-sm shadow-md">
                                          {i + 1}
                                        </span>
                                        <span className="text-gray-700 pt-1" dangerouslySetInnerHTML={{ __html: processedItem }} />
                                      </li>
                                    );
                                  })}
                                </ol>
                              );
                            }
                            // Check if it's a bullet list
                            else if (paragraph.includes('\n- ') || paragraph.startsWith('- ')) {
                              const items = paragraph.split('\n').filter(line => line.trim().startsWith('- '));
                              return (
                                <ul key={index} className="space-y-2 ml-2 my-4">
                                  {items.map((item, i) => {
                                    const cleanItem = item.replace('- ', '');
                                    const processedItem = cleanItem
                                      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>')
                                      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
                                      .replace(/`(.*?)`/g, '<code class="bg-gray-200 px-2 py-1 rounded text-sm">$1</code>');
                                    return (
                                      <li key={i} className="flex items-start gap-3 text-gray-700">
                                        <CheckCircle className="text-green-500 flex-shrink-0 mt-1" size={18} />
                                        <span dangerouslySetInnerHTML={{ __html: processedItem }} />
                                      </li>
                                    );
                                  })}
                                </ul>
                              );
                            }
                            // Regular paragraph
                            else if (paragraph.trim()) {
                              // Process inline markdown (bold, italic, code)
                              const processedText = paragraph
                                .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-gray-900">$1</strong>')
                                .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
                                .replace(/`(.*?)`/g, '<code class="bg-gray-200 px-2 py-1 rounded text-sm font-mono text-purple-700">$1</code>');
                              return <p key={index} className="text-gray-700 text-base leading-relaxed" dangerouslySetInnerHTML={{ __html: processedText }} />;
                            }
                            return null;
                              }).filter(Boolean)}
                            </div>
                          </div>

                          {/* Progress indicator */}
                          <div className="flex items-center justify-center mt-6 pt-4 border-t border-blue-200">
                            <p className="text-sm text-blue-700 font-medium">
                              {contentSlide < contentSlides.length - 1
                                ? `Tarjeta ${contentSlide + 1} de ${contentSlides.length} - Usa los botones de abajo para navegar`
                                : '¡Has completado la lectura! Continúa al quiz'}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Quiz Preview - Only show on last slide */}
                      {contentSlide === contentSlides.length - 1 && selectedModule.total_preguntas > 0 && (
                        <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 p-8 rounded-2xl border-2 border-purple-300 shadow-lg">
                          <div className="flex items-center gap-4 mb-6">
                            <div className="p-4 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg">
                              <Brain className="text-white" size={36} />
                            </div>
                            <div>
                              <h4 className="font-bold text-purple-900 text-2xl">Evaluación de Conocimientos</h4>
                              <p className="text-purple-700 text-lg">Pon a prueba lo que has aprendido</p>
                            </div>
                          </div>

                          <div className="grid md:grid-cols-3 gap-4 mt-6">
                            <div className="bg-white p-5 rounded-xl shadow-md border-2 border-purple-200">
                              <div className="flex items-center gap-2 text-purple-600 mb-2">
                                <Star size={24} />
                                <span className="font-bold text-2xl">+{selectedModule.puntos_completar}</span>
                              </div>
                              <p className="text-sm text-gray-600">Puntos base</p>
                            </div>
                            {selectedModule.puntos_quiz_perfecto && (
                              <div className="bg-white p-5 rounded-xl shadow-md border-2 border-yellow-300">
                                <div className="flex items-center gap-2 text-yellow-600 mb-2">
                                  <Trophy size={24} />
                                  <span className="font-bold text-2xl">+{selectedModule.puntos_quiz_perfecto}</span>
                                </div>
                                <p className="text-sm text-gray-600">Bonus perfecto</p>
                              </div>
                            )}
                            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-5 rounded-xl shadow-md border-2 border-green-300">
                              <div className="flex items-center gap-2 text-green-700 mb-2">
                                <Gift size={24} />
                                <span className="font-bold text-2xl">
                                  Q{((selectedModule.puntos_completar + (selectedModule.puntos_quiz_perfecto || 0)) * 0.05).toFixed(2)}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 font-semibold">Créditos máximos</p>
                            </div>
                          </div>

                          <div className="mt-6 bg-white/80 p-5 rounded-xl border border-purple-200">
                            <p className="text-gray-700 leading-relaxed">
                              <strong className="text-purple-900">💡 Recuerda:</strong> Los créditos se calculan automáticamente
                              (Q1 por cada 20 puntos) y se aplicarán como descuento en tu próxima suscripción.
                              ¡Obtén 100% de respuestas correctas para el bonus máximo!
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* Quiz Section */}
                {showQuiz && !quizResult && (
                  <div className="space-y-4 sm:space-y-6">
                    {/* Quiz Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl shadow-xl">
                      <h3 className="text-lg sm:text-2xl md:text-3xl font-bold mb-2 sm:mb-3 flex items-center gap-2 sm:gap-3">
                        <Brain size={24} className="flex-shrink-0" />
                        <span className="hidden sm:inline">Evaluación de Conocimientos</span>
                        <span className="sm:hidden">Quiz</span>
                      </h3>
                      <p className="text-blue-100 text-sm sm:text-base md:text-lg mb-4 sm:mb-6">
                        <span className="hidden sm:inline">Responde todas las preguntas cuidadosamente. ¡Buena suerte!</span>
                        <span className="sm:hidden">¡Buena suerte!</span>
                      </p>

                      {/* Progress Indicator */}
                      <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-2 sm:mb-3">
                          <span className="text-sm sm:text-base md:text-lg font-semibold">Progreso:</span>
                          <span className="text-lg sm:text-xl md:text-2xl font-bold">
                            {Object.keys(quizAnswers).length}/{selectedModule.preguntas.length}
                          </span>
                        </div>
                        <div className="h-2 sm:h-3 bg-white/30 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-yellow-400 to-orange-400 transition-all duration-300 rounded-full"
                            style={{ width: `${(Object.keys(quizAnswers).length / selectedModule.preguntas.length) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Questions */}
                    {selectedModule.preguntas.map((question, index) => {
                      const answered = quizAnswers[question.id];
                      return (
                        <div
                          key={question.id}
                          className={`p-3 sm:p-4 md:p-6 rounded-xl sm:rounded-2xl border-2 transition-all ${
                            answered
                              ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-purple-50 shadow-lg'
                              : 'border-gray-300 bg-white hover:border-blue-300 hover:shadow-md'
                          }`}
                        >
                          <div className="flex items-start gap-2 sm:gap-3 md:gap-4 mb-3 sm:mb-4 md:mb-5">
                            <div className={`w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center font-bold text-sm sm:text-base md:text-xl flex-shrink-0 shadow-md ${
                              answered
                                ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white'
                                : 'bg-gray-200 text-gray-600'
                            }`}>
                              {index + 1}
                            </div>
                            <p className="font-semibold text-sm sm:text-base md:text-lg lg:text-xl text-gray-900 flex-1 leading-relaxed pt-0.5 sm:pt-1 md:pt-2">
                              {question.pregunta}
                            </p>
                          </div>

                          <div className="space-y-2 sm:space-y-3 ml-0 sm:ml-10 md:ml-14 lg:ml-16">
                            {['A', 'B', 'C', 'D'].map((option) => {
                              const optionText = question[`opcion_${option.toLowerCase()}`];
                              const isSelected = quizAnswers[question.id] === option;

                              return (
                                <label
                                  key={option}
                                  className={`flex items-start gap-2 sm:gap-3 md:gap-4 p-3 sm:p-4 md:p-5 rounded-lg sm:rounded-xl border-2 cursor-pointer transition-all min-h-[48px] ${
                                    isSelected
                                      ? 'border-blue-600 bg-blue-50 shadow-md'
                                      : 'border-gray-200 hover:border-blue-400 hover:bg-blue-50/50 hover:shadow-sm active:bg-blue-100'
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name={`question-${question.id}`}
                                    checked={isSelected}
                                    onChange={() => handleQuizAnswer(question.id, option)}
                                    className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 mt-0.5 flex-shrink-0 cursor-pointer"
                                  />
                                  <span className={`flex-1 text-sm sm:text-base md:text-lg ${isSelected ? 'font-semibold text-blue-900' : 'text-gray-700'}`}>
                                    <strong className="mr-1 sm:mr-2">{option}.</strong> {optionText}
                                  </span>
                                  {isSelected && <CheckCircle className="text-blue-600 flex-shrink-0" size={20} />}
                                </label>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Quiz Results */}
                {quizResult && (
                  <div className="space-y-4 sm:space-y-6 md:space-y-8">
                    {/* Results Summary */}
                    <div className={`p-4 sm:p-6 md:p-10 rounded-xl sm:rounded-2xl md:rounded-3xl text-center shadow-2xl ${
                      quizResult.quiz_perfecto
                        ? 'bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500 text-white'
                        : quizResult.porcentaje >= 70
                        ? 'bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 text-white'
                        : 'bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 text-white'
                    }`}>
                      <div className="mb-4 sm:mb-6 md:mb-8">
                        {quizResult.quiz_perfecto ? (
                          <Trophy className="mx-auto animate-bounce" size={60} />
                        ) : quizResult.porcentaje >= 70 ? (
                          <CheckCircle className="mx-auto" size={60} />
                        ) : (
                          <Target className="mx-auto" size={60} />
                        )}
                      </div>

                      <h3 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-2 sm:mb-4">
                        {quizResult.quiz_perfecto ? '¡PERFECTO!' :
                         quizResult.porcentaje >= 70 ? '¡MUY BIEN!' :
                         '¡SIGUE INTENTANDO!'}
                      </h3>
                      <p className="text-lg sm:text-xl md:text-2xl lg:text-3xl mb-4 sm:mb-6 md:mb-8 opacity-95">
                        {quizResult.correctas}/{quizResult.total} correctas
                        <span className="block text-base sm:text-lg md:text-xl lg:text-2xl mt-1 sm:mt-2">({quizResult.porcentaje}%)</span>
                      </p>

                      <div className="grid grid-cols-2 gap-3 sm:gap-4 md:gap-6 max-w-3xl mx-auto">
                        <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 lg:p-8 backdrop-blur-sm border-2 border-white/30">
                          <Star className="mx-auto mb-2 sm:mb-3" size={28} />
                          <p className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-1 sm:mb-2">+{quizResult.puntos_obtenidos}</p>
                          <p className="text-xs sm:text-sm md:text-base lg:text-lg opacity-90">Puntos</p>
                        </div>
                        <div className="bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 lg:p-8 backdrop-blur-sm border-2 border-white/30">
                          <Gift className="mx-auto mb-2 sm:mb-3" size={28} />
                          <p className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-1 sm:mb-2">Q{quizResult.creditos_ganados.toFixed(2)}</p>
                          <p className="text-xs sm:text-sm md:text-base lg:text-lg opacity-90">Créditos</p>
                        </div>
                      </div>

                      {quizResult.quiz_perfecto && (
                        <div className="mt-4 sm:mt-6 md:mt-8 bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 backdrop-blur-sm border-2 border-white/30">
                          <p className="text-base sm:text-lg md:text-2xl font-bold mb-1 sm:mb-2">🏆 ¡QUIZ PERFECTO!</p>
                          <p className="text-xs sm:text-sm md:text-base lg:text-lg opacity-90">
                            Ganaste puntos bonus
                          </p>
                        </div>
                      )}

                      <div className="mt-4 sm:mt-6 md:mt-8 bg-white/30 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 backdrop-blur-sm border-2 border-white/40">
                        <p className="text-xs sm:text-sm md:text-base lg:text-lg leading-relaxed">
                          💰 <strong className="text-base sm:text-lg md:text-xl lg:text-2xl">Q{quizResult.creditos_ganados.toFixed(2)}</strong>
                          <span className="hidden sm:inline"> se aplicarán como descuento en tu próxima suscripción</span>
                          <span className="sm:hidden"> en créditos</span>
                        </p>
                      </div>

                      {quizResult.logros_desbloqueados && quizResult.logros_desbloqueados.length > 0 && (
                        <div className="mt-4 sm:mt-6 md:mt-8 bg-white/20 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 backdrop-blur-sm border-2 border-white/30">
                          <Award className="mx-auto mb-2 sm:mb-3" size={28} />
                          <p className="font-bold text-base sm:text-lg md:text-2xl mb-2 sm:mb-4">🎖️ ¡LOGROS!</p>
                          <div className="space-y-1 sm:space-y-2">
                            {quizResult.logros_desbloqueados.map((logro: any, i: number) => (
                              <p key={i} className="text-xs sm:text-sm md:text-base lg:text-lg font-semibold">
                                🏆 {logro.nombre} <span className="text-yellow-200">(+{logro.puntos_bonus})</span>
                              </p>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Promo Codes Earned */}
                      {quizResult.recompensas_codigo && quizResult.recompensas_codigo.length > 0 && (
                        <div className="mt-4 sm:mt-6 md:mt-8 bg-gradient-to-br from-green-400/30 to-emerald-400/30 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 backdrop-blur-sm border-2 border-green-300/50">
                          <Gift className="mx-auto mb-2 sm:mb-3 text-green-200" size={32} />
                          <p className="font-bold text-base sm:text-lg md:text-2xl mb-2 sm:mb-4">🎁 ¡CÓDIGOS GANADOS!</p>
                          <p className="text-green-100 text-xs sm:text-sm mb-2 sm:mb-4 hidden sm:block">Usa estos códigos para descuentos</p>
                          <div className="space-y-2 sm:space-y-3">
                            {quizResult.recompensas_codigo.map((promo: any, i: number) => (
                              <div key={i} className="bg-white/20 rounded-lg sm:rounded-xl p-2 sm:p-3 md:p-4 border border-white/30">
                                <div className="flex items-center justify-between gap-2">
                                  <div className="min-w-0">
                                    <p className="font-bold text-sm sm:text-base md:text-xl tracking-wider truncate">{promo.codigo || promo.code}</p>
                                    <p className="text-[10px] sm:text-xs md:text-sm text-green-100 truncate">{promo.descripcion || promo.description || 'Descuento'}</p>
                                  </div>
                                  <div className="flex-shrink-0">
                                    <span className="inline-block px-2 sm:px-3 py-0.5 sm:py-1 bg-green-500/40 rounded-full text-[10px] sm:text-xs md:text-sm font-bold">
                                      {promo.descuento || promo.discount || '10'}%
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          <p className="text-[10px] sm:text-xs md:text-sm text-green-100 mt-2 sm:mt-4">
                            💡 Guardados en tu perfil
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Detailed Review */}
                    <div className="space-y-3 sm:space-y-4 md:space-y-5">
                      <h4 className="font-bold text-lg sm:text-xl md:text-2xl lg:text-3xl flex items-center gap-2 sm:gap-3 text-gray-900">
                        <Brain size={20} className="text-blue-600 flex-shrink-0 sm:w-6 sm:h-6 md:w-8 md:h-8" />
                        <span className="hidden sm:inline">Revisión Detallada</span>
                        <span className="sm:hidden">Revisión</span>
                      </h4>
                      <p className="text-gray-600 text-xs sm:text-sm md:text-base lg:text-lg">Revisa tus respuestas</p>

                      {quizResult.detalles.map((detalle: any, index: number) => (
                        <div
                          key={index}
                          className={`p-3 sm:p-4 md:p-6 rounded-xl sm:rounded-2xl border-2 shadow-md ${
                            detalle.es_correcta
                              ? 'border-green-400 bg-gradient-to-br from-green-50 to-emerald-50'
                              : 'border-red-400 bg-gradient-to-br from-red-50 to-pink-50'
                          }`}
                        >
                          <div className="flex items-start gap-2 sm:gap-3 md:gap-4 mb-2 sm:mb-3 md:mb-4">
                            {detalle.es_correcta ? (
                              <CheckCircle className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
                            ) : (
                              <XCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-sm sm:text-base md:text-lg lg:text-xl mb-2 sm:mb-3 md:mb-4 text-gray-900">{detalle.pregunta}</p>
                              <div className="space-y-2 sm:space-y-3 bg-white p-2 sm:p-3 md:p-4 lg:p-5 rounded-lg sm:rounded-xl border-2 border-gray-200">
                                <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-3">
                                  <span className="font-bold text-gray-700 text-xs sm:text-sm md:text-base sm:min-w-[100px] md:min-w-[140px]">Tu respuesta:</span>
                                  <span className={`font-bold text-sm sm:text-base md:text-lg ${detalle.es_correcta ? 'text-green-700' : 'text-red-700'}`}>
                                    {detalle.tu_respuesta}
                                    {detalle.es_correcta ? ' ✓' : ' ✗'}
                                  </span>
                                </div>
                                {!detalle.es_correcta && (
                                  <>
                                    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-3">
                                      <span className="font-bold text-gray-700 text-xs sm:text-sm md:text-base sm:min-w-[100px] md:min-w-[140px]">Correcta:</span>
                                      <span className="font-bold text-sm sm:text-base md:text-lg text-green-700">{detalle.respuesta_correcta} ✓</span>
                                    </div>
                                    {detalle.explicacion && (
                                      <div className="mt-2 sm:mt-3 md:mt-4 pt-2 sm:pt-3 md:pt-4 border-t-2 border-gray-200">
                                        <p className="font-bold text-gray-700 mb-1 sm:mb-2 text-xs sm:text-sm md:text-base flex items-center gap-1 sm:gap-2">
                                          <BookOpen size={14} className="flex-shrink-0" />
                                          Explicación:
                                        </p>
                                        <p className="text-gray-700 italic leading-relaxed bg-blue-50 p-2 sm:p-3 md:p-4 rounded-lg text-xs sm:text-sm md:text-base">
                                          {detalle.explicacion}
                                        </p>
                                      </div>
                                    )}
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-3 sm:p-4 md:p-6 border-t bg-gray-50 flex flex-col sm:flex-row gap-2 sm:gap-3 flex-shrink-0">
                {/* Close/Cancel Button */}
                <button
                  onClick={() => {
                    setSelectedModule(null);
                    setShowQuiz(false);
                    setQuizAnswers({});
                    setQuizResult(null);
                  }}
                  className="btn btn-outline text-sm sm:text-base font-semibold py-2.5 sm:py-3 min-h-[44px] order-last sm:order-first"
                >
                  {quizResult ? 'Cerrar' : 'Cancelar'}
                </button>

                {/* Content Navigation - Anterior button */}
                {!showQuiz && !quizResult && contentSlide > 0 && (
                  <button
                    onClick={() => setContentSlide(contentSlide - 1)}
                    className="btn btn-outline text-sm sm:text-base font-semibold flex items-center justify-center gap-1.5 sm:gap-2 py-2.5 sm:py-3 min-h-[44px]"
                  >
                    <ChevronLeft size={18} />
                    <span className="hidden sm:inline">Anterior</span>
                    <span className="sm:hidden">Atrás</span>
                  </button>
                )}

                {/* Content Navigation - Next button */}
                {!showQuiz && !quizResult && contentSlide < contentSlides.length - 1 && (
                  <button
                    onClick={() => setContentSlide(contentSlide + 1)}
                    className="btn btn-primary flex-1 text-sm sm:text-base md:text-lg font-semibold flex items-center justify-center gap-2 sm:gap-3 py-2.5 sm:py-3 min-h-[44px]"
                  >
                    <span className="hidden sm:inline">Siguiente Tarjeta</span>
                    <span className="sm:hidden">Siguiente</span>
                    <ChevronRight size={18} />
                  </button>
                )}

                {/* Start Quiz Button - shown on last slide */}
                {!showQuiz && !quizResult && selectedModule.total_preguntas > 0 && contentSlide === contentSlides.length - 1 && (
                  <button
                    onClick={() => setShowQuiz(true)}
                    className="btn btn-primary flex-1 text-sm sm:text-base md:text-lg font-semibold flex items-center justify-center gap-2 sm:gap-3 py-2.5 sm:py-3 min-h-[44px]"
                  >
                    <Brain size={20} />
                    <span className="hidden sm:inline">Comenzar Quiz ({selectedModule.total_preguntas})</span>
                    <span className="sm:hidden">Quiz ({selectedModule.total_preguntas})</span>
                    <ChevronRight size={18} />
                  </button>
                )}

                {/* Submit Quiz Button */}
                {showQuiz && !quizResult && (
                  <button
                    onClick={submitQuiz}
                    disabled={completing || Object.keys(quizAnswers).length < selectedModule.preguntas.length}
                    className="btn btn-primary flex-1 text-sm sm:text-base md:text-lg font-semibold flex items-center justify-center gap-2 sm:gap-3 py-2.5 sm:py-3 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {completing ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span className="hidden sm:inline">Evaluando...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle size={20} />
                        <span className="hidden sm:inline">Enviar ({Object.keys(quizAnswers).length}/{selectedModule.preguntas.length})</span>
                        <span className="sm:hidden">Enviar ({Object.keys(quizAnswers).length}/{selectedModule.preguntas.length})</span>
                      </>
                    )}
                  </button>
                )}

                {/* Quiz Result - Back to Modules */}
                {quizResult && (
                  <button
                    onClick={() => {
                      setSelectedModule(null);
                      setShowQuiz(false);
                      setQuizAnswers({});
                      setQuizResult(null);
                    }}
                    className="btn btn-primary flex-1 text-sm sm:text-base md:text-lg font-semibold flex items-center justify-center gap-2 sm:gap-3 py-2.5 sm:py-3 min-h-[44px]"
                  >
                    <CheckCircle size={20} />
                    <span className="hidden sm:inline">Volver a Módulos</span>
                    <span className="sm:hidden">Volver</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

