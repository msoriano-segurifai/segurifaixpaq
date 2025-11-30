import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI, assistanceAPI, mapsAPI } from '../../services/api';
import {
  MapPin, Truck, Heart, Home, Shield, Phone, AlertTriangle,
  Navigation, CheckCircle, Loader2, Clock, Car, AlertCircle
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
  const [userSubscriptions, setUserSubscriptions] = useState<any[]>([]);
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [validatingVehicle, setValidatingVehicle] = useState(false);
  const [vehicleValidation, setVehicleValidation] = useState<any>(null);
  const [validatingHealth, setValidatingHealth] = useState(false);
  const [healthValidation, setHealthValidation] = useState<any>(null);
  const [location, setLocation] = useState<{ lat: number; lng: number; address: string } | null>(null);
  const [locating, setLocating] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    phone: '',
    location_address: '',
    location_city: 'Guatemala City',
    location_state: 'Guatemala',
    location_latitude: 0,
    location_longitude: 0,
    priority: 'MEDIUM',
    // Vehicle information (for roadside assistance)
    vehicle_make: '',
    vehicle_model: '',
    vehicle_year: '',
    vehicle_color: '',
    vehicle_plate: '',
    vehicle_vin: '',
    // Health questionnaire (for health assistance)
    health_emergency_type: '',
    health_symptoms: [] as string[],
    health_other_symptoms: '',
    health_patient_age: '',
    health_patient_gender: '',
    health_pre_existing_conditions: '',
    health_medications: '',
    health_people_affected: '1',
    health_consciousness_level: 'CONSCIOUS',
    health_breathing_difficulty: false,
    health_chest_pain: false,
    health_bleeding: false,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [categoriesRes, subscriptionsRes] = await Promise.all([
        servicesAPI.getCategories(),
        servicesAPI.getMySubscriptions()
      ]);

      const categoriesData = categoriesRes.data.categories || categoriesRes.data;
      setCategories(Array.isArray(categoriesData) ? categoriesData : []);

      const subsData = subscriptionsRes.data.subscriptions || subscriptionsRes.data;
      setUserSubscriptions(Array.isArray(subsData) ? subsData : []);
    } catch (error) {
      console.error('Failed to load data:', error);
      setCategories([]);
      setUserSubscriptions([]);
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
            location_address: response.data.formatted_address || 'Ubicacion actual',
            location_state: prev.location_state || 'Guatemala'
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

  const validateVehicleInfo = async () => {
    setValidatingVehicle(true);
    try {
      const response = await assistanceAPI.validateVehicle({
        make: formData.vehicle_make,
        model: formData.vehicle_model,
        year: formData.vehicle_year,
        plate: formData.vehicle_plate,
        color: formData.vehicle_color,
        vin: formData.vehicle_vin
      });

      setVehicleValidation(response.data);

      if (response.data.validation_status === 'APPROVED' || response.data.validation_status === 'PENDING_REVIEW') {
        setStep(4);
      }
    } catch (error: any) {
      console.error('Vehicle validation error:', error);
      setVehicleValidation({
        validation_status: 'FAILED',
        validation_message: error.response?.data?.error || 'Error al validar información del vehículo'
      });
    } finally {
      setValidatingVehicle(false);
    }
  };

  const isRoadsideAssistance = () => {
    const selectedCat = categories.find(c => c.id === selectedCategory);
    return selectedCat?.category_type?.toUpperCase() === 'ROADSIDE' ||
           selectedCat?.category_type?.toUpperCase() === 'VEHICULAR';
  };

  const isHealthAssistance = () => {
    const selectedCat = categories.find(c => c.id === selectedCategory);
    return selectedCat?.category_type?.toUpperCase() === 'HEALTH' ||
           selectedCat?.category_type?.toUpperCase() === 'MEDICAL';
  };

  const validateHealthQuestionnaire = async () => {
    setValidatingHealth(true);
    try {
      // Build description from questionnaire
      const symptoms = formData.health_symptoms.join(', ');
      const otherSymptoms = formData.health_other_symptoms ? ` (Otros: ${formData.health_other_symptoms})` : '';

      const questionnaireData = {
        emergency_type: formData.health_emergency_type,
        symptoms: `${symptoms}${otherSymptoms}`,
        patient_age: formData.health_patient_age,
        patient_gender: formData.health_patient_gender,
        consciousness_level: formData.health_consciousness_level,
        breathing_difficulty: formData.health_breathing_difficulty,
        chest_pain: formData.health_chest_pain,
        bleeding: formData.health_bleeding,
        pre_existing_conditions: formData.health_pre_existing_conditions,
        medications: formData.health_medications,
        people_affected: formData.health_people_affected,
      };

      const response = await assistanceAPI.validateHealth(questionnaireData);

      setHealthValidation(response.data);

      // Auto-generate description from questionnaire
      const autoDescription = `Tipo de emergencia: ${formData.health_emergency_type}. Síntomas: ${symptoms}${otherSymptoms}. Paciente: ${formData.health_patient_gender}, ${formData.health_patient_age} años. Nivel de conciencia: ${formData.health_consciousness_level}. ${formData.health_breathing_difficulty ? 'Dificultad respiratoria. ' : ''}${formData.health_chest_pain ? 'Dolor de pecho. ' : ''}${formData.health_bleeding ? 'Sangrado. ' : ''}`;

      setFormData(prev => ({ ...prev, description: autoDescription }));

      if (response.data.validation_status === 'APPROVED' || response.data.validation_status === 'PENDING_REVIEW') {
        setStep(4);
      }
    } catch (error: any) {
      console.error('Health validation error:', error);
      setHealthValidation({
        validation_status: 'FAILED',
        validation_message: error.response?.data?.error || 'Error al validar información de salud'
      });
    } finally {
      setValidatingHealth(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedCategory) return;
    setSubmitting(true);

    try {
      // Find user subscription that matches the selected category
      const selectedCat = categories.find(c => c.id === selectedCategory);
      const categoryType = selectedCat?.category_type?.toUpperCase() || '';

      // Map category types to possible plan name keywords
      const categoryKeywords: Record<string, string[]> = {
        'ROADSIDE': ['drive', 'roadside', 'vial', 'vehicular', 'auto', 'carro'],
        'VEHICULAR': ['drive', 'roadside', 'vial', 'vehicular', 'auto', 'carro'],
        'HEALTH': ['health', 'salud', 'medical', 'medica'],
        'MEDICAL': ['health', 'salud', 'medical', 'medica'],
        'HOME': ['home', 'hogar', 'casa'],
        'LEGAL': ['legal', 'juridico', 'juridica'],
      };

      const keywords = categoryKeywords[categoryType] || [categoryType.toLowerCase()];

      const matchingSubscription = userSubscriptions.find(sub => {
        if (sub.status !== 'ACTIVE') return false;
        const planName = sub.plan_name?.toLowerCase() || '';
        const category = sub.category?.toLowerCase() || '';
        return keywords.some(keyword => planName.includes(keyword) || category.includes(keyword));
      });

      if (!matchingSubscription) {
        alert('No tienes una suscripción activa para este tipo de servicio. Por favor, suscríbete primero.');
        setSubmitting(false);
        return;
      }

      const requestData: any = {
        ...formData,
        service_category: selectedCategory,
        user_service: matchingSubscription.id,
        incident_type: selectedCat?.category_type || 'OTHER',
      };

      // Add vehicle info if roadside assistance
      if (isRoadsideAssistance()) {
        requestData.vehicle_info = {
          make: formData.vehicle_make,
          model: formData.vehicle_model,
          year: formData.vehicle_year,
          plate: formData.vehicle_plate,
          color: formData.vehicle_color,
          vin: formData.vehicle_vin,
          validation_status: vehicleValidation?.validation_status,
          validation_id: vehicleValidation?.id
        };
      }

      // Add health questionnaire info if health assistance
      if (isHealthAssistance()) {
        requestData.health_info = {
          emergency_type: formData.health_emergency_type,
          symptoms: formData.health_symptoms.join(', ') + (formData.health_other_symptoms ? ` (Otros: ${formData.health_other_symptoms})` : ''),
          patient_age: formData.health_patient_age,
          patient_gender: formData.health_patient_gender,
          consciousness_level: formData.health_consciousness_level,
          breathing_difficulty: formData.health_breathing_difficulty,
          chest_pain: formData.health_chest_pain,
          bleeding: formData.health_bleeding,
          pre_existing_conditions: formData.health_pre_existing_conditions,
          medications: formData.health_medications,
          people_affected: formData.health_people_affected,
          validation_status: healthValidation?.validation_status,
          validation_id: healthValidation?.id
        };
      }

      const response = await assistanceAPI.createRequest(requestData);

      // Get the created request ID from response
      const createdRequestId = response.data?.id || response.data?.request?.id;

      if (vehicleValidation?.validation_status === 'PENDING_REVIEW') {
        alert('Solicitud creada! Tu información vehicular está en revisión por un agente MAWDY. Te notificaremos pronto.');
      } else if (healthValidation?.validation_status === 'PENDING_REVIEW') {
        alert('Solicitud creada! Tu información médica está en revisión por un agente MAWDY. Te contactaremos pronto.');
      } else {
        alert('Solicitud creada exitosamente! Te contactaremos pronto.');
      }

      // Navigate to request details/tracking page if we have an ID
      if (createdRequestId) {
        navigate(`/app/requests/${createdRequestId}`);
      } else {
        navigate('/app/requests');
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error ||
                      error.response?.data?.detail ||
                      JSON.stringify(error.response?.data) ||
                      'Error al crear solicitud';
      alert(errorMsg);
      console.error('Error creating request:', error.response?.data);
    } finally {
      setSubmitting(false);
    }
  };

  const getCategoryIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'roadside':
      case 'vehicular':
        return <Truck className="text-red-500" size={32} />;
      case 'health':
        return <Heart className="text-pink-500" size={32} />;
      case 'home':
        return <Home className="text-blue-500" size={32} />;
      case 'legal':
        return <Shield className="text-purple-500" size={32} />;
      default:
        return <AlertTriangle className="text-orange-500" size={32} />;
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
        <div className="flex items-center justify-center gap-2 overflow-x-auto pb-2">
          {[
            { num: 1, label: 'Servicio' },
            { num: 2, label: 'Ubicación' },
            ...(isRoadsideAssistance() ? [{ num: 3, label: 'Vehículo' }] : []),
            ...(isHealthAssistance() ? [{ num: 3, label: 'Salud' }] : []),
            { num: isRoadsideAssistance() || isHealthAssistance() ? 4 : 3, label: 'Detalles' },
            { num: isRoadsideAssistance() || isHealthAssistance() ? 5 : 4, label: 'Confirmar' }
          ].map((s, idx, arr) => (
            <React.Fragment key={s.num}>
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${
                  step >= s.num ? 'bg-blue-600 text-white shadow-lg' : 'bg-gray-200 text-gray-500'
                }`}>
                  {step > s.num ? <CheckCircle size={20} /> : s.num}
                </div>
                <span className={`text-xs mt-1 whitespace-nowrap ${step >= s.num ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                  {s.label}
                </span>
              </div>
              {idx < arr.length - 1 && <div className={`w-8 h-1 mt-[-20px] ${step > s.num ? 'bg-blue-600' : 'bg-gray-200'}`} />}
            </React.Fragment>
          ))}
        </div>

        {/* Step 1: Select Category */}
        {step === 1 && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4">¿Qué tipo de asistencia necesitas?</h2>
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
            <h2 className="text-lg font-bold mb-4">¿Dónde te encuentras?</h2>

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
                  {locating ? 'Obteniendo ubicación...' : 'Usar mi ubicación actual'}
                </span>
              </div>
            </button>

            {location && (
              <div className="p-4 bg-green-50 rounded-xl mb-4 flex items-start gap-3">
                <MapPin className="text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <p className="font-medium text-green-800">Ubicación detectada</p>
                  <p className="text-sm text-green-600">{location.address}</p>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="label">Dirección *</label>
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
                Atrás
              </button>
              <button
                onClick={() => setStep(isRoadsideAssistance() ? 3 : 3)}
                disabled={!formData.location_address}
                className="btn btn-primary flex-1"
              >
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Health Questionnaire (Only for Health Assistance) */}
        {step === 3 && isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-pink-100 rounded-xl">
                  <Heart className="text-pink-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Cuestionario de Emergencia Médica</h2>
                  <p className="text-sm text-gray-600">Ayúdanos a entender tu situación para brindarte la mejor asistencia</p>
                </div>
              </div>
            </div>

            <div className="space-y-5">
              {/* Emergency Type */}
              <div>
                <label className="label">Tipo de emergencia *</label>
                <select
                  value={formData.health_emergency_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_emergency_type: e.target.value }))}
                  className="input"
                >
                  <option value="">Selecciona el tipo de emergencia</option>
                  <option value="ACCIDENTE">Accidente</option>
                  <option value="ENFERMEDAD_REPENTINA">Enfermedad repentina</option>
                  <option value="DOLOR_CRONICO">Dolor crónico</option>
                  <option value="LESION">Lesión</option>
                  <option value="DIFICULTAD_RESPIRATORIA">Dificultad respiratoria</option>
                  <option value="PROBLEMA_CARDIACO">Problema cardíaco</option>
                  <option value="INTOXICACION">Intoxicación</option>
                  <option value="OTRO">Otro</option>
                </select>
              </div>

              {/* Critical Symptoms Checkboxes */}
              <div className="p-4 bg-red-50 border-2 border-red-200 rounded-xl">
                <label className="label text-red-900 mb-3">Síntomas críticos (marcar si aplica)</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.health_breathing_difficulty}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_breathing_difficulty: e.target.checked }))}
                      className="w-5 h-5 text-red-600 rounded"
                    />
                    <span className="font-medium text-red-900">Dificultad para respirar</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.health_chest_pain}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_chest_pain: e.target.checked }))}
                      className="w-5 h-5 text-red-600 rounded"
                    />
                    <span className="font-medium text-red-900">Dolor de pecho</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.health_bleeding}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_bleeding: e.target.checked }))}
                      className="w-5 h-5 text-red-600 rounded"
                    />
                    <span className="font-medium text-red-900">Sangrado severo</span>
                  </label>
                </div>
              </div>

              {/* Main Symptoms */}
              <div>
                <label className="label">Síntomas principales *</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    'Dolor', 'Fiebre', 'Náuseas', 'Mareo', 'Vómito', 'Diarrea',
                    'Debilidad', 'Confusión', 'Convulsiones', 'Pérdida de conciencia'
                  ].map((symptom) => (
                    <label key={symptom} className="flex items-center gap-2 cursor-pointer p-2 hover:bg-gray-50 rounded">
                      <input
                        type="checkbox"
                        checked={formData.health_symptoms.includes(symptom)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData(prev => ({ ...prev, health_symptoms: [...prev.health_symptoms, symptom] }));
                          } else {
                            setFormData(prev => ({ ...prev, health_symptoms: prev.health_symptoms.filter(s => s !== symptom) }));
                          }
                        }}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <span className="text-sm">{symptom}</span>
                    </label>
                  ))}
                </div>
                <textarea
                  value={formData.health_other_symptoms}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_other_symptoms: e.target.value }))}
                  className="input mt-2"
                  rows={2}
                  placeholder="Otros síntomas no listados..."
                />
              </div>

              {/* Patient Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Edad del paciente *</label>
                  <input
                    type="number"
                    value={formData.health_patient_age}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_patient_age: e.target.value }))}
                    className="input"
                    placeholder="Ej: 45"
                    min="0"
                    max="120"
                  />
                </div>
                <div>
                  <label className="label">Género *</label>
                  <select
                    value={formData.health_patient_gender}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_patient_gender: e.target.value }))}
                    className="input"
                  >
                    <option value="">Seleccionar</option>
                    <option value="MASCULINO">Masculino</option>
                    <option value="FEMENINO">Femenino</option>
                    <option value="OTRO">Otro</option>
                  </select>
                </div>
              </div>

              {/* Consciousness Level */}
              <div>
                <label className="label">Nivel de conciencia *</label>
                <select
                  value={formData.health_consciousness_level}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_consciousness_level: e.target.value }))}
                  className="input"
                >
                  <option value="CONSCIOUS">Consciente y alerta</option>
                  <option value="DROWSY">Somnoliento pero responde</option>
                  <option value="CONFUSED">Confundido</option>
                  <option value="UNCONSCIOUS">Inconsciente</option>
                </select>
              </div>

              {/* Pre-existing Conditions */}
              <div>
                <label className="label">Condiciones preexistentes</label>
                <textarea
                  value={formData.health_pre_existing_conditions}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_pre_existing_conditions: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Ej: Diabetes, hipertensión, asma..."
                />
              </div>

              {/* Current Medications */}
              <div>
                <label className="label">Medicamentos actuales</label>
                <textarea
                  value={formData.health_medications}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_medications: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Medicamentos que toma regularmente..."
                />
              </div>

              {/* Number of People Affected */}
              <div>
                <label className="label">Número de personas afectadas</label>
                <select
                  value={formData.health_people_affected}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_people_affected: e.target.value }))}
                  className="input"
                >
                  <option value="1">1 persona</option>
                  <option value="2">2 personas</option>
                  <option value="3">3 personas</option>
                  <option value="4+">4 o más personas</option>
                </select>
              </div>

              {/* Validation Result */}
              {healthValidation && (
                <div className={`p-4 rounded-xl border-2 ${
                  healthValidation.validation_status === 'APPROVED'
                    ? 'bg-green-50 border-green-300'
                    : healthValidation.validation_status === 'PENDING_REVIEW'
                    ? healthValidation.urgency_level === 'CRITICAL'
                      ? 'bg-red-50 border-red-400'
                      : healthValidation.urgency_level === 'HIGH'
                      ? 'bg-orange-50 border-orange-300'
                      : 'bg-yellow-50 border-yellow-300'
                    : 'bg-red-50 border-red-300'
                }`}>
                  <div className="flex items-start gap-3">
                    {healthValidation.validation_status === 'APPROVED' && (
                      <>
                        <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                        <div>
                          <p className="font-bold text-green-900">✓ Información Validada</p>
                          {healthValidation.urgency_level && (
                            <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-bold ${
                              healthValidation.urgency_level === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                              healthValidation.urgency_level === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                              healthValidation.urgency_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>
                              Urgencia: {healthValidation.urgency_level}
                            </span>
                          )}
                          <p className="text-sm text-green-700 mt-1">{healthValidation.validation_message}</p>
                        </div>
                      </>
                    )}
                    {healthValidation.validation_status === 'PENDING_REVIEW' && (
                      <>
                        <AlertCircle className={`flex-shrink-0 ${
                          healthValidation.urgency_level === 'CRITICAL' ? 'text-red-600' :
                          healthValidation.urgency_level === 'HIGH' ? 'text-orange-600' :
                          'text-yellow-600'
                        }`} size={24} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className={`font-bold ${
                              healthValidation.urgency_level === 'CRITICAL' ? 'text-red-900' :
                              healthValidation.urgency_level === 'HIGH' ? 'text-orange-900' :
                              'text-yellow-900'
                            }`}>
                              {healthValidation.urgency_level === 'CRITICAL' ? '🚨 EMERGENCIA CRÍTICA - Agente Notificado' :
                               healthValidation.urgency_level === 'HIGH' ? '⚠️ Alta Urgencia - Revisión Prioritaria' :
                               '⏳ Revisión de Agente MAWDY Requerida'}
                            </p>
                            {healthValidation.urgency_level && (
                              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                                healthValidation.urgency_level === 'CRITICAL' ? 'bg-red-200 text-red-800 animate-pulse' :
                                healthValidation.urgency_level === 'HIGH' ? 'bg-orange-200 text-orange-800' :
                                healthValidation.urgency_level === 'MEDIUM' ? 'bg-yellow-200 text-yellow-800' :
                                'bg-blue-200 text-blue-800'
                              }`}>
                                {healthValidation.urgency_level}
                              </span>
                            )}
                          </div>
                          <p className={`text-sm mt-1 ${
                            healthValidation.urgency_level === 'CRITICAL' ? 'text-red-700' :
                            healthValidation.urgency_level === 'HIGH' ? 'text-orange-700' :
                            'text-yellow-700'
                          }`}>
                            {healthValidation.validation_message || 'Un agente médico MAWDY revisará tu caso.'}
                          </p>
                          {healthValidation.urgency_level === 'CRITICAL' && (
                            <div className="mt-3 p-3 bg-red-100 rounded-lg">
                              <p className="text-sm text-red-800 font-medium">
                                📞 Si la situación empeora, llama directamente:
                              </p>
                              <a href="tel:+50212345678" className="text-lg font-bold text-red-900 hover:underline">
                                +502 1234-5678
                              </a>
                            </div>
                          )}
                          <p className={`text-xs mt-2 ${
                            healthValidation.urgency_level === 'CRITICAL' ? 'text-red-600' :
                            healthValidation.urgency_level === 'HIGH' ? 'text-orange-600' :
                            'text-yellow-600'
                          }`}>
                            {healthValidation.urgency_level === 'CRITICAL'
                              ? 'Tu solicitud ha sido escalada. Un profesional te contactará en los próximos minutos.'
                              : 'Puedes continuar con tu solicitud. Un profesional evaluará tu situación.'}
                          </p>
                        </div>
                      </>
                    )}
                    {healthValidation.validation_status === 'FAILED' && (
                      <>
                        <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                        <div>
                          <p className="font-bold text-red-900">✗ Error en Validación</p>
                          <p className="text-sm text-red-700 mt-1">{healthValidation.validation_message}</p>
                          <p className="text-xs text-red-600 mt-2">Por favor, verifica la información e intenta de nuevo.</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => {
                  // If already validated, proceed to next step
                  if (healthValidation && (healthValidation.validation_status === 'APPROVED' || healthValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    // Auto-validate with AI
                    validateHealthQuestionnaire();
                  }
                }}
                disabled={
                  !formData.health_emergency_type ||
                  formData.health_symptoms.length === 0 ||
                  !formData.health_patient_age ||
                  !formData.health_patient_gender ||
                  validatingHealth
                }
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingHealth ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Validando con IA...
                  </>
                ) : healthValidation && (healthValidation.validation_status === 'APPROVED' || healthValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Continuar'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Vehicle Info (Only for Roadside Assistance) */}
        {step === 3 && isRoadsideAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-blue-100 rounded-xl">
                  <Car className="text-blue-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Información del Vehículo</h2>
                  <p className="text-sm text-gray-600">Necesitamos validar tu vehículo para brindarte el mejor servicio</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Marca *</label>
                  <input
                    type="text"
                    value={formData.vehicle_make}
                    onChange={(e) => setFormData(prev => ({ ...prev, vehicle_make: e.target.value }))}
                    className="input"
                    placeholder="Ej: Toyota"
                  />
                </div>
                <div>
                  <label className="label">Modelo *</label>
                  <input
                    type="text"
                    value={formData.vehicle_model}
                    onChange={(e) => setFormData(prev => ({ ...prev, vehicle_model: e.target.value }))}
                    className="input"
                    placeholder="Ej: Corolla"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Año *</label>
                  <input
                    type="text"
                    value={formData.vehicle_year}
                    onChange={(e) => setFormData(prev => ({ ...prev, vehicle_year: e.target.value }))}
                    className="input"
                    placeholder="Ej: 2020"
                    maxLength={4}
                  />
                </div>
                <div>
                  <label className="label">Color</label>
                  <input
                    type="text"
                    value={formData.vehicle_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, vehicle_color: e.target.value }))}
                    className="input"
                    placeholder="Ej: Blanco"
                  />
                </div>
              </div>

              <div>
                <label className="label">Placa *</label>
                <input
                  type="text"
                  value={formData.vehicle_plate}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_plate: e.target.value.toUpperCase() }))}
                  className="input"
                  placeholder="Ej: P-123ABC"
                />
              </div>

              <div>
                <label className="label">VIN (Opcional)</label>
                <input
                  type="text"
                  value={formData.vehicle_vin}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_vin: e.target.value.toUpperCase() }))}
                  className="input"
                  placeholder="Número de identificación vehicular (17 dígitos)"
                  maxLength={17}
                />
                <p className="text-xs text-gray-500 mt-1">El VIN ayuda a una validación más rápida</p>
              </div>

              {/* Validation Result */}
              {vehicleValidation && (
                <div className={`p-4 rounded-xl border-2 ${
                  vehicleValidation.validation_status === 'APPROVED'
                    ? 'bg-green-50 border-green-300'
                    : vehicleValidation.validation_status === 'PENDING_REVIEW'
                    ? 'bg-yellow-50 border-yellow-300'
                    : 'bg-red-50 border-red-300'
                }`}>
                  <div className="flex items-start gap-3">
                    {vehicleValidation.validation_status === 'APPROVED' && (
                      <>
                        <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                        <div>
                          <p className="font-bold text-green-900">✓ Vehículo Validado por IA</p>
                          {vehicleValidation.confidence_score && (
                            <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-bold bg-green-100 text-green-700">
                              Confianza: {Math.round(vehicleValidation.confidence_score * 100)}%
                            </span>
                          )}
                          <p className="text-sm text-green-700 mt-1">{vehicleValidation.validation_message}</p>
                        </div>
                      </>
                    )}
                    {vehicleValidation.validation_status === 'PENDING_REVIEW' && (
                      <>
                        <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                        <div className="flex-1">
                          <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY en Proceso</p>
                          <p className="text-sm text-yellow-700 mt-1">
                            {vehicleValidation.validation_message || 'La IA no pudo validar automáticamente. Un agente MAWDY revisará tu información.'}
                          </p>
                          <div className="mt-3 p-3 bg-yellow-100 rounded-lg">
                            <p className="text-xs text-yellow-800">
                              <strong>¿Por qué requiere revisión?</strong> Esto puede ocurrir si:
                            </p>
                            <ul className="text-xs text-yellow-700 mt-1 list-disc list-inside">
                              <li>La combinación marca/modelo/año es poco común</li>
                              <li>El formato de placa es atípico</li>
                              <li>Se necesita verificación adicional</li>
                            </ul>
                          </div>
                          <p className="text-xs text-yellow-600 mt-2">
                            ✓ Puedes continuar con tu solicitud. Te notificaremos cuando se complete la revisión.
                          </p>
                        </div>
                      </>
                    )}
                    {vehicleValidation.validation_status === 'FAILED' && (
                      <>
                        <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                        <div>
                          <p className="font-bold text-red-900">✗ Validación Fallida</p>
                          <p className="text-sm text-red-700 mt-1">{vehicleValidation.validation_message}</p>
                          <p className="text-xs text-red-600 mt-2">Por favor, verifica la información del vehículo e intenta de nuevo.</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => {
                  if (vehicleValidation && (vehicleValidation.validation_status === 'APPROVED' || vehicleValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateVehicleInfo();
                  }
                }}
                disabled={
                  !formData.vehicle_make ||
                  !formData.vehicle_model ||
                  !formData.vehicle_year ||
                  !formData.vehicle_plate ||
                  validatingVehicle
                }
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingVehicle ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Validando con IA...
                  </>
                ) : vehicleValidation && (vehicleValidation.validation_status === 'APPROVED' || vehicleValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Validar Vehículo'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3/4: Details */}
        {step === (isRoadsideAssistance() || isHealthAssistance() ? 4 : 3) && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4">Detalles de la solicitud</h2>

            <div className="space-y-4">
              <div>
                <label className="label">Describe tu emergencia *</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="input min-h-[100px]"
                  placeholder="Describe brevemente lo que necesitas..."
                />
              </div>

              <div>
                <label className="label">Teléfono de contacto *</label>
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

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(isRoadsideAssistance() || isHealthAssistance() ? 3 : 2)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => setStep(isRoadsideAssistance() || isHealthAssistance() ? 5 : 4)}
                disabled={!formData.description || !formData.phone}
                className="btn btn-primary flex-1"
              >
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Step 4/5: Confirmation */}
        {step === (isRoadsideAssistance() || isHealthAssistance() ? 5 : 4) && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Shield className="text-green-600" />
              Confirma tu solicitud
            </h2>

            {/* Order Summary */}
            <div className="space-y-4 mb-6">
              {/* Service Details */}
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{categories.find(c => c.id === selectedCategory)?.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{formData.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Incluido en plan</p>
                    <p className="text-2xl font-bold text-green-700">Q0</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-blue-700">
                  <MapPin size={14} />
                  <span className="truncate">{formData.location_address}</span>
                </div>
              </div>

              {/* Vehicle Info (if roadside) */}
              {isRoadsideAssistance() && (
                <div className="p-4 bg-white border-2 border-blue-200 rounded-xl">
                  <h4 className="font-bold mb-3 flex items-center gap-2">
                    <Car className="text-blue-600" size={18} />
                    Información del Vehículo
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Vehículo:</span>
                      <p className="font-medium">{formData.vehicle_year} {formData.vehicle_make} {formData.vehicle_model}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Placa:</span>
                      <p className="font-medium">{formData.vehicle_plate}</p>
                    </div>
                    {formData.vehicle_color && (
                      <div>
                        <span className="text-gray-600">Color:</span>
                        <p className="font-medium">{formData.vehicle_color}</p>
                      </div>
                    )}
                    {vehicleValidation && (
                      <div className="col-span-2">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                          vehicleValidation.validation_status === 'APPROVED'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {vehicleValidation.validation_status === 'APPROVED' && '✓ Validado por IA'}
                          {vehicleValidation.validation_status === 'PENDING_REVIEW' && '⏳ Revisión MAWDY en proceso'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Health Info (if health assistance) */}
              {isHealthAssistance() && (
                <div className={`p-4 bg-white border-2 rounded-xl ${
                  healthValidation?.urgency_level === 'CRITICAL' ? 'border-red-300' :
                  healthValidation?.urgency_level === 'HIGH' ? 'border-orange-300' :
                  'border-pink-200'
                }`}>
                  <h4 className="font-bold mb-3 flex items-center gap-2">
                    <Heart className="text-pink-600" size={18} />
                    Información de Emergencia Médica
                    {healthValidation?.urgency_level && (
                      <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-bold ${
                        healthValidation.urgency_level === 'CRITICAL' ? 'bg-red-100 text-red-700 animate-pulse' :
                        healthValidation.urgency_level === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                        healthValidation.urgency_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {healthValidation.urgency_level === 'CRITICAL' ? '🚨 CRÍTICO' :
                         healthValidation.urgency_level === 'HIGH' ? '⚠️ ALTA' :
                         healthValidation.urgency_level === 'MEDIUM' ? 'MEDIA' : 'BAJA'}
                      </span>
                    )}
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Emergencia:</span>
                      <p className="font-medium">{formData.health_emergency_type}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Paciente:</span>
                      <p className="font-medium">{formData.health_patient_gender}, {formData.health_patient_age} años</p>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Síntomas:</span>
                      <p className="font-medium">{formData.health_symptoms.join(', ')}</p>
                    </div>
                    {(formData.health_breathing_difficulty || formData.health_chest_pain || formData.health_bleeding) && (
                      <div className="col-span-2 flex flex-wrap gap-2">
                        {formData.health_breathing_difficulty && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">Dificultad Respiratoria</span>
                        )}
                        {formData.health_chest_pain && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">Dolor de Pecho</span>
                        )}
                        {formData.health_bleeding && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">Sangrado</span>
                        )}
                      </div>
                    )}
                    {healthValidation && (
                      <div className="col-span-2 mt-2">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                          healthValidation.validation_status === 'APPROVED'
                            ? 'bg-green-100 text-green-700'
                            : healthValidation.urgency_level === 'CRITICAL'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {healthValidation.validation_status === 'APPROVED' && '✓ Validado'}
                          {healthValidation.validation_status === 'PENDING_REVIEW' && (
                            healthValidation.urgency_level === 'CRITICAL'
                              ? '🚨 Agente MAWDY notificado'
                              : '⏳ Revisión MAWDY en proceso'
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* What to Expect */}
              <div className="p-4 bg-white border-2 border-blue-200 rounded-xl">
                <h4 className="font-bold mb-3 flex items-center gap-2">
                  <Clock className="text-blue-600" size={18} />
                  Qué esperar
                </h4>
                <div className="space-y-2 text-sm text-gray-700">
                  <div className="flex items-start gap-2">
                    <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Técnico asignado en menos de 2 minutos</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Tiempo estimado de llegada: 15-30 minutos</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Tracking en tiempo real de tu técnico</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Servicio profesional garantizado</span>
                  </div>
                </div>
              </div>

              {/* Contact Info */}
              <div className="p-3 bg-blue-50 rounded-lg flex items-center gap-2">
                <Phone className="text-blue-600" size={18} />
                <div className="text-sm">
                  <span className="text-gray-600">Contacto:</span>
                  <span className="font-medium text-blue-900 ml-2">{formData.phone}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button onClick={() => setStep(isRoadsideAssistance() || isHealthAssistance() ? 4 : 3)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <Loader2 className="animate-spin" size={18} />
                ) : (
                  <CheckCircle size={18} />
                )}
                {submitting ? 'Confirmando...' : 'Confirmar Solicitud'}
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
