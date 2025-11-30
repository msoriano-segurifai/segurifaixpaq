import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { dispatchAPI } from '../../services/api';
import {
  MapPin, Clock, DollarSign, Navigation, Truck, AlertTriangle,
  RefreshCw, CheckCircle, Star
} from 'lucide-react';

interface AvailableJob {
  id: number;
  request_number: string;
  title: string;
  service_type: string;
  priority: string;
  location: {
    address: string;
    city: string;
    latitude: number;
    longitude: number;
  };
  distance_km: number;
  eta_minutes: number;
  payout: number;
  created_at: string;
}

export const AvailableJobs: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<AvailableJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState<number | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    getCurrentLocation();
    loadJobs();
  }, []);

  const getCurrentLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCurrentLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        });
      },
      (error) => console.error('Error obteniendo ubicacion:', error)
    );
  };

  const loadJobs = async () => {
    try {
      const response = await dispatchAPI.getAvailableJobs();
      setJobs(response.data.jobs || response.data || []);
    } catch (error) {
      console.error('Error cargando trabajos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptJob = async (jobId: number) => {
    setAccepting(jobId);
    try {
      await dispatchAPI.acceptJob(jobId);
      navigate('/tech/active');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al aceptar el trabajo');
    } finally {
      setAccepting(null);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'HIGH':
      case 'CRITICAL':
        return 'bg-red-100 text-red-700 border-red-300';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      default:
        return 'bg-green-100 text-green-700 border-green-300';
    }
  };

  const getPriorityLabel = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'HIGH': return 'Alta';
      case 'CRITICAL': return 'Urgente';
      case 'MEDIUM': return 'Media';
      default: return 'Normal';
    }
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

  return (
    <Layout variant="field-tech">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Trabajos Disponibles</h1>
            <p className="text-gray-500">{jobs.length} trabajos cerca de ti</p>
          </div>
          <button
            onClick={() => { setLoading(true); loadJobs(); }}
            className="p-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
          >
            <RefreshCw size={20} />
          </button>
        </div>

        {/* Location Status */}
        {currentLocation && (
          <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-3 rounded-xl">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            GPS Activo - Mostrando trabajos cercanos
          </div>
        )}

        {/* Jobs List */}
        {jobs.length === 0 ? (
          <div className="card text-center py-12">
            <Truck className="mx-auto mb-4 text-gray-400" size={48} />
            <h2 className="text-xl font-bold text-gray-700">No hay trabajos disponibles</h2>
            <p className="text-gray-500 mt-2">Revisa mas tarde para nuevas solicitudes</p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => (
              <div key={job.id} className="card">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{job.title}</h3>
                    <p className="text-sm text-gray-500">{job.request_number}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityBadge(job.priority)}`}>
                    {getPriorityLabel(job.priority)}
                  </span>
                </div>

                {/* Location */}
                <div className="flex items-start gap-3 mb-4 p-3 bg-gray-50 rounded-xl">
                  <MapPin className="text-red-500 flex-shrink-0 mt-1" size={18} />
                  <div>
                    <p className="font-medium">{job.location?.address}</p>
                    <p className="text-sm text-gray-500">{job.location?.city}</p>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 bg-blue-50 rounded-xl">
                    <Navigation className="mx-auto text-blue-600 mb-1" size={20} />
                    <p className="text-lg font-bold text-blue-900">{job.distance_km || '?'} km</p>
                    <p className="text-xs text-blue-600">Distancia</p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-xl">
                    <Clock className="mx-auto text-orange-600 mb-1" size={20} />
                    <p className="text-lg font-bold text-orange-900">{job.eta_minutes || '?'} min</p>
                    <p className="text-xs text-orange-600">Tiempo Est.</p>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-xl">
                    <DollarSign className="mx-auto text-green-600 mb-1" size={20} />
                    <p className="text-lg font-bold text-green-900">Q{job.payout || 0}</p>
                    <p className="text-xs text-green-600">Pago</p>
                  </div>
                </div>

                {/* Accept Button */}
                <button
                  onClick={() => handleAcceptJob(job.id)}
                  disabled={accepting === job.id}
                  className="w-full py-3 bg-red-600 text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-red-700 transition-colors disabled:opacity-50"
                >
                  {accepting === job.id ? (
                    <>
                      <RefreshCw className="animate-spin" size={20} />
                      Aceptando...
                    </>
                  ) : (
                    <>
                      <CheckCircle size={20} />
                      Aceptar Trabajo
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Tips */}
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-start gap-3">
            <Star className="text-yellow-600 flex-shrink-0" size={20} />
            <div>
              <p className="font-medium text-yellow-800">Consejo</p>
              <p className="text-sm text-yellow-700">
                Acepta trabajos rapidamente para mejorar tu calificacion y recibir mas solicitudes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
