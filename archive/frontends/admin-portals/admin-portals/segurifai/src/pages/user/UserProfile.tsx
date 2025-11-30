import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { userAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import {
  User, Mail, Phone, MapPin, Calendar, Shield, Star, Edit2,
  Camera, CheckCircle, Clock, Award, RefreshCw, Bell, Lock
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
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    phone: '',
    address: '',
    city: ''
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await userAPI.getProfile();
      setProfile(response.data);
      setEditForm({
        name: response.data.name || '',
        phone: response.data.phone || '',
        address: response.data.address || '',
        city: response.data.city || ''
      });
    } catch (error) {
      // Mock data for demo
      const mockProfile: UserProfileData = {
        id: 1,
        name: user?.first_name + ' ' + user?.last_name || 'Usuario',
        email: user?.email || 'usuario@email.com',
        phone: '+502 5555 1234',
        member_since: new Date().toISOString(),
        active_subscriptions: 2,
        completed_requests: 5,
        total_points: 250,
        level: 3,
        level_name: 'Aprendiz Avanzado',
        emergency_contacts: [
          { id: 1, name: 'Juan Perez', phone: '+502 4444 5555', relationship: 'Familiar' }
        ],
        preferences: {
          notifications_enabled: true,
          sms_alerts: true,
          email_updates: true,
          location_sharing: true
        }
      };
      setProfile(mockProfile);
      setEditForm({
        name: mockProfile.name,
        phone: mockProfile.phone,
        address: mockProfile.address || '',
        city: mockProfile.city || ''
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      await userAPI.updateProfile(editForm);
      await loadProfile();
      setEditing(false);
      alert('Perfil actualizado exitosamente!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al actualizar perfil');
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
            <button className="btn btn-outline btn-sm">Agregar</button>
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

        {/* Preferences */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <Bell size={18} />
            Preferencias
          </h3>
          <div className="space-y-4">
            {[
              { key: 'notifications_enabled', label: 'Notificaciones Push', icon: Bell },
              { key: 'sms_alerts', label: 'Alertas SMS', icon: Phone },
              { key: 'email_updates', label: 'Actualizaciones por Email', icon: Mail },
              { key: 'location_sharing', label: 'Compartir Ubicacion', icon: MapPin }
            ].map((pref) => (
              <div key={pref.key} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <pref.icon className="text-gray-400" size={18} />
                  <span>{pref.label}</span>
                </div>
                <div className={`w-12 h-7 rounded-full transition-colors ${
                  profile?.preferences?.[pref.key as keyof UserPreferences] ? 'bg-blue-500' : 'bg-gray-300'
                }`}>
                  <div className={`w-5 h-5 bg-white rounded-full shadow mt-1 transition-transform ${
                    profile?.preferences?.[pref.key as keyof UserPreferences] ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Security */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <Lock size={18} />
            Seguridad
          </h3>
          <button className="w-full p-3 bg-gray-50 rounded-xl text-left hover:bg-gray-100 transition-colors">
            <div className="flex items-center justify-between">
              <span>Cambiar Contrasena</span>
              <Lock className="text-gray-400" size={18} />
            </div>
          </button>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="w-full py-3 bg-red-50 text-red-600 rounded-xl font-medium hover:bg-red-100 transition-colors"
        >
          Cerrar Sesion
        </button>
      </div>
    </Layout>
  );
};
