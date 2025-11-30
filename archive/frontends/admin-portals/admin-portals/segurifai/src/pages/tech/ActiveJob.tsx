import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { dispatchAPI } from '../../services/api';
import {
  MapPin, Navigation, Phone, CheckCircle, Play, Flag, Clock,
  User, Truck, AlertTriangle, ArrowRight, RefreshCw, DollarSign
} from 'lucide-react';

interface Job {
  job_id: number;
  request_id: number;
  request_number: string;
  title: string;
  status: string;
  location: {
    address: string;
    city: string;
    latitude: number;
    longitude: number;
  };
  customer: {
    name: string;
    phone: string;
  };
  earnings: number;
  eta_minutes: number;
  distance_km: number;
}

type JobStatus = 'ASSIGNED' | 'EN_ROUTE' | 'ARRIVED' | 'IN_PROGRESS' | 'COMPLETED';

const statusFlow: JobStatus[] = ['ASSIGNED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED'];

const statusConfig: Record<JobStatus, { label: string; action: string; icon: React.ReactNode; color: string }> = {
  ASSIGNED: { label: 'Asignado', action: 'Iniciar Viaje', icon: <Navigation size={20} />, color: 'bg-blue-600' },
  EN_ROUTE: { label: 'En Camino', action: 'Marcar Llegada', icon: <Flag size={20} />, color: 'bg-orange-500' },
  ARRIVED: { label: 'En Ubicacion', action: 'Iniciar Servicio', icon: <Play size={20} />, color: 'bg-yellow-500' },
  IN_PROGRESS: { label: 'En Servicio', action: 'Completar', icon: <CheckCircle size={20} />, color: 'bg-green-500' },
  COMPLETED: { label: 'Completado', action: '', icon: <CheckCircle size={20} />, color: 'bg-green-600' },
};

