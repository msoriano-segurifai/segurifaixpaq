import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { assistanceAPI } from '../../services/api';
import {
  MapPin, Clock, CheckCircle, Truck, AlertCircle, Eye, Phone,
  Navigation, RefreshCw, FileText, Camera, Sparkles
} from 'lucide-react';

interface Request {
  id: number;
  request_number: string;
  title: string;
  status: string;
  priority: string;
  location_address: string;
  created_at: string;
  provider?: { company_name: string; phone?: string };
  tracking_status?: string;
  eta_minutes?: number;
}

export const MyRequests: React.FC = () => {
  const [requests, setRequests] = useState<Request[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);
  const [tracking, setTracking] = useState<any>(null);

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      const response = await assistanceAPI.getMyRequests();
      setRequests(response.data.results || response.data || []);
    } catch (error) {
      console.error('Failed to load requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTracking = async (request: Request) => {
    setSelectedRequest(request);
    try {
      const response = await assistanceAPI.getLiveTracking(request.id);
      setTracking(response.data);
    } catch (error) {
      console.error('Failed to load tracking:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { color: string; label: string }> = {
      PENDING: { color: 'badge-warning', label: 'Pendiente' },
      ASSIGNED: { color: 'badge-info', label: 'Asignado' },
      EN_ROUTE: { color: 'badge-info', label: 'En Camino' },
      ARRIVED: { color: 'badge-success', label: 'Llego' },
      IN_PROGRESS: { color: 'badge-warning', label: 'En Servicio' },
      COMPLETED: { color: 'badge-success', label: 'Completado' },
      CANCELLED: { color: 'badge-danger', label: 'Cancelado' },
    };
    const config = configs[status] || { color: 'badge-info', label: status };
    return <span className={`badge ${config.color}`}>{config.label}</span>;
  };

  const activeRequests = requests.filter(r => !['COMPLETED', 'CANCELLED'].includes(r.status));
  const pastRequests = requests.filter(r => ['COMPLETED', 'CANCELLED'].includes(r.status));

  return (
    <Layout variant="user">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Mis Solicitudes</h1>
          <button onClick={loadRequests} className="btn btn-outline btn-sm flex items-center gap-2">
            <RefreshCw size={16} />
            Actualizar
          </button>
        </div>

        {/* Active Requests */}
        {activeRequests.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Solicitudes Activas
            </h2>
            <div className="space-y-4">
              {activeRequests.map((req) => (
                <div key={req.id} className="card border-l-4 border-l-blue-500">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-bold">{req.title}</p>
                      <p className="text-sm text-gray-500">{req.request_number}</p>
                    </div>
                    {getStatusBadge(req.status)}
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                    <MapPin size={14} />
                    <span>{req.location_address}</span>
                  </div>

                  {req.status === 'EN_ROUTE' && req.eta_minutes && (
                    <div className="p-3 bg-blue-50 rounded-lg mb-3">
                      <div className="flex items-center gap-2">
                        <Truck className="text-blue-600" size={20} />
                        <div>
                          <p className="font-medium text-blue-800">Tecnico en camino</p>
                          <p className="text-sm text-blue-600">Llegada estimada: {req.eta_minutes} min</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {req.provider && (
                    <div className="p-3 bg-gray-50 rounded-lg mb-3">
                      <p className="font-medium">{req.provider.company_name}</p>
                      {req.provider.phone && (
                        <a href={`tel:${req.provider.phone}`} className="text-sm text-blue-600 flex items-center gap-1">
                          <Phone size={14} />
                          {req.provider.phone}
                        </a>
                      )}
                    </div>
                  )}

                  {/* Evidence Submission Banner */}
                  <div className="p-3 bg-purple-50 rounded-lg mb-3 border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="text-purple-600" size={18} />
                      <span className="font-medium text-purple-800">Evidencia con IA</span>
                    </div>
                    <p className="text-sm text-purple-700 mb-2">
                      Sube fotos o completa el formulario. Nuestro sistema de IA revisara tu evidencia automaticamente.
                    </p>
                    <Link
                      to={`/app/requests/${req.id}/evidence`}
                      className="btn btn-sm bg-purple-600 text-white hover:bg-purple-700 flex items-center justify-center gap-2 w-full"
                    >
                      <Camera size={16} />
                      Enviar Evidencia
                    </Link>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => loadTracking(req)}
                      className="btn btn-primary btn-sm flex-1 flex items-center justify-center gap-2"
                    >
                      <Navigation size={16} />
                      Ver Tracking
                    </button>
                    <button className="btn btn-outline btn-sm flex items-center gap-2">
                      <Phone size={16} />
                      Llamar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Past Requests */}
        <div>
          <h2 className="text-lg font-semibold mb-3">Historial</h2>
          {pastRequests.length > 0 ? (
            <div className="space-y-3">
              {pastRequests.map((req) => (
                <div key={req.id} className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{req.title}</p>
                      <p className="text-sm text-gray-500">{req.request_number}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(req.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {getStatusBadge(req.status)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card text-center text-gray-500 py-8">
              <Clock className="mx-auto mb-2 opacity-50" size={32} />
              <p>No tienes solicitudes anteriores</p>
            </div>
          )}
        </div>

        {/* Tracking Modal */}
        {selectedRequest && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-end md:items-center justify-center">
            <div className="bg-white rounded-t-2xl md:rounded-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold">Tracking en Vivo</h2>
                  <button
                    onClick={() => setSelectedRequest(null)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                  >
                    ✕
                  </button>
                </div>

                <div className="mb-4">
                  <p className="font-medium">{selectedRequest.title}</p>
                  <p className="text-sm text-gray-500">{selectedRequest.request_number}</p>
                </div>

                {/* Map Placeholder */}
                <div className="h-48 bg-gray-100 rounded-xl flex items-center justify-center mb-4">
                  <div className="text-center text-gray-500">
                    <MapPin size={32} className="mx-auto mb-2 opacity-50" />
                    <p>Mapa en tiempo real</p>
                  </div>
                </div>

                {/* Timeline */}
                <div className="space-y-4">
                  {[
                    { status: 'PENDING', label: 'Solicitud recibida', done: true },
                    { status: 'ASSIGNED', label: 'Tecnico asignado', done: ['ASSIGNED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status) },
                    { status: 'EN_ROUTE', label: 'En camino', done: ['EN_ROUTE', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status) },
                    { status: 'ARRIVED', label: 'Llego a ubicacion', done: ['ARRIVED', 'IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status) },
                    { status: 'IN_PROGRESS', label: 'Servicio en progreso', done: ['IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status) },
                    { status: 'COMPLETED', label: 'Completado', done: selectedRequest.status === 'COMPLETED' },
                  ].map((step, i) => (
                    <div key={step.status} className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        step.done ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                      }`}>
                        {step.done ? <CheckCircle size={18} /> : i + 1}
                      </div>
                      <span className={step.done ? 'font-medium' : 'text-gray-500'}>{step.label}</span>
                    </div>
                  ))}
                </div>

                {tracking?.eta && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-xl">
                    <p className="text-blue-800 font-medium">
                      Tiempo estimado: {tracking.eta.eta_minutes} minutos
                    </p>
                    <p className="text-sm text-blue-600">
                      Distancia: {tracking.eta.distance_km} km
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {requests.length === 0 && !loading && (
          <div className="card text-center py-12">
            <AlertCircle className="mx-auto mb-4 text-gray-400" size={48} />
            <h3 className="text-lg font-medium text-gray-700">No tienes solicitudes</h3>
            <p className="text-gray-500 mb-4">¿Necesitas ayuda?</p>
            <Link to="/app/request" className="btn btn-primary">
              Solicitar Asistencia
            </Link>
          </div>
        )}
      </div>
    </Layout>
  );
};
