import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { dispatchAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import {
  User, Star, Truck, DollarSign, Clock, Award, Calendar,
  Phone, Mail, MapPin, Edit2, Camera, CheckCircle, RefreshCw
} from 'lucide-react';

interface TechProfileData {
  id: number;
  name: string;
  email: string;
  phone: string;
  profile_picture?: string;
  tech_type: string;
  is_available: boolean;
  rating: number;
  total_jobs: number;
  completed_jobs: number;
  total_earnings: number;
  current_month_earnings: number;
  avg_response_time: number;
  member_since: string;
  certifications: string[];
  service_areas: string[];
  vehicle_info?: {
    type: string;
    plate: string;
    model: string;
  };
}

export const TechProfile: React.FC = () => {
  const { logout } = useAuth();
  const [profile, setProfile] = useState<TechProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAvailable, setIsAvailable] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await dispatchAPI.getMyProfile();
      setProfile(response.data);
      setIsAvailable(response.data.is_available);
    } catch (error) {
      console.error('Error cargando perfil:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleAvailability = async () => {
    setUpdating(true);
    try {
      if (!isAvailable) {
        // Going online - get current location
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(async (position) => {
            await dispatchAPI.goOnline(position.coords.latitude, position.coords.longitude);
            setIsAvailable(true);
            setUpdating(false);
          });
        }
      } else {
        await dispatchAPI.goOffline();
        setIsAvailable(false);
        setUpdating(false);
      }
    } catch (error) {
      console.error('Error actualizando disponibilidad:', error);
      setUpdating(false);
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
      <div className="space-y-4 pb-8">
        {/* Profile Header */}
        <div className="card bg-gradient-to-r from-red-600 to-red-700 text-white">
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
              <button className="absolute -bottom-1 -right-1 p-2 bg-white rounded-full text-red-600 shadow-lg">
                <Camera size={14} />
              </button>
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold">{profile?.name || 'Tecnico'}</h1>
              <p className="text-red-200">{profile?.tech_type || 'Tecnico de Campo'}</p>
              <div className="flex items-center gap-1 mt-1">
                <Star className="fill-yellow-400 text-yellow-400" size={16} />
                <span className="font-bold">{profile?.rating?.toFixed(1) || '5.0'}</span>
                <span className="text-red-200 text-sm">({profile?.completed_jobs || 0} trabajos)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Availability Toggle */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold">Disponibilidad</h3>
              <p className="text-sm text-gray-500">
                {isAvailable ? 'Estas recibiendo solicitudes' : 'No estas recibiendo solicitudes'}
              </p>
            </div>
            <button
              onClick={toggleAvailability}
              disabled={updating}
              className={`relative w-14 h-8 rounded-full transition-colors ${
                isAvailable ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <div className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow transition-transform ${
                isAvailable ? 'right-1' : 'left-1'
              }`} />
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="card text-center">
            <DollarSign className="mx-auto text-green-600 mb-2" size={28} />
            <p className="text-2xl font-bold">Q{profile?.current_month_earnings || 0}</p>
            <p className="text-sm text-gray-500">Este Mes</p>
          </div>
          <div className="card text-center">
            <Truck className="mx-auto text-blue-600 mb-2" size={28} />
            <p className="text-2xl font-bold">{profile?.completed_jobs || 0}</p>
            <p className="text-sm text-gray-500">Trabajos Completados</p>
          </div>
          <div className="card text-center">
            <Clock className="mx-auto text-orange-600 mb-2" size={28} />
            <p className="text-2xl font-bold">{profile?.avg_response_time || 0} min</p>
            <p className="text-sm text-gray-500">Tiempo Respuesta</p>
          </div>
          <div className="card text-center">
            <DollarSign className="mx-auto text-purple-600 mb-2" size={28} />
            <p className="text-2xl font-bold">Q{profile?.total_earnings || 0}</p>
            <p className="text-sm text-gray-500">Total Historico</p>
          </div>
        </div>

        {/* Contact Info */}
        <div className="card">
          <h3 className="font-bold mb-4 flex items-center gap-2">
            <User size={18} />
            Informacion de Contacto
          </h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
              <Mail className="text-gray-400" size={18} />
              <span>{profile?.email || 'No especificado'}</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
              <Phone className="text-gray-400" size={18} />
              <span>{profile?.phone || 'No especificado'}</span>
            </div>
          </div>
        </div>

        {/* Vehicle Info */}
        {profile?.vehicle_info && (
          <div className="card">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Truck size={18} />
              Informacion del Vehiculo
            </h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Tipo</p>
                <p className="font-bold">{profile.vehicle_info.type}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Placa</p>
                <p className="font-bold">{profile.vehicle_info.plate}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Modelo</p>
                <p className="font-bold">{profile.vehicle_info.model}</p>
              </div>
            </div>
          </div>
        )}

        {/* Certifications */}
        {profile?.certifications && profile.certifications.length > 0 && (
          <div className="card">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Award size={18} />
              Certificaciones
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.certifications.map((cert, i) => (
                <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm flex items-center gap-1">
                  <CheckCircle size={14} />
                  {cert}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Member Since */}
        <div className="card bg-gray-50">
          <div className="flex items-center gap-3">
            <Calendar className="text-gray-400" size={20} />
            <div>
              <p className="text-sm text-gray-500">Miembro desde</p>
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

        {/* Logout Button */}
        <button
          onClick={logout}
          className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
        >
          Cerrar Sesion
        </button>
      </div>
    </Layout>
  );
};
