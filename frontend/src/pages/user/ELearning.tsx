import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { elearningAPI } from '../../services/api';
import {
  BookOpen, Award, Star, CheckCircle, Play, Trophy, Gift,
  Brain, Heart, Car, Shield, XCircle, Lock,
  Zap, ArrowRight, ArrowLeft, Target, TrendingUp, Sparkles, ChevronRight, ChevronLeft,
  Lightbulb, AlertTriangle, Info, Clock, HelpCircle, Bookmark
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
        <div className="bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-3xl p-8 md:p-10 text-white shadow-2xl">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-sm">
                <Sparkles className="text-yellow-300" size={32} />
              </div>
              <div>
                <h1 className="text-4xl md:text-5xl font-bold">Centro de Aprendizaje</h1>
                <p className="text-blue-100 text-lg mt-1">Aprende y gana descuentos en tus suscripciones</p>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <div className="bg-white/20 rounded-2xl p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-2">
                  <Trophy className="text-yellow-300" size={28} />
                  <TrendingUp className="text-green-300" size={20} />
                </div>
                <p className="text-3xl font-bold mb-1">{totalPoints}</p>
                <p className="text-sm text-blue-100">Puntos Totales</p>
              </div>

              <div className="bg-white/20 rounded-2xl p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-2">
                  <Gift className="text-green-300" size={28} />
                  <Sparkles className="text-yellow-300" size={20} />
                </div>
                <p className="text-3xl font-bold mb-1">Q{estimatedCredits.toFixed(2)}</p>
                <p className="text-sm text-blue-100">Créditos Ganados</p>
              </div>

              <div className="bg-white/20 rounded-2xl p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-2">
                  <CheckCircle className="text-green-300" size={28} />
                  <Target className="text-orange-300" size={20} />
                </div>
                <p className="text-3xl font-bold mb-1">{completedCount}/{modules.length}</p>
                <p className="text-sm text-blue-100">Módulos Completos</p>
              </div>

              <div className="bg-white/20 rounded-2xl p-5 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-all">
                <div className="flex items-center justify-between mb-2">
                  <Brain className="text-purple-300" size={28} />
                  <Award className="text-pink-300" size={20} />
                </div>
                <p className="text-3xl font-bold mb-1">{points?.puntos?.nivel || 'NOVATO'}</p>
                <p className="text-sm text-blue-100">Tu Nivel</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-6 bg-white/20 rounded-2xl p-5 backdrop-blur-sm border border-white/30">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-lg">Progreso General</span>
                <span className="font-bold text-xl">{progressPercentage.toFixed(0)}%</span>
              </div>
              <div className="h-4 bg-white/30 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-500 rounded-full shadow-lg"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <p className="text-sm text-blue-100 mt-2">
                {completedCount === modules.length
                  ? '🎉 ¡Felicidades! Has completado todos los módulos'
                  : `Te faltan ${modules.length - completedCount} módulo${modules.length - completedCount !== 1 ? 's' : ''} para completar`}
              </p>
            </div>

            {/* Credits Explanation */}
            <div className="mt-6 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-2xl p-5 backdrop-blur-sm border-2 border-yellow-400/50">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-yellow-400/30 rounded-xl">
                  <Gift className="text-yellow-200" size={28} />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-lg mb-2">💰 Sistema de Recompensas</h3>
                  <p className="text-blue-100 leading-relaxed">
                    Por cada <strong>20 puntos</strong> que acumules, ganas <strong>Q1.00 en créditos</strong>.
                    Estos créditos se aplican automáticamente como descuento en tu próxima suscripción.
                    ¡Aprende más para ahorrar más! 🎓
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modules Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Módulos Educativos</h2>
              <p className="text-gray-600 mt-1">Selecciona un módulo para comenzar tu aprendizaje</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                    <div className="absolute top-0 right-0 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs font-bold px-4 py-2 rounded-bl-2xl flex items-center gap-2 shadow-lg">
                      <CheckCircle size={16} />
                      COMPLETADO
                    </div>
                  )}
                  {isInProgress && !isCompleted && (
                    <div className="absolute top-0 right-0 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-bold px-4 py-2 rounded-bl-2xl flex items-center gap-2 shadow-lg">
                      <Zap size={16} />
                      EN PROGRESO
                    </div>
                  )}

                  <div className="p-6">
                    {/* Module Header */}
                    <div className="flex items-start gap-4 mb-4">
                      <div className={`p-4 rounded-2xl transition-all ${
                        isCompleted ? 'bg-green-100' :
                        isInProgress ? 'bg-blue-100' :
                        'bg-gray-100 group-hover:bg-blue-50'
                      }`}>
                        {getCategoryIcon(module.categoria)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-bold text-gray-500">MÓDULO {module.orden}</span>
                          {isLocked && (
                            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded-full">🔒 Bloqueado</span>
                          )}
                        </div>
                        <h3 className="font-bold text-xl mb-2 text-gray-900 leading-tight">{module.titulo}</h3>
                        <p className="text-sm text-gray-600 line-clamp-2">{module.descripcion}</p>
                      </div>
                    </div>

                    {/* Module Meta */}
                    <div className="flex flex-wrap gap-2 mb-5">
                      <span className={`text-xs px-3 py-1.5 rounded-full font-semibold border ${getDifficultyColor(module.dificultad)}`}>
                        {module.dificultad}
                      </span>
                      <span className="text-xs px-3 py-1.5 rounded-full bg-purple-100 text-purple-700 font-semibold border border-purple-300">
                        ⏱️ {module.duracion_minutos} min
                      </span>
                      <span className="text-xs px-3 py-1.5 rounded-full bg-blue-100 text-blue-700 font-semibold border border-blue-300 flex items-center gap-1">
                        <Star size={14} />
                        +{module.puntos_completar} pts
                      </span>
                    </div>

                    {/* Quiz Info */}
                    {module.total_preguntas > 0 && (
                      <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-xl mb-5 border-2 border-yellow-300">
                        <div className="flex items-center gap-3 mb-2">
                          <Brain className="text-orange-600" size={20} />
                          <span className="font-bold text-orange-900">{module.total_preguntas} Preguntas de Evaluación</span>
                        </div>
                        {module.puntos_quiz_perfecto ? (
                          <div className="flex items-start gap-2 text-sm">
                            <Trophy className="text-yellow-600 flex-shrink-0 mt-0.5" size={16} />
                            <p className="text-yellow-800">
                              <strong>Bonus perfecto:</strong> +{module.puntos_quiz_perfecto} pts adicionales =
                              <strong className="text-green-700"> Q{((module.puntos_completar + module.puntos_quiz_perfecto) * 0.05).toFixed(2)}</strong> en créditos
                            </p>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-sm">
                            <Gift className="text-green-600 flex-shrink-0 mt-0.5" size={16} />
                            <p className="text-yellow-800">
                              Completa el quiz y gana hasta <strong className="text-green-700">Q{(module.puntos_completar * 0.05).toFixed(2)}</strong>
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action Button */}
                    <button
                      onClick={() => !isLocked && startModule(module)}
                      disabled={loadingModule || isLocked}
                      className={`w-full btn flex items-center justify-center gap-2 font-semibold transition-all py-3 px-4 text-sm md:text-base min-h-[48px] ${
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
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          <span className="hidden sm:inline">Cargando...</span>
                        </>
                      ) : isLocked ? (
                        <>
                          <Lock size={18} className="flex-shrink-0" />
                          <span>Completar Módulo Anterior</span>
                        </>
                      ) : isCompleted ? (
                        <>
                          <CheckCircle size={20} className="flex-shrink-0" />
                          <span className="hidden sm:inline">Revisar Módulo</span>
                          <span className="sm:hidden">Revisar</span>
                          <ArrowRight size={18} className="flex-shrink-0" />
                        </>
                      ) : isInProgress ? (
                        <>
                          <Play size={20} className="flex-shrink-0" />
                          <span className="hidden sm:inline">Continuar Módulo</span>
                          <span className="sm:hidden">Continuar</span>
                          <ArrowRight size={18} className="flex-shrink-0" />
                        </>
                      ) : (
                        <>
                          <Play size={20} className="flex-shrink-0" />
                          <span className="hidden sm:inline">Comenzar Módulo</span>
                          <span className="sm:hidden">Comenzar</span>
                          <ArrowRight size={18} className="flex-shrink-0" />
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
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-white rounded-3xl max-w-5xl w-full my-8 shadow-2xl">
              {/* Modal Header */}
              <div className="p-8 border-b bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50">
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-white rounded-2xl shadow-lg">
                    {getCategoryIcon(selectedModule.categoria)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-500 bg-white px-3 py-1 rounded-full">
                        MÓDULO {selectedModule.orden}
                      </span>
                      <span className={`text-xs px-3 py-1 rounded-full font-semibold ${getDifficultyColor(selectedModule.dificultad)}`}>
                        {selectedModule.dificultad}
                      </span>
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-1">{selectedModule.titulo}</h2>
                    <p className="text-gray-600 text-lg">{selectedModule.descripcion}</p>
                  </div>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-8 max-h-[60vh] overflow-y-auto">
                {!showQuiz && !quizResult && (
                  <>
                    {/* Module Content - Carousel UI */}
                    <div className="mb-8">
                      {/* Progress Header */}
                      <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm py-3 px-4 -mx-4 mb-6 border-b shadow-sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Clock size={16} />
                            <span>~{selectedModule.duracion_minutos} min de lectura</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-1">
                              {contentSlides.map((_, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => setContentSlide(idx)}
                                  className={`w-2.5 h-2.5 rounded-full transition-all ${
                                    idx === contentSlide
                                      ? 'bg-blue-600 w-6'
                                      : idx < contentSlide
                                      ? 'bg-green-500'
                                      : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                            <span className="text-sm font-medium text-blue-600">
                              +{selectedModule.puntos_completar} pts
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Carousel Card */}
                      <div className="relative">
                        <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8 rounded-2xl border-2 border-blue-200 min-h-[400px] shadow-lg">
                          {/* Slide Counter */}
                          <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-white/80 rounded-xl shadow">
                                <BookOpen className="text-blue-600" size={24} />
                              </div>
                              <div>
                                <h3 className="text-xl font-bold text-blue-900">
                                  Tarjeta {contentSlide + 1} de {contentSlides.length}
                                </h3>
                                <p className="text-sm text-blue-700">Lee cada tarjeta para continuar</p>
                              </div>
                            </div>
                            <div className="text-sm font-bold text-blue-600 bg-white px-3 py-1 rounded-full shadow">
                              {Math.round(((contentSlide + 1) / contentSlides.length) * 100)}% completado
                            </div>
                          </div>

                          {/* Carousel Content */}
                          <div className="prose max-w-none">
                            <div className="text-gray-800 leading-relaxed text-lg space-y-4 bg-white/70 p-6 rounded-xl">
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
                  <div className="space-y-6">
                    {/* Quiz Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
                      <h3 className="text-3xl font-bold mb-3 flex items-center gap-3">
                        <Brain size={36} />
                        Evaluación de Conocimientos
                      </h3>
                      <p className="text-blue-100 text-lg mb-6">
                        Responde todas las preguntas cuidadosamente. ¡Buena suerte! 🍀
                      </p>

                      {/* Progress Indicator */}
                      <div className="bg-white/20 rounded-2xl p-6 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-lg font-semibold">Progreso del Quiz:</span>
                          <span className="text-2xl font-bold">
                            {Object.keys(quizAnswers).length} / {selectedModule.preguntas.length}
                          </span>
                        </div>
                        <div className="h-3 bg-white/30 rounded-full overflow-hidden">
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
                          className={`p-6 rounded-2xl border-2 transition-all ${
                            answered
                              ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-purple-50 shadow-lg'
                              : 'border-gray-300 bg-white hover:border-blue-300 hover:shadow-md'
                          }`}
                        >
                          <div className="flex items-start gap-4 mb-5">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-md ${
                              answered
                                ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white'
                                : 'bg-gray-200 text-gray-600'
                            }`}>
                              {index + 1}
                            </div>
                            <p className="font-semibold text-xl text-gray-900 flex-1 leading-relaxed pt-2">
                              {question.pregunta}
                            </p>
                          </div>

                          <div className="space-y-3 ml-16">
                            {['A', 'B', 'C', 'D'].map((option) => {
                              const optionText = question[`opcion_${option.toLowerCase()}`];
                              const isSelected = quizAnswers[question.id] === option;

                              return (
                                <label
                                  key={option}
                                  className={`flex items-start gap-4 p-5 rounded-xl border-2 cursor-pointer transition-all ${
                                    isSelected
                                      ? 'border-blue-600 bg-blue-50 shadow-md scale-[1.02]'
                                      : 'border-gray-200 hover:border-blue-400 hover:bg-blue-50/50 hover:shadow-sm'
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name={`question-${question.id}`}
                                    checked={isSelected}
                                    onChange={() => handleQuizAnswer(question.id, option)}
                                    className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0 cursor-pointer"
                                  />
                                  <span className={`flex-1 text-lg ${isSelected ? 'font-semibold text-blue-900' : 'text-gray-700'}`}>
                                    <strong className="mr-2">{option}.</strong> {optionText}
                                  </span>
                                  {isSelected && <CheckCircle className="text-blue-600" size={24} />}
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
                  <div className="space-y-8">
                    {/* Results Summary */}
                    <div className={`p-10 rounded-3xl text-center shadow-2xl ${
                      quizResult.quiz_perfecto
                        ? 'bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500 text-white'
                        : quizResult.porcentaje >= 70
                        ? 'bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 text-white'
                        : 'bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 text-white'
                    }`}>
                      <div className="mb-8">
                        {quizResult.quiz_perfecto ? (
                          <Trophy className="mx-auto animate-bounce" size={100} />
                        ) : quizResult.porcentaje >= 70 ? (
                          <CheckCircle className="mx-auto" size={100} />
                        ) : (
                          <Target className="mx-auto" size={100} />
                        )}
                      </div>

                      <h3 className="text-5xl font-bold mb-4">
                        {quizResult.quiz_perfecto ? '¡PERFECTO! 🎉' :
                         quizResult.porcentaje >= 70 ? '¡MUY BIEN! ✅' :
                         '¡SIGUE INTENTANDO! 📚'}
                      </h3>
                      <p className="text-3xl mb-8 opacity-95">
                        {quizResult.correctas} de {quizResult.total} respuestas correctas
                        <span className="block text-2xl mt-2">({quizResult.porcentaje}%)</span>
                      </p>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
                        <div className="bg-white/20 rounded-2xl p-8 backdrop-blur-sm border-2 border-white/30">
                          <Star className="mx-auto mb-3" size={48} />
                          <p className="text-5xl font-bold mb-2">+{quizResult.puntos_obtenidos}</p>
                          <p className="text-lg opacity-90">Puntos Ganados</p>
                        </div>
                        <div className="bg-white/20 rounded-2xl p-8 backdrop-blur-sm border-2 border-white/30">
                          <Gift className="mx-auto mb-3" size={48} />
                          <p className="text-5xl font-bold mb-2">Q{quizResult.creditos_ganados.toFixed(2)}</p>
                          <p className="text-lg opacity-90">Créditos Ganados</p>
                        </div>
                      </div>

                      {quizResult.quiz_perfecto && (
                        <div className="mt-8 bg-white/20 rounded-2xl p-6 backdrop-blur-sm border-2 border-white/30">
                          <p className="text-2xl font-bold mb-2">🏆 ¡QUIZ PERFECTO!</p>
                          <p className="text-lg opacity-90">
                            Ganaste puntos bonus por responder todo correctamente
                          </p>
                        </div>
                      )}

                      <div className="mt-8 bg-white/30 rounded-2xl p-6 backdrop-blur-sm border-2 border-white/40">
                        <p className="text-lg leading-relaxed">
                          💰 Tus créditos de <strong className="text-2xl">Q{quizResult.creditos_ganados.toFixed(2)}</strong> se
                          aplicarán automáticamente como descuento en tu próxima suscripción
                        </p>
                      </div>

                      {quizResult.logros_desbloqueados && quizResult.logros_desbloqueados.length > 0 && (
                        <div className="mt-8 bg-white/20 rounded-2xl p-6 backdrop-blur-sm border-2 border-white/30">
                          <Award className="mx-auto mb-3" size={40} />
                          <p className="font-bold text-2xl mb-4">🎖️ ¡LOGROS DESBLOQUEADOS!</p>
                          <div className="space-y-2">
                            {quizResult.logros_desbloqueados.map((logro: any, i: number) => (
                              <p key={i} className="text-lg font-semibold">
                                🏆 {logro.nombre} <span className="text-yellow-200">(+{logro.puntos_bonus} pts)</span>
                              </p>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Promo Codes Earned */}
                      {quizResult.recompensas_codigo && quizResult.recompensas_codigo.length > 0 && (
                        <div className="mt-8 bg-gradient-to-br from-green-400/30 to-emerald-400/30 rounded-2xl p-6 backdrop-blur-sm border-2 border-green-300/50">
                          <Gift className="mx-auto mb-3 text-green-200" size={48} />
                          <p className="font-bold text-2xl mb-4">🎁 ¡CÓDIGOS PROMOCIONALES GANADOS!</p>
                          <p className="text-green-100 mb-4">Usa estos códigos para obtener descuentos en tus suscripciones</p>
                          <div className="space-y-3">
                            {quizResult.recompensas_codigo.map((promo: any, i: number) => (
                              <div key={i} className="bg-white/20 rounded-xl p-4 border border-white/30">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="font-bold text-xl tracking-wider">{promo.codigo || promo.code}</p>
                                    <p className="text-sm text-green-100">{promo.descripcion || promo.description || 'Descuento especial'}</p>
                                  </div>
                                  <div className="text-right">
                                    <span className="inline-block px-3 py-1 bg-green-500/40 rounded-full text-sm font-bold">
                                      {promo.descuento || promo.discount || '10'}% OFF
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          <p className="text-sm text-green-100 mt-4">
                            💡 Tus códigos están guardados en tu perfil y sección de Recompensas
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Detailed Review */}
                    <div className="space-y-5">
                      <h4 className="font-bold text-3xl flex items-center gap-3 text-gray-900">
                        <Brain size={32} className="text-blue-600" />
                        Revisión Detallada
                      </h4>
                      <p className="text-gray-600 text-lg">Revisa tus respuestas y aprende de los errores</p>

                      {quizResult.detalles.map((detalle: any, index: number) => (
                        <div
                          key={index}
                          className={`p-6 rounded-2xl border-2 shadow-md ${
                            detalle.es_correcta
                              ? 'border-green-400 bg-gradient-to-br from-green-50 to-emerald-50'
                              : 'border-red-400 bg-gradient-to-br from-red-50 to-pink-50'
                          }`}
                        >
                          <div className="flex items-start gap-4 mb-4">
                            {detalle.es_correcta ? (
                              <CheckCircle className="text-green-600 flex-shrink-0 mt-1" size={32} />
                            ) : (
                              <XCircle className="text-red-600 flex-shrink-0 mt-1" size={32} />
                            )}
                            <div className="flex-1">
                              <p className="font-semibold text-xl mb-4 text-gray-900">{detalle.pregunta}</p>
                              <div className="space-y-3 bg-white p-5 rounded-xl border-2 border-gray-200">
                                <div className="flex items-start gap-3">
                                  <span className="font-bold text-gray-700 min-w-[140px]">Tu respuesta:</span>
                                  <span className={`font-bold text-lg ${detalle.es_correcta ? 'text-green-700' : 'text-red-700'}`}>
                                    {detalle.tu_respuesta}
                                    {detalle.es_correcta ? ' âœ“' : ' âœ—'}
                                  </span>
                                </div>
                                {!detalle.es_correcta && (
                                  <>
                                    <div className="flex items-start gap-3">
                                      <span className="font-bold text-gray-700 min-w-[140px]">Correcta:</span>
                                      <span className="font-bold text-lg text-green-700">{detalle.respuesta_correcta} âœ“</span>
                                    </div>
                                    {detalle.explicacion && (
                                      <div className="mt-4 pt-4 border-t-2 border-gray-200">
                                        <p className="font-bold text-gray-700 mb-2 flex items-center gap-2">
                                          <BookOpen size={18} />
                                          Explicación:
                                        </p>
                                        <p className="text-gray-700 italic leading-relaxed bg-blue-50 p-4 rounded-lg">
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
              <div className="p-8 border-t bg-gray-50 flex gap-4">
                {/* Close/Cancel Button */}
                <button
                  onClick={() => {
                    setSelectedModule(null);
                    setShowQuiz(false);
                    setQuizAnswers({});
                    setQuizResult(null);
                  }}
                  className="btn btn-outline text-lg font-semibold"
                >
                  {quizResult ? 'Cerrar' : 'Cancelar'}
                </button>

                {/* Content Navigation - Anterior button */}
                {!showQuiz && !quizResult && contentSlide > 0 && (
                  <button
                    onClick={() => setContentSlide(contentSlide - 1)}
                    className="btn btn-outline text-lg font-semibold flex items-center justify-center gap-2"
                  >
                    <ChevronLeft size={20} />
                    Anterior
                  </button>
                )}

                {/* Content Navigation - Next button */}
                {!showQuiz && !quizResult && contentSlide < contentSlides.length - 1 && (
                  <button
                    onClick={() => setContentSlide(contentSlide + 1)}
                    className="btn btn-primary flex-1 text-lg font-semibold flex items-center justify-center gap-3"
                  >
                    Siguiente Tarjeta
                    <ChevronRight size={20} />
                  </button>
                )}

                {/* Start Quiz Button - shown on last slide */}
                {!showQuiz && !quizResult && selectedModule.total_preguntas > 0 && contentSlide === contentSlides.length - 1 && (
                  <button
                    onClick={() => setShowQuiz(true)}
                    className="btn btn-primary flex-1 text-lg font-semibold flex items-center justify-center gap-3"
                  >
                    <Brain size={24} />
                    Comenzar Quiz ({selectedModule.total_preguntas} preguntas)
                    <ChevronRight size={20} />
                  </button>
                )}

                {/* Submit Quiz Button */}
                {showQuiz && !quizResult && (
                  <button
                    onClick={submitQuiz}
                    disabled={completing || Object.keys(quizAnswers).length < selectedModule.preguntas.length}
                    className="btn btn-primary flex-1 text-lg font-semibold flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {completing ? (
                      <>
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                        Evaluando...
                      </>
                    ) : (
                      <>
                        <CheckCircle size={24} />
                        Enviar Respuestas ({Object.keys(quizAnswers).length}/{selectedModule.preguntas.length})
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
                    className="btn btn-primary flex-1 text-lg font-semibold flex items-center justify-center gap-3"
                  >
                    <CheckCircle size={24} />
                    Volver a Módulos
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

