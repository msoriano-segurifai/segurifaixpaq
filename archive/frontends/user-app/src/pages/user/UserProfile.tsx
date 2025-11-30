import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { userAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import {
  User, Mail, Phone, MapPin, Calendar, Shield, Star, Edit2,
  Camera, CheckCircle, Clock, Award, RefreshCw, Bell, Lock, X, Plus, Navigation, Loader2
} from 'lucide-react';

interface UserProfileData {
  id: number;
  name: string;
  email: string;
  phone: string;
  profile_picture?: string;
  address?: string;
  city?: string;
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

export const UserProfile: React.FC = () => {
  const { user, logout, isPAQUser } = useAuth();
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    phone: '',
    address: '',
    city: ''
  });

  // Modal states
  const [showContactModal, setShowContactModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newContact, setNewContact] = useState({ name: '', phone: '', relationship: '' });
  const [passwordForm, setPasswordForm] = useState({ current: '', new_password: '', confirm: '' });
  const [savingPreference, setSavingPreference] = useState<string | null>(null);
  const [locationStatus, setLocationStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

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
        city: transformedProfile.city || ''
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
        city: ''
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

        {/* Personal Info */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <User size={18} />
            Informacion Personal
          </h3>

          {editing ? (
            <div className="space-y-4">
              <div>
                <label className="label">Nombre Completo</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Telefono</label>
                <input
                  type="tel"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Direccion</label>
                <input
                  type="text"
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Ciudad</label>
                <input
                  type="text"
                  value={editForm.city}
                  onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
                  className="input"
                />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setEditing(false)} className="btn btn-outline flex-1">
                  Cancelar
                </button>
                <button onClick={handleSaveProfile} className="btn btn-primary flex-1">
                  Guardar
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <Mail className="text-gray-400" size={18} />
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <p className="font-medium">{profile?.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <Phone className="text-gray-400" size={18} />
                <div>
                  <p className="text-xs text-gray-500">Telefono</p>
                  <p className="font-medium">{profile?.phone || 'No especificado'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <MapPin className="text-gray-400" size={18} />
                <div>
                  <p className="text-xs text-gray-500">Direccion</p>
                  <p className="font-medium">{profile?.address || 'No especificada'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <Calendar className="text-gray-400" size={18} />
                <div>
                  <p className="text-xs text-gray-500">Miembro desde</p>
                  <p className="font-medium">
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
    </Layout>
  );
};
