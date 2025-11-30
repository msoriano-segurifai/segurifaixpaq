import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI, assistanceAPI, mapsAPI } from '../../services/api';
import {
  MapPin, Truck, Heart, Home, Shield, Phone, AlertTriangle,
  Navigation, CheckCircle, Loader2, Clock, Car, AlertCircle,
  Fuel, Key, Zap, Ambulance, User, Plane, Scale, LifeBuoy,
  Stethoscope, Pill, Activity, TestTube, Apple, Brain,
  Package, HeartPulse, Lock, X
} from 'lucide-react';

// Use Car icon as Taxi alias since Taxi is not available in this version
const Taxi = Car;

interface ServiceCategory {
  id: number;
  name: string;
  description: string;
  icon: string;
  category_type: string;
}

// Service flow types
type ServiceFlowType = 'IMMEDIATE' | 'SCHEDULED' | 'CLAIM' | 'CALLBACK';

// MAWDY Service Types - Complete catalog from PDF specifications
interface MAWDYService {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  planType: 'DRIVE' | 'HEALTH';
  limitPerYear: number | null; // null = unlimited
  coverageAmount: number; // in USD
  requiresVehicleInfo?: boolean;
  requiresHealthInfo?: boolean;
  requiresSpecificForm?: boolean;
  formType?: 'vehicle' | 'health' | 'legal' | 'taxi' | 'generic' | 'consultation' | 'video_consultation' | 'lab_exam' | 'medication' | 'delivery';
  // Service flow categorization
  serviceFlow: ServiceFlowType;
  // Follow-up questions for AI chatbot
  followUpQuestions?: string[];
}