export const ActiveJob: React.FC = () => {
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [eta, setEta] = useState<{ minutes: number; distance: number } | null>(null);

  const loadActiveJob = async () => {
    try {
      const response = await dispatchAPI.getMyProfile();
      const activeJob = response.data.active_job;
      if (activeJob) {
        setJob(activeJob);
      } else {
        // No active job - redirect to dashboard
        navigate('/tech');
      }
    } catch (error) {
      console.error('Failed to load active job:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateLocation = useCallback(async () => {
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setCurrentLocation({ lat: latitude, lng: longitude });

        if (job && job.status === 'EN_ROUTE') {
          try {
            await dispatchAPI.updateLocation({
              latitude,
              longitude,
              heading: 0,
              speed: 0,
            });
          } catch (error) {
            console.error('Failed to update location:', error);
          }
        }
      },
      (error) => console.error('Geolocation error:', error),
      { enableHighAccuracy: true }
    );
  }, [job]);

  useEffect(() => {
    loadActiveJob();
  }, []);

  useEffect(() => {
    // Update location every 10 seconds when en route
    if (job?.status === 'EN_ROUTE') {
      updateLocation();
      const interval = setInterval(updateLocation, 10000);
      return () => clearInterval(interval);
    }
  }, [job?.status, updateLocation]);

  const handleStatusAction = async () => {
    if (!job) return;
    setUpdating(true);

    try {
      switch (job.status) {
        case 'ASSIGNED':
          await dispatchAPI.departForJob(job.request_id);
          break;
        case 'EN_ROUTE':
          await dispatchAPI.markArrived(job.request_id);
          break;
        case 'ARRIVED':
          await dispatchAPI.startService(job.request_id);
          break;
        case 'IN_PROGRESS':
          await dispatchAPI.completeService(job.request_id);
          navigate('/tech');
          return;
      }
      await loadActiveJob();
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al actualizar estado');
    } finally {
      setUpdating(false);
    }
  };

  const getCurrentStatusIndex = () => {
    if (!job) return 0;
    return statusFlow.indexOf(job.status as JobStatus);
  };

  const getActionButton = () => {
    if (!job || job.status === 'COMPLETED') return null;
    const config = statusConfig[job.status as JobStatus];

    return (
      <button
        onClick={handleStatusAction}
        disabled={updating}
        className={`w-full py-4 ${config.color} text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 shadow-lg hover:opacity-90 transition-all disabled:opacity-50`}
      >
        {updating ? (
          <RefreshCw className="animate-spin" size={24} />
        ) : (
          config.icon
        )}
        {updating ? 'Actualizando...' : config.action}
      </button>
    );
  };

  if (loading) {
    return (
      <Layout variant="field-tech">
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="animate-spin text-red-600" size={48} />
        </div>
      </Layout>
    );
  }

  if (!job) {
    return (
      <Layout variant="field-tech">
        <div className="text-center py-12">
          <Truck className="mx-auto mb-4 text-gray-400" size={48} />
          <h2 className="text-xl font-bold text-gray-700">No hay trabajo activo</h2>
          <p className="text-gray-500 mt-2">Revisa los trabajos disponibles</p>
          <button onClick={() => navigate('/tech/jobs')} className="btn btn-mawdy mt-4">
            Ver Trabajos Disponibles
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="field-tech">
      <div className="space-y-4 pb-24">
        {/* Status Header */}
        <div className={`card ${statusConfig[job.status as JobStatus]?.color || 'bg-gray-500'} text-white`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-80">Estado Actual</p>
              <h2 className="text-2xl font-bold">{statusConfig[job.status as JobStatus]?.label}</h2>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold">Q{job.earnings}</p>
              <p className="text-sm opacity-80">Ganancia</p>
            </div>
          </div>
        </div>

        {/* Progress Timeline */}
        <div className="card">
          <h3 className="font-bold mb-4">Progreso del Trabajo</h3>
          <div className="flex items-center justify-between">
            {statusFlow.slice(0, -1).map((status, i) => {
              const currentIndex = getCurrentStatusIndex();
              const isCompleted = i < currentIndex;
              const isCurrent = i === currentIndex;

              return (
                <React.Fragment key={status}>
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isCompleted ? 'bg-green-500 text-white' :
                      isCurrent ? 'bg-red-500 text-white animate-pulse' :
                      'bg-gray-200 text-gray-500'
                    }`}>
                      {isCompleted ? <CheckCircle size={20} /> : statusConfig[status].icon}
                    </div>
                    <span className={`text-xs mt-1 ${isCurrent ? 'font-bold' : 'text-gray-500'}`}>
                      {statusConfig[status].label.split(' ')[0]}
                    </span>
                  </div>
                  {i < statusFlow.length - 2 && (
                    <div className={`flex-1 h-1 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Map Placeholder */}
        <div className="card p-0 overflow-hidden">
          <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 relative">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <MapPin className="mx-auto text-red-500 mb-2" size={32} />
                <p className="text-sm text-gray-600">
                  {job.status === 'EN_ROUTE' ? 'Navegando...' : 'Mapa de ruta'}
                </p>
              </div>
            </div>

            {/* Distance & ETA Overlay */}
            {job.status === 'EN_ROUTE' && (
              <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white p-3 flex justify-around">
                <div className="text-center">
                  <p className="text-xl font-bold">{job.eta_minutes} min</p>
                  <p className="text-xs opacity-80">ETA</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold">{job.distance_km} km</p>
                  <p className="text-xs opacity-80">Distancia</p>
                </div>
              </div>
            )}

            {/* Current Location Indicator */}
            {currentLocation && (
              <div className="absolute top-2 right-2 bg-white rounded-lg px-2 py-1 shadow text-xs flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                GPS Activo
              </div>
            )}
          </div>
        </div>

        {/* Job Details */}
        <div className="card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="font-bold text-lg">{job.title}</p>
              <p className="text-sm text-gray-500">{job.request_number}</p>
            </div>
            <span className="badge badge-info">{job.status}</span>
          </div>

          {/* Customer Info */}
          <div className="p-4 bg-gray-50 rounded-xl mb-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                <User size={20} />
              </div>
              <div className="flex-1">
                <p className="font-medium">{job.customer?.name || 'Cliente'}</p>
                <p className="text-sm text-gray-500">Cliente</p>
              </div>
              {job.customer?.phone && (
                <a
                  href={`tel:${job.customer.phone}`}
                  className="p-3 bg-green-500 text-white rounded-xl"
                >
                  <Phone size={20} />
                </a>
              )}
            </div>
          </div>

          {/* Location */}
          <div className="flex items-start gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <MapPin className="text-red-600" size={20} />
            </div>
            <div className="flex-1">
              <p className="font-medium">{job.location?.address}</p>
              <p className="text-sm text-gray-500">{job.location?.city}</p>
            </div>
            <a
              href={`https://www.google.com/maps/dir/?api=1&destination=${job.location?.latitude},${job.location?.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline btn-sm flex items-center gap-1"
            >
              <Navigation size={14} />
              Navegar
            </a>
          </div>
        </div>

        {/* Quick Actions */}
        {job.status === 'EN_ROUTE' && (
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-3">
              <AlertTriangle className="text-blue-600" />
              <div>
                <p className="font-medium text-blue-800">Recuerda actualizar tu ubicacion</p>
                <p className="text-sm text-blue-600">El cliente puede ver tu posicion en tiempo real</p>
              </div>
            </div>
          </div>
        )}

        {/* Fixed Action Button */}
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t shadow-lg lg:left-64">
          {getActionButton()}
        </div>
      </div>
    </Layout>
  );
};
