import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { userAPI, servicesAPI, assistanceAPI, mapsAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import {
  User, Mail, Phone, MapPin, Calendar, Shield, Star, Edit2,
  Camera, CheckCircle, Clock, Award, RefreshCw, Bell, Lock, X, Plus, Navigation, Loader2,
  CreditCard, XCircle, ChevronRight, Car, Heart, Download, FileText, Check, Home, Search
} from 'lucide-react';
import { generateTermsAndConditionsPDF, getPlanTypeFromName } from '../../utils/termsAndConditions';

interface UserProfileData {
  id: number;
  name: string;
  email: string;
  phone: string;
  profile_picture?: string;
  address?: string;
  city?: string;
  state?: string;
  home_latitude?: number;
  home_longitude?: number;
  member_since: string;
  active_subscriptions: number;
  completed_requests: number;
  total_points: number;
  level: number;
  level_name: string;
  emergency_contacts: EmergencyContact[];
  preferences: UserPreferences;
}

interface EmergencyContact {
  id: number;
  name: string;
  phone: string;
  relationship: string;
}

interface UserPreferences {
  notifications_enabled: boolean;
  sms_alerts: boolean;
  email_updates: boolean;
  location_sharing: boolean;
}

interface Subscription {
  id: number;
  plan_name: string;
  plan_category: string;
  status: string;
  start_date: string;
  end_date: string;
  days_remaining?: number;
  plan_price?: number;
  plan_features?: string[];
}

interface AssistanceRequest {
  id: number;
  title: string;
  status: string;
  priority: string;
  created_at: string;
  service_category_name?: string;
  incident_type?: string;
}

// Plan benefits data for the details modal - SegurifAI Dec 2025 - All limits in GTQ
const PLAN_BENEFITS: Record<string, { price: number; benefits: string[] }> = {
  'Protege tu Tarjeta': {
    price: 34.99,
    benefits: [
      'Seguro Muerte Accidental Q3,000',
      'Tarjetas Perdidas o Robadas (48hrs para notificar)',
      'Protección contra Clonación de Tarjeta',
      'Protección contra Falsificación de Banda Magnética',
      'Cobertura Digital: Ingeniería Social',
      'Cobertura Digital: Phishing',
      'Cobertura Digital: Robo de Identidad',
      'Cobertura Digital: Suplantación (Spoofing)',
      'Cobertura Digital: Vishing',
      'Cobertura compras fraudulentas por internet',
      'Asistencias SegurifAI incluidas'
    ]
  },
  'Protege tu Salud': {
    price: 34.99,
    benefits: [
      'Seguro Muerte Accidental Q3,000',
      'Orientación Médica Telefónica (Ilimitado)',
      'Conexión con Especialistas de la Red (Ilimitado)',
      'Consulta Presencial Médico/Ginecólogo/Pediatra (3/año, Q1,170)',
      'Coordinación de Medicamentos a Domicilio (Ilimitado)',
      'Cuidados Post Operatorios Enfermera (1/año, Q780)',
      'Envío Artículos Aseo por Hospitalización (1/año, Q780)',
      'Exámenes Lab: Heces, Orina, Hematología (2/año, Q780)',
      'Exámenes: Papanicoláu/Mamografía/Antígeno (2/año, Q780)',
      'Nutricionista Video Consulta Familiar (4/año, Q1,170)',
      'Psicología Video Consulta Familiar (4/año, Q1,170)',
      'Servicio de Mensajería por Hospitalización (2/año, Q470)',
      'Taxi Familiar por Hospitalización (2/año, Q780)',
      'Traslado en Ambulancia por Accidente (2/año, Q1,170)',
      'Taxi al Domicilio tras Alta (1/año, Q780)',
      'Asistencias SegurifAI incluidas'
    ]
  },
  'Protege tu Ruta': {
    price: 39.99,
    benefits: [
      'Seguro Muerte Accidental Q3,000',
      'Grúa del Vehículo (3/año, Q1,170)',
      'Abasto de Combustible 1 galón (3/año, Q1,170 combinado)',
      'Cambio de Neumáticos (3/año, Q1,170 combinado)',
      'Paso de Corriente (3/año, Q1,170 combinado)',
      'Emergencia de Cerrajería (3/año, Q1,170 combinado)',
      'Servicio de Ambulancia por Accidente (1/año, Q780)',
      'Servicio de Conductor Profesional (1/año, Q470)',
      'Taxi al Aeropuerto (1/año, Q470)',
      'Asistencia Legal Telefónica (1/año, Q1,560)',
      'Apoyo Económico Sala Emergencia (1/año, Q7,800)',
      'Rayos X (1/año, Q2,340, hasta 20% descuento)',
      'Descuentos en Red de Proveedores (hasta 20%)',
      'Asistente Telefónico Cotización Repuestos',
      'Asistente Telefónico Referencias Médicas por Accidente',
      'Asistencias SegurifAI incluidas'
    ]
  }
};

export const UserProfile: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, isPAQUser } = useAuth();
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    home_latitude: null as number | null,
    home_longitude: null as number | null
  });

  // Modal states
  const [showContactModal, setShowContactModal] = useState(false);
  const [showHomeAddressModal, setShowHomeAddressModal] = useState(false);
  const [addressSearch, setAddressSearch] = useState('');
  const [searchingAddress, setSearchingAddress] = useState(false);
  const [savingHomeAddress, setSavingHomeAddress] = useState(false);
  const [homeAddressForm, setHomeAddressForm] = useState({
    address: '',
    city: '',
    state: '',
    latitude: null as number | null,
    longitude: null as number | null
  });
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newContact, setNewContact] = useState({ name: '', phone: '', relationship: '' });
  const [passwordForm, setPasswordForm] = useState({ current: '', new_password: '', confirm: '' });
  const [savingPreference, setSavingPreference] = useState<string | null>(null);
  const [locationStatus, setLocationStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);

  // Subscriptions state
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loadingSubscriptions, setLoadingSubscriptions] = useState(true);
  const [cancellingSubscription, setCancellingSubscription] = useState<number | null>(null);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [showPlanDetailsModal, setShowPlanDetailsModal] = useState(false);

  // Recent requests state
  const [recentRequests, setRecentRequests] = useState<AssistanceRequest[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(true);

  useEffect(() => {
    loadProfile();
    loadSubscriptions();
    loadRecentRequests();
  }, []);

  const loadSubscriptions = async () => {
    try {
      const response = await servicesAPI.getMySubscriptions();
      const subs = response.data.subscriptions || response.data || [];
      setSubscriptions(subs);
    } catch (error) {
      console.error('Failed to load subscriptions:', error);
      setSubscriptions([]);
    } finally {
      setLoadingSubscriptions(false);
    }
  };

  const loadRecentRequests = async () => {
    try {
      const response = await assistanceAPI.getMyRequests();
      const requests = response.data.requests || response.data || [];
      // Get only the 5 most recent requests
      setRecentRequests(requests.slice(0, 5));
    } catch (error) {
      console.error('Failed to load recent requests:', error);
      setRecentRequests([]);
    } finally {
      setLoadingRequests(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'PENDING': return 'bg-yellow-100 text-yellow-700';
      case 'ACCEPTED': return 'bg-blue-100 text-blue-700';
      case 'IN_PROGRESS': return 'bg-purple-100 text-purple-700';
      case 'COMPLETED': return 'bg-green-100 text-green-700';
      case 'CANCELLED': return 'bg-gray-100 text-gray-700';
      case 'REJECTED': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'PENDING': return 'Pendiente';
      case 'ACCEPTED': return 'Aceptado';
      case 'IN_PROGRESS': return 'En Progreso';
      case 'COMPLETED': return 'Completado';
      case 'CANCELLED': return 'Cancelado';
      case 'REJECTED': return 'Rechazado';
      default: return status;
    }
  };

  const handleCancelSubscription = async (subscriptionId: number) => {
    if (!confirm('¿Estás seguro que deseas cancelar esta suscripción?')) return;

    setCancellingSubscription(subscriptionId);
    try {
      await servicesAPI.cancelSubscription(subscriptionId);
      await loadSubscriptions();
      await loadProfile();
      alert('Suscripción cancelada exitosamente');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al cancelar suscripción');
    } finally {
      setCancellingSubscription(null);
    }
  };

  const handleRenewSubscription = async (subscriptionId: number) => {
    try {
      await servicesAPI.initiateRenewal(subscriptionId);
      alert('Renovación iniciada. Por favor completa el pago.');
      navigate('/app/subscriptions');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al renovar suscripción');
    }
  };

  const loadProfile = async () => {
    try {
      const response = await userAPI.getProfile();
      const data = response.data;

      // Transform API response to match frontend interface
      const transformedProfile: UserProfileData = {
        id: data.id,
        name: data.full_name || `${data.first_name || ''} ${data.last_name || ''}`.trim() || 'Usuario',
        email: data.email,
        phone: data.phone_number || '',
        profile_picture: data.profile_image,
        address: data.address || '',
        city: data.city || '',
        member_since: data.date_joined,
        // These will be populated from full profile if available
        active_subscriptions: 0,
        completed_requests: 0,
        total_points: 0,
        level: 1,
        level_name: 'Novato',
        emergency_contacts: data.emergency_contact_name ? [
          {
            id: 1,
            name: data.emergency_contact_name,
            phone: data.emergency_contact_phone || '',
            relationship: 'Contacto de Emergencia'
          }
        ] : [],
        preferences: {
          notifications_enabled: true,
          sms_alerts: true,
          email_updates: true,
          location_sharing: true
        }
      };

      setProfile(transformedProfile);
      setEditForm({
        name: transformedProfile.name,
        phone: transformedProfile.phone,
        address: transformedProfile.address || '',
        city: transformedProfile.city || '',
        state: transformedProfile.state || '',
        home_latitude: transformedProfile.home_latitude || null,
        home_longitude: transformedProfile.home_longitude || null
      });

      // Try to load full profile for additional data
      try {
        const fullProfile = await userAPI.getFullProfile();
        const fullData = fullProfile.data;
        if (fullData.e_learning?.points) {
          transformedProfile.total_points = fullData.e_learning.points.total_points || 0;
          transformedProfile.level_name = fullData.e_learning.points.level_display || 'Novato';
        }
        if (fullData.subscription) {
          transformedProfile.active_subscriptions = fullData.subscription.total_subscriptions || 0;
        }
        setProfile({ ...transformedProfile });
      } catch (fullError) {
        // Full profile data is optional, continue with basic profile
        console.log('Full profile not available, using basic profile');
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      // Fallback to user context data
      const fallbackProfile: UserProfileData = {
        id: 1,
        name: user?.first_name && user?.last_name
          ? `${user.first_name} ${user.last_name}`
          : user?.email?.split('@')[0] || 'Usuario',
        email: user?.email || '',
        phone: '',
        member_since: new Date().toISOString(),
        active_subscriptions: 0,
        completed_requests: 0,
        total_points: 0,
        level: 1,
        level_name: 'Novato',
        emergency_contacts: [],
        preferences: {
          notifications_enabled: true,
          sms_alerts: true,
          email_updates: true,
          location_sharing: true
        }
      };
      setProfile(fallbackProfile);
      setEditForm({
        name: fallbackProfile.name,
        phone: fallbackProfile.phone,
        address: '',
        city: '',
        state: '',
        home_latitude: null,
        home_longitude: null
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      // Transform frontend field names to backend field names
      const nameParts = editForm.name.trim().split(' ');
      const firstName = nameParts[0] || '';
      const lastName = nameParts.slice(1).join(' ') || '';

      await userAPI.updateProfile({
        first_name: firstName,
        last_name: lastName,
        phone_number: editForm.phone,
        address: editForm.address,
        city: editForm.city
      });
      await loadProfile();
      setEditing(false);
      alert('Perfil actualizado exitosamente!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al actualizar perfil');
    }
  };

  // Search address using Google Maps API
  const handleSearchAddress = async () => {
    if (!addressSearch.trim()) return;

    setSearchingAddress(true);
    try {
      const response = await mapsAPI.geocode(addressSearch);
      const result = response.data;

      if (result && result.formatted_address) {
        setHomeAddressForm({
          address: result.formatted_address,
          city: result.city || '',
          state: result.state || '',
          latitude: result.latitude,
          longitude: result.longitude
        });
      } else {
        alert('No se encontró la dirección. Intenta con una dirección más específica.');
      }
    } catch (error: any) {
      console.error('Geocode error:', error);
      alert('Error al buscar la dirección. Intenta de nuevo.');
    } finally {
      setSearchingAddress(false);
    }
  };

  // Get current location
  const handleGetCurrentLocation = async () => {
    setSearchingAddress(true);
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        });
      });

      const { latitude, longitude } = position.coords;
      const response = await mapsAPI.reverseGeocode(latitude, longitude);
      const result = response.data;

      if (result && result.formatted_address) {
        setHomeAddressForm({
          address: result.formatted_address,
          city: result.city || '',
          state: result.state || '',
          latitude: latitude,
          longitude: longitude
        });
        setAddressSearch(result.formatted_address);
      }
    } catch (error: any) {
      console.error('Location error:', error);
      alert('No se pudo obtener tu ubicación. Verifica los permisos de ubicación.');
    } finally {
      setSearchingAddress(false);
    }
  };

  // Save home address
  const handleSaveHomeAddress = async () => {
    if (!homeAddressForm.address || !homeAddressForm.latitude) {
      alert('Por favor busca y selecciona una dirección válida.');
      return;
    }

    setSavingHomeAddress(true);
    try {
      await userAPI.updateProfile({
        address: homeAddressForm.address,
        city: homeAddressForm.city,
        state: homeAddressForm.state,
        home_latitude: homeAddressForm.latitude,
        home_longitude: homeAddressForm.longitude
      });
      await loadProfile();
      setShowHomeAddressModal(false);
      setAddressSearch('');
      setHomeAddressForm({ address: '', city: '', state: '', latitude: null, longitude: null });
      alert('Dirección guardada exitosamente!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al guardar la dirección');
    } finally {
      setSavingHomeAddress(false);
    }
  };

  // Toggle preference handler
  const handleTogglePreference = async (key: keyof UserPreferences) => {
    if (!profile) return;

    setSavingPreference(key);
    const newValue = !profile.preferences[key];

    // Handle location sharing specially
    if (key === 'location_sharing' && newValue) {
      await handleEnableLocationSharing();
    }

    try {
      const updatedPrefs = { ...profile.preferences, [key]: newValue };
      await userAPI.updateProfile({ preferences: updatedPrefs });
      setProfile({ ...profile, preferences: updatedPrefs });
    } catch (error) {
      console.error('Error updating preference:', error);
      // Still update UI on error for demo
      setProfile({
        ...profile,
        preferences: { ...profile.preferences, [key]: newValue }
      });
    } finally {
      setSavingPreference(null);
    }
  };

  // Location sharing handler
  const handleEnableLocationSharing = async () => {
    setLocationStatus('loading');
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        });
      });

      const { latitude, longitude } = position.coords;
      setCurrentLocation({ lat: latitude, lng: longitude });
      setLocationStatus('success');

      // Save location to backend
      try {
        await userAPI.updateProfile({
          last_location: { lat: latitude, lng: longitude }
        });
      } catch (err) {
        console.log('Location saved locally');
      }
    } catch (error) {
      console.error('Location error:', error);
      setLocationStatus('error');
      alert('No se pudo obtener tu ubicación. Por favor habilita los permisos de ubicación en tu navegador.');
    }
  };

  // Add emergency contact
  const handleAddContact = async () => {
    if (!newContact.name || !newContact.phone || !newContact.relationship) {
      alert('Por favor completa todos los campos');
      return;
    }

    try {
      await userAPI.addEmergencyContact(newContact);
      await loadProfile();
      setShowContactModal(false);
      setNewContact({ name: '', phone: '', relationship: '' });
      alert('Contacto agregado exitosamente!');
    } catch (error) {
      // For demo, just add locally
      if (profile) {
        const updatedContacts = [
          ...profile.emergency_contacts,
          { id: Date.now(), ...newContact }
        ];
        setProfile({ ...profile, emergency_contacts: updatedContacts });
        setShowContactModal(false);
        setNewContact({ name: '', phone: '', relationship: '' });
      }
    }
  };

  // Change password
  const handleChangePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm) {
      alert('Las contraseñas no coinciden');
      return;
    }
    if (passwordForm.new_password.length < 8) {
      alert('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    try {
      await userAPI.changePassword({
        current_password: passwordForm.current,
        new_password: passwordForm.new_password
      });
      setShowPasswordModal(false);
      setPasswordForm({ current: '', new_password: '', confirm: '' });
      alert('Contraseña actualizada exitosamente!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al cambiar contraseña');
    }
  };

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="animate-spin text-blue-600" size={48} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="user">
      <div className="max-w-2xl mx-auto space-y-6 pb-8">
        {/* Profile Header */}
        <div className="card bg-gradient-to-r from-blue-600 to-blue-700 text-white">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center">
                {profile?.profile_picture ? (
                  <img
                    src={profile.profile_picture}
                    alt="Perfil"
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <User size={40} />
                )}
              </div>
              <button className="absolute -bottom-1 -right-1 p-2 bg-white rounded-full text-blue-600 shadow-lg">
                <Camera size={14} />
              </button>
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold">{profile?.name}</h1>
              <div className="flex items-center gap-2 text-blue-200">
                <Star size={14} />
                <span>Nivel {profile?.level} - {profile?.level_name}</span>
              </div>
              <p className="text-sm text-blue-200 mt-1">{profile?.total_points} puntos</p>
            </div>
            <button
              onClick={() => setEditing(!editing)}
              className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
            >
              <Edit2 size={18} />
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <Shield className="mx-auto text-blue-600 mb-2" size={24} />
            <p className="text-2xl font-bold">{profile?.active_subscriptions}</p>
            <p className="text-xs text-gray-500">Suscripciones</p>
          </div>
          <div className="card text-center">
            <CheckCircle className="mx-auto text-green-600 mb-2" size={24} />
            <p className="text-2xl font-bold">{profile?.completed_requests}</p>
            <p className="text-xs text-gray-500">Solicitudes</p>
          </div>
          <div className="card text-center">
            <Award className="mx-auto text-yellow-600 mb-2" size={24} />
            <p className="text-2xl font-bold">{profile?.total_points}</p>
            <p className="text-xs text-gray-500">Puntos</p>
          </div>
        </div>

        {/* Subscriptions Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <CreditCard size={18} />
              Mis Suscripciones
            </h3>
            <button
              onClick={() => navigate('/app/subscriptions')}
              className="text-blue-600 text-sm font-medium flex items-center gap-1 hover:text-blue-800"
            >
              Ver Planes
              <ChevronRight size={16} />
            </button>
          </div>

          {loadingSubscriptions ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="animate-spin text-blue-600" size={24} />
            </div>
          ) : subscriptions.length === 0 ? (
            <div className="text-center py-6">
              <Shield className="mx-auto text-gray-300 mb-3" size={48} />
              <p className="text-gray-500 mb-4">No tienes suscripciones activas</p>
              <button
                onClick={() => navigate('/app/subscriptions')}
                className="btn btn-primary"
              >
                Ver Planes Disponibles
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Filter out CANCELLED plans - only show ACTIVE and other status */}
              {subscriptions.filter(sub => sub.status !== 'CANCELLED').map((sub) => (
                <div
                  key={sub.id}
                  className={`p-4 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
                    sub.status === 'ACTIVE'
                      ? 'bg-green-50 border-green-200 hover:border-green-400'
                      : 'bg-yellow-50 border-yellow-200 hover:border-yellow-400'
                  }`}
                  onClick={() => {
                    setSelectedSubscription(sub);
                    setShowPlanDetailsModal(true);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        sub.plan_category === 'ROADSIDE' ? 'bg-blue-100' : sub.plan_category === 'CARD_INSURANCE' ? 'bg-emerald-100' : 'bg-pink-100'
                      }`}>
                        {sub.plan_category === 'ROADSIDE' ? (
                          <Car className="text-blue-600" size={20} />
                        ) : sub.plan_category === 'CARD_INSURANCE' ? (
                          <Shield className="text-emerald-600" size={20} />
                        ) : (
                          <Heart className="text-pink-600" size={20} />
                        )}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">
                          {sub.plan_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {sub.plan_category === 'ROADSIDE' ? 'Protege tu Ruta' : sub.plan_category === 'CARD_INSURANCE' ? 'Protege tu Tarjeta' : 'Protege tu Salud'}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        sub.status === 'ACTIVE' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {sub.status === 'ACTIVE' ? 'Activo' : sub.status}
                      </span>
                      <span className="text-xs text-blue-600 font-medium flex items-center gap-1">
                        <FileText size={12} />
                        Ver detalles
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-sm">
                    <div className="text-gray-600">
                      <span className="block">
                        Vence: {new Date(sub.end_date).toLocaleDateString('es-GT')}
                      </span>
                      {sub.days_remaining !== undefined && sub.days_remaining > 0 && sub.status === 'ACTIVE' && (
                        <span className={`text-xs ${sub.days_remaining <= 7 ? 'text-orange-600 font-medium' : 'text-gray-500'}`}>
                          {sub.days_remaining} dias restantes
                        </span>
                      )}
                    </div>

                    {sub.status === 'ACTIVE' && (
                      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                        {sub.days_remaining !== undefined && sub.days_remaining <= 7 && (
                          <button
                            onClick={() => handleRenewSubscription(sub.id)}
                            className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            Renovar
                          </button>
                        )}
                        <button
                          onClick={() => handleCancelSubscription(sub.id)}
                          disabled={cancellingSubscription === sub.id}
                          className="px-3 py-1 border border-red-300 text-red-600 text-xs font-medium rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50 flex items-center gap-1"
                        >
                          {cancellingSubscription === sub.id ? (
                            <Loader2 className="animate-spin" size={12} />
                          ) : (
                            <XCircle size={12} />
                          )}
                          Cancelar
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Requests Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <Clock size={18} />
              Mis Solicitudes Recientes
            </h3>
            <button
              onClick={() => navigate('/app/requests')}
              className="text-blue-600 text-sm font-medium flex items-center gap-1 hover:text-blue-800"
            >
              Ver Todas
              <ChevronRight size={16} />
            </button>
          </div>

          {loadingRequests ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="animate-spin text-blue-600" size={24} />
            </div>
          ) : recentRequests.length === 0 ? (
            <div className="text-center py-6">
              <Clock className="mx-auto text-gray-300 mb-3" size={48} />
              <p className="text-gray-500 mb-4">No tienes solicitudes recientes</p>
              <button
                onClick={() => navigate('/app/assistance')}
                className="btn btn-primary"
              >
                Solicitar Asistencia
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentRequests.map((request) => (
                <div
                  key={request.id}
                  onClick={() => navigate(`/app/requests/${request.id}`)}
                  className="p-4 rounded-xl border border-gray-200 hover:border-blue-300 cursor-pointer transition-all hover:shadow-md"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">
                        {request.title || request.incident_type || 'Solicitud de Asistencia'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {request.service_category_name || 'Asistencia General'}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(request.created_at).toLocaleDateString('es-GT', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 ml-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {getStatusLabel(request.status)}
                      </span>
                      {request.priority && request.priority !== 'MEDIUM' && (
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          request.priority === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                        }`}>
                          {request.priority === 'HIGH' ? 'Alta Prioridad' : 'Baja Prioridad'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Health Portal Link */}
        <div
          onClick={() => navigate('/app/health')}
          className="card bg-gradient-to-r from-pink-50 to-purple-50 border-2 border-pink-200 hover:border-pink-400 cursor-pointer transition-all hover:shadow-lg"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-pink-500 to-purple-500 rounded-2xl flex items-center justify-center">
              <Heart className="text-white" size={28} />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-gray-900">Portal de Salud</h3>
              <p className="text-sm text-gray-600">Historial, citas, resultados y medicamentos</p>
            </div>
            <ChevronRight className="text-pink-400" size={24} />
          </div>
        </div>

        {/* Personal Info */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <User size={18} />
              Información Personal
            </h3>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="text-blue-600 text-sm font-medium flex items-center gap-1 hover:text-blue-800"
              >
                <Edit2 size={14} />
                Editar
              </button>
            )}
          </div>

          {editing ? (
            <div className="space-y-4">
              <div>
                <label className="label">Nombre Completo</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="input"
                  placeholder="Tu nombre completo"
                />
              </div>
              <div>
                <label className="label">Teléfono</label>
                <input
                  type="tel"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="input"
                  placeholder="+502 5555-1234"
                />
              </div>
              <p className="text-xs text-gray-500 bg-blue-50 p-3 rounded-lg">
                Para cambiar tu dirección, utiliza la sección "Dirección de Casa" más abajo.
              </p>
              <div className="flex gap-3">
                <button onClick={() => setEditing(false)} className="btn btn-outline flex-1">
                  Cancelar
                </button>
                <button onClick={handleSaveProfile} className="btn btn-primary flex-1">
                  Guardar Cambios
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <User className="text-blue-600" size={16} />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Nombre Completo</p>
                  <p className="font-medium text-gray-900">{profile?.name || 'No especificado'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Mail className="text-green-600" size={16} />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Correo Electrónico</p>
                  <p className="font-medium text-gray-900">{profile?.email}</p>
                </div>
                <CheckCircle className="text-green-500" size={16} />
              </div>
              <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Phone className="text-purple-600" size={16} />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Teléfono</p>
                  <p className="font-medium text-gray-900">{profile?.phone || 'No especificado'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <Calendar className="text-amber-600" size={16} />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Miembro desde</p>
                  <p className="font-medium text-gray-900">
                    {profile?.member_since
                      ? new Date(profile.member_since).toLocaleDateString('es-GT', {
                          year: 'numeric',
                          month: 'long'
                        })
                      : 'No especificado'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Home Address Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <Home size={18} />
              Dirección de Casa
            </h3>
            <button
              onClick={() => {
                setShowHomeAddressModal(true);
                if (profile?.address) {
                  setAddressSearch(profile.address);
                  setHomeAddressForm({
                    address: profile.address || '',
                    city: profile.city || '',
                    state: profile.state || '',
                    latitude: profile.home_latitude || null,
                    longitude: profile.home_longitude || null
                  });
                }
              }}
              className="btn btn-outline btn-sm flex items-center gap-1"
            >
              <Edit2 size={14} />
              {profile?.address ? 'Editar' : 'Agregar'}
            </button>
          </div>

          {profile?.address ? (
            <div className="space-y-3">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <MapPin className="text-blue-600" size={20} />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{profile.address}</p>
                    {(profile.city || profile.state) && (
                      <p className="text-sm text-gray-600 mt-1">
                        {[profile.city, profile.state].filter(Boolean).join(', ')}
                      </p>
                    )}
                    {profile.home_latitude && profile.home_longitude && (
                      <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                        <CheckCircle size={12} />
                        Ubicación exacta guardada
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-6">
              <Home className="mx-auto text-gray-300 mb-3" size={48} />
              <p className="text-gray-500 mb-4">No has guardado tu dirección de casa</p>
              <button
                onClick={() => setShowHomeAddressModal(true)}
                className="btn btn-primary"
              >
                Agregar Dirección
              </button>
            </div>
          )}
        </div>

        {/* Emergency Contacts */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <Phone size={18} />
              Contactos de Emergencia
            </h3>
            <button
              onClick={() => setShowContactModal(true)}
              className="btn btn-outline btn-sm flex items-center gap-1"
            >
              <Plus size={14} />
              Agregar
            </button>
          </div>
          {profile?.emergency_contacts && profile.emergency_contacts.length > 0 ? (
            <div className="space-y-3">
              {profile.emergency_contacts.map((contact) => (
                <div key={contact.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <div>
                    <p className="font-medium">{contact.name}</p>
                    <p className="text-sm text-gray-500">{contact.relationship}</p>
                  </div>
                  <a href={`tel:${contact.phone}`} className="text-blue-600 font-medium">
                    {contact.phone}
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-4">
              No hay contactos de emergencia registrados
            </p>
          )}
        </div>

        {/* Preferences - Only Push Notifications and Location Sharing */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <Bell size={18} />
            Preferencias
          </h3>
          <div className="space-y-4">
            {[
              { key: 'notifications_enabled', label: 'Notificaciones Push', icon: Bell },
              { key: 'location_sharing', label: 'Compartir Ubicación', icon: MapPin }
            ].map((pref) => (
              <button
                key={pref.key}
                onClick={() => handleTogglePreference(pref.key as keyof UserPreferences)}
                disabled={savingPreference === pref.key}
                className="w-full flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg transition-colors disabled:opacity-50"
              >
                <div className="flex items-center gap-3">
                  <pref.icon className="text-gray-400" size={18} />
                  <span>{pref.label}</span>
                  {pref.key === 'location_sharing' && locationStatus === 'loading' && (
                    <Loader2 className="animate-spin text-blue-500" size={16} />
                  )}
                  {pref.key === 'location_sharing' && currentLocation && profile?.preferences?.location_sharing && (
                    <span className="text-xs text-green-600 flex items-center gap-1">
                      <Navigation size={12} />
                      Ubicación activa
                    </span>
                  )}
                </div>
                <div className={`w-12 h-7 rounded-full transition-colors relative ${
                  profile?.preferences?.[pref.key as keyof UserPreferences] ? 'bg-blue-500' : 'bg-gray-300'
                }`}>
                  <div className={`w-5 h-5 bg-white rounded-full shadow absolute top-1 transition-transform ${
                    profile?.preferences?.[pref.key as keyof UserPreferences] ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </div>
              </button>
            ))}
          </div>

          {/* Location Map Preview */}
          {currentLocation && profile?.preferences?.location_sharing && (
            <div className="mt-4 p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <Navigation className="text-green-600" size={18} />
                <span className="font-medium text-green-800">Tu ubicación está siendo compartida</span>
              </div>
              <p className="text-sm text-green-700">
                Lat: {currentLocation.lat.toFixed(6)}, Lng: {currentLocation.lng.toFixed(6)}
              </p>
              <p className="text-xs text-green-600 mt-1">
                Esta ubicación se usa para servicios de emergencia
              </p>
            </div>
          )}
        </div>

        {/* Security - Only show for non-PAQ users */}
        {!isPAQUser && (
          <div className="card">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Lock size={18} />
              Seguridad
            </h3>
            <button
              onClick={() => setShowPasswordModal(true)}
              className="w-full p-3 bg-gray-50 rounded-xl text-left hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span>Cambiar Contraseña</span>
                <Lock className="text-gray-400" size={18} />
              </div>
            </button>
          </div>
        )}

        {/* Logout */}
        <button
          onClick={logout}
          className="w-full py-3 bg-red-50 text-red-600 rounded-xl font-medium hover:bg-red-100 transition-colors"
        >
          Cerrar Sesión
        </button>
      </div>

      {/* Add Emergency Contact Modal */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Agregar Contacto de Emergencia</h3>
              <button
                onClick={() => setShowContactModal(false)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Nombre</label>
                <input
                  type="text"
                  value={newContact.name}
                  onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                  placeholder="Nombre completo"
                  className="input"
                />
              </div>
              <div>
                <label className="label">Teléfono</label>
                <input
                  type="tel"
                  value={newContact.phone}
                  onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                  placeholder="+502 5555-1234"
                  className="input"
                />
              </div>
              <div>
                <label className="label">Relación</label>
                <select
                  value={newContact.relationship}
                  onChange={(e) => setNewContact({ ...newContact, relationship: e.target.value })}
                  className="input"
                >
                  <option value="">Seleccionar...</option>
                  <option value="Familiar">Familiar</option>
                  <option value="Cónyuge">Cónyuge</option>
                  <option value="Padre/Madre">Padre/Madre</option>
                  <option value="Hijo/Hija">Hijo/Hija</option>
                  <option value="Hermano/Hermana">Hermano/Hermana</option>
                  <option value="Amigo">Amigo</option>
                  <option value="Otro">Otro</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowContactModal(false)}
                className="flex-1 btn btn-outline"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddContact}
                className="flex-1 btn btn-primary"
              >
                Agregar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Cambiar Contraseña</h3>
              <button
                onClick={() => setShowPasswordModal(false)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Contraseña Actual</label>
                <input
                  type="password"
                  value={passwordForm.current}
                  onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                  placeholder="••••••••"
                  className="input"
                />
              </div>
              <div>
                <label className="label">Nueva Contraseña</label>
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  placeholder="••••••••"
                  className="input"
                />
                <p className="text-xs text-gray-500 mt-1">Mínimo 8 caracteres</p>
              </div>
              <div>
                <label className="label">Confirmar Contraseña</label>
                <input
                  type="password"
                  value={passwordForm.confirm}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                  placeholder="••••••••"
                  className="input"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowPasswordModal(false)}
                className="flex-1 btn btn-outline"
              >
                Cancelar
              </button>
              <button
                onClick={handleChangePassword}
                className="flex-1 btn btn-primary"
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Plan Details Modal */}
      {showPlanDetailsModal && selectedSubscription && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Detalles del Plan</h3>
              <button
                onClick={() => {
                  setShowPlanDetailsModal(false);
                  setSelectedSubscription(null);
                }}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X size={20} />
              </button>
            </div>

            {/* Plan Header */}
            <div className={`p-4 rounded-xl mb-4 ${
              selectedSubscription.plan_category === 'ROADSIDE'
                ? 'bg-blue-50 border border-blue-200'
                : selectedSubscription.plan_category === 'CARD_INSURANCE'
                ? 'bg-emerald-50 border border-emerald-200'
                : 'bg-pink-50 border border-pink-200'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-lg ${
                  selectedSubscription.plan_category === 'ROADSIDE'
                    ? 'bg-blue-100'
                    : selectedSubscription.plan_category === 'CARD_INSURANCE'
                    ? 'bg-emerald-100'
                    : 'bg-pink-100'
                }`}>
                  {selectedSubscription.plan_category === 'ROADSIDE' ? (
                    <Car className="text-blue-600" size={28} />
                  ) : selectedSubscription.plan_category === 'CARD_INSURANCE' ? (
                    <Shield className="text-emerald-600" size={28} />
                  ) : (
                    <Heart className="text-pink-600" size={28} />
                  )}
                </div>
                <div>
                  <h4 className="font-bold text-lg text-gray-900">
                    {selectedSubscription.plan_name}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {selectedSubscription.plan_category === 'ROADSIDE'
                      ? 'Protege tu Ruta'
                      : selectedSubscription.plan_category === 'CARD_INSURANCE'
                      ? 'Protege tu Tarjeta'
                      : 'Protege tu Salud'}
                  </p>
                  {selectedSubscription.days_remaining !== undefined && selectedSubscription.days_remaining >= 0 && (
                    <p className={`text-sm font-medium mt-1 ${selectedSubscription.days_remaining <= 7 ? 'text-orange-600' : 'text-green-600'}`}>
                      {selectedSubscription.days_remaining} días restantes
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Price - use API price when available */}
            <div className="bg-gray-50 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Costo Mensual:</span>
                <span className="text-2xl font-bold text-blue-600">
                  Q{selectedSubscription.plan_price?.toFixed(2) || PLAN_BENEFITS[selectedSubscription.plan_name]?.price.toFixed(2) || '0.00'}
                </span>
              </div>
              <div className="flex items-center justify-between mt-2 text-sm">
                <span className="text-gray-500">Vigencia:</span>
                <span className="text-gray-700">
                  {new Date(selectedSubscription.start_date).toLocaleDateString('es-GT')} - {new Date(selectedSubscription.end_date).toLocaleDateString('es-GT')}
                </span>
              </div>
            </div>

            {/* Benefits List - use API features when available, fallback to local constant */}
            <div className="mb-4">
              <h5 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Shield size={16} className="text-blue-600" />
                Servicios y Beneficios Incluidos
              </h5>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                {(selectedSubscription.plan_features || PLAN_BENEFITS[selectedSubscription.plan_name]?.benefits || []).map((benefit, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <Check className="text-green-500 flex-shrink-0 mt-0.5" size={16} />
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Terms & Conditions Download */}
            <div className="border-t pt-4 mt-4">
              <h5 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <FileText size={16} className="text-gray-600" />
                Términos y Condiciones
              </h5>
              <button
                onClick={() => {
                  if (selectedSubscription) {
                    generateTermsAndConditionsPDF({
                      name: selectedSubscription.plan_name,
                      type: getPlanTypeFromName(selectedSubscription.plan_name),
                    });
                  }
                }}
                className="flex items-center justify-center gap-2 w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
              >
                <Download size={18} />
                Descargar Términos y Condiciones (PDF)
              </button>
              <p className="text-xs text-gray-500 mt-2 text-center">
                Al utilizar nuestros servicios, aceptas los términos y condiciones descritos en el documento.
              </p>
            </div>

            {/* Close Button */}
            <button
              onClick={() => {
                setShowPlanDetailsModal(false);
                setSelectedSubscription(null);
              }}
              className="w-full mt-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}

      {/* Home Address Modal */}
      {showHomeAddressModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Home className="text-blue-600" size={24} />
                Dirección de Casa
              </h3>
              <button
                onClick={() => {
                  setShowHomeAddressModal(false);
                  setAddressSearch('');
                  setHomeAddressForm({ address: '', city: '', state: '', latitude: null, longitude: null });
                }}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X size={20} />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              Busca tu dirección usando Google Maps para guardar tu ubicación exacta.
            </p>

            {/* Address Search */}
            <div className="space-y-4">
              <div>
                <label className="label">Buscar Dirección</label>
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={addressSearch}
                      onChange={(e) => setAddressSearch(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearchAddress()}
                      className="input pr-10"
                      placeholder="Ej: 6a Avenida 12-34, Zona 10, Guatemala"
                    />
                    {searchingAddress && (
                      <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-gray-400" size={18} />
                    )}
                  </div>
                  <button
                    onClick={handleSearchAddress}
                    disabled={searchingAddress || !addressSearch.trim()}
                    className="btn btn-primary px-4"
                  >
                    <Search size={18} />
                  </button>
                </div>
              </div>

              {/* Use Current Location Button */}
              <button
                onClick={handleGetCurrentLocation}
                disabled={searchingAddress}
                className="w-full py-3 border-2 border-dashed border-blue-300 rounded-xl text-blue-600 font-medium flex items-center justify-center gap-2 hover:bg-blue-50 transition-colors"
              >
                <Navigation size={18} />
                Usar Mi Ubicación Actual
              </button>

              {/* Selected Address Preview */}
              {homeAddressForm.address && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
                    <div className="flex-1">
                      <p className="font-medium text-green-900">{homeAddressForm.address}</p>
                      {(homeAddressForm.city || homeAddressForm.state) && (
                        <p className="text-sm text-green-700 mt-1">
                          {[homeAddressForm.city, homeAddressForm.state].filter(Boolean).join(', ')}
                        </p>
                      )}
                      {homeAddressForm.latitude && homeAddressForm.longitude && (
                        <p className="text-xs text-green-600 mt-2">
                          Coordenadas: {homeAddressForm.latitude.toFixed(6)}, {homeAddressForm.longitude.toFixed(6)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowHomeAddressModal(false);
                  setAddressSearch('');
                  setHomeAddressForm({ address: '', city: '', state: '', latitude: null, longitude: null });
                }}
                className="btn btn-outline flex-1"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveHomeAddress}
                disabled={savingHomeAddress || !homeAddressForm.address}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {savingHomeAddress ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Guardando...
                  </>
                ) : (
                  'Guardar Dirección'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
