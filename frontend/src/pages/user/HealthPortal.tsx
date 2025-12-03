import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { assistanceAPI, userAPI } from '../../services/api';
import {
  Heart, Calendar, FileText, Pill, Clock, CheckCircle, AlertCircle,
  Phone, Video, MapPin, ChevronRight, RefreshCw, User, Activity,
  Stethoscope, TestTube, Truck, ClipboardList, History, Filter,
  Download, Eye, Star, Building2, Loader2
} from 'lucide-react';

interface HealthRecord {
  id: number;
  type: 'appointment' | 'test_result' | 'medication' | 'consultation';
  title: string;
  date: string;
  status: 'completed' | 'pending' | 'scheduled' | 'cancelled';
  provider?: string;
  details?: string;
  result_url?: string;
}

interface AssistanceHistory {
  id: number;
  request_number: string;
  title: string;
  status: string;
  created_at: string;
  service_type: string;
  provider_name?: string;
}

interface MedicalAppointment {
  id: number;
  specialty: string;
  doctor_name: string;
  date: string;
  time: string;
  location: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  notes?: string;
}

export const HealthPortal: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'history' | 'appointments' | 'results' | 'medications'>('history');
  const [loading, setLoading] = useState(true);
  const [assistanceHistory, setAssistanceHistory] = useState<AssistanceHistory[]>([]);
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [appointments, setAppointments] = useState<MedicalAppointment[]>([]);
  const [filter, setFilter] = useState<'all' | 'health' | 'vehicle' | 'home'>('all');

  // Booking modal state
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [bookingType, setBookingType] = useState<'general' | 'specialist' | 'video'>('general');
  const [bookingForm, setBookingForm] = useState({
    specialty: '',
    preferred_date: '',
    preferred_time: '',
    reason: '',
    notes: ''
  });
  const [bookingLoading, setBookingLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load assistance history
      const historyResponse = await assistanceAPI.getMyRequests();
      const requests = historyResponse.data.results || historyResponse.data || [];
      setAssistanceHistory(Array.isArray(requests) ? requests : []);

      // Simulated health records (in production, this would come from SegurifAI API)
      setHealthRecords([
        {
          id: 1,
          type: 'consultation',
          title: 'Consulta Medicina General',
          date: '2024-11-15',
          status: 'completed',
          provider: 'Dr. Maria Garcia',
          details: 'Chequeo general - Todo en orden'
        },
        {
          id: 2,
          type: 'test_result',
          title: 'Examen de Sangre Completo',
          date: '2024-11-10',
          status: 'completed',
          provider: 'Laboratorio Central',
          result_url: '#'
        },
        {
          id: 3,
          type: 'medication',
          title: 'Medicamento Recetado',
          date: '2024-11-05',
          status: 'completed',
          details: 'Paracetamol 500mg - Entregado'
        }
      ]);

      setAppointments([
        {
          id: 1,
          specialty: 'Medicina General',
          doctor_name: 'Dr. Carlos Rodriguez',
          date: '2024-12-05',
          time: '10:00 AM',
          location: 'Clinica SegurifAI - Zona 10',
          status: 'scheduled'
        }
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookAppointment = async () => {
    if (!bookingForm.specialty || !bookingForm.preferred_date || !bookingForm.reason) {
      alert('Por favor completa los campos requeridos');
      return;
    }

    setBookingLoading(true);
    try {
      // In production, this would call the SegurifAI booking API
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Add to local appointments
      const newAppointment: MedicalAppointment = {
        id: Date.now(),
        specialty: bookingForm.specialty,
        doctor_name: 'Por asignar',
        date: bookingForm.preferred_date,
        time: bookingForm.preferred_time || 'Por confirmar',
        location: 'Por confirmar',
        status: 'scheduled',
        notes: bookingForm.reason
      };

      setAppointments([newAppointment, ...appointments]);
      setShowBookingModal(false);
      setBookingForm({ specialty: '', preferred_date: '', preferred_time: '', reason: '', notes: '' });
      alert('Cita solicitada exitosamente. Te contactaremos para confirmar.');
    } catch (error) {
      alert('Error al solicitar cita. Intenta de nuevo.');
    } finally {
      setBookingLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { color: string; label: string }> = {
      completed: { color: 'bg-green-100 text-green-700', label: 'Completado' },
      COMPLETED: { color: 'bg-green-100 text-green-700', label: 'Completado' },
      pending: { color: 'bg-yellow-100 text-yellow-700', label: 'Pendiente' },
      PENDING: { color: 'bg-yellow-100 text-yellow-700', label: 'Pendiente' },
      scheduled: { color: 'bg-blue-100 text-blue-700', label: 'Programado' },
      ASSIGNED: { color: 'bg-blue-100 text-blue-700', label: 'En Proceso' },
      EN_ROUTE: { color: 'bg-blue-100 text-blue-700', label: 'En Camino' },
      ARRIVED: { color: 'bg-purple-100 text-purple-700', label: 'Llegado' },
      IN_PROGRESS: { color: 'bg-orange-100 text-orange-700', label: 'En Servicio' },
      cancelled: { color: 'bg-red-100 text-red-700', label: 'Cancelado' },
      CANCELLED: { color: 'bg-red-100 text-red-700', label: 'Cancelado' },
    };
    const config = configs[status] || { color: 'bg-gray-100 text-gray-700', label: status };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>{config.label}</span>;
  };

  const getServiceIcon = (serviceType: string) => {
    if (serviceType?.toLowerCase().includes('salud') || serviceType?.toLowerCase().includes('health')) {
      return <Heart className="text-pink-500" size={18} />;
    }
    if (serviceType?.toLowerCase().includes('vial') || serviceType?.toLowerCase().includes('road')) {
      return <Activity className="text-blue-500" size={18} />;
    }
    return <ClipboardList className="text-gray-500" size={18} />;
  };

  const filteredHistory = assistanceHistory.filter(item => {
    if (filter === 'all') return true;
    if (filter === 'health') return item.service_type?.toLowerCase().includes('health') || item.service_type?.toLowerCase().includes('salud');
    if (filter === 'vehicle') return item.service_type?.toLowerCase().includes('road') || item.service_type?.toLowerCase().includes('vial');
    return true;
  });

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="animate-spin text-pink-600" size={48} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="user">
      <div className="space-y-6 pb-8">
        {/* Header */}
        <div className="card bg-gradient-to-r from-pink-600 to-purple-600 text-white">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
              <Heart size={32} />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold">Portal de Salud</h1>
              <p className="text-pink-100">Gestiona tu historial medico y citas</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => { setBookingType('general'); setShowBookingModal(true); }}
            className="card hover:shadow-lg transition-shadow border-2 border-transparent hover:border-pink-200"
          >
            <div className="flex flex-col items-center text-center py-2">
              <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center mb-2">
                <Calendar className="text-pink-600" size={24} />
              </div>
              <p className="font-semibold text-gray-900">Agendar Cita</p>
              <p className="text-xs text-gray-500">Medico general o especialista</p>
            </div>
          </button>

          <button
            onClick={() => { setBookingType('video'); setShowBookingModal(true); }}
            className="card hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-200"
          >
            <div className="flex flex-col items-center text-center py-2">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                <Video className="text-blue-600" size={24} />
              </div>
              <p className="font-semibold text-gray-900">Video Consulta</p>
              <p className="text-xs text-gray-500">Atencion inmediata</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/app/request')}
            className="card hover:shadow-lg transition-shadow border-2 border-transparent hover:border-green-200"
          >
            <div className="flex flex-col items-center text-center py-2">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-2">
                <Pill className="text-green-600" size={24} />
              </div>
              <p className="font-semibold text-gray-900">Pedir Medicamento</p>
              <p className="text-xs text-gray-500">Entrega a domicilio</p>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('results')}
            className="card hover:shadow-lg transition-shadow border-2 border-transparent hover:border-purple-200"
          >
            <div className="flex flex-col items-center text-center py-2">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-2">
                <TestTube className="text-purple-600" size={24} />
              </div>
              <p className="font-semibold text-gray-900">Ver Resultados</p>
              <p className="text-xs text-gray-500">Examenes de laboratorio</p>
            </div>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { id: 'history', label: 'Historial', icon: History },
            { id: 'appointments', label: 'Citas', icon: Calendar },
            { id: 'results', label: 'Resultados', icon: FileText },
            { id: 'medications', label: 'Medicamentos', icon: Pill }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'bg-pink-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {/* Filter */}
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-gray-500" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2"
              >
                <option value="all">Todos los servicios</option>
                <option value="health">Solo Salud</option>
                <option value="vehicle">Solo Vial</option>
              </select>
            </div>

            {/* History List */}
            {filteredHistory.length > 0 ? (
              <div className="space-y-3">
                {filteredHistory.map((item) => (
                  <div key={item.id} className="card hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        {getServiceIcon(item.service_type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-gray-900">{item.title}</p>
                            <p className="text-xs text-gray-500">{item.request_number}</p>
                          </div>
                          {getStatusBadge(item.status)}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {new Date(item.created_at).toLocaleDateString('es-GT')}
                          </span>
                          {item.provider_name && (
                            <span className="flex items-center gap-1">
                              <User size={14} />
                              {item.provider_name}
                            </span>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="text-gray-400" size={20} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="card text-center py-12">
                <History className="mx-auto text-gray-300 mb-4" size={48} />
                <p className="text-gray-500">No hay historial de solicitudes</p>
                <Link to="/app/request" className="btn btn-primary mt-4">
                  Solicitar Asistencia
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Appointments Tab */}
        {activeTab === 'appointments' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">Mis Citas</h3>
              <button
                onClick={() => setShowBookingModal(true)}
                className="btn btn-primary btn-sm"
              >
                Nueva Cita
              </button>
            </div>

            {appointments.length > 0 ? (
              <div className="space-y-3">
                {appointments.map((apt) => (
                  <div key={apt.id} className="card border-l-4 border-l-pink-500">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-gray-900">{apt.specialty}</p>
                        <p className="text-sm text-gray-600">{apt.doctor_name}</p>
                      </div>
                      {getStatusBadge(apt.status)}
                    </div>
                    <div className="mt-3 space-y-2 text-sm text-gray-600">
                      <p className="flex items-center gap-2">
                        <Calendar size={14} />
                        {new Date(apt.date).toLocaleDateString('es-GT', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                      <p className="flex items-center gap-2">
                        <Clock size={14} />
                        {apt.time}
                      </p>
                      <p className="flex items-center gap-2">
                        <MapPin size={14} />
                        {apt.location}
                      </p>
                    </div>
                    {apt.status === 'scheduled' && (
                      <div className="mt-3 flex gap-2">
                        <button className="btn btn-outline btn-sm flex-1">
                          Reagendar
                        </button>
                        <button className="btn btn-outline btn-sm text-red-600 border-red-200 flex-1">
                          Cancelar
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="card text-center py-12">
                <Calendar className="mx-auto text-gray-300 mb-4" size={48} />
                <p className="text-gray-500">No tienes citas programadas</p>
                <button
                  onClick={() => setShowBookingModal(true)}
                  className="btn btn-primary mt-4"
                >
                  Agendar Cita
                </button>
              </div>
            )}
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && (
          <div className="space-y-4">
            <h3 className="font-semibold">Resultados de Examenes</h3>

            {healthRecords.filter(r => r.type === 'test_result').length > 0 ? (
              <div className="space-y-3">
                {healthRecords.filter(r => r.type === 'test_result').map((record) => (
                  <div key={record.id} className="card">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-purple-100 rounded-lg">
                          <TestTube className="text-purple-600" size={18} />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{record.title}</p>
                          <p className="text-sm text-gray-600">{record.provider}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(record.date).toLocaleDateString('es-GT')}
                          </p>
                        </div>
                      </div>
                      {getStatusBadge(record.status)}
                    </div>
                    {record.result_url && (
                      <div className="mt-3 flex gap-2">
                        <button className="btn btn-outline btn-sm flex items-center gap-1">
                          <Eye size={14} />
                          Ver Resultado
                        </button>
                        <button className="btn btn-outline btn-sm flex items-center gap-1">
                          <Download size={14} />
                          Descargar PDF
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="card text-center py-12">
                <FileText className="mx-auto text-gray-300 mb-4" size={48} />
                <p className="text-gray-500">No hay resultados disponibles</p>
                <p className="text-xs text-gray-400 mt-2">
                  Los resultados de tus examenes apareceran aqui
                </p>
              </div>
            )}
          </div>
        )}

        {/* Medications Tab */}
        {activeTab === 'medications' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">Mis Medicamentos</h3>
              <button
                onClick={() => navigate('/app/request')}
                className="btn btn-primary btn-sm"
              >
                Pedir Medicamento
              </button>
            </div>

            {healthRecords.filter(r => r.type === 'medication').length > 0 ? (
              <div className="space-y-3">
                {healthRecords.filter(r => r.type === 'medication').map((record) => (
                  <div key={record.id} className="card">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                          <Pill className="text-green-600" size={18} />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{record.title}</p>
                          <p className="text-sm text-gray-600">{record.details}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(record.date).toLocaleDateString('es-GT')}
                          </p>
                        </div>
                      </div>
                      {getStatusBadge(record.status)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="card text-center py-12">
                <Pill className="mx-auto text-gray-300 mb-4" size={48} />
                <p className="text-gray-500">No hay medicamentos registrados</p>
                <button
                  onClick={() => navigate('/app/request')}
                  className="btn btn-primary mt-4"
                >
                  Solicitar Entrega de Medicamento
                </button>
              </div>
            )}
          </div>
        )}

        {/* SegurifAI Health Services Banner */}
        <div className="card bg-gradient-to-r from-pink-50 to-purple-50 border border-pink-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center">
              <Stethoscope className="text-pink-600" size={24} />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-gray-900">Servicios de Salud SegurifAI</p>
              <p className="text-sm text-gray-600">
                Accede a consultas, examenes y medicamentos con tu plan
              </p>
            </div>
            <Link
              to="/app/subscriptions"
              className="btn btn-primary btn-sm"
            >
              Ver Planes
            </Link>
          </div>
        </div>
      </div>

      {/* Booking Modal */}
      {showBookingModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">
                  {bookingType === 'video' ? 'Agendar Video Consulta' : 'Agendar Cita Medica'}
                </h3>
                <button
                  onClick={() => setShowBookingModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-full"
                >
                  <AlertCircle size={20} className="rotate-45" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Specialty Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Especialidad *
                  </label>
                  <select
                    value={bookingForm.specialty}
                    onChange={(e) => setBookingForm({ ...bookingForm, specialty: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-pink-500 focus:ring-2 focus:ring-pink-200"
                  >
                    <option value="">Seleccionar especialidad</option>
                    <option value="general">Medicina General</option>
                    <option value="pediatria">Pediatria</option>
                    <option value="ginecologia">Ginecologia</option>
                    <option value="nutricion">Nutricion</option>
                    <option value="psicologia">Psicologia</option>
                    <option value="dermatologia">Dermatologia</option>
                    <option value="cardiologia">Cardiologia</option>
                    <option value="otra">Otra Especialidad</option>
                  </select>
                </div>

                {/* Date Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fecha Preferida *
                  </label>
                  <input
                    type="date"
                    value={bookingForm.preferred_date}
                    onChange={(e) => setBookingForm({ ...bookingForm, preferred_date: e.target.value })}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-pink-500 focus:ring-2 focus:ring-pink-200"
                  />
                </div>

                {/* Time Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Horario Preferido
                  </label>
                  <select
                    value={bookingForm.preferred_time}
                    onChange={(e) => setBookingForm({ ...bookingForm, preferred_time: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-pink-500 focus:ring-2 focus:ring-pink-200"
                  >
                    <option value="">Cualquier horario</option>
                    <option value="morning">Manana (8:00 - 12:00)</option>
                    <option value="afternoon">Tarde (14:00 - 18:00)</option>
                    <option value="evening">Noche (18:00 - 20:00)</option>
                  </select>
                </div>

                {/* Reason */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Motivo de la Consulta *
                  </label>
                  <textarea
                    value={bookingForm.reason}
                    onChange={(e) => setBookingForm({ ...bookingForm, reason: e.target.value })}
                    placeholder="Describe brevemente el motivo de tu consulta"
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-pink-500 focus:ring-2 focus:ring-pink-200"
                  />
                </div>

                {/* Video consultation note */}
                {bookingType === 'video' && (
                  <div className="p-4 bg-blue-50 rounded-xl">
                    <div className="flex items-start gap-2">
                      <Video className="text-blue-600 flex-shrink-0 mt-0.5" size={18} />
                      <div>
                        <p className="text-sm font-medium text-blue-800">Video Consulta</p>
                        <p className="text-xs text-blue-600">
                          Recibiras un enlace para conectarte desde tu celular o computadora
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowBookingModal(false)}
                  className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleBookAppointment}
                  disabled={bookingLoading}
                  className="flex-1 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-bold rounded-xl hover:from-pink-700 hover:to-purple-700 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {bookingLoading ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Solicitando...
                    </>
                  ) : (
                    <>
                      <Calendar size={20} />
                      Solicitar Cita
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
