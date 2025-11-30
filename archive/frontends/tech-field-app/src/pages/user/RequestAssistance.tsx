import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI, assistanceAPI, mapsAPI } from '../../services/api';
import {
  MapPin, Truck, Heart, Home, Shield, Phone, AlertTriangle,
  Navigation, CheckCircle, Loader2
} from 'lucide-react';

interface ServiceCategory {
  id: number;
  name: string;
  description: string;
  icon: string;
  category_type: string;
}

export const RequestAssistance: React.FC = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [location, setLocation] = useState<{ lat: number; lng: number; address: string } | null>(null);
  const [locating, setLocating] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    phone: '',
    location_address: '',
    location_city: 'Guatemala City',
    location_latitude: 0,
    location_longitude: 0,
    priority: 'MEDIUM',
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await servicesAPI.getCategories();
      setCategories(response.data.categories || response.data || []);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentLocation = () => {
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const response = await mapsAPI.reverseGeocode(latitude, longitude);
          setLocation({
            lat: latitude,
            lng: longitude,
            address: response.data.formatted_address || 'Ubicacion actual'
          });
          setFormData(prev => ({
            ...prev,
            location_latitude: latitude,
            location_longitude: longitude,
            location_address: response.data.formatted_address || 'Ubicacion actual'
          }));
        } catch {
          setLocation({ lat: latitude, lng: longitude, address: 'Ubicacion actual' });
        }
        setLocating(false);
      },
      (error) => {
        console.error('Geolocation error:', error);
        setLocating(false);
        alert('No se pudo obtener tu ubicacion. Por favor ingresa la direccion manualmente.');
      }
    );
  };

  const handleSubmit = async () => {
    if (!selectedCategory) return;
    setSubmitting(true);

    try {
      const response = await assistanceAPI.createRequest({
        ...formData,
        service_category: selectedCategory,
        incident_type: categories.find(c => c.id === selectedCategory)?.category_type || 'OTHER',
      });

      alert('Solicitud creada exitosamente! Te contactaremos pronto.');
      navigate('/app/requests');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al crear solicitud');
    } finally {
      setSubmitting(false);
    }
  };

  const getCategoryIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'vehicular': return <Truck className="text-red-500" size={32} />;
      case 'health': return <Heart className="text-pink-500" size={32} />;
      case 'home': return <Home className="text-blue-500" size={32} />;
      case 'legal': return <Shield className="text-purple-500" size={32} />;
      default: return <AlertTriangle className="text-orange-500" size={32} />;
    }
  };

  return (
    <Layout variant="user">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Solicitar Asistencia</h1>
          <p className="text-gray-500 mt-1">Estamos aqui para ayudarte 24/7</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2">
          {[1, 2, 3].map((s) => (
            <React.Fragment key={s}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {s}
              </div>
              {s < 3 && <div className={`w-16 h-1 ${step > s ? 'bg-blue-600' : 'bg-gray-200'}`} />}
            </React.Fragment>
          ))}
        </div>

        {/* Step 1: Select Category */}
        {step === 1 && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4">¿Que tipo de asistencia necesitas?</h2>
            <div className="grid grid-cols-2 gap-4">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    setSelectedCategory(cat.id);
                    setFormData(prev => ({ ...prev, title: `Asistencia ${cat.name}` }));
                  }}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    selectedCategory === cat.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="mb-2">{getCategoryIcon(cat.category_type)}</div>
                  <h3 className="font-bold">{cat.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{cat.description}</p>
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={!selectedCategory}
              className="btn btn-primary w-full mt-6"
            >
              Continuar
            </button>
          </div>
        )}

        {/* Step 2: Location */}
        {step === 2 && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4">¿Donde te encuentras?</h2>

            <button
              onClick={getCurrentLocation}
              disabled={locating}
              className="w-full p-4 border-2 border-dashed border-blue-300 rounded-xl bg-blue-50 hover:bg-blue-100 transition-colors mb-4"
            >
              <div className="flex items-center justify-center gap-3">
                {locating ? (
                  <Loader2 className="animate-spin text-blue-600" />
                ) : (
                  <Navigation className="text-blue-600" />
                )}
                <span className="font-medium text-blue-700">
                  {locating ? 'Obteniendo ubicacion...' : 'Usar mi ubicacion actual'}
                </span>
              </div>
            </button>

            {location && (
              <div className="p-4 bg-green-50 rounded-xl mb-4 flex items-start gap-3">
                <MapPin className="text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <p className="font-medium text-green-800">Ubicacion detectada</p>
                  <p className="text-sm text-green-600">{location.address}</p>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="label">Direccion</label>
                <input
                  type="text"
                  value={formData.location_address}
                  onChange={(e) => setFormData(prev => ({ ...prev, location_address: e.target.value }))}
                  className="input"
                  placeholder="Ej: 6a Avenida 10-50, Zona 10"
                />
              </div>
              <div>
                <label className="label">Ciudad</label>
                <input
                  type="text"
                  value={formData.location_city}
                  onChange={(e) => setFormData(prev => ({ ...prev, location_city: e.target.value }))}
                  className="input"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(1)} className="btn btn-outline flex-1">
                Atras
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!formData.location_address}
                className="btn btn-primary flex-1"
              >
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Details */}
        {step === 3 && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4">Detalles de la solicitud</h2>

            <div className="space-y-4">
              <div>
                <label className="label">Describe tu emergencia</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="input min-h-[100px]"
                  placeholder="Describe brevemente lo que necesitas..."
                />
              </div>

              <div>
                <label className="label">Telefono de contacto</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    className="input pl-10"
                    placeholder="+502 1234 5678"
                  />
                </div>
              </div>

              <div>
                <label className="label">Prioridad</label>
                <div className="flex gap-2">
                  {[
                    { value: 'LOW', label: 'Baja', color: 'bg-green-100 text-green-700 border-green-300' },
                    { value: 'MEDIUM', label: 'Media', color: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
                    { value: 'HIGH', label: 'Alta', color: 'bg-red-100 text-red-700 border-red-300' },
                  ].map((p) => (
                    <button
                      key={p.value}
                      onClick={() => setFormData(prev => ({ ...prev, priority: p.value }))}
                      className={`flex-1 py-2 px-4 rounded-lg border-2 font-medium transition-all ${
                        formData.priority === p.value ? p.color : 'bg-gray-50 text-gray-500 border-gray-200'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="mt-6 p-4 bg-gray-50 rounded-xl">
              <h3 className="font-medium mb-2">Resumen</h3>
              <div className="text-sm space-y-1 text-gray-600">
                <p>Servicio: {categories.find(c => c.id === selectedCategory)?.name}</p>
                <p>Ubicacion: {formData.location_address}</p>
                <p>Prioridad: {formData.priority}</p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">
                Atras
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || !formData.description}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <Loader2 className="animate-spin" size={18} />
                ) : (
                  <CheckCircle size={18} />
                )}
                {submitting ? 'Enviando...' : 'Enviar Solicitud'}
              </button>
            </div>
          </div>
        )}

        {/* Emergency Contact */}
        <div className="text-center text-sm text-gray-500">
          <p>¿Emergencia inmediata? Llama al</p>
          <a href="tel:+50212345678" className="text-red-600 font-bold text-lg">
            +502 1234 5678
          </a>
        </div>
      </div>
    </Layout>
  );
};
