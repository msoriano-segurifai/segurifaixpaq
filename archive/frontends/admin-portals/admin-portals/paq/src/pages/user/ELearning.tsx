import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { elearningAPI } from '../../services/api';
import {
  BookOpen, Play, CheckCircle, Clock, Star, Award, Lock,
  ChevronRight, Trophy, Zap, Target
} from 'lucide-react';

interface Module {
  id: number;
  titulo: string;
  descripcion: string;
  categoria: string;
  duracion_minutos: number;
  puntos_completar: number;
  tiene_quiz: boolean;
  orden: number;
}

interface Progress {
  modulo: { id: number; titulo: string };
  estado: string;
  porcentaje_quiz: number | null;
  puntos_obtenidos: number;
}

export const ELearning: React.FC = () => {
  const [modules, setModules] = useState<Module[]>([]);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [points, setPoints] = useState<any>(null);
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);

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
      setModules(modulesRes.data.modules || modulesRes.data || []);
      setProgress(progressRes.data.progress || progressRes.data || []);
      setPoints(pointsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getModuleStatus = (moduleId: number) => {
    const p = progress.find(pr => pr.modulo?.id === moduleId);
    return p?.estado || 'NOT_STARTED';
  };

  const startModule = async (module: Module) => {
    try {
      await elearningAPI.startModule(module.id);
      setSelectedModule(module);
      await loadData();
    } catch (error) {
      console.error('Failed to start module:', error);
    }
  };

  const completeModule = async (quizScore?: number) => {
    if (!selectedModule) return;
    setCompleting(true);
    try {
      await elearningAPI.completeModule(selectedModule.id, quizScore);
      setSelectedModule(null);
      await loadData();
      alert('Modulo completado! Ganaste puntos!');
    } catch (error) {
      console.error('Failed to complete module:', error);
    } finally {
      setCompleting(false);
    }
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'SEGURIDAD': return <Target className="text-red-500" />;
      case 'VEHICULAR': return <Zap className="text-blue-500" />;
      case 'SALUD': return <Award className="text-green-500" />;
      default: return <BookOpen className="text-purple-500" />;
    }
  };

  return (
    <Layout variant="user">
      <div className="space-y-6">
        {/* Header with Points */}
        <div className="card bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Centro de Aprendizaje</h1>
              <p className="text-blue-100 mt-1">Aprende y gana puntos canjeables</p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 justify-end">
                <Star className="text-yellow-300" />
                <span className="text-3xl font-bold">{points?.puntos_totales || 0}</span>
              </div>
              <p className="text-blue-100 text-sm">{points?.nivel_display || 'Novato'}</p>
            </div>
          </div>

          {/* Level Progress */}
          {points?.next_level && (
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Progreso a {points.next_level.level}</span>
                <span>{points.next_level.progress_percentage}%</span>
              </div>
              <div className="h-2 bg-white/30 rounded-full">
                <div
                  className="h-full bg-yellow-400 rounded-full transition-all"
                  style={{ width: `${points.next_level.progress_percentage}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <BookOpen className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{progress.filter(p => p.estado === 'COMPLETADO').length}</p>
            <p className="text-sm text-gray-500">Completados</p>
          </div>
          <div className="card text-center">
            <Clock className="mx-auto text-orange-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{progress.filter(p => p.estado === 'EN_PROGRESO').length}</p>
            <p className="text-sm text-gray-500">En Progreso</p>
          </div>
          <div className="card text-center">
            <Trophy className="mx-auto text-yellow-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{points?.racha_dias || 0}</p>
            <p className="text-sm text-gray-500">Dias Racha</p>
          </div>
        </div>

        {/* Modules Grid */}
        <div>
          <h2 className="text-xl font-bold mb-4">Modulos Disponibles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {modules.map((module) => {
              const status = getModuleStatus(module.id);
              const isCompleted = status === 'COMPLETADO';
              const isInProgress = status === 'EN_PROGRESO';

              return (
                <div
                  key={module.id}
                  className={`card card-hover relative ${isCompleted ? 'border-green-500 border-2' : ''}`}
                >
                  {isCompleted && (
                    <div className="absolute -top-2 -right-2 bg-green-500 rounded-full p-1">
                      <CheckCircle size={20} className="text-white" />
                    </div>
                  )}

                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-3 bg-gray-100 rounded-xl">
                      {getCategoryIcon(module.categoria)}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold">{module.titulo}</h3>
                      <p className="text-sm text-gray-500">{module.categoria}</p>
                    </div>
                  </div>

                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {module.descripcion}
                  </p>

                  <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      {module.duracion_minutos} min
                    </span>
                    <span className="flex items-center gap-1">
                      <Star size={14} className="text-yellow-500" />
                      +{module.puntos_completar} pts
                    </span>
                  </div>

                  <button
                    onClick={() => isCompleted ? null : startModule(module)}
                    disabled={isCompleted}
                    className={`w-full btn flex items-center justify-center gap-2 ${
                      isCompleted
                        ? 'bg-green-100 text-green-700 cursor-default'
                        : isInProgress
                        ? 'btn-primary'
                        : 'btn-outline'
                    }`}
                  >
                    {isCompleted ? (
                      <>
                        <CheckCircle size={18} />
                        Completado
                      </>
                    ) : isInProgress ? (
                      <>
                        <Play size={18} />
                        Continuar
                      </>
                    ) : (
                      <>
                        <Play size={18} />
                        Comenzar
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Module Modal */}
        {selectedModule && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  {getCategoryIcon(selectedModule.categoria)}
                  <div>
                    <h2 className="text-xl font-bold">{selectedModule.titulo}</h2>
                    <p className="text-sm text-gray-500">{selectedModule.categoria}</p>
                  </div>
                </div>

                <div className="prose max-w-none mb-6">
                  <p>{selectedModule.descripcion}</p>

                  <div className="bg-blue-50 p-4 rounded-lg my-4">
                    <h4 className="font-bold text-blue-900">Contenido del Modulo:</h4>
                    <ul className="mt-2 space-y-2">
                      <li>✓ Introduccion y conceptos basicos</li>
                      <li>✓ Mejores practicas y consejos</li>
                      <li>✓ Casos de estudio</li>
                      {selectedModule.tiene_quiz && <li>✓ Quiz de evaluacion</li>}
                    </ul>
                  </div>

                  <p className="text-sm text-gray-600">
                    Tiempo estimado: {selectedModule.duracion_minutos} minutos
                  </p>
                </div>

                {selectedModule.tiene_quiz && (
                  <div className="bg-yellow-50 p-4 rounded-lg mb-6">
                    <h4 className="font-bold text-yellow-800 mb-2">Quiz de Evaluacion</h4>
                    <p className="text-sm text-yellow-700 mb-4">
                      Responde correctamente para obtener puntos extra!
                    </p>
                    <div className="space-y-3">
                      <div className="p-3 bg-white rounded-lg border">
                        <p className="font-medium mb-2">Pregunta 1: ¿Cual es la mejor practica?</p>
                        <div className="space-y-2">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="q1" className="text-blue-600" />
                            <span>Opcion A</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="q1" className="text-blue-600" />
                            <span>Opcion B (Correcta)</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={() => setSelectedModule(null)}
                    className="btn btn-outline flex-1"
                  >
                    Cerrar
                  </button>
                  <button
                    onClick={() => completeModule(selectedModule.tiene_quiz ? 100 : undefined)}
                    disabled={completing}
                    className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                  >
                    {completing ? 'Guardando...' : (
                      <>
                        <CheckCircle size={18} />
                        Completar (+{selectedModule.puntos_completar} pts)
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