const MAWDY_SERVICES: MAWDYService[] = [
  // === PLAN DRIVE (VIAL) SERVICES - $3.15/month ===
  // IMMEDIATE SERVICES - Real-time tracking (food delivery style)
  {
    id: 'tow_truck',
    name: 'Grúa del Vehículo',
    description: 'Servicio de grúa para remolcar tu vehículo a un taller o lugar seguro',
    icon: <Truck className="text-red-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 3,
    coverageAmount: 150,
    requiresVehicleInfo: true,
    formType: 'vehicle',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿El vehículo puede moverse?', '¿Está en lugar seguro?', '¿Tiene las llaves?']
  },
  {
    id: 'fuel_delivery',
    name: 'Abasto de Combustible',
    description: 'Entrega de combustible de emergencia cuando te quedas sin gasolina',
    icon: <Fuel className="text-orange-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: null,
    coverageAmount: 50,
    requiresVehicleInfo: true,
    formType: 'vehicle',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Qué tipo de combustible usa su vehículo?', '¿Está en carretera o ciudad?']
  },
  {
    id: 'tire_change',
    name: 'Cambio de Neumáticos',
    description: 'Asistencia para cambiar neumáticos ponchados en carretera',
    icon: <Car className="text-gray-600" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 3,
    coverageAmount: 150,
    requiresVehicleInfo: true,
    formType: 'vehicle',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Tiene llanta de repuesto?', '¿Cuántas llantas están dañadas?']
  },
  {
    id: 'jump_start',
    name: 'Paso de Corriente',
    description: 'Servicio de arranque con cables cuando la batería está descargada',
    icon: <Zap className="text-yellow-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: null,
    coverageAmount: 50,
    requiresVehicleInfo: true,
    formType: 'vehicle',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Hace cuánto no enciende?', '¿La batería es nueva o vieja?']
  },
  {
    id: 'locksmith_vehicle',
    name: 'Cerrajería Vehicular',
    description: 'Servicio de cerrajero para abrir tu vehículo o hacer llaves',
    icon: <Key className="text-amber-600" size={24} />,
    planType: 'DRIVE',
    limitPerYear: null,
    coverageAmount: 75,
    requiresVehicleInfo: true,
    formType: 'vehicle',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Las llaves están adentro o perdidas?', '¿El vehículo tiene alarma?']
  },
  {
    id: 'ambulance_drive',
    name: 'Ambulancia (Plan Vial)',
    description: 'Traslado de emergencia en ambulancia por accidente vehicular',
    icon: <Ambulance className="text-red-600" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 1,
    coverageAmount: 100,
    requiresHealthInfo: true,
    formType: 'health',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Cuántas personas necesitan traslado?', '¿Hay heridas visibles?', '¿La persona está consciente?']
  },
  // SCHEDULED SERVICES
  {
    id: 'professional_driver',
    name: 'Conductor Profesional',
    description: 'Conductor designado para llevarte a ti y tu vehículo a casa',
    icon: <User className="text-blue-600" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 1,
    coverageAmount: 60,
    requiresVehicleInfo: true,
    formType: 'vehicle',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Para qué fecha y hora lo necesita?', '¿Motivo: enfermedad o consumo de alcohol?']
  },
  {
    id: 'airport_taxi',
    name: 'Taxi al Aeropuerto',
    description: 'Servicio de taxi para llevarte al aeropuerto',
    icon: <Plane className="text-sky-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 1,
    coverageAmount: 60,
    formType: 'taxi',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Fecha y hora del vuelo?', '¿Terminal de salida?', '¿Cuánto equipaje lleva?']
  },
  // CALLBACK SERVICES
  {
    id: 'legal_assistance',
    name: 'Asistencia Legal',
    description: 'Orientación legal telefónica y referencias a abogados',
    icon: <Scale className="text-purple-600" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 1,
    coverageAmount: 200,
    formType: 'legal',
    serviceFlow: 'CALLBACK',
    followUpQuestions: ['¿Es relacionado a un accidente reciente?', '¿Ya presentó denuncia?', '¿Necesita representación legal?']
  },
  // CLAIM SERVICES
  {
    id: 'emergency_support',
    name: 'Apoyo Económico Emergencia',
    description: 'Apoyo económico en caso de accidente grave o fallecimiento',
    icon: <LifeBuoy className="text-red-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 1,
    coverageAmount: 1000,
    formType: 'generic',
    serviceFlow: 'CLAIM',
    followUpQuestions: ['¿Tiene documentación del accidente?', '¿Fue atendido en hospital?']
  },
  {
    id: 'xray_service',
    name: 'Rayos X',
    description: 'Reembolso por servicio de rayos X en caso de lesión por accidente',
    icon: <Activity className="text-cyan-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: 1,
    coverageAmount: 300,
    requiresHealthInfo: true,
    formType: 'lab_exam',
    serviceFlow: 'CLAIM',  // Reembolso - user pays first, then claims reimbursement
    followUpQuestions: ['¿Qué parte del cuerpo se radiografió?', '¿Tiene la factura del servicio?', '¿Tiene orden médica?']
  },
  {
    id: 'network_discounts',
    name: 'Descuentos en Red',
    description: '20% de descuento en servicios de la red MAWDY',
    icon: <CheckCircle className="text-green-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: null,
    coverageAmount: 0,
    formType: 'generic',
    serviceFlow: 'CALLBACK'
  },
  {
    id: 'medical_references',
    name: 'Referencias Médicas',
    description: 'Referencias a especialistas médicos de la red',
    icon: <Stethoscope className="text-teal-500" size={24} />,
    planType: 'DRIVE',
    limitPerYear: null,
    coverageAmount: 0,
    formType: 'generic',
    serviceFlow: 'CALLBACK',
    followUpQuestions: ['¿Qué tipo de especialista necesita?', '¿Tiene diagnóstico previo?']
  },

  // === PLAN HEALTH (SALUD) SERVICES - $2.90/month ===
  // CALLBACK SERVICES
  {
    id: 'medical_orientation',
    name: 'Orientación Médica Telefónica',
    description: 'Consulta médica telefónica 24/7 con profesionales de salud',
    icon: <Phone className="text-green-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: null,
    coverageAmount: 0,
    formType: 'health',
    serviceFlow: 'CALLBACK',
    followUpQuestions: ['¿Cuáles son sus síntomas principales?', '¿Hace cuánto empezaron?']
  },
  {
    id: 'specialist_connection',
    name: 'Conexión con Especialistas',
    description: 'Referencias y citas con médicos especialistas',
    icon: <Stethoscope className="text-blue-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: null,
    coverageAmount: 0,
    formType: 'consultation',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Qué especialidad necesita?', '¿Tiene referencia de médico general?']
  },
  // SCHEDULED SERVICES - Consultations
  {
    id: 'in_person_consultation',
    name: 'Consulta Médica Presencial',
    description: 'Consulta presencial con médico general, ginecólogo o pediatra',
    icon: <HeartPulse className="text-pink-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 3,
    coverageAmount: 150,
    requiresHealthInfo: true,
    formType: 'consultation',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Qué tipo de médico necesita (general, ginecólogo, pediatra)?', '¿Es para usted o familiar?', '¿Fecha preferida para la cita?']
  },
  // DELIVERY SERVICES
  {
    id: 'medication_delivery',
    name: 'Medicamentos a Domicilio',
    description: 'Coordinación de entrega de medicamentos recetados a tu domicilio',
    icon: <Pill className="text-purple-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: null,
    coverageAmount: 50,
    formType: 'medication',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Tiene receta médica?', '¿Qué medicamentos necesita?', '¿Es urgente o puede esperar 24hrs?']
  },
  // CLAIM/SCHEDULED SERVICES - Post hospitalization
  {
    id: 'post_op_care',
    name: 'Cuidados Post-Operatorios',
    description: 'Enfermera a domicilio para el titular después de cirugía',
    icon: <Activity className="text-red-400" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 1,
    coverageAmount: 100,
    requiresHealthInfo: true,
    formType: 'health',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Qué tipo de cirugía tuvo?', '¿Cuándo fue dado de alta?', '¿Qué cuidados específicos necesita?']
  },
  {
    id: 'hygiene_supplies',
    name: 'Artículos de Aseo',
    description: 'Kit de artículos de higiene personal por hospitalización',
    icon: <Package className="text-cyan-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 1,
    coverageAmount: 100,
    formType: 'delivery',
    serviceFlow: 'CLAIM',
    followUpQuestions: ['¿En qué hospital está hospitalizado?', '¿Qué artículos necesita específicamente?']
  },
  // LAB EXAM SERVICES
  {
    id: 'lab_exams',
    name: 'Exámenes de Laboratorio',
    description: 'Análisis clínicos: heces, orina y hematología (grupo familiar)',
    icon: <TestTube className="text-indigo-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 2,
    coverageAmount: 100,
    requiresHealthInfo: true,
    formType: 'lab_exam',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Qué exámenes necesita?', '¿Tiene orden médica?', '¿Es para usted o familiar?']
  },
  {
    id: 'pap_mammogram',
    name: 'Papanicolau/Mamografía/Antígeno',
    description: 'Exámenes especializados: PAP, mamografía o antígeno prostático',
    icon: <Heart className="text-pink-400" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 2,
    coverageAmount: 100,
    requiresHealthInfo: true,
    formType: 'lab_exam',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Qué examen necesita (PAP, mamografía, antígeno)?', '¿Tiene orden médica?', '¿Fecha preferida?']
  },
  // VIDEO CONSULTATION SERVICES
  {
    id: 'nutritionist',
    name: 'Nutricionista (Video)',
    description: 'Video consulta con nutricionista (grupo familiar)',
    icon: <Apple className="text-green-400" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 4,
    coverageAmount: 150,
    formType: 'video_consultation',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Cuál es su objetivo (bajar peso, dieta especial, diabetes)?', '¿Tiene condiciones médicas?']
  },
  {
    id: 'psychology',
    name: 'Psicología (Video)',
    description: 'Video consulta con psicólogo (núcleo familiar)',
    icon: <Brain className="text-violet-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 4,
    coverageAmount: 150,
    formType: 'video_consultation',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿Es primera vez o seguimiento?', '¿Motivo principal de consulta?', '¿Para quién es la consulta?']
  },
  // DELIVERY/IMMEDIATE SERVICES
  {
    id: 'courier_service',
    name: 'Mensajería Hospitalización',
    description: 'Mensajería para documentos o artículos por emergencia hospitalaria',
    icon: <Package className="text-amber-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 2,
    coverageAmount: 60,
    formType: 'delivery',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Qué necesita enviar/recibir?', '¿Dirección de recogida y entrega?']
  },
  // TAXI SERVICES
  {
    id: 'family_taxi',
    name: 'Taxi para Familiar',
    description: 'Transporte para familiar que acompaña al hospital (15km)',
    icon: <Taxi className="text-yellow-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 2,
    coverageAmount: 100,
    formType: 'taxi',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿A qué hospital van?', '¿Cuántos familiares?']
  },
  // AMBULANCE SERVICES
  {
    id: 'ambulance_health',
    name: 'Ambulancia (Plan Salud)',
    description: 'Traslado de emergencia en ambulancia',
    icon: <Ambulance className="text-red-600" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 2,
    coverageAmount: 150,
    requiresHealthInfo: true,
    formType: 'health',
    serviceFlow: 'IMMEDIATE',
    followUpQuestions: ['¿Cuál es la emergencia?', '¿La persona está consciente?', '¿A qué hospital desea ir?']
  },
  {
    id: 'post_discharge_taxi',
    name: 'Taxi Post-Alta',
    description: 'Transporte a casa después del alta hospitalaria',
    icon: <Taxi className="text-green-500" size={24} />,
    planType: 'HEALTH',
    limitPerYear: 1,
    coverageAmount: 100,
    formType: 'taxi',
    serviceFlow: 'SCHEDULED',
    followUpQuestions: ['¿De qué hospital?', '¿Fecha y hora de alta?', '¿Necesita silla de ruedas?']
  },
];

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

  // New state for MAWDY service selection
  const [selectedPlanType, setSelectedPlanType] = useState<'DRIVE' | 'HEALTH' | null>(null);
  const [selectedService, setSelectedService] = useState<MAWDYService | null>(null);
  const [validatingService, setValidatingService] = useState(false);
  const [serviceValidation, setServiceValidation] = useState<any>(null);

  // Additional form data for specific service types
  const [taxiFormData, setTaxiFormData] = useState({
    pickup_location: '',
    destination: '',
    pickup_time: '',
    num_passengers: '1',
    special_needs: '',
  });

  const [legalFormData, setLegalFormData] = useState({
    legal_issue_type: '',
    issue_description: '',
    urgency: 'MEDIUM',
    related_to_accident: false,
  });

  const [genericFormData, setGenericFormData] = useState({
    service_details: '',
    special_requirements: '',
  });

  // Consultation form (in-person doctor visits)
  const [consultationFormData, setConsultationFormData] = useState({
    consultation_type: '', // general, gynecologist, pediatrician, specialist
    specialist_type: '', // if specialist
    patient_type: 'TITULAR', // TITULAR, SPOUSE, CHILD
    patient_name: '',
    patient_age: '',
    reason_for_visit: '',
    symptoms_description: '',
    preferred_date: '',
    preferred_time: 'MORNING', // MORNING, AFTERNOON, EVENING
    has_medical_order: false,
    additional_notes: '',
  });

  // Video consultation form (nutritionist, psychology)
  const [videoConsultationFormData, setVideoConsultationFormData] = useState({
    consultation_type: '', // nutritionist, psychology
    patient_type: 'TITULAR',
    patient_name: '',
    is_first_consultation: true,
    main_reason: '',
    medical_conditions: '',
    preferred_date: '',
    preferred_time: 'MORNING',
    has_stable_internet: true,
    additional_notes: '',
  });

  // Lab exam form
  const [labExamFormData, setLabExamFormData] = useState({
    exam_type: '', // blood, urine, stool, pap, mammogram, prostate_antigen
    patient_type: 'TITULAR',
    patient_name: '',
    patient_age: '',
    has_medical_order: false,
    fasting_required: false,
    preferred_date: '',
    preferred_location: '', // clinic or home (if available)
    special_instructions: '',
  });

  // Medication delivery form
  const [medicationFormData, setMedicationFormData] = useState({
    has_prescription: false,
    prescription_details: '',
    medications_list: '',
    pharmacy_preference: '',
    urgency_level: 'NORMAL', // URGENT, NORMAL
    delivery_address: '',
    delivery_time_preference: '',
    special_instructions: '',
  });

  // Delivery/courier form
  const [deliveryFormData, setDeliveryFormData] = useState({
    delivery_type: '', // documents, supplies, medication
    pickup_address: '',
    delivery_address: '',
    item_description: '',
    urgency_level: 'NORMAL',
    recipient_name: '',
    recipient_phone: '',
    special_instructions: '',
  });

  // Follow-up questions state (for AI-powered questions)
  const [followUpAnswers, setFollowUpAnswers] = useState<Record<string, string>>({});
  const [showFollowUp, setShowFollowUp] = useState(false);

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
    // Road assistance triage fields
    roadside_emergency_type: '',
    roadside_is_safe_location: true,
    roadside_traffic_blocked: false,
    roadside_hazard_lights_on: false,
    roadside_passengers_count: '1',
    roadside_has_spare_tire: false,
    roadside_tire_position: '',
    roadside_battery_age: '',
    roadside_fuel_type: 'REGULAR',
    roadside_fuel_amount: '5',
    roadside_keys_location: '',
    roadside_towing_destination: '',
    roadside_towing_distance: '',
    roadside_additional_details: '',
    // Health questionnaire (for health assistance) - SAMPLE Format
    health_emergency_type: '',
    // S - Signs/Symptoms
    health_symptoms: [] as string[],
    health_other_symptoms: '',
    // A - Allergies
    health_allergies: '',
    health_has_allergies: false,
    // M - Medications
    health_medications: '',
    health_is_on_medications: false,
    // P - Past Medical History
    health_pre_existing_conditions: '',
    health_has_conditions: false,
    // L - Last Oral Intake
    health_last_intake: '',
    health_last_intake_time: '',
    // E - Events Leading Up
    health_events_leading: '',
    // Patient Demographics
    health_patient_age: '',
    health_patient_gender: '',
    health_patient_weight: '',
    health_patient_name: '',
    health_patient_relationship: 'TITULAR',
    health_people_affected: '1',
    // Vitals / Critical Indicators
    health_consciousness_level: 'CONSCIOUS',
    health_breathing_difficulty: false,
    health_chest_pain: false,
    health_bleeding: false,
    health_pain_scale: 0,
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
    // Check based on selected MAWDY service or legacy category
    if (selectedService) {
      return selectedService.requiresVehicleInfo === true;
    }
    const selectedCat = categories.find(c => c.id === selectedCategory);
    return selectedCat?.category_type?.toUpperCase() === 'ROADSIDE' ||
           selectedCat?.category_type?.toUpperCase() === 'VEHICULAR';
  };

  const isHealthAssistance = () => {
    // Check based on selected MAWDY service or legacy category
    if (selectedService) {
      return selectedService.requiresHealthInfo === true;
    }
    const selectedCat = categories.find(c => c.id === selectedCategory);
    return selectedCat?.category_type?.toUpperCase() === 'HEALTH' ||
           selectedCat?.category_type?.toUpperCase() === 'MEDICAL';
  };

  // Check if user has a specific plan type subscription
  const hasPlanType = (planType: 'DRIVE' | 'HEALTH'): boolean => {
    const keywords = planType === 'DRIVE'
      ? ['drive', 'vial', 'roadside', 'vehicular', 'auto']
      : ['health', 'salud', 'medical', 'medica'];

    return userSubscriptions.some(sub => {
      if (sub.status !== 'ACTIVE') return false;
      const planName = (sub.plan_name || sub.plan?.name || '').toLowerCase();
      const category = (sub.category || sub.plan?.category?.name || '').toLowerCase();
      return keywords.some(k => planName.includes(k) || category.includes(k));
    });
  };

  // Get available services based on user's subscriptions
  const getAvailableServices = (planType: 'DRIVE' | 'HEALTH'): MAWDYService[] => {
    if (!hasPlanType(planType)) return [];
    return MAWDY_SERVICES.filter(s => s.planType === planType);
  };

  // Get the subscription that matches a plan type
  const getMatchingSubscription = (planType: 'DRIVE' | 'HEALTH') => {
    const keywords = planType === 'DRIVE'
      ? ['drive', 'vial', 'roadside', 'vehicular', 'auto']
      : ['health', 'salud', 'medical', 'medica'];

    return userSubscriptions.find(sub => {
      if (sub.status !== 'ACTIVE') return false;
      const planName = (sub.plan_name || sub.plan?.name || '').toLowerCase();
      const category = (sub.category || sub.plan?.category?.name || '').toLowerCase();
      return keywords.some(k => planName.includes(k) || category.includes(k));
    });
  };

  // Generic AI validation for any service type
  const validateServiceRequest = async () => {
    if (!selectedService) return;
    setValidatingService(true);

    try {
      // Build validation data based on service type
      const validationData: any = {
        service_id: selectedService.id,
        service_name: selectedService.name,
        plan_type: selectedService.planType,
        form_type: selectedService.formType,
        description: formData.description,
        location: formData.location_address,
      };

      // Add form-specific data based on form type - Complete data for MAWDY
      if (selectedService.formType === 'taxi') {
        validationData.taxi_info = {
          pickup_location: taxiFormData.pickup_location,
          destination: taxiFormData.destination,
          pickup_time: taxiFormData.pickup_time,
          num_passengers: taxiFormData.num_passengers,
          special_needs: taxiFormData.special_needs,
        };
      } else if (selectedService.formType === 'legal') {
        validationData.legal_info = {
          legal_issue_type: legalFormData.legal_issue_type,
          issue_description: legalFormData.issue_description,
          urgency: legalFormData.urgency,
          related_to_accident: legalFormData.related_to_accident,
        };
      } else if (selectedService.formType === 'generic') {
        validationData.generic_info = {
          service_details: genericFormData.service_details,
          special_requirements: genericFormData.special_requirements,
        };
      } else if (selectedService.formType === 'consultation') {
        validationData.consultation_info = {
          specialty: consultationFormData.consultation_type,
          specialist_type: consultationFormData.specialist_type,
          patient_type: consultationFormData.patient_type,
          patient_name: consultationFormData.patient_name,
          patient_age: consultationFormData.patient_age,
          reason: consultationFormData.reason_for_visit,
          symptoms_description: consultationFormData.symptoms_description,
          preferred_date: consultationFormData.preferred_date,
          preferred_time: consultationFormData.preferred_time,
          has_medical_order: consultationFormData.has_medical_order,
          additional_notes: consultationFormData.additional_notes,
        };
      } else if (selectedService.formType === 'video_consultation') {
        validationData.video_consultation_info = {
          specialty: videoConsultationFormData.consultation_type,
          patient_type: videoConsultationFormData.patient_type,
          patient_name: videoConsultationFormData.patient_name,
          is_first_consultation: videoConsultationFormData.is_first_consultation,
          symptoms: videoConsultationFormData.main_reason,
          medical_conditions: videoConsultationFormData.medical_conditions,
          preferred_date: videoConsultationFormData.preferred_date,
          preferred_time: videoConsultationFormData.preferred_time,
          has_stable_internet: videoConsultationFormData.has_stable_internet,
          additional_notes: videoConsultationFormData.additional_notes,
        };
      } else if (selectedService.formType === 'lab_exam') {
        validationData.lab_exam_info = {
          exam_types: [labExamFormData.exam_type],
          patient_type: labExamFormData.patient_type,
          patient_name: labExamFormData.patient_name,
          patient_age: labExamFormData.patient_age,
          has_medical_order: labExamFormData.has_medical_order,
          fasting_required: labExamFormData.fasting_required,
          preferred_date: labExamFormData.preferred_date,
          preferred_location: labExamFormData.preferred_location,
          home_service: labExamFormData.preferred_location === 'home',
          special_instructions: labExamFormData.special_instructions,
        };
      } else if (selectedService.formType === 'medication') {
        validationData.medication_info = {
          medications: medicationFormData.medications_list,
          has_prescription: medicationFormData.has_prescription,
          prescription_details: medicationFormData.prescription_details,
          pharmacy_preference: medicationFormData.pharmacy_preference,
          urgency: medicationFormData.urgency_level,
          delivery_address: medicationFormData.delivery_address,
          delivery_time_preference: medicationFormData.delivery_time_preference,
          special_instructions: medicationFormData.special_instructions,
        };
      } else if (selectedService.formType === 'delivery') {
        validationData.delivery_info = {
          delivery_type: deliveryFormData.delivery_type,
          pickup_address: deliveryFormData.pickup_address,
          delivery_address: deliveryFormData.delivery_address,
          items: deliveryFormData.item_description,
          urgency_level: deliveryFormData.urgency_level,
          urgent: deliveryFormData.urgency_level === 'URGENT',
          recipient_name: deliveryFormData.recipient_name,
          recipient_phone: deliveryFormData.recipient_phone,
          special_instructions: deliveryFormData.special_instructions,
        };
      }

      // Call generic validation endpoint (with fallback to auto-approve for simple services)
      const response = await assistanceAPI.validateService(validationData);
      setServiceValidation(response.data);

      if (response.data.validation_status === 'APPROVED' || response.data.validation_status === 'PENDING_REVIEW') {
        setStep(isRoadsideAssistance() || isHealthAssistance() ? 4 : 3);
      }
    } catch (error: any) {
      console.error('Service validation error:', error);
      // Auto-approve simple services if validation endpoint is not available
      if (error.response?.status === 404 || error.response?.status === 501) {
        setServiceValidation({
          validation_status: 'APPROVED',
          validation_message: 'Servicio validado automáticamente',
          auto_approved: true,
        });
        setStep(isRoadsideAssistance() || isHealthAssistance() ? 4 : 3);
      } else {
        setServiceValidation({
          validation_status: 'PENDING_REVIEW',
          validation_message: 'Tu solicitud será revisada por un agente MAWDY',
        });
        setStep(isRoadsideAssistance() || isHealthAssistance() ? 4 : 3);
      }
    } finally {
      setValidatingService(false);
    }
  };

  // Check if service requires specific form (not vehicle or health questionnaire)
  const requiresSpecificForm = () => {
    if (!selectedService) return false;
    return ['taxi', 'legal', 'generic', 'consultation', 'video_consultation', 'lab_exam', 'medication', 'delivery'].includes(selectedService.formType || '');
  };

  // Check if service requires location step (IMMEDIATE services need location, others handle it in their own forms)
  const requiresLocationStep = () => {
    if (!selectedService) return true; // Default to requiring location for safety
    // IMMEDIATE services always need location (roadside, ambulance, etc.)
    if (selectedService.serviceFlow === 'IMMEDIATE') return true;
    // SCHEDULED/CALLBACK/CLAIM services have their own address handling in their forms
    // or don't need physical location (video calls, phone callbacks)
    return false;
  };

  // Get service flow type indicator
  const getServiceFlowLabel = (flow: ServiceFlowType) => {
    switch (flow) {
      case 'IMMEDIATE':
        return { label: 'Servicio Inmediato', color: 'bg-red-100 text-red-700', icon: '🚨' };
      case 'SCHEDULED':
        return { label: 'Agendar Cita', color: 'bg-blue-100 text-blue-700', icon: '📅' };
      case 'CALLBACK':
        return { label: 'Te Llamamos', color: 'bg-green-100 text-green-700', icon: '📞' };
      case 'CLAIM':
        return { label: 'Solicitar Reembolso', color: 'bg-purple-100 text-purple-700', icon: '📋' };
    }
  };

  // Check if the current form data for this service type is valid
  const isServiceFormValid = () => {
    if (!selectedService) return false;

    switch (selectedService.formType) {
      case 'taxi':
        return taxiFormData.pickup_location.trim() !== '' && taxiFormData.destination.trim() !== '';
      case 'legal':
        return legalFormData.legal_issue_type !== '' && legalFormData.issue_description.trim() !== '';
      case 'generic':
        return genericFormData.service_details.trim() !== '';
      case 'consultation':
        return consultationFormData.consultation_type !== '' && consultationFormData.reason_for_visit.trim() !== '';
      case 'video_consultation':
        return videoConsultationFormData.consultation_type !== '' && videoConsultationFormData.main_reason.trim() !== '';
      case 'lab_exam':
        return labExamFormData.exam_type !== '';
      case 'medication':
        return medicationFormData.medications_list.trim() !== '';
      case 'delivery':
        return deliveryFormData.delivery_type !== '' && deliveryFormData.item_description.trim() !== '';
      default:
        return true;
    }
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
    // Require either selectedService (new flow) or selectedCategory (legacy)
    if (!selectedService && !selectedCategory) return;
    setSubmitting(true);

    try {
      // Get matching subscription based on new MAWDY service or legacy category
      let matchingSubscription;
      let incidentType = 'OTHER';

      if (selectedService && selectedPlanType) {
        // New MAWDY service flow
        matchingSubscription = getMatchingSubscription(selectedPlanType);
        incidentType = selectedService.id; // Use service ID as incident type
      } else {
        // Legacy category flow
        const selectedCat = categories.find(c => c.id === selectedCategory);
        const categoryType = selectedCat?.category_type?.toUpperCase() || '';

        const categoryKeywords: Record<string, string[]> = {
          'ROADSIDE': ['drive', 'roadside', 'vial', 'vehicular', 'auto', 'carro'],
          'VEHICULAR': ['drive', 'roadside', 'vial', 'vehicular', 'auto', 'carro'],
          'HEALTH': ['health', 'salud', 'medical', 'medica'],
          'MEDICAL': ['health', 'salud', 'medical', 'medica'],
          'HOME': ['home', 'hogar', 'casa'],
          'LEGAL': ['legal', 'juridico', 'juridica'],
        };

        const keywords = categoryKeywords[categoryType] || [categoryType.toLowerCase()];

        matchingSubscription = userSubscriptions.find(sub => {
          if (sub.status !== 'ACTIVE') return false;
          const planName = sub.plan_name?.toLowerCase() || '';
          const category = sub.category?.toLowerCase() || '';
          return keywords.some(keyword => planName.includes(keyword) || category.includes(keyword));
        });

        incidentType = selectedCat?.category_type || 'OTHER';
      }

      if (!matchingSubscription) {
        alert('No tienes una suscripción activa para este tipo de servicio. Por favor, suscríbete primero.');
        setSubmitting(false);
        return;
      }

      const requestData: any = {
        ...formData,
        // Round coordinates to 6 decimal places (max 9 digits total for backend)
        location_latitude: Math.round(formData.location_latitude * 1000000) / 1000000,
        location_longitude: Math.round(formData.location_longitude * 1000000) / 1000000,
        // Convert vehicle_year to integer for backend validation
        vehicle_year: formData.vehicle_year ? parseInt(formData.vehicle_year, 10) || null : null,
        service_category: selectedCategory,
        user_service: matchingSubscription.id,
        incident_type: incidentType,
      };

      // Add MAWDY service metadata
      if (selectedService) {
        requestData.mawdy_service = {
          service_id: selectedService.id,
          service_name: selectedService.name,
          plan_type: selectedService.planType,
          limit_per_year: selectedService.limitPerYear,
          coverage_amount: selectedService.coverageAmount,
          form_type: selectedService.formType,
        };
      }

      // Add vehicle info if roadside assistance
      if (isRoadsideAssistance()) {
        requestData.vehicle_info = {
          // Vehicle Details
          make: formData.vehicle_make,
          model: formData.vehicle_model,
          year: formData.vehicle_year ? parseInt(formData.vehicle_year, 10) : null,
          plate: formData.vehicle_plate,
          color: formData.vehicle_color,
          vin: formData.vehicle_vin,
          // Roadside Emergency Triage
          emergency_type: formData.roadside_emergency_type,
          is_safe_location: formData.roadside_is_safe_location,
          traffic_blocked: formData.roadside_traffic_blocked,
          hazard_lights_on: formData.roadside_hazard_lights_on,
          passengers_count: formData.roadside_passengers_count,
          // Type-specific details
          tire_position: formData.roadside_tire_position,
          has_spare_tire: formData.roadside_has_spare_tire,
          battery_age: formData.roadside_battery_age,
          fuel_type: formData.roadside_fuel_type,
          fuel_amount: formData.roadside_fuel_amount,
          keys_location: formData.roadside_keys_location,
          towing_destination: formData.roadside_towing_destination,
          towing_distance: formData.roadside_towing_distance,
          additional_details: formData.roadside_additional_details,
          // Validation
          validation_status: vehicleValidation?.validation_status,
          validation_id: vehicleValidation?.id
        };
      }

      // Add health questionnaire info if health assistance (SAMPLE format)
      if (isHealthAssistance()) {
        requestData.health_info = {
          // Emergency details
          emergency_type: formData.health_emergency_type,
          // S - Signs/Symptoms
          symptoms: formData.health_symptoms.join(', ') + (formData.health_other_symptoms ? ` (Otros: ${formData.health_other_symptoms})` : ''),
          pain_scale: formData.health_pain_scale,
          // A - Allergies
          has_allergies: formData.health_has_allergies,
          allergies: formData.health_allergies,
          // M - Medications
          is_on_medications: formData.health_is_on_medications,
          medications: formData.health_medications,
          // P - Past Medical History
          has_conditions: formData.health_has_conditions,
          pre_existing_conditions: formData.health_pre_existing_conditions,
          // L - Last Oral Intake
          last_intake_time: formData.health_last_intake_time,
          last_intake: formData.health_last_intake,
          // E - Events Leading Up
          events_leading: formData.health_events_leading,
          // Patient Demographics
          patient_name: formData.health_patient_name,
          patient_relationship: formData.health_patient_relationship,
          patient_age: formData.health_patient_age,
          patient_gender: formData.health_patient_gender,
          patient_weight: formData.health_patient_weight,
          // Critical Indicators
          consciousness_level: formData.health_consciousness_level,
          breathing_difficulty: formData.health_breathing_difficulty,
          chest_pain: formData.health_chest_pain,
          bleeding: formData.health_bleeding,
          // Additional info
          people_affected: formData.health_people_affected,
          validation_status: healthValidation?.validation_status,
          validation_id: healthValidation?.id,
          urgency_level: healthValidation?.urgency_level
        };
      }

      // Add service-specific validation if available
      if (serviceValidation) {
        requestData.service_validation = {
          validation_status: serviceValidation.validation_status,
          validation_id: serviceValidation.id,
          validation_message: serviceValidation.validation_message,
        };
      }

      const response = await assistanceAPI.createRequest(requestData);

      // Get the created request ID from response
      const createdRequestId = response.data?.id || response.data?.request?.id;

      if (vehicleValidation?.validation_status === 'PENDING_REVIEW') {
        alert('Solicitud creada! Tu información vehicular está en revisión por un agente MAWDY. Te notificaremos pronto.');
      } else if (healthValidation?.validation_status === 'PENDING_REVIEW') {
        alert('Solicitud creada! Tu información médica está en revisión por un agente MAWDY. Te contactaremos pronto.');
      } else if (serviceValidation?.validation_status === 'PENDING_REVIEW') {
        alert('Solicitud creada! Tu solicitud está en revisión por un agente MAWDY. Te contactaremos pronto.');
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

        {/* Step 1: Select Service Type - MAWDY Complete Catalog */}
        {step === 1 && (
          <div className="card">
            {!selectedPlanType ? (
              // Plan Type Selection
              <>
                <h2 className="text-lg font-bold mb-2">¿Qué tipo de asistencia necesitas?</h2>
                <p className="text-sm text-gray-500 mb-4">Selecciona el tipo de plan para ver los servicios disponibles</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Plan Drive (Vial) */}
                  <button
                    onClick={() => hasPlanType('DRIVE') && setSelectedPlanType('DRIVE')}
                    disabled={!hasPlanType('DRIVE')}
                    className={`p-5 rounded-xl border-2 transition-all text-left ${
                      hasPlanType('DRIVE')
                        ? 'border-red-200 hover:border-red-400 hover:bg-red-50 cursor-pointer'
                        : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-3 bg-red-100 rounded-xl">
                        <Truck className="text-red-600" size={28} />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg">Plan Drive</h3>
                        <p className="text-xs text-gray-500">Asistencia Vial</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">Grúa, combustible, cerrajería, conductor profesional y más...</p>
                    <div className="flex flex-wrap gap-1">
                      <span className="px-2 py-0.5 bg-red-50 text-red-700 text-xs rounded">13 servicios</span>
                      {hasPlanType('DRIVE') ? (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">Activo</span>
                      ) : (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">Sin suscripción</span>
                      )}
                    </div>
                  </button>

                  {/* Plan Health (Salud) */}
                  <button
                    onClick={() => hasPlanType('HEALTH') && setSelectedPlanType('HEALTH')}
                    disabled={!hasPlanType('HEALTH')}
                    className={`p-5 rounded-xl border-2 transition-all text-left ${
                      hasPlanType('HEALTH')
                        ? 'border-pink-200 hover:border-pink-400 hover:bg-pink-50 cursor-pointer'
                        : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-3 bg-pink-100 rounded-xl">
                        <Heart className="text-pink-600" size={28} />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg">Plan Health</h3>
                        <p className="text-xs text-gray-500">Asistencia Médica</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">Consultas, laboratorios, nutrición, psicología y más...</p>
                    <div className="flex flex-wrap gap-1">
                      <span className="px-2 py-0.5 bg-pink-50 text-pink-700 text-xs rounded">14 servicios</span>
                      {hasPlanType('HEALTH') ? (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">Activo</span>
                      ) : (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">Sin suscripción</span>
                      )}
                    </div>
                  </button>
                </div>

                {/* No subscriptions warning */}
                {!hasPlanType('DRIVE') && !hasPlanType('HEALTH') && (
                  <div className="mt-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-xl">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">No tienes suscripciones activas</p>
                        <p className="text-sm text-yellow-700 mt-1">Para solicitar asistencia, primero debes suscribirte a un plan MAWDY.</p>
                        <button
                          onClick={() => navigate('/app/plans')}
                          className="mt-2 text-sm font-medium text-yellow-800 hover:text-yellow-900 underline"
                        >
                          Ver planes disponibles →
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              // Specific Service Selection
              <>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => {
                        setSelectedPlanType(null);
                        setSelectedService(null);
                      }}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <X className="text-gray-500" size={20} />
                    </button>
                    <div className={`p-2 rounded-lg ${selectedPlanType === 'DRIVE' ? 'bg-red-100' : 'bg-pink-100'}`}>
                      {selectedPlanType === 'DRIVE' ? (
                        <Truck className="text-red-600" size={24} />
                      ) : (
                        <Heart className="text-pink-600" size={24} />
                      )}
                    </div>
                    <div>
                      <h2 className="font-bold">{selectedPlanType === 'DRIVE' ? 'Plan Drive' : 'Plan Health'}</h2>
                      <p className="text-xs text-gray-500">Selecciona un servicio</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                  {getAvailableServices(selectedPlanType).map((service) => (
                    <button
                      key={service.id}
                      onClick={() => {
                        setSelectedService(service);
                        setFormData(prev => ({ ...prev, title: `Asistencia: ${service.name}` }));
                        // Also set the category based on plan type for backend compatibility
                        const matchingCat = categories.find(c =>
                          selectedPlanType === 'DRIVE'
                            ? c.category_type?.toUpperCase() === 'ROADSIDE'
                            : c.category_type?.toUpperCase() === 'HEALTH'
                        );
                        if (matchingCat) setSelectedCategory(matchingCat.id);
                      }}
                      className={`w-full p-4 rounded-xl border-2 transition-all text-left flex items-center gap-4 ${
                        selectedService?.id === service.id
                          ? selectedPlanType === 'DRIVE' ? 'border-red-500 bg-red-50' : 'border-pink-500 bg-pink-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className={`p-2 rounded-lg flex-shrink-0 ${
                        selectedService?.id === service.id
                          ? selectedPlanType === 'DRIVE' ? 'bg-red-100' : 'bg-pink-100'
                          : 'bg-gray-100'
                      }`}>
                        {service.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <h3 className="font-bold text-sm">{service.name}</h3>
                          <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${getServiceFlowLabel(service.serviceFlow).color}`}>
                            {getServiceFlowLabel(service.serviceFlow).icon} {getServiceFlowLabel(service.serviceFlow).label}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 truncate">{service.description}</p>
                      </div>
                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        {service.limitPerYear !== null ? (
                          <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded whitespace-nowrap">
                            {service.limitPerYear}/año
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded whitespace-nowrap">
                            Ilimitado
                          </span>
                        )}
                        {service.coverageAmount > 0 && (
                          <span className="text-xs text-gray-500">${service.coverageAmount}</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setStep(2)}
                  disabled={!selectedService}
                  className="btn btn-primary w-full mt-4"
                >
                  Continuar con {selectedService?.name || 'el servicio'}
                </button>
              </>
            )}
          </div>
        )}

        {/* Step 2: Location (only for IMMEDIATE services) */}
        {step === 2 && requiresLocationStep() && (
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

        {/* Step 2: Skip location - go directly to form for non-IMMEDIATE services */}
        {step === 2 && !requiresLocationStep() && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4">Información del Servicio</h2>
            <p className="text-gray-600 mb-4">
              Este servicio no requiere tu ubicación actual. Por favor completa la información solicitada.
            </p>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(1)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => setStep(3)}
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

              {/* Patient Relationship */}
              <div>
                <label className="label">¿Quién necesita la atención? *</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'TITULAR', label: 'Yo mismo' },
                    { value: 'FAMILIAR', label: 'Familiar' },
                    { value: 'OTRO', label: 'Otra persona' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, health_patient_relationship: opt.value }))}
                      className={`py-2 px-3 rounded-lg border-2 text-sm font-medium transition-all ${
                        formData.health_patient_relationship === opt.value
                          ? 'bg-pink-100 text-pink-700 border-pink-300'
                          : 'bg-gray-50 text-gray-500 border-gray-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Patient Name (if not titular) */}
              {formData.health_patient_relationship !== 'TITULAR' && (
                <div>
                  <label className="label">Nombre del paciente *</label>
                  <input
                    type="text"
                    value={formData.health_patient_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_patient_name: e.target.value }))}
                    className="input"
                    placeholder="Nombre completo del paciente"
                  />
                </div>
              )}

              {/* Patient Demographics */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">Edad *</label>
                  <input
                    type="number"
                    value={formData.health_patient_age}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_patient_age: e.target.value }))}
                    className="input"
                    placeholder="Años"
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
                <div>
                  <label className="label">Peso (lbs)</label>
                  <input
                    type="number"
                    value={formData.health_patient_weight}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_patient_weight: e.target.value }))}
                    className="input"
                    placeholder="Lbs"
                    min="0"
                    max="500"
                  />
                </div>
              </div>

              {/* Pain Scale */}
              <div>
                <label className="label">Nivel de dolor (0 = Sin dolor, 10 = Dolor insoportable)</label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="0"
                    max="10"
                    value={formData.health_pain_scale}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_pain_scale: parseInt(e.target.value) }))}
                    className="flex-1 h-3 bg-gradient-to-r from-green-300 via-yellow-300 to-red-500 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className={`text-2xl font-bold min-w-[3rem] text-center ${
                    formData.health_pain_scale <= 3 ? 'text-green-600' :
                    formData.health_pain_scale <= 6 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {formData.health_pain_scale}
                  </span>
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

              {/* SAMPLE FORMAT - A: Allergies */}
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <label className="label text-orange-900 mb-0 flex items-center gap-2">
                    <span className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold">A</span>
                    Alergias
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.health_has_allergies}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_has_allergies: e.target.checked }))}
                      className="w-4 h-4 text-orange-600 rounded"
                    />
                    <span className="text-sm text-orange-700">Tiene alergias</span>
                  </label>
                </div>
                {formData.health_has_allergies && (
                  <textarea
                    value={formData.health_allergies}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_allergies: e.target.value }))}
                    className="input"
                    rows={2}
                    placeholder="Medicamentos, alimentos, picaduras, látex, etc..."
                  />
                )}
                {!formData.health_has_allergies && (
                  <p className="text-sm text-orange-600">Sin alergias conocidas (NKDA)</p>
                )}
              </div>

              {/* SAMPLE FORMAT - M: Medications */}
              <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <label className="label text-purple-900 mb-0 flex items-center gap-2">
                    <span className="w-6 h-6 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs font-bold">M</span>
                    Medicamentos Actuales
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.health_is_on_medications}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_is_on_medications: e.target.checked }))}
                      className="w-4 h-4 text-purple-600 rounded"
                    />
                    <span className="text-sm text-purple-700">Toma medicamentos</span>
                  </label>
                </div>
                {formData.health_is_on_medications && (
                  <textarea
                    value={formData.health_medications}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_medications: e.target.value }))}
                    className="input"
                    rows={2}
                    placeholder="Lista de medicamentos con dosis (ej: Metformina 500mg, Aspirina 81mg...)"
                  />
                )}
                {!formData.health_is_on_medications && (
                  <p className="text-sm text-purple-600">No toma medicamentos actualmente</p>
                )}
              </div>

              {/* SAMPLE FORMAT - P: Past Medical History */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <label className="label text-blue-900 mb-0 flex items-center gap-2">
                    <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">P</span>
                    Historial Médico
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.health_has_conditions}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_has_conditions: e.target.checked }))}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <span className="text-sm text-blue-700">Tiene condiciones</span>
                  </label>
                </div>
                {formData.health_has_conditions && (
                  <textarea
                    value={formData.health_pre_existing_conditions}
                    onChange={(e) => setFormData(prev => ({ ...prev, health_pre_existing_conditions: e.target.value }))}
                    className="input"
                    rows={2}
                    placeholder="Diabetes, hipertensión, asma, cirugías previas, hospitalizaciones..."
                  />
                )}
                {!formData.health_has_conditions && (
                  <p className="text-sm text-blue-600">Sin condiciones médicas conocidas</p>
                )}
              </div>

              {/* SAMPLE FORMAT - L: Last Oral Intake */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
                <label className="label text-green-900 mb-3 flex items-center gap-2">
                  <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold">L</span>
                  Última Ingesta Oral
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-green-700 block mb-1">¿Cuándo comió/bebió por última vez?</label>
                    <select
                      value={formData.health_last_intake_time}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_last_intake_time: e.target.value }))}
                      className="input"
                    >
                      <option value="">Seleccionar</option>
                      <option value="LESS_1H">Hace menos de 1 hora</option>
                      <option value="1_4H">Hace 1-4 horas</option>
                      <option value="4_8H">Hace 4-8 horas</option>
                      <option value="MORE_8H">Hace más de 8 horas</option>
                      <option value="UNKNOWN">No sabe/No recuerda</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-green-700 block mb-1">¿Qué consumió?</label>
                    <input
                      type="text"
                      value={formData.health_last_intake}
                      onChange={(e) => setFormData(prev => ({ ...prev, health_last_intake: e.target.value }))}
                      className="input"
                      placeholder="Ej: Desayuno, almuerzo, agua..."
                    />
                  </div>
                </div>
              </div>

              {/* SAMPLE FORMAT - E: Events Leading Up */}
              <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
                <label className="label text-indigo-900 mb-2 flex items-center gap-2">
                  <span className="w-6 h-6 bg-indigo-500 text-white rounded-full flex items-center justify-center text-xs font-bold">E</span>
                  Eventos que Llevaron a la Emergencia
                </label>
                <textarea
                  value={formData.health_events_leading}
                  onChange={(e) => setFormData(prev => ({ ...prev, health_events_leading: e.target.value }))}
                  className="input"
                  rows={3}
                  placeholder="Describa qué estaba haciendo antes de la emergencia, cómo empezaron los síntomas, qué actividades realizaba..."
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

              {/* Road Assistance Triage Section */}
              <div className="border-t-2 border-dashed border-gray-200 pt-5 mt-5">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <AlertTriangle className="text-orange-500" size={20} />
                  Tipo de Emergencia Vial
                </h3>

                {/* Emergency Type Selection */}
                <div className="grid grid-cols-2 gap-3 mb-5">
                  {[
                    { value: 'FLAT_TIRE', label: 'Llanta Pinchada', icon: '🛞', color: 'bg-gray-100 border-gray-300 text-gray-800' },
                    { value: 'BATTERY', label: 'Batería Descargada', icon: '🔋', color: 'bg-yellow-100 border-yellow-300 text-yellow-800' },
                    { value: 'FUEL', label: 'Sin Combustible', icon: '⛽', color: 'bg-red-100 border-red-300 text-red-800' },
                    { value: 'LOCKSMITH', label: 'Cerrajería', icon: '🔐', color: 'bg-purple-100 border-purple-300 text-purple-800' },
                    { value: 'TOWING', label: 'Grúa/Remolque', icon: '🚛', color: 'bg-blue-100 border-blue-300 text-blue-800' },
                    { value: 'STUCK', label: 'Vehículo Atascado', icon: '🚗', color: 'bg-orange-100 border-orange-300 text-orange-800' },
                  ].map((type) => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, roadside_emergency_type: type.value }))}
                      className={`p-3 rounded-xl border-2 text-left transition-all ${
                        formData.roadside_emergency_type === type.value
                          ? `${type.color} shadow-md`
                          : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <span className="text-2xl block mb-1">{type.icon}</span>
                      <span className="text-sm font-medium">{type.label}</span>
                    </button>
                  ))}
                </div>

                {/* Safety Assessment */}
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl mb-4">
                  <label className="label text-red-900 mb-3 flex items-center gap-2">
                    <Shield className="text-red-600" size={18} />
                    Evaluación de Seguridad
                  </label>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.roadside_is_safe_location}
                        onChange={(e) => setFormData(prev => ({ ...prev, roadside_is_safe_location: e.target.checked }))}
                        className="w-5 h-5 text-green-600 rounded"
                      />
                      <span className="text-sm font-medium text-gray-700">Estoy en un lugar seguro (fuera del tráfico)</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.roadside_hazard_lights_on}
                        onChange={(e) => setFormData(prev => ({ ...prev, roadside_hazard_lights_on: e.target.checked }))}
                        className="w-5 h-5 text-yellow-600 rounded"
                      />
                      <span className="text-sm font-medium text-gray-700">Tengo las luces de emergencia encendidas</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.roadside_traffic_blocked}
                        onChange={(e) => setFormData(prev => ({ ...prev, roadside_traffic_blocked: e.target.checked }))}
                        className="w-5 h-5 text-red-600 rounded"
                      />
                      <span className="text-sm font-medium text-gray-700">Estoy bloqueando el tráfico (requiere atención urgente)</span>
                    </label>
                  </div>
                  <div className="mt-3">
                    <label className="text-sm text-gray-600 block mb-1">Número de pasajeros</label>
                    <select
                      value={formData.roadside_passengers_count}
                      onChange={(e) => setFormData(prev => ({ ...prev, roadside_passengers_count: e.target.value }))}
                      className="input"
                    >
                      <option value="1">Solo yo</option>
                      <option value="2">2 personas</option>
                      <option value="3">3 personas</option>
                      <option value="4+">4 o más personas</option>
                    </select>
                  </div>
                </div>

                {/* Flat Tire Specific Fields */}
                {formData.roadside_emergency_type === 'FLAT_TIRE' && (
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl mb-4">
                    <label className="label text-gray-900 mb-3">Detalles de la Llanta</label>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-gray-600 block mb-1">¿Cuál llanta?</label>
                        <select
                          value={formData.roadside_tire_position}
                          onChange={(e) => setFormData(prev => ({ ...prev, roadside_tire_position: e.target.value }))}
                          className="input"
                        >
                          <option value="">Seleccionar</option>
                          <option value="FRONT_LEFT">Delantera Izquierda</option>
                          <option value="FRONT_RIGHT">Delantera Derecha</option>
                          <option value="REAR_LEFT">Trasera Izquierda</option>
                          <option value="REAR_RIGHT">Trasera Derecha</option>
                          <option value="MULTIPLE">Varias llantas</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm text-gray-600 block mb-1">¿Tiene repuesto?</label>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({ ...prev, roadside_has_spare_tire: true }))}
                            className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                              formData.roadside_has_spare_tire
                                ? 'bg-green-100 text-green-700 border-green-300'
                                : 'bg-gray-50 text-gray-500 border-gray-200'
                            }`}
                          >
                            Sí
                          </button>
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({ ...prev, roadside_has_spare_tire: false }))}
                            className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                              !formData.roadside_has_spare_tire
                                ? 'bg-red-100 text-red-700 border-red-300'
                                : 'bg-gray-50 text-gray-500 border-gray-200'
                            }`}
                          >
                            No
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Battery Specific Fields */}
                {formData.roadside_emergency_type === 'BATTERY' && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl mb-4">
                    <label className="label text-yellow-900 mb-3">Detalles de la Batería</label>
                    <div>
                      <label className="text-sm text-yellow-700 block mb-1">Antigüedad de la batería</label>
                      <select
                        value={formData.roadside_battery_age}
                        onChange={(e) => setFormData(prev => ({ ...prev, roadside_battery_age: e.target.value }))}
                        className="input"
                      >
                        <option value="">Seleccionar</option>
                        <option value="NEW">Nueva (menos de 1 año)</option>
                        <option value="1_2_YEARS">1-2 años</option>
                        <option value="2_4_YEARS">2-4 años</option>
                        <option value="OLD">Más de 4 años</option>
                        <option value="UNKNOWN">No sé</option>
                      </select>
                    </div>
                    <p className="text-xs text-yellow-600 mt-2">
                      Si la batería tiene más de 3 años, es posible que necesite reemplazo.
                    </p>
                  </div>
                )}

                {/* Fuel Specific Fields */}
                {formData.roadside_emergency_type === 'FUEL' && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl mb-4">
                    <label className="label text-red-900 mb-3">Detalles de Combustible</label>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-red-700 block mb-1">Tipo de combustible</label>
                        <select
                          value={formData.roadside_fuel_type}
                          onChange={(e) => setFormData(prev => ({ ...prev, roadside_fuel_type: e.target.value }))}
                          className="input"
                        >
                          <option value="REGULAR">Gasolina Regular</option>
                          <option value="SUPER">Gasolina Super</option>
                          <option value="DIESEL">Diésel</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm text-red-700 block mb-1">Cantidad (galones)</label>
                        <select
                          value={formData.roadside_fuel_amount}
                          onChange={(e) => setFormData(prev => ({ ...prev, roadside_fuel_amount: e.target.value }))}
                          className="input"
                        >
                          <option value="2">2 galones</option>
                          <option value="5">5 galones</option>
                          <option value="10">10 galones</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* Locksmith Specific Fields */}
                {formData.roadside_emergency_type === 'LOCKSMITH' && (
                  <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl mb-4">
                    <label className="label text-purple-900 mb-3">Detalles de Cerrajería</label>
                    <div>
                      <label className="text-sm text-purple-700 block mb-1">¿Dónde están las llaves?</label>
                      <select
                        value={formData.roadside_keys_location}
                        onChange={(e) => setFormData(prev => ({ ...prev, roadside_keys_location: e.target.value }))}
                        className="input"
                      >
                        <option value="">Seleccionar</option>
                        <option value="INSIDE_CAR">Dentro del vehículo</option>
                        <option value="LOST">Perdidas</option>
                        <option value="BROKEN">Rotas en la cerradura</option>
                        <option value="STOLEN">Robadas</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Towing Specific Fields */}
                {formData.roadside_emergency_type === 'TOWING' && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl mb-4">
                    <label className="label text-blue-900 mb-3">Detalles de Remolque</label>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm text-blue-700 block mb-1">¿A dónde desea remolcar el vehículo?</label>
                        <input
                          type="text"
                          value={formData.roadside_towing_destination}
                          onChange={(e) => setFormData(prev => ({ ...prev, roadside_towing_destination: e.target.value }))}
                          className="input"
                          placeholder="Taller, casa, concesionario..."
                        />
                      </div>
                      <div>
                        <label className="text-sm text-blue-700 block mb-1">Distancia aproximada</label>
                        <select
                          value={formData.roadside_towing_distance}
                          onChange={(e) => setFormData(prev => ({ ...prev, roadside_towing_distance: e.target.value }))}
                          className="input"
                        >
                          <option value="">Seleccionar</option>
                          <option value="0_10">Menos de 10 km</option>
                          <option value="10_25">10-25 km</option>
                          <option value="25_50">25-50 km</option>
                          <option value="50+">Más de 50 km</option>
                        </select>
                      </div>
                    </div>
                    <p className="text-xs text-blue-600 mt-2">
                      El servicio incluye hasta 50 km de remolque. Distancias mayores pueden tener costo adicional.
                    </p>
                  </div>
                )}

                {/* Additional Details */}
                <div>
                  <label className="label">Detalles adicionales</label>
                  <textarea
                    value={formData.roadside_additional_details}
                    onChange={(e) => setFormData(prev => ({ ...prev, roadside_additional_details: e.target.value }))}
                    className="input"
                    rows={2}
                    placeholder="Cualquier información adicional que nos ayude a asistirte mejor..."
                  />
                </div>
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

        {/* Step 3: Taxi Service Form */}
        {step === 3 && selectedService?.formType === 'taxi' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-yellow-100 rounded-xl">
                  <Taxi className="text-yellow-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">{selectedService.name}</h2>
                  <p className="text-sm text-gray-600">Información del servicio de transporte</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Dirección de recogida *</label>
                <input
                  type="text"
                  value={taxiFormData.pickup_location}
                  onChange={(e) => setTaxiFormData(prev => ({ ...prev, pickup_location: e.target.value }))}
                  className="input"
                  placeholder="¿Dónde te recogemos?"
                />
              </div>

              <div>
                <label className="label">Destino *</label>
                <input
                  type="text"
                  value={taxiFormData.destination}
                  onChange={(e) => setTaxiFormData(prev => ({ ...prev, destination: e.target.value }))}
                  className="input"
                  placeholder="¿A dónde vas?"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Fecha y hora preferida</label>
                  <input
                    type="datetime-local"
                    value={taxiFormData.pickup_time}
                    onChange={(e) => setTaxiFormData(prev => ({ ...prev, pickup_time: e.target.value }))}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Número de pasajeros</label>
                  <select
                    value={taxiFormData.num_passengers}
                    onChange={(e) => setTaxiFormData(prev => ({ ...prev, num_passengers: e.target.value }))}
                    className="input"
                  >
                    <option value="1">1 pasajero</option>
                    <option value="2">2 pasajeros</option>
                    <option value="3">3 pasajeros</option>
                    <option value="4">4 pasajeros</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="label">Necesidades especiales (opcional)</label>
                <textarea
                  value={taxiFormData.special_needs}
                  onChange={(e) => setTaxiFormData(prev => ({ ...prev, special_needs: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Silla de ruedas, equipaje extra, etc..."
                />
              </div>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Solicitud Validada por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu solicitud ha sido aprobada automáticamente.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un agente revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => {
                  // Auto-generate description first
                  const desc = `Taxi ${selectedService.name}: Recogida en ${taxiFormData.pickup_location}, destino ${taxiFormData.destination}. ${taxiFormData.num_passengers} pasajero(s).${taxiFormData.special_needs ? ` Notas: ${taxiFormData.special_needs}` : ''}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  // Then validate or continue
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Legal Assistance Form */}
        {step === 3 && selectedService?.formType === 'legal' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-purple-100 rounded-xl">
                  <Scale className="text-purple-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Asistencia Legal</h2>
                  <p className="text-sm text-gray-600">Cuéntanos sobre tu situación legal</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Tipo de asunto legal *</label>
                <select
                  value={legalFormData.legal_issue_type}
                  onChange={(e) => setLegalFormData(prev => ({ ...prev, legal_issue_type: e.target.value }))}
                  className="input"
                >
                  <option value="">Selecciona el tipo de asunto</option>
                  <option value="ACCIDENTE_TRANSITO">Accidente de tránsito</option>
                  <option value="ASUNTOS_CIVILES">Asuntos civiles</option>
                  <option value="ASUNTOS_LABORALES">Asuntos laborales</option>
                  <option value="DEFENSA_PENAL">Defensa penal</option>
                  <option value="CONTRATOS">Contratos</option>
                  <option value="FAMILIA">Derecho de familia</option>
                  <option value="OTRO">Otro</option>
                </select>
              </div>

              <div>
                <label className="label">Describe tu situación *</label>
                <textarea
                  value={legalFormData.issue_description}
                  onChange={(e) => setLegalFormData(prev => ({ ...prev, issue_description: e.target.value }))}
                  className="input min-h-[120px]"
                  placeholder="Describe brevemente el problema legal que tienes..."
                />
              </div>

              <div>
                <label className="label">Urgencia</label>
                <div className="flex gap-2">
                  {[
                    { value: 'LOW', label: 'Consulta general', color: 'bg-green-100 text-green-700 border-green-300' },
                    { value: 'MEDIUM', label: 'Necesito orientación', color: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
                    { value: 'HIGH', label: 'Urgente', color: 'bg-red-100 text-red-700 border-red-300' },
                  ].map((p) => (
                    <button
                      key={p.value}
                      onClick={() => setLegalFormData(prev => ({ ...prev, urgency: p.value }))}
                      className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium transition-all ${
                        legalFormData.urgency === p.value ? p.color : 'bg-gray-50 text-gray-500 border-gray-200'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                <input
                  type="checkbox"
                  checked={legalFormData.related_to_accident}
                  onChange={(e) => setLegalFormData(prev => ({ ...prev, related_to_accident: e.target.checked }))}
                  className="w-5 h-5 text-purple-600 rounded"
                />
                <span className="text-sm">Este asunto está relacionado con un accidente vehicular</span>
              </label>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Solicitud Validada por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu solicitud ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un asesor legal revisará tu caso.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => {
                  const desc = `Asistencia Legal - ${legalFormData.legal_issue_type}: ${legalFormData.issue_description}${legalFormData.related_to_accident ? ' (Relacionado con accidente vehicular)' : ''}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Generic Service Form */}
        {step === 3 && selectedService?.formType === 'generic' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className={`p-3 rounded-xl ${selectedPlanType === 'DRIVE' ? 'bg-red-100' : 'bg-pink-100'}`}>
                  {selectedService.icon}
                </div>
                <div>
                  <h2 className="text-lg font-bold">{selectedService.name}</h2>
                  <p className="text-sm text-gray-600">{selectedService.description}</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">¿Qué necesitas? *</label>
                <textarea
                  value={genericFormData.service_details}
                  onChange={(e) => setGenericFormData(prev => ({ ...prev, service_details: e.target.value }))}
                  className="input min-h-[120px]"
                  placeholder={`Describe lo que necesitas para el servicio de ${selectedService.name}...`}
                />
              </div>

              <div>
                <label className="label">Requerimientos especiales (opcional)</label>
                <textarea
                  value={genericFormData.special_requirements}
                  onChange={(e) => setGenericFormData(prev => ({ ...prev, special_requirements: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Algún detalle adicional que debamos saber..."
                />
              </div>

              {/* Service limits info */}
              <div className="p-4 bg-blue-50 rounded-xl">
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-blue-600 flex-shrink-0" size={20} />
                  <div className="text-sm">
                    <p className="font-medium text-blue-900">Información del servicio</p>
                    <p className="text-blue-700 mt-1">
                      {selectedService.limitPerYear !== null
                        ? `Este servicio tiene un límite de ${selectedService.limitPerYear} uso(s) por año.`
                        : 'Este servicio está disponible de forma ilimitada.'}
                      {selectedService.coverageAmount > 0 && (
                        <span className="block mt-1">Cobertura máxima: ${selectedService.coverageAmount} USD</span>
                      )}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Solicitud Validada por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu solicitud ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un agente revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">
                Atrás
              </button>
              <button
                onClick={() => {
                  const desc = `${selectedService.name}: ${genericFormData.service_details}${genericFormData.special_requirements ? `. Requerimientos: ${genericFormData.special_requirements}` : ''}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Consultation Form (In-person medical consultations) */}
        {step === 3 && selectedService?.formType === 'consultation' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-pink-100 rounded-xl">
                  <HeartPulse className="text-pink-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Agendar Consulta Médica</h2>
                  <p className="text-sm text-gray-600">{selectedService.description}</p>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getServiceFlowLabel(selectedService.serviceFlow).color}`}>
                {getServiceFlowLabel(selectedService.serviceFlow).icon} {getServiceFlowLabel(selectedService.serviceFlow).label}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Tipo de consulta *</label>
                <select
                  value={consultationFormData.consultation_type}
                  onChange={(e) => setConsultationFormData(prev => ({ ...prev, consultation_type: e.target.value }))}
                  className="input"
                >
                  <option value="">Selecciona el tipo de médico</option>
                  <option value="GENERAL">Médico General</option>
                  <option value="GYNECOLOGIST">Ginecólogo</option>
                  <option value="PEDIATRICIAN">Pediatra</option>
                  <option value="SPECIALIST">Especialista</option>
                </select>
              </div>

              {consultationFormData.consultation_type === 'SPECIALIST' && (
                <div>
                  <label className="label">¿Qué especialidad?</label>
                  <input
                    type="text"
                    value={consultationFormData.specialist_type}
                    onChange={(e) => setConsultationFormData(prev => ({ ...prev, specialist_type: e.target.value }))}
                    className="input"
                    placeholder="Ej: Cardiólogo, Dermatólogo, etc."
                  />
                </div>
              )}

              <div>
                <label className="label">¿Para quién es la consulta? *</label>
                <div className="flex gap-2">
                  {[
                    { value: 'TITULAR', label: 'Para mí (Titular)' },
                    { value: 'SPOUSE', label: 'Cónyuge' },
                    { value: 'CHILD', label: 'Hijo(a)' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setConsultationFormData(prev => ({ ...prev, patient_type: opt.value }))}
                      className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium transition-all ${
                        consultationFormData.patient_type === opt.value
                          ? 'bg-pink-100 text-pink-700 border-pink-300'
                          : 'bg-gray-50 text-gray-500 border-gray-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {consultationFormData.patient_type !== 'TITULAR' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Nombre del paciente</label>
                    <input
                      type="text"
                      value={consultationFormData.patient_name}
                      onChange={(e) => setConsultationFormData(prev => ({ ...prev, patient_name: e.target.value }))}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">Edad</label>
                    <input
                      type="number"
                      value={consultationFormData.patient_age}
                      onChange={(e) => setConsultationFormData(prev => ({ ...prev, patient_age: e.target.value }))}
                      className="input"
                      min="0"
                      max="120"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="label">Motivo de la consulta *</label>
                <textarea
                  value={consultationFormData.reason_for_visit}
                  onChange={(e) => setConsultationFormData(prev => ({ ...prev, reason_for_visit: e.target.value }))}
                  className="input min-h-[80px]"
                  placeholder="¿Por qué necesita la consulta?"
                />
              </div>

              <div>
                <label className="label">Síntomas (opcional)</label>
                <textarea
                  value={consultationFormData.symptoms_description}
                  onChange={(e) => setConsultationFormData(prev => ({ ...prev, symptoms_description: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Describe los síntomas si los hay..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Fecha preferida</label>
                  <input
                    type="date"
                    value={consultationFormData.preferred_date}
                    onChange={(e) => setConsultationFormData(prev => ({ ...prev, preferred_date: e.target.value }))}
                    className="input"
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div>
                  <label className="label">Horario preferido</label>
                  <select
                    value={consultationFormData.preferred_time}
                    onChange={(e) => setConsultationFormData(prev => ({ ...prev, preferred_time: e.target.value }))}
                    className="input"
                  >
                    <option value="MORNING">Mañana (8am - 12pm)</option>
                    <option value="AFTERNOON">Tarde (12pm - 5pm)</option>
                    <option value="EVENING">Noche (5pm - 8pm)</option>
                  </select>
                </div>
              </div>

              <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                <input
                  type="checkbox"
                  checked={consultationFormData.has_medical_order}
                  onChange={(e) => setConsultationFormData(prev => ({ ...prev, has_medical_order: e.target.checked }))}
                  className="w-5 h-5 text-pink-600 rounded"
                />
                <span className="text-sm">Tengo orden médica o referencia de otro doctor</span>
              </label>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Consulta Validada por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu consulta ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un coordinador médico revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">Atrás</button>
              <button
                onClick={() => {
                  const patientInfo = consultationFormData.patient_type !== 'TITULAR'
                    ? `Paciente: ${consultationFormData.patient_name}, ${consultationFormData.patient_age} años. `
                    : '';
                  const desc = `Consulta ${consultationFormData.consultation_type}${consultationFormData.specialist_type ? ` (${consultationFormData.specialist_type})` : ''}: ${patientInfo}${consultationFormData.reason_for_visit}. ${consultationFormData.symptoms_description ? `Síntomas: ${consultationFormData.symptoms_description}` : ''}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Video Consultation Form (Nutritionist, Psychology) */}
        {step === 3 && selectedService?.formType === 'video_consultation' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-violet-100 rounded-xl">
                  {selectedService.icon}
                </div>
                <div>
                  <h2 className="text-lg font-bold">Agendar Video Consulta</h2>
                  <p className="text-sm text-gray-600">{selectedService.description}</p>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getServiceFlowLabel(selectedService.serviceFlow).color}`}>
                {getServiceFlowLabel(selectedService.serviceFlow).icon} {getServiceFlowLabel(selectedService.serviceFlow).label}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Tipo de consulta *</label>
                <select
                  value={videoConsultationFormData.consultation_type}
                  onChange={(e) => setVideoConsultationFormData(prev => ({ ...prev, consultation_type: e.target.value }))}
                  className="input"
                >
                  <option value="">Selecciona el tipo</option>
                  <option value="NUTRITIONIST">Nutricionista</option>
                  <option value="PSYCHOLOGY">Psicología</option>
                </select>
              </div>

              <div>
                <label className="label">¿Es tu primera consulta?</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setVideoConsultationFormData(prev => ({ ...prev, is_first_consultation: true }))}
                    className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                      videoConsultationFormData.is_first_consultation
                        ? 'bg-violet-100 text-violet-700 border-violet-300'
                        : 'bg-gray-50 text-gray-500 border-gray-200'
                    }`}
                  >
                    Sí, primera vez
                  </button>
                  <button
                    onClick={() => setVideoConsultationFormData(prev => ({ ...prev, is_first_consultation: false }))}
                    className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                      !videoConsultationFormData.is_first_consultation
                        ? 'bg-violet-100 text-violet-700 border-violet-300'
                        : 'bg-gray-50 text-gray-500 border-gray-200'
                    }`}
                  >
                    Es seguimiento
                  </button>
                </div>
              </div>

              <div>
                <label className="label">¿Para quién es la consulta?</label>
                <div className="flex gap-2">
                  {[
                    { value: 'TITULAR', label: 'Para mí' },
                    { value: 'FAMILY', label: 'Familiar' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setVideoConsultationFormData(prev => ({ ...prev, patient_type: opt.value }))}
                      className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                        videoConsultationFormData.patient_type === opt.value
                          ? 'bg-violet-100 text-violet-700 border-violet-300'
                          : 'bg-gray-50 text-gray-500 border-gray-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="label">Motivo principal de la consulta *</label>
                <textarea
                  value={videoConsultationFormData.main_reason}
                  onChange={(e) => setVideoConsultationFormData(prev => ({ ...prev, main_reason: e.target.value }))}
                  className="input min-h-[80px]"
                  placeholder={videoConsultationFormData.consultation_type === 'NUTRITIONIST'
                    ? "Ej: Quiero bajar de peso, necesito dieta para diabetes, etc."
                    : "Ej: Ansiedad, estrés laboral, problemas familiares, etc."}
                />
              </div>

              <div>
                <label className="label">Condiciones médicas relevantes</label>
                <textarea
                  value={videoConsultationFormData.medical_conditions}
                  onChange={(e) => setVideoConsultationFormData(prev => ({ ...prev, medical_conditions: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="¿Tienes alguna condición médica que debamos saber?"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Fecha preferida</label>
                  <input
                    type="date"
                    value={videoConsultationFormData.preferred_date}
                    onChange={(e) => setVideoConsultationFormData(prev => ({ ...prev, preferred_date: e.target.value }))}
                    className="input"
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div>
                  <label className="label">Horario preferido</label>
                  <select
                    value={videoConsultationFormData.preferred_time}
                    onChange={(e) => setVideoConsultationFormData(prev => ({ ...prev, preferred_time: e.target.value }))}
                    className="input"
                  >
                    <option value="MORNING">Mañana</option>
                    <option value="AFTERNOON">Tarde</option>
                    <option value="EVENING">Noche</option>
                  </select>
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-xl">
                <p className="text-sm text-blue-800">
                  <strong>Requisitos para la video consulta:</strong>
                </p>
                <ul className="text-sm text-blue-700 mt-2 space-y-1">
                  <li>• Conexión estable a internet</li>
                  <li>• Dispositivo con cámara y micrófono</li>
                  <li>• Lugar tranquilo y privado</li>
                </ul>
              </div>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Video Consulta Validada por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu video consulta ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un coordinador revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">Atrás</button>
              <button
                onClick={() => {
                  const desc = `Video Consulta ${videoConsultationFormData.consultation_type}: ${videoConsultationFormData.is_first_consultation ? 'Primera consulta' : 'Seguimiento'}. Motivo: ${videoConsultationFormData.main_reason}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Lab Exam Form */}
        {step === 3 && selectedService?.formType === 'lab_exam' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-indigo-100 rounded-xl">
                  <TestTube className="text-indigo-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Agendar Examen</h2>
                  <p className="text-sm text-gray-600">{selectedService.description}</p>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getServiceFlowLabel(selectedService.serviceFlow).color}`}>
                {getServiceFlowLabel(selectedService.serviceFlow).icon} {getServiceFlowLabel(selectedService.serviceFlow).label}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Tipo de examen *</label>
                <select
                  value={labExamFormData.exam_type}
                  onChange={(e) => setLabExamFormData(prev => ({ ...prev, exam_type: e.target.value }))}
                  className="input"
                >
                  <option value="">Selecciona el examen</option>
                  {selectedService.id === 'pap_mammogram' ? (
                    <>
                      <option value="PAP">Papanicolau</option>
                      <option value="MAMMOGRAM">Mamografía</option>
                      <option value="PROSTATE">Antígeno Prostático</option>
                    </>
                  ) : selectedService.id === 'xray_service' ? (
                    <>
                      <option value="XRAY_CHEST">Rayos X - Tórax</option>
                      <option value="XRAY_SPINE">Rayos X - Columna</option>
                      <option value="XRAY_EXTREMITY">Rayos X - Extremidad</option>
                      <option value="XRAY_OTHER">Rayos X - Otro</option>
                    </>
                  ) : (
                    <>
                      <option value="BLOOD">Hematología (sangre)</option>
                      <option value="URINE">Análisis de orina</option>
                      <option value="STOOL">Análisis de heces</option>
                      <option value="COMPLETE">Perfil completo</option>
                    </>
                  )}
                </select>
              </div>

              <div>
                <label className="label">¿Para quién es el examen?</label>
                <div className="flex gap-2">
                  {[
                    { value: 'TITULAR', label: 'Para mí' },
                    { value: 'FAMILY', label: 'Familiar' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setLabExamFormData(prev => ({ ...prev, patient_type: opt.value }))}
                      className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                        labExamFormData.patient_type === opt.value
                          ? 'bg-indigo-100 text-indigo-700 border-indigo-300'
                          : 'bg-gray-50 text-gray-500 border-gray-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {labExamFormData.patient_type !== 'TITULAR' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Nombre del paciente</label>
                    <input
                      type="text"
                      value={labExamFormData.patient_name}
                      onChange={(e) => setLabExamFormData(prev => ({ ...prev, patient_name: e.target.value }))}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">Edad</label>
                    <input
                      type="number"
                      value={labExamFormData.patient_age}
                      onChange={(e) => setLabExamFormData(prev => ({ ...prev, patient_age: e.target.value }))}
                      className="input"
                      min="0"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="label">Fecha preferida</label>
                <input
                  type="date"
                  value={labExamFormData.preferred_date}
                  onChange={(e) => setLabExamFormData(prev => ({ ...prev, preferred_date: e.target.value }))}
                  className="input"
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                <input
                  type="checkbox"
                  checked={labExamFormData.has_medical_order}
                  onChange={(e) => setLabExamFormData(prev => ({ ...prev, has_medical_order: e.target.checked }))}
                  className="w-5 h-5 text-indigo-600 rounded"
                />
                <span className="text-sm">Tengo orden médica</span>
              </label>

              {['BLOOD', 'COMPLETE'].includes(labExamFormData.exam_type) && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
                  <p className="text-sm text-yellow-800 font-medium">⚠️ Importante: Ayuno requerido</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Este examen requiere ayuno de 8-12 horas antes de la toma de muestra.
                  </p>
                </div>
              )}

              <div>
                <label className="label">Instrucciones especiales (opcional)</label>
                <textarea
                  value={labExamFormData.special_instructions}
                  onChange={(e) => setLabExamFormData(prev => ({ ...prev, special_instructions: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Alguna indicación especial que debamos saber..."
                />
              </div>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Examen Validado por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu solicitud de examen ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un coordinador médico revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">Atrás</button>
              <button
                onClick={() => {
                  const patientInfo = labExamFormData.patient_type !== 'TITULAR'
                    ? `Paciente: ${labExamFormData.patient_name}. `
                    : '';
                  const desc = `Examen ${labExamFormData.exam_type}: ${patientInfo}${labExamFormData.has_medical_order ? 'Con orden médica. ' : ''}${labExamFormData.special_instructions || ''}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Medication Delivery Form */}
        {step === 3 && selectedService?.formType === 'medication' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-purple-100 rounded-xl">
                  <Pill className="text-purple-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Solicitar Medicamentos</h2>
                  <p className="text-sm text-gray-600">{selectedService.description}</p>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getServiceFlowLabel(selectedService.serviceFlow).color}`}>
                {getServiceFlowLabel(selectedService.serviceFlow).icon} {getServiceFlowLabel(selectedService.serviceFlow).label}
              </span>
            </div>

            <div className="space-y-4">
              <label className="flex items-center gap-3 p-4 bg-green-50 border-2 border-green-200 rounded-xl cursor-pointer">
                <input
                  type="checkbox"
                  checked={medicationFormData.has_prescription}
                  onChange={(e) => setMedicationFormData(prev => ({ ...prev, has_prescription: e.target.checked }))}
                  className="w-5 h-5 text-green-600 rounded"
                />
                <div>
                  <span className="font-medium text-green-900">Tengo receta médica</span>
                  <p className="text-xs text-green-700">Requerido para medicamentos controlados</p>
                </div>
              </label>

              {medicationFormData.has_prescription && (
                <div>
                  <label className="label">Detalles de la receta</label>
                  <textarea
                    value={medicationFormData.prescription_details}
                    onChange={(e) => setMedicationFormData(prev => ({ ...prev, prescription_details: e.target.value }))}
                    className="input"
                    rows={2}
                    placeholder="Doctor que la emitió, fecha, etc."
                  />
                </div>
              )}

              <div>
                <label className="label">Lista de medicamentos *</label>
                <textarea
                  value={medicationFormData.medications_list}
                  onChange={(e) => setMedicationFormData(prev => ({ ...prev, medications_list: e.target.value }))}
                  className="input min-h-[100px]"
                  placeholder="Escribe los medicamentos que necesitas, uno por línea:&#10;Ej: Paracetamol 500mg - 1 caja&#10;Omeprazol 20mg - 2 cajas"
                />
              </div>

              <div>
                <label className="label">¿Qué tan urgente es?</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setMedicationFormData(prev => ({ ...prev, urgency_level: 'NORMAL' }))}
                    className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                      medicationFormData.urgency_level === 'NORMAL'
                        ? 'bg-blue-100 text-blue-700 border-blue-300'
                        : 'bg-gray-50 text-gray-500 border-gray-200'
                    }`}
                  >
                    Normal (24-48 hrs)
                  </button>
                  <button
                    onClick={() => setMedicationFormData(prev => ({ ...prev, urgency_level: 'URGENT' }))}
                    className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                      medicationFormData.urgency_level === 'URGENT'
                        ? 'bg-red-100 text-red-700 border-red-300'
                        : 'bg-gray-50 text-gray-500 border-gray-200'
                    }`}
                  >
                    Urgente (mismo día)
                  </button>
                </div>
              </div>

              <div>
                <label className="label">Dirección de entrega</label>
                <input
                  type="text"
                  value={medicationFormData.delivery_address}
                  onChange={(e) => setMedicationFormData(prev => ({ ...prev, delivery_address: e.target.value }))}
                  className="input"
                  placeholder="Dirección completa para la entrega"
                />
              </div>

              <div>
                <label className="label">Instrucciones especiales</label>
                <textarea
                  value={medicationFormData.special_instructions}
                  onChange={(e) => setMedicationFormData(prev => ({ ...prev, special_instructions: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Ej: Dejar con el portero, llamar antes de llegar, etc."
                />
              </div>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Solicitud Validada por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu solicitud de medicamentos ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un farmacéutico revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">Atrás</button>
              <button
                onClick={() => {
                  const desc = `Medicamentos a domicilio (${medicationFormData.urgency_level === 'URGENT' ? 'URGENTE' : 'Normal'}): ${medicationFormData.medications_list}. ${medicationFormData.has_prescription ? 'Con receta médica.' : ''} Entregar en: ${medicationFormData.delivery_address || formData.location_address}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Delivery/Courier Form */}
        {step === 3 && selectedService?.formType === 'delivery' && !isRoadsideAssistance() && !isHealthAssistance() && (
          <div className="card">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-amber-100 rounded-xl">
                  <Package className="text-amber-600" size={28} />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Solicitar Envío</h2>
                  <p className="text-sm text-gray-600">{selectedService.description}</p>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getServiceFlowLabel(selectedService.serviceFlow).color}`}>
                {getServiceFlowLabel(selectedService.serviceFlow).icon} {getServiceFlowLabel(selectedService.serviceFlow).label}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Tipo de envío *</label>
                <select
                  value={deliveryFormData.delivery_type}
                  onChange={(e) => setDeliveryFormData(prev => ({ ...prev, delivery_type: e.target.value }))}
                  className="input"
                >
                  <option value="">Selecciona el tipo</option>
                  <option value="DOCUMENTS">Documentos</option>
                  <option value="SUPPLIES">Artículos personales</option>
                  <option value="HYGIENE_KIT">Kit de higiene</option>
                  <option value="OTHER">Otro</option>
                </select>
              </div>

              <div>
                <label className="label">¿Qué necesitas enviar/recibir? *</label>
                <textarea
                  value={deliveryFormData.item_description}
                  onChange={(e) => setDeliveryFormData(prev => ({ ...prev, item_description: e.target.value }))}
                  className="input min-h-[80px]"
                  placeholder="Describe los artículos a enviar..."
                />
              </div>

              <div>
                <label className="label">Dirección de recogida</label>
                <input
                  type="text"
                  value={deliveryFormData.pickup_address}
                  onChange={(e) => setDeliveryFormData(prev => ({ ...prev, pickup_address: e.target.value }))}
                  className="input"
                  placeholder="¿Dónde recogemos?"
                />
              </div>

              <div>
                <label className="label">Dirección de entrega</label>
                <input
                  type="text"
                  value={deliveryFormData.delivery_address}
                  onChange={(e) => setDeliveryFormData(prev => ({ ...prev, delivery_address: e.target.value }))}
                  className="input"
                  placeholder="¿Dónde entregamos?"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Nombre del destinatario</label>
                  <input
                    type="text"
                    value={deliveryFormData.recipient_name}
                    onChange={(e) => setDeliveryFormData(prev => ({ ...prev, recipient_name: e.target.value }))}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Teléfono del destinatario</label>
                  <input
                    type="tel"
                    value={deliveryFormData.recipient_phone}
                    onChange={(e) => setDeliveryFormData(prev => ({ ...prev, recipient_phone: e.target.value }))}
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label className="label">Urgencia</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setDeliveryFormData(prev => ({ ...prev, urgency_level: 'NORMAL' }))}
                    className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                      deliveryFormData.urgency_level === 'NORMAL'
                        ? 'bg-blue-100 text-blue-700 border-blue-300'
                        : 'bg-gray-50 text-gray-500 border-gray-200'
                    }`}
                  >
                    Normal
                  </button>
                  <button
                    onClick={() => setDeliveryFormData(prev => ({ ...prev, urgency_level: 'URGENT' }))}
                    className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium ${
                      deliveryFormData.urgency_level === 'URGENT'
                        ? 'bg-red-100 text-red-700 border-red-300'
                        : 'bg-gray-50 text-gray-500 border-gray-200'
                    }`}
                  >
                    Urgente
                  </button>
                </div>
              </div>

              <div>
                <label className="label">Instrucciones especiales</label>
                <textarea
                  value={deliveryFormData.special_instructions}
                  onChange={(e) => setDeliveryFormData(prev => ({ ...prev, special_instructions: e.target.value }))}
                  className="input"
                  rows={2}
                  placeholder="Instrucciones adicionales..."
                />
              </div>
            </div>

            {/* AI Validation Result */}
            {serviceValidation && (
              <div className={`p-4 rounded-xl border-2 ${
                serviceValidation.validation_status === 'APPROVED'
                  ? 'bg-green-50 border-green-300'
                  : serviceValidation.validation_status === 'PENDING_REVIEW'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-3">
                  {serviceValidation.validation_status === 'APPROVED' && (
                    <>
                      <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-green-900">✓ Envío Validado por IA</p>
                        <p className="text-sm text-green-700 mt-1">{serviceValidation.validation_message || 'Tu solicitud de envío ha sido aprobada.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'PENDING_REVIEW' && (
                    <>
                      <AlertCircle className="text-yellow-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-yellow-900">⏳ Revisión de Agente MAWDY</p>
                        <p className="text-sm text-yellow-700 mt-1">{serviceValidation.validation_message || 'Un coordinador revisará tu solicitud.'}</p>
                      </div>
                    </>
                  )}
                  {serviceValidation.validation_status === 'FAILED' && (
                    <>
                      <AlertCircle className="text-red-600 flex-shrink-0" size={24} />
                      <div>
                        <p className="font-bold text-red-900">✗ Validación Fallida</p>
                        <p className="text-sm text-red-700 mt-1">{serviceValidation.validation_message}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => setStep(2)} className="btn btn-outline flex-1">Atrás</button>
              <button
                onClick={() => {
                  const desc = `Envío ${deliveryFormData.delivery_type}: ${deliveryFormData.item_description}. De: ${deliveryFormData.pickup_address} A: ${deliveryFormData.delivery_address}. Destinatario: ${deliveryFormData.recipient_name}`;
                  setFormData(prev => ({ ...prev, description: desc }));
                  if (serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW')) {
                    setStep(4);
                  } else {
                    validateServiceRequest();
                  }
                }}
                disabled={!isServiceFormValid() || validatingService}
                className="btn btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {validatingService ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Evaluando con IA...
                  </>
                ) : serviceValidation && (serviceValidation.validation_status === 'APPROVED' || serviceValidation.validation_status === 'PENDING_REVIEW') ? (
                  'Continuar'
                ) : (
                  'Evaluar con IA'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3/4: Details */}
        {step === (isRoadsideAssistance() || isHealthAssistance() ? 4 : (requiresSpecificForm() ? 4 : 3)) && (
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
              <button
                onClick={() => setStep(isRoadsideAssistance() || isHealthAssistance() ? 3 : (requiresSpecificForm() ? 3 : 2))}
                className="btn btn-outline flex-1"
              >
                Atrás
              </button>
              <button
                onClick={() => setStep(isRoadsideAssistance() || isHealthAssistance() ? 5 : (requiresSpecificForm() ? 5 : 4))}
                disabled={!formData.description || !formData.phone}
                className="btn btn-primary flex-1"
              >
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Step 4/5: Confirmation */}
        {step === (isRoadsideAssistance() || isHealthAssistance() ? 5 : (requiresSpecificForm() ? 5 : 4)) && (
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Shield className="text-green-600" />
              Confirma tu solicitud
            </h2>

            {/* Order Summary */}
            <div className="space-y-4 mb-6">
              {/* MAWDY Service Details */}
              <div className={`p-4 rounded-xl ${
                selectedPlanType === 'DRIVE'
                  ? 'bg-gradient-to-r from-red-50 to-orange-50'
                  : selectedPlanType === 'HEALTH'
                  ? 'bg-gradient-to-r from-pink-50 to-purple-50'
                  : 'bg-gradient-to-r from-blue-50 to-purple-50'
              }`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3">
                    {selectedService && (
                      <div className={`p-2 rounded-lg ${
                        selectedPlanType === 'DRIVE' ? 'bg-red-100' : 'bg-pink-100'
                      }`}>
                        {selectedService.icon}
                      </div>
                    )}
                    <div>
                      <h3 className="font-bold text-lg">
                        {selectedService?.name || categories.find(c => c.id === selectedCategory)?.name}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {selectedPlanType === 'DRIVE' ? 'Plan Drive (Vial)' :
                         selectedPlanType === 'HEALTH' ? 'Plan Health (Salud)' :
                         categories.find(c => c.id === selectedCategory)?.description}
                      </p>
                      <p className="text-sm text-gray-600 mt-2">{formData.description}</p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-gray-500">Incluido en plan</p>
                    <p className="text-2xl font-bold text-green-700">Q0</p>
                    {selectedService?.coverageAmount && selectedService.coverageAmount > 0 && (
                      <p className="text-xs text-gray-500">Cobertura: ${selectedService.coverageAmount}</p>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  {formData.location_address && (
                    <div className="flex items-center gap-1 text-blue-700">
                      <MapPin size={14} />
                      <span className="truncate max-w-[200px]">{formData.location_address}</span>
                    </div>
                  )}
                  {selectedService?.limitPerYear !== null && selectedService?.limitPerYear !== undefined && (
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                      {selectedService.limitPerYear} usos/año
                    </span>
                  )}
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
              <button
                onClick={() => setStep(isRoadsideAssistance() || isHealthAssistance() ? 4 : (requiresSpecificForm() ? 4 : 3))}
                className="btn btn-outline flex-1"
              >
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
