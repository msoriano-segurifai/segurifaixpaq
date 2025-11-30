import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { TrackingMap } from '../../components/TrackingMap';
import { assistanceAPI } from '../../services/api';
import {
  MapPin, Clock, CheckCircle, Truck, AlertCircle, Eye, Phone,
  Navigation, RefreshCw, FileText, User, Star
} from 'lucide-react';

interface Request {
  id: number;
  request_number: string;
  title: string;
  status: string;
  priority: string;
  location_address: string;
  location_latitude?: number;
  location_longitude?: number;
  created_at: string;
  provider?: { company_name: string; phone?: string };
  assigned_tech_name?: string;
  assigned_tech_phone?: string;
  estimated_arrival_time?: string;
  tracking_status?: string;
  eta_minutes?: number;
}

export const MyRequests: React.FC = () => {
  const [requests, setRequests] = useState<Request[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);
  const [tracking, setTracking] = useState<any>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);

  useEffect(() => {
    loadRequests();
  }, []);

  // Auto-refresh tracking every 10 seconds when modal is open
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (selectedRequest) {
      // Initial load
      loadTracking(selectedRequest);

      // Set up auto-refresh for active requests
      if (!['COMPLETED', 'CANCELLED'].includes(selectedRequest.status)) {
        interval = setInterval(() => {
          loadTracking(selectedRequest, true); // Silent refresh
        }, 10000); // Every 10 seconds
      }
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedRequest]);

  const loadRequests = async () => {
    try {
      const response = await assistanceAPI.getMyRequests();
      const data = response.data.results || response.data;
      // Ensure we always set an array, even if API returns unexpected format
      setRequests(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load requests:', error);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const loadTracking = async (request: Request, silent = false) => {
    if (!silent) {
      setSelectedRequest(request);
      setTrackingLoading(true);
    }
    try {
      const response = await assistanceAPI.getLiveTracking(request.id);
      setTracking(response.data);
    } catch (error) {
      console.error('Failed to load tracking:', error);
    } finally {
      if (!silent) setTrackingLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { color: string; label: string }> = {
      PENDING: { color: 'badge-warning', label: 'Pendiente' },
      ASSIGNED: { color: 'badge-info', label: 'En Camino' },
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

                  {(req.status === 'ASSIGNED' || req.status === 'EN_ROUTE') && (
                    <div className="p-3 bg-blue-50 rounded-lg mb-3">
                      <div className="flex items-center gap-2">
                        <Truck className="text-blue-600" size={20} />
                        <div>
                          <p className="font-medium text-blue-800">
                            {req.status === 'ASSIGNED' ? 'En Camino' : 'Tecnico en camino'}
                          </p>
                          {req.estimated_arrival_time && (
                            <p className="text-sm text-blue-600">
                              Llegada estimada: {new Date(req.estimated_arrival_time).toLocaleTimeString('es-GT', { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          )}
                          {req.eta_minutes && (
                            <p className="text-sm text-blue-600">Llegada estimada: {req.eta_minutes} min</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {(req.assigned_tech_name || req.provider) && (
                    <div className="p-3 bg-gray-50 rounded-lg mb-3">
                      <p className="font-medium">
                        {req.assigned_tech_name || req.provider?.company_name}
                      </p>
                      {(req.assigned_tech_phone || req.provider?.phone) && (
                        <a
                          href={`tel:${req.assigned_tech_phone || req.provider?.phone}`}
                          className="text-sm text-blue-600 flex items-center gap-1"
                        >
                          <Phone size={14} />
                          {req.assigned_tech_phone || req.provider?.phone}
                        </a>
                      )}
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={() => loadTracking(req)}
                      className="btn btn-primary btn-sm flex-1 flex items-center justify-center gap-2"
                    >
                      <Navigation size={16} />
                      Ver Tracking
                    </button>
                    {(req.assigned_tech_phone || req.provider?.phone) && (
                      <a
                        href={`tel:${req.assigned_tech_phone || req.provider?.phone}`}
                        className="btn btn-outline btn-sm flex items-center gap-2"
                      >
                        <Phone size={16} />
                        Llamar
                      </a>
                    )}
                    {req.status === 'PENDING' && (
                      <button
                        onClick={async () => {
                          if (confirm('¿Estás seguro que deseas cancelar esta solicitud?')) {
                            try {
                              await assistanceAPI.cancelRequest(req.id);
                              alert('Solicitud cancelada exitosamente');
                              await loadRequests();
                            } catch (error: any) {
                              alert(error.response?.data?.error || 'Error al cancelar solicitud');
                            }
                          }
                        }}
                        className="btn btn-outline btn-sm text-red-600 border-red-300 hover:bg-red-50 flex items-center gap-2"
                      >
                        <AlertCircle size={16} />
                        Cancelar
                      </button>
                    )}
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
            <div className="bg-white rounded-t-2xl md:rounded-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold">Tracking en Vivo</h2>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  </div>
                  <button
                    onClick={() => {
                      setSelectedRequest(null);
                      setTracking(null);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                  >
                    ✕
                  </button>
                </div>

                <div className="mb-4">
                  <p className="font-medium">{selectedRequest.title}</p>
                  <p className="text-sm text-gray-500">{selectedRequest.request_number}</p>
                </div>

                {trackingLoading && !tracking ? (
                  <div className="flex items-center justify-center py-12">
                    <RefreshCw className="animate-spin text-blue-600" size={32} />
                  </div>
                ) : (
                  <>
                    {/* Provider Info - Uber Eats Driver Style */}
                    {(tracking?.provider || tracking?.location?.provider) && (
                      <div className="card mb-4 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {/* Tech Avatar/Photo */}
                            <div className="relative">
                              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
                                {tracking.provider.driver_name?.[0] || 'M'}
                              </div>
                              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                                <CheckCircle size={12} className="text-white" />
                              </div>
                            </div>
                            <div>
                              <p className="font-bold text-lg">{tracking.provider.driver_name || 'Tecnico Mawdy'}</p>
                              <p className="text-sm text-gray-600">{tracking.provider.company_name}</p>
                              <div className="flex items-center gap-1 mt-1">
                                <Star size={14} className="text-yellow-500 fill-yellow-500" />
                                <span className="text-sm font-medium">4.9</span>
                                <span className="text-xs text-gray-500">(128 servicios)</span>
                              </div>
                            </div>
                          </div>
                          {tracking.provider.phone && (
                            <a
                              href={`tel:${tracking.provider.phone}`}
                              className="btn bg-green-600 hover:bg-green-700 text-white btn-sm flex items-center gap-1 shadow-lg"
                            >
                              <Phone size={14} />
                              Llamar
                            </a>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Live Location */}
                    {tracking?.location?.provider && (
                      <div className="card mb-4 border-2 border-blue-200">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <Navigation size={24} className="text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <p className="font-bold text-blue-900 mb-1">Ubicacion Actual del Tecnico</p>
                            <div className="space-y-1 text-sm text-gray-600">
                              <p>
                                Latitud: {tracking.location.provider.latitude?.toFixed(6) || 'N/A'}
                              </p>
                              <p>
                                Longitud: {tracking.location.provider.longitude?.toFixed(6) || 'N/A'}
                              </p>
                              {tracking.location.provider.updated_at && (
                                <p className="text-xs text-gray-500 mt-2">
                                  Actualizado: {new Date(tracking.location.provider.updated_at).toLocaleTimeString()}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* ETA Info - Always show when tracking tech is en route */}
                    {(tracking?.eta?.minutes || tracking?.eta?.eta_minutes || tracking?.location?.distance_km) ? (
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="card text-center bg-blue-50">
                          <Clock className="mx-auto mb-2 text-blue-600" size={24} />
                          <p className="text-2xl font-bold text-blue-900">
                            {tracking.eta?.minutes || tracking.eta?.eta_minutes || '--'}
                          </p>
                          <p className="text-sm text-blue-700">minutos</p>
                        </div>
                        <div className="card text-center bg-purple-50">
                          <MapPin className="mx-auto mb-2 text-purple-600" size={24} />
                          <p className="text-2xl font-bold text-purple-900">
                            {tracking.location?.distance_km?.toFixed(1) || tracking.eta?.distance_km?.toFixed(1) || '--'}
                          </p>
                          <p className="text-sm text-purple-700">kilometros</p>
                        </div>
                      </div>
                    ) : selectedRequest.status === 'ASSIGNED' || selectedRequest.status === 'EN_ROUTE' ? (
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="card text-center bg-blue-50">
                          <Clock className="mx-auto mb-2 text-blue-600" size={24} />
                          <div className="animate-pulse">
                            <div className="h-8 bg-blue-200 rounded w-16 mx-auto mb-1"></div>
                          </div>
                          <p className="text-sm text-blue-700">Calculando...</p>
                        </div>
                        <div className="card text-center bg-purple-50">
                          <MapPin className="mx-auto mb-2 text-purple-600" size={24} />
                          <div className="animate-pulse">
                            <div className="h-8 bg-purple-200 rounded w-16 mx-auto mb-1"></div>
                          </div>
                          <p className="text-sm text-purple-700">Calculando...</p>
                        </div>
                      </div>
                    ) : null}

                    {/* Live Tracking Map */}
                    {tracking?.location?.provider && selectedRequest.location_latitude && selectedRequest.location_longitude ? (
                      <div className="mb-4">
                        <TrackingMap
                          userLocation={{
                            lat: parseFloat(selectedRequest.location_latitude.toString()),
                            lng: parseFloat(selectedRequest.location_longitude.toString())
                          }}
                          techLocation={{
                            lat: tracking.location.provider.latitude || 14.6349,
                            lng: tracking.location.provider.longitude || -90.5069
                          }}
                          techName={tracking.provider?.name || 'Tecnico'}
                          eta={tracking.eta?.minutes}
                          autoRefresh={!['COMPLETED', 'CANCELLED'].includes(selectedRequest.status)}
                          onRefresh={() => loadTracking(selectedRequest, true)}
                        />
                      </div>
                    ) : (
                      <div className="h-64 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center mb-4 border-2 border-dashed border-blue-300">
                        <div className="text-center text-blue-700">
                          <div className="relative">
                            <MapPin size={48} className="mx-auto mb-3 animate-bounce" />
                            {(selectedRequest.status === 'ASSIGNED' || selectedRequest.status === 'EN_ROUTE') && (
                              <div className="absolute -top-1 -right-4 w-4 h-4 bg-green-500 rounded-full animate-ping"></div>
                            )}
                          </div>
                          <p className="font-bold text-lg">Vista de Mapa</p>
                          {selectedRequest.status === 'PENDING' ? (
                            <p className="text-sm text-blue-600 mt-1">Buscando tecnico cercano...</p>
                          ) : (
                            <p className="text-sm text-blue-600 mt-1">Obteniendo ubicacion del tecnico...</p>
                          )}
                          <button
                            onClick={() => loadTracking(selectedRequest, true)}
                            className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto"
                          >
                            <RefreshCw size={14} />
                            Actualizar
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Timeline - Uber Eats Style Progress */}
                    <div className="card bg-white">
                      <h3 className="font-bold mb-6 text-lg">Estado del Servicio</h3>
                      <div className="relative">
                        {/* Progress Line */}
                        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                        <div className="space-y-6">
                          {[
                            { status: 'PENDING', label: 'Solicitud recibida', icon: <CheckCircle size={18} />, desc: 'Tu solicitud fue recibida exitosamente' },
                            { status: 'ASSIGNED', label: 'Tecnico asignado', icon: <User size={18} />, desc: 'Un tecnico fue asignado a tu solicitud' },
                            { status: 'EN_ROUTE', label: 'Tecnico en camino', icon: <Truck size={18} />, desc: 'El tecnico esta de camino a tu ubicacion' },
                            { status: 'ARRIVED', label: 'Tecnico llego', icon: <MapPin size={18} />, desc: 'El tecnico llego a tu ubicacion' },
                            { status: 'IN_PROGRESS', label: 'Servicio en progreso', icon: <RefreshCw size={18} />, desc: 'El tecnico esta trabajando en tu solicitud' },
                            { status: 'COMPLETED', label: 'Servicio completado', icon: <CheckCircle size={18} />, desc: 'Tu servicio fue completado exitosamente' },
                          ].map((step, i) => {
                            const done = i === 0 ||
                              (step.status === 'ASSIGNED' && ['ASSIGNED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status)) ||
                              (step.status === 'EN_ROUTE' && ['EN_ROUTE', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status)) ||
                              (step.status === 'ARRIVED' && ['ARRIVED', 'IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status)) ||
                              (step.status === 'IN_PROGRESS' && ['IN_PROGRESS', 'COMPLETED'].includes(selectedRequest.status)) ||
                              (step.status === 'COMPLETED' && selectedRequest.status === 'COMPLETED');

                            const current = selectedRequest.status === step.status;

                            return (
                              <div key={step.status} className="relative flex items-start gap-4">
                                {/* Icon Circle */}
                                <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                                  current ? 'bg-blue-600 text-white ring-4 ring-blue-100 shadow-lg' :
                                  done ? 'bg-green-500 text-white shadow-md' :
                                  'bg-gray-200 text-gray-400'
                                }`}>
                                  {current && step.status !== 'COMPLETED' ? (
                                    <RefreshCw className="animate-spin" size={18} />
                                  ) : (
                                    step.icon
                                  )}
                                </div>

                                {/* Content */}
                                <div className="flex-1 pb-6">
                                  <div className="flex items-center justify-between mb-1">
                                    <h4 className={`font-bold ${
                                      current ? 'text-blue-900 text-lg' :
                                      done ? 'text-gray-900' :
                                      'text-gray-500'
                                    }`}>
                                      {step.label}
                                    </h4>
                                    {current && (
                                      <span className="px-3 py-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-xs font-bold rounded-full shadow-md">
                                        EN PROGRESO
                                      </span>
                                    )}
                                    {done && !current && (
                                      <CheckCircle size={16} className="text-green-500" />
                                    )}
                                  </div>
                                  <p className={`text-sm ${
                                    current ? 'text-blue-700' :
                                    done ? 'text-gray-600' :
                                    'text-gray-400'
                                  }`}>
                                    {step.desc}
                                  </p>
                                  {/* Show ETA for EN_ROUTE status */}
                                  {current && step.status === 'EN_ROUTE' && (tracking?.eta?.minutes || tracking?.eta?.eta_minutes) && (
                                    <div className="mt-2 flex items-center gap-2 text-blue-700">
                                      <Clock size={16} />
                                      <span className="text-sm font-medium">
                                        Llegada estimada en {tracking.eta?.minutes || tracking.eta?.eta_minutes} minutos
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>

                    {/* Auto-refresh indicator */}
                    {!['COMPLETED', 'CANCELLED'].includes(selectedRequest.status) && (
                      <div className="mt-4 text-center text-xs text-gray-500">
                        <RefreshCw className="inline mr-1 animate-spin" size={12} />
                        Actualizandose automaticamente cada 10 segundos
                      </div>
                    )}
                  </>
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
