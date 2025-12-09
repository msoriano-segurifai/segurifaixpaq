import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI, userAPI, promoCodesAPI, elearningAPI, aiAPI } from '../../services/api';
import {
  Check, Star, Shield, Truck, Heart, Clock, Wallet, CreditCard,
  ChevronLeft, ChevronRight, Phone, MapPin,
  Ambulance, Home, Scale, Car, Fuel, Key,
  Users, FileText, Zap, Loader2, X, AlertCircle, Table2, Minus, Tag, Gift,
  Sparkles, Send, MessageSquare, Lock, BarChart3
} from 'lucide-react';

// Helper to normalize Guatemala phone numbers to 8 digits
const normalizePhoneNumber = (phone: string): string => {
  // Remove all non-digit characters
  const digits = phone.replace(/\D/g, '');
  // Remove Guatemala country code (502) if present
  if (digits.startsWith('502') && digits.length > 8) {
    return digits.slice(3);
  }
  return digits;
};

interface Plan {
  id: number;
  name: string;
  description: string;
  price_monthly: string | number;
  price_yearly: string | number;
  features: string[];
  is_featured: boolean;
  category_type: string;
  category_name: string;
}

// SegurifAI Benefits Data - Dec 2025
// Prices in GTQ (Quetzales guatemaltecos)
// Protege tu Tarjeta: Q34.99/mes | Protege tu Salud: Q34.99/mes | Protege tu Ruta: Q39.99/mes

// Complete service list for comparison table - SegurifAI Dec 2025
// Three plans: Protege tu Tarjeta, Protege tu Salud, Protege tu Ruta
interface ServiceItem {
  id: string;
  name: string;
  category: 'vial' | 'salud' | 'tarjeta';
  tarjetaLimit: string;
  tarjetaValue: string;
  saludLimit: string;
  saludValue: string;
  rutaLimit: string;
  rutaValue: string;
}

const ALL_SERVICES: ServiceItem[] = [
  // TARJETA SERVICES (Protege tu Tarjeta - Q34.99/mes) - Card Protection
  { id: 'muerte_tarjeta', name: 'Seguro Muerte Accidental', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Q3,000', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'tarjeta_perdida', name: 'Tarjetas Perdidas o Robadas', category: 'tarjeta', tarjetaLimit: '48hrs', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'clonacion', name: 'Protección contra Clonación', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'banda_magnetica', name: 'Falsificación Banda Magnética', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'ingenieria_social', name: 'Cobertura Ingeniería Social', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'phishing', name: 'Cobertura Phishing', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'robo_identidad', name: 'Robo de Identidad Digital', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'spoofing', name: 'Suplantación (Spoofing)', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'vishing', name: 'Fraude Telefónico (Vishing)', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },
  { id: 'compras_internet', name: 'Compras Fraudulentas por Internet', category: 'tarjeta', tarjetaLimit: 'Incluido', tarjetaValue: 'Incluido', saludLimit: '-', saludValue: '-', rutaLimit: '-', rutaValue: '-' },

  // SALUD SERVICES (Protege tu Salud - Q34.99/mes) - Health Assistance - All limits in GTQ
  { id: 'muerte_salud', name: 'Seguro Muerte Accidental', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: 'Incluido', saludValue: 'Q3,000', rutaLimit: '-', rutaValue: '-' },
  { id: 'orientacion_medica', name: 'Orientación Médica Telefónica 24/7', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: 'Ilimitado', saludValue: 'Incluido', rutaLimit: '-', rutaValue: '-' },
  { id: 'especialistas', name: 'Conexión con Especialistas de la Red', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: 'Ilimitado', saludValue: 'Incluido', rutaLimit: '-', rutaValue: '-' },
  { id: 'medicamentos', name: 'Coordinación Medicamentos a Domicilio', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: 'Ilimitado', saludValue: 'Incluido', rutaLimit: '-', rutaValue: '-' },
  { id: 'consulta_presencial', name: 'Consulta Presencial (General/Ginecólogo/Pediatra)', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '3/año', saludValue: 'Q1,170', rutaLimit: '-', rutaValue: '-' },
  { id: 'enfermera', name: 'Cuidados Post-Op Enfermera', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '1/año', saludValue: 'Q780', rutaLimit: '-', rutaValue: '-' },
  { id: 'aseo', name: 'Artículos de Aseo por Hospitalización', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '1/año', saludValue: 'Q780', rutaLimit: '-', rutaValue: '-' },
  { id: 'lab_basico', name: 'Exámenes Lab (Heces, Orina, Hematología)', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '2/año', saludValue: 'Q780', rutaLimit: '-', rutaValue: '-' },
  { id: 'lab_especial', name: 'Exámenes (Papanicoláu/Mamografía/Antígeno)', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '2/año', saludValue: 'Q780', rutaLimit: '-', rutaValue: '-' },
  { id: 'nutricionista', name: 'Nutricionista Video Consulta (Grupo Familiar)', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '4/año', saludValue: 'Q1,170', rutaLimit: '-', rutaValue: '-' },
  { id: 'psicologia', name: 'Psicología Video Consulta (Núcleo Familiar)', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '4/año', saludValue: 'Q1,170', rutaLimit: '-', rutaValue: '-' },
  { id: 'mensajeria', name: 'Mensajería por Hospitalización', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '2/año', saludValue: 'Q470', rutaLimit: '-', rutaValue: '-' },
  { id: 'taxi_familiar', name: 'Taxi Familiar por Hospitalización', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '2/año', saludValue: 'Q780', rutaLimit: '-', rutaValue: '-' },
  { id: 'ambulancia_salud', name: 'Traslado en Ambulancia por Accidente', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '2/año', saludValue: 'Q1,170', rutaLimit: '-', rutaValue: '-' },
  { id: 'taxi_alta', name: 'Taxi al Domicilio tras Alta', category: 'salud', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '1/año', saludValue: 'Q780', rutaLimit: '-', rutaValue: '-' },

  // RUTA SERVICES (Protege tu Ruta - Q39.99/mes) - Roadside Assistance - All limits in GTQ
  { id: 'muerte_ruta', name: 'Seguro Muerte Accidental', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: 'Incluido', rutaValue: 'Q3,000' },
  { id: 'grua', name: 'Grúa del Vehículo (Accidente o falla)', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '3/año', rutaValue: 'Q1,170' },
  { id: 'combustible', name: 'Abasto de Combustible (1 galón)', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '3/año', rutaValue: 'Q1,170 comb.' },
  { id: 'neumaticos', name: 'Cambio de Neumáticos', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '3/año', rutaValue: 'Q1,170 comb.' },
  { id: 'corriente', name: 'Paso de Corriente', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '3/año', rutaValue: 'Q1,170 comb.' },
  { id: 'cerrajeria', name: 'Emergencia de Cerrajería', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '3/año', rutaValue: 'Q1,170 comb.' },
  { id: 'ambulancia_vial', name: 'Servicio de Ambulancia por Accidente', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '1/año', rutaValue: 'Q780' },
  { id: 'conductor', name: 'Conductor Profesional (enfermedad/embriaguez)', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '1/año', rutaValue: 'Q470' },
  { id: 'taxi_aeropuerto', name: 'Taxi al Aeropuerto (viaje al extranjero)', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '1/año', rutaValue: 'Q470' },
  { id: 'legal', name: 'Asistencia Legal Telefónica', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '1/año', rutaValue: 'Q1,560' },
  { id: 'emergencia_hospital', name: 'Apoyo Económico Sala Emergencia', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '1/año', rutaValue: 'Q7,800' },
  { id: 'rayos_x', name: 'Rayos X', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: '1/año', rutaValue: 'Q2,340' },
  { id: 'descuentos', name: 'Descuentos en Red de Proveedores', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: 'Incluido', rutaValue: 'Hasta 20%' },
  { id: 'asistentes', name: 'Asistentes Telefónicos (Repuestos, Médicos)', category: 'vial', tarjetaLimit: '-', tarjetaValue: '-', saludLimit: '-', saludValue: '-', rutaLimit: 'Incluido', rutaValue: 'Incluido' },
];

const SEGURIFAI_BENEFITS: Record<string, {
  serviciosIncluidos: Array<{ icon: React.ReactNode; title: string; description: string; limit?: string }>;
  beneficiosPremium: Array<{ icon: React.ReactNode; title: string; description: string }>;
  coberturaKm: number;
  eventosAnuales: number | string;
  tiempoRespuesta: string;
  planType: 'vial' | 'salud' | 'tarjeta';
}> = {
  // Protege tu Tarjeta (Q34.99/mes) - Card Protection
  'Tarjeta': {
    planType: 'tarjeta',
    serviciosIncluidos: [
      { icon: <Shield size={20} />, title: 'Seguro Muerte Accidental', description: 'Cobertura por fallecimiento', limit: 'Q3,000' },
      { icon: <Wallet size={20} />, title: 'Tarjetas Perdidas o Robadas', description: 'Protección ante pérdida o robo', limit: '48hrs notificar' },
      { icon: <Shield size={20} />, title: 'Protección Clonación', description: 'Falsificación de tarjeta', limit: 'Incluido' },
      { icon: <Shield size={20} />, title: 'Banda Magnética', description: 'Falsificación de banda magnética', limit: 'Incluido' },
      { icon: <Users size={20} />, title: 'Ingeniería Social', description: 'Protección contra manipulación', limit: 'Incluido' },
      { icon: <Shield size={20} />, title: 'Phishing', description: 'Protección contra phishing', limit: 'Incluido' },
      { icon: <Shield size={20} />, title: 'Robo de Identidad', description: 'Protección de identidad digital', limit: 'Incluido' },
      { icon: <Shield size={20} />, title: 'Spoofing', description: 'Suplantación de identidad', limit: 'Incluido' },
      { icon: <Phone size={20} />, title: 'Vishing', description: 'Fraude telefónico', limit: 'Incluido' },
      { icon: <Wallet size={20} />, title: 'Compras Fraudulentas', description: 'Compras no autorizadas por internet', limit: 'Incluido' },
    ],
    beneficiosPremium: [
      { icon: <Shield size={20} />, title: 'Asistencias SegurifAI', description: 'Red de asistencias incluida' },
      { icon: <Clock size={20} />, title: 'Disponibilidad 24/7', description: 'Reporte de fraude siempre disponible' },
      { icon: <MapPin size={20} />, title: 'Cobertura Nacional', description: 'Válido en toda Guatemala' },
      { icon: <Shield size={20} />, title: 'Respaldo SegurifAI', description: 'Respaldado por SegurifAI Guatemala' },
    ],
    coberturaKm: 999,
    eventosAnuales: 'Ilimitado',
    tiempoRespuesta: '48hrs'
  },
  // Protege tu Salud (Q34.99/mes) - Health Assistance - All limits in GTQ
  'Salud': {
    planType: 'salud',
    serviciosIncluidos: [
      { icon: <Shield size={20} />, title: 'Seguro Muerte Accidental', description: 'Cobertura por fallecimiento', limit: 'Q3,000' },
      { icon: <Phone size={20} />, title: 'Orientación Médica Telefónica', description: 'Consulta médica por teléfono 24/7', limit: 'Ilimitado' },
      { icon: <Users size={20} />, title: 'Conexión con Especialistas', description: 'Referencia a médicos de la red', limit: 'Ilimitado' },
      { icon: <Truck size={20} />, title: 'Medicamentos a Domicilio', description: 'Coordinación de envío de medicamentos', limit: 'Ilimitado' },
      { icon: <Heart size={20} />, title: 'Consulta Presencial', description: 'Médico general, ginecólogo o pediatra', limit: '3/año - Q1,170' },
      { icon: <Home size={20} />, title: 'Cuidados Post-Op Enfermera', description: 'Enfermera a domicilio', limit: '1/año - Q780' },
      { icon: <FileText size={20} />, title: 'Artículos de Aseo', description: 'Envío por hospitalización', limit: '1/año - Q780' },
      { icon: <FileText size={20} />, title: 'Exámenes Lab Básicos', description: 'Heces, orina y hematología', limit: '2/año - Q780' },
      { icon: <FileText size={20} />, title: 'Exámenes Especializados', description: 'Papanicoláu, mamografía, antígeno', limit: '2/año - Q780' },
      { icon: <Users size={20} />, title: 'Nutricionista Video', description: 'Video consulta (grupo familiar)', limit: '4/año - Q1,170' },
      { icon: <Heart size={20} />, title: 'Psicología Video', description: 'Video consulta (núcleo familiar)', limit: '4/año - Q1,170' },
      { icon: <Truck size={20} />, title: 'Mensajería Hospitalización', description: 'Servicio de mensajería por emergencia', limit: '2/año - Q470' },
      { icon: <Car size={20} />, title: 'Taxi Familiar', description: 'Por hospitalización del titular', limit: '2/año - Q780' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia por Accidente', description: 'Traslado del titular', limit: '2/año - Q1,170' },
      { icon: <Car size={20} />, title: 'Taxi Post Alta', description: 'Traslado al domicilio', limit: '1/año - Q780' },
    ],
    beneficiosPremium: [
      { icon: <Users size={20} />, title: 'Cobertura Familiar', description: 'Incluye grupo familiar y núcleo familiar' },
      { icon: <Shield size={20} />, title: 'Asistencias SegurifAI', description: 'Red de asistencias incluida' },
      { icon: <Clock size={20} />, title: 'Disponibilidad 24/7', description: 'Orientación médica siempre disponible' },
      { icon: <Shield size={20} />, title: 'Respaldo SegurifAI', description: 'Respaldado por SegurifAI Guatemala' },
    ],
    coberturaKm: 15,
    eventosAnuales: '15+',
    tiempoRespuesta: '24hrs'
  },
  // Protege tu Ruta (Q39.99/mes) - Roadside Assistance - All limits in GTQ
  'Ruta': {
    planType: 'vial',
    serviciosIncluidos: [
      { icon: <Shield size={20} />, title: 'Seguro Muerte Accidental', description: 'Cobertura por fallecimiento', limit: 'Q3,000' },
      { icon: <Truck size={20} />, title: 'Grúa del Vehículo', description: 'Por accidente o falla mecánica', limit: '3/año - Q1,170' },
      { icon: <Fuel size={20} />, title: 'Abasto de Combustible', description: '1 galón de emergencia', limit: '3/año - Q1,170 comb.' },
      { icon: <Car size={20} />, title: 'Cambio de Neumáticos', description: 'Instalación de llanta de repuesto', limit: '3/año - Q1,170 comb.' },
      { icon: <Zap size={20} />, title: 'Paso de Corriente', description: 'Servicio de arranque de batería', limit: '3/año - Q1,170 comb.' },
      { icon: <Key size={20} />, title: 'Cerrajería Vehicular', description: 'Apertura de vehículo 24/7', limit: '3/año - Q1,170 comb.' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia por Accidente', description: 'Traslado médico de emergencia', limit: '1/año - Q780' },
      { icon: <Users size={20} />, title: 'Conductor Profesional', description: 'Por enfermedad o embriaguez', limit: '1/año - Q470' },
      { icon: <Car size={20} />, title: 'Taxi al Aeropuerto', description: 'Por viaje del titular al extranjero', limit: '1/año - Q470' },
      { icon: <Scale size={20} />, title: 'Asistencia Legal Telefónica', description: 'Asesoría legal por accidente', limit: '1/año - Q1,560' },
      { icon: <Heart size={20} />, title: 'Apoyo Emergencia Hospital', description: 'Pago directo al hospital por accidente', limit: '1/año - Q7,800' },
      { icon: <FileText size={20} />, title: 'Rayos X', description: 'Servicio de radiografía', limit: '1/año - Q2,340' },
    ],
    beneficiosPremium: [
      { icon: <Star size={20} />, title: 'Descuentos en Red', description: 'Hasta 20% en proveedores asociados' },
      { icon: <Phone size={20} />, title: 'Asistentes Telefónicos', description: 'Cotización repuestos y referencias médicas' },
      { icon: <Shield size={20} />, title: 'Asistencias SegurifAI', description: 'Red de asistencias incluida' },
      { icon: <Shield size={20} />, title: 'Respaldo SegurifAI', description: 'Respaldado por SegurifAI Guatemala' },
    ],
    coberturaKm: 150,
    eventosAnuales: '14+',
    tiempoRespuesta: '30 min'
  },
};

// Map plan names to benefit keys based on SegurifAI products
const getPlanBenefitKey = (planName: string): string => {
  const name = planName.toLowerCase();
  if (name.includes('tarjeta') || name.includes('card')) return 'Tarjeta';
  if (name.includes('salud') || name.includes('health') || name.includes('médic')) return 'Salud';
  if (name.includes('ruta') || name.includes('vial') || name.includes('drive') || name.includes('road')) return 'Ruta';
  // Default to Ruta for roadside plans
  return 'Ruta';
};

export const Subscriptions: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [currentPlanIndex, setCurrentPlanIndex] = useState(0);
  const [showPAQModal, setShowPAQModal] = useState(false);
  const [selectedPlanForPurchase, setSelectedPlanForPurchase] = useState<Plan | null>(null);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [serviceFilter, setServiceFilter] = useState<'all' | 'vial' | 'salud' | 'tarjeta'>('all');

  // User Profile State (for PAQ phone number)
  const [userProfile, setUserProfile] = useState<any>(null);

  // PAQ PAYPAQ Flow State
  const [paqStep, setPaqStep] = useState<'phone' | 'code' | 'success'>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [paypaqCode, setPaypaqCode] = useState('');
  const [paqError, setPaqError] = useState('');
  const [paqLoading, setPaqLoading] = useState(false);
  const [pendingData, setPendingData] = useState<any>(null);  // Store pending subscription data for confirmation

  // Promo Code State
  const [promoCode, setPromoCode] = useState('');
  const [promoValidating, setPromoValidating] = useState(false);
  const [promoDiscount, setPromoDiscount] = useState<{
    code: string;
    discount_type: string;
    discount_value: number;
    discount_amount: number;
    description: string;
  } | null>(null);
  const [promoError, setPromoError] = useState('');

  // E-Learning State - Promo codes available only until first module completed
  const [hasCompletedFirstModule, setHasCompletedFirstModule] = useState(false);
  const [elearningChecked, setElearningChecked] = useState(false);

  // AI Plan Suggestion State - supports both recommendations and comparisons
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<{
    // Common fields
    is_comparison?: boolean;
    is_combo?: boolean;
    message: string;
    // Recommendation fields
    recommended_plan?: string;
    confidence?: string;
    reason?: string;
    key_services?: string[];
    price_monthly?: string;
    price_yearly?: string;
    // Combo fields
    included_plans?: string[];
    individual_prices?: string[];
    // Comparison fields
    compared_plans?: string[];
    comparison_details?: Array<{
      aspect: string;
      plan1: string;
      plan2: string;
      winner: string;
    }>;
    recommendation?: string;
    key_differences?: string[];
  } | null>(null);
  const [aiError, setAiError] = useState('');

  useEffect(() => {
    loadData();
    loadUserProfile();
    checkElearningProgress();
  }, []);

  // Check if user has completed any e-learning modules
  const checkElearningProgress = async () => {
    try {
      const response = await elearningAPI.getMyProgress();
      const progressData = response.data?.estadisticas || response.data;
      const completedModules = progressData?.modulos_completados || 0;
      setHasCompletedFirstModule(completedModules > 0);
    } catch (error) {
      console.log('Could not check e-learning progress');
      setHasCompletedFirstModule(false);
    } finally {
      setElearningChecked(true);
    }
  };

  const loadUserProfile = async () => {
    try {
      const response = await userAPI.getProfile();
      setUserProfile(response.data);
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  // Auto-select featured plan on load
  useEffect(() => {
    if (plans.length > 0) {
      const featuredIndex = plans.findIndex(p => p.is_featured);
      if (featuredIndex !== -1) {
        setCurrentPlanIndex(featuredIndex);
      }
    }
  }, [plans]);

  const loadData = async () => {
    try {
      const plansRes = await servicesAPI.getPlans();
      // Include ALL plan types: ROADSIDE, HEALTH, and INSURANCE (Seguro de Accidentes Personales)
      const allPlans = plansRes.data.plans || plansRes.data || [];
      setPlans(allPlans);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (plan: Plan, usePAQ: boolean = false) => {
    setPurchasing(plan.id);
    setShowPAQModal(false);
    try {
      if (usePAQ) {
        // Use PAQ wallet payment flow
        // For demo purposes, using a simplified flow
        await servicesAPI.purchaseSubscription(plan.id, billingCycle);
      } else {
        // Regular card payment
        await servicesAPI.purchaseSubscription(plan.id, billingCycle);
      }
      await loadData();
      alert(usePAQ
        ? '¡Pago con PAQ Wallet exitoso! Tu suscripción está activa.'
        : '¡Suscripción comprada exitosamente!'
      );
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al procesar la compra');
    } finally {
      setPurchasing(null);
      setSelectedPlanForPurchase(null);
    }
  };

  const openPAQModal = (plan: Plan) => {
    setSelectedPlanForPurchase(plan);
    setShowPAQModal(true);
    // Reset PAYPAQ flow state and pre-fill user's phone number
    setPaqStep('phone');
    setPhoneNumber(userProfile?.phone_number || '');
    setPaypaqCode('');
    setPaqError('');
    setPaqLoading(false);
  };

  const closePAQModal = () => {
    setShowPAQModal(false);
    setSelectedPlanForPurchase(null);
    setPaqStep('phone');
    setPhoneNumber('');
    setPaypaqCode('');
    setPaqError('');
    setPaqLoading(false);
    setPendingData(null);
    // Reset promo code state
    setPromoCode('');
    setPromoDiscount(null);
    setPromoError('');
  };

  // Validate promo code
  const validatePromoCode = async () => {
    if (!promoCode.trim()) {
      setPromoError('');
      setPromoDiscount(null);
      return;
    }

    setPromoValidating(true);
    setPromoError('');

    try {
      const response = await promoCodesAPI.validatePromoCode(promoCode.trim().toUpperCase());
      const data = response.data;

      if (data.valid) {
        // Calculate discount amount based on plan price
        const planPrice = billingCycle === 'monthly'
          ? parseFloat(String(selectedPlanForPurchase?.price_monthly)) || 0
          : parseFloat(String(selectedPlanForPurchase?.price_yearly)) || 0;

        let discountAmount = 0;
        if (data.discount_type === 'PERCENTAGE') {
          discountAmount = (planPrice * data.discount_value) / 100;
          if (data.max_discount_amount && discountAmount > data.max_discount_amount) {
            discountAmount = data.max_discount_amount;
          }
        } else if (data.discount_type === 'FIXED_AMOUNT') {
          discountAmount = Math.min(data.discount_value, planPrice);
        }

        setPromoDiscount({
          code: data.code,
          discount_type: data.discount_type,
          discount_value: data.discount_value,
          discount_amount: discountAmount,
          description: data.description || `${data.discount_value}${data.discount_type === 'PERCENTAGE' ? '%' : ' GTQ'} de descuento`
        });
      } else {
        setPromoError(data.error || 'Código promocional no válido');
        setPromoDiscount(null);
      }
    } catch (error: any) {
      setPromoError(error.response?.data?.error || 'Error al validar código promocional');
      setPromoDiscount(null);
    } finally {
      setPromoValidating(false);
    }
  };

  // Calculate final price after promo discount
  const getFinalPrice = (): number => {
    if (!selectedPlanForPurchase) return 0;
    const basePrice = billingCycle === 'monthly'
      ? parseFloat(String(selectedPlanForPurchase.price_monthly)) || 0
      : parseFloat(String(selectedPlanForPurchase.price_yearly)) || 0;

    if (promoDiscount) {
      return Math.max(0, basePrice - promoDiscount.discount_amount);
    }
    return basePrice;
  };

  // Get AI Plan Suggestion
  const getAIPlanSuggestion = async () => {
    if (!aiPrompt.trim()) {
      setAiError('Por favor describe tus necesidades de asistencia o seguro');
      return;
    }

    setAiLoading(true);
    setAiError('');
    setAiSuggestion(null);

    try {
      const response = await aiAPI.getPlanSuggestion(aiPrompt.trim());
      const data = response.data;

      // Backend returns { success: true, recommendation: { ... } }
      const recommendation = data.recommendation || data;

      if (recommendation.recommended_plan) {
        setAiSuggestion({
          recommended_plan: recommendation.recommended_plan,
          confidence: recommendation.confidence || 'medium',
          reason: recommendation.reason || '',
          key_services: recommendation.key_services || [],
          message: recommendation.message || ''
        });

        // Auto-navigate to the recommended plan in the carousel
        const planIndex = plans.findIndex(p => {
          const name = p.name.toLowerCase();
          const recommended = recommendation.recommended_plan.toLowerCase();
          return name.includes(recommended) ||
                 // Match new SegurifAI plan names
                 (recommended.includes('tarjeta') && name.includes('tarjeta')) ||
                 (recommended.includes('salud') && name.includes('salud')) ||
                 (recommended.includes('ruta') && name.includes('ruta')) ||
                 // Legacy fallback matching
                 (recommended.includes('vial') && (name.includes('ruta') || name.includes('vial'))) ||
                 (recommended.includes('médic') && name.includes('salud'));
        });
        if (planIndex !== -1) {
          setCurrentPlanIndex(planIndex);
        }
      } else {
        setAiError('No se pudo obtener una recomendación. Intenta de nuevo.');
      }
    } catch (error: any) {
      console.error('AI suggestion error:', error);
      setAiError(error.response?.data?.error || 'Error al procesar tu solicitud. Intenta de nuevo.');
    } finally {
      setAiLoading(false);
    }
  };

  // Step 1: Request PAYPAQ code - sends SMS to customer
  const requestPAYPAQCode = async () => {
    if (!selectedPlanForPurchase || !phoneNumber.trim()) {
      setPaqError('Por favor ingresa tu número de teléfono');
      return;
    }

    setPaqLoading(true);
    setPaqError('');

    try {
      const normalizedPhone = normalizePhoneNumber(phoneNumber);
      if (normalizedPhone.length !== 8) {
        setPaqError('Número de teléfono inválido. Debe ser 8 dígitos.');
        setPaqLoading(false);
        return;
      }
      const response = await servicesAPI.purchaseWithPAQ({
        plan_id: selectedPlanForPurchase.id,
        billing_cycle: billingCycle,
        phone_number: normalizedPhone
      });
      // Store the pending_data from response for use in confirmation step
      setPendingData(response.data.pending_data);
      setPaqStep('code');
    } catch (error: any) {
      setPaqError(error.response?.data?.error || 'Error al generar código PAYPAQ');
    } finally {
      setPaqLoading(false);
    }
  };

  // Step 2: Confirm payment with PAYPAQ code
  const confirmPAYPAQPayment = async () => {
    if (!paypaqCode.trim()) {
      setPaqError('Por favor ingresa el código PAYPAQ');
      return;
    }

    if (!pendingData) {
      setPaqError('Datos de suscripción no encontrados. Reinicia el proceso.');
      return;
    }

    setPaqLoading(true);
    setPaqError('');

    try {
      const normalizedPhone = normalizePhoneNumber(phoneNumber);
      await servicesAPI.confirmPAQPayment({
        paypaq_code: paypaqCode.trim().toUpperCase(),  // PAYPAQ codes are uppercase
        phone_number: normalizedPhone,
        pending_data: pendingData  // Pass the pending data from step 1
      });
      setPaqStep('success');
      await loadData(); // Refresh subscriptions
    } catch (error: any) {
      setPaqError(error.response?.data?.error || 'Código PAYPAQ inválido o expirado');
    } finally {
      setPaqLoading(false);
    }
  };

  // Consistent plan colors: Blue for Vial (Ruta), Pink for Health (Salud), Green for Card (Tarjeta)
  const getPlanColors = (categoryType: string) => {
    const type = categoryType?.toUpperCase();
    const isVial = type === 'ROADSIDE';
    const isCardInsurance = type === 'CARD_INSURANCE';

    if (isVial) {
      return {
        isVial: true,
        isCardInsurance: false,
        iconBg: 'from-blue-100 to-blue-200',
        accent: 'text-blue-600',
        button: 'from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800',
        border: 'border-blue-500',
        badge: 'from-blue-600 to-blue-700',
        indicator: 'bg-blue-600',
        priceBg: 'from-blue-50 to-blue-100',
      };
    }

    if (isCardInsurance) {
      return {
        isVial: false,
        isCardInsurance: true,
        iconBg: 'from-emerald-100 to-green-200',
        accent: 'text-emerald-600',
        button: 'from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700',
        border: 'border-emerald-500',
        badge: 'from-emerald-600 to-green-600',
        indicator: 'bg-emerald-600',
        priceBg: 'from-emerald-50 to-green-100',
      };
    }

    // Default: Health (Pink)
    return {
      isVial: false,
      isCardInsurance: false,
      iconBg: 'from-pink-100 to-rose-200',
      accent: 'text-pink-600',
      button: 'from-pink-600 to-rose-600 hover:from-pink-700 hover:to-rose-700',
      border: 'border-pink-500',
      badge: 'from-pink-600 to-rose-600',
      indicator: 'bg-pink-600',
      priceBg: 'from-pink-50 to-rose-100',
    };
  };

  const getIcon = (categoryType: string) => {
    switch (categoryType?.toUpperCase()) {
      case 'ROADSIDE': return <Car className="text-blue-600" size={32} />;
      case 'CARD_INSURANCE': return <CreditCard className="text-emerald-600" size={32} />;
      case 'HEALTH': return <Heart className="text-pink-600" size={32} />;
      default: return <Star className="text-purple-600" size={32} />;
    }
  };

  const nextPlan = () => {
    setCurrentPlanIndex((prev) => (prev + 1) % plans.length);
  };

  const prevPlan = () => {
    setCurrentPlanIndex((prev) => (prev - 1 + plans.length) % plans.length);
  };

  const currentPlan = plans[currentPlanIndex];
  const benefitKey = currentPlan ? getPlanBenefitKey(currentPlan.name) : 'Ruta';
  const currentBenefits = SEGURIFAI_BENEFITS[benefitKey] || SEGURIFAI_BENEFITS['Ruta'];

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="user">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Planes de Protección</h1>
          <p className="text-gray-500 mt-2">Protege tu Tarjeta, tu Salud y tu Ruta con SegurifAI</p>
        </div>

        {/* Billing Toggle */}
        <div className="flex justify-center">
          <div className="bg-gray-100 p-1 rounded-xl inline-flex">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                billingCycle === 'monthly'
                  ? 'bg-white shadow text-blue-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Mensual
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                billingCycle === 'yearly'
                  ? 'bg-white shadow text-blue-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Anual
            </button>
          </div>
        </div>

        {/* Plan Carousel */}
        {plans.length === 0 && !loading && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <p className="text-gray-500">No hay planes disponibles en este momento.</p>
            <p className="text-sm text-gray-400 mt-2">Por favor, intenta de nuevo más tarde.</p>
          </div>
        )}
        {plans.length > 0 && currentPlan && (
          <div className="relative">
            {/* Carousel Navigation */}
            <div className="flex items-center justify-center gap-4 mb-6">
              <button
                onClick={prevPlan}
                className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                aria-label="Plan anterior"
              >
                <ChevronLeft size={24} />
              </button>

              {/* Plan Indicators */}
              <div className="flex gap-2">
                {plans.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentPlanIndex(index)}
                    className={`w-3 h-3 rounded-full transition-all ${
                      index === currentPlanIndex
                        ? 'bg-blue-600 w-8'
                        : 'bg-gray-300 hover:bg-gray-400'
                    }`}
                    aria-label={`Ver plan ${index + 1}`}
                  />
                ))}
              </div>

              <button
                onClick={nextPlan}
                className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                aria-label="Plan siguiente"
              >
                <ChevronRight size={24} />
              </button>
            </div>

            {/* Current Plan Card - Color-coded by plan type */}
            {(() => {
              const colors = getPlanColors(currentPlan.category_type);
              return (
                <div className={`card relative mx-auto max-w-2xl transition-all duration-300 ${
                  currentPlan.is_featured ? `border-2 ${colors.border} shadow-xl` : 'shadow-lg'
                }`}>
                  {currentPlan.is_featured && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className={`bg-gradient-to-r ${colors.badge} text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg`}>
                        ⭐ Más Popular
                      </span>
                    </div>
                  )}

                  <div className="text-center mb-6 pt-4">
                    <div className={`w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${colors.iconBg} flex items-center justify-center`}>
                      {getIcon(currentPlan.category_type)}
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900">{currentPlan.name}</h3>
                    <p className="text-gray-500 mt-1">{currentPlan.description}</p>
                    <span className={`inline-block mt-2 text-xs font-medium px-3 py-1 rounded-full ${
                      colors.isVial ? 'bg-blue-100 text-blue-700' :
                      colors.isCardInsurance ? 'bg-emerald-100 text-emerald-700' :
                      'bg-pink-100 text-pink-700'
                    }`}>
                      {colors.isVial ? '🚗 Protege tu Ruta' : colors.isCardInsurance ? '💳 Protege tu Tarjeta' : '💊 Protege tu Salud'}
                    </span>
                  </div>

                  {/* Price Display */}
                  <div className={`text-center mb-6 p-4 bg-gradient-to-r ${colors.priceBg} rounded-xl`}>
                    <div className="flex items-baseline justify-center gap-1">
                      <span className={`text-5xl font-bold ${colors.isVial ? 'text-blue-900' : 'text-pink-900'}`}>
                        Q{billingCycle === 'monthly' ? currentPlan.price_monthly : currentPlan.price_yearly}
                      </span>
                      <span className="text-gray-500 text-lg">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                    </div>
                  </div>

                  {/* Coverage Stats - Hide KM for Card plans */}
                  <div className={`grid ${colors.isCardInsurance ? 'grid-cols-2' : 'grid-cols-3'} gap-4 mb-6`}>
                    {!colors.isCardInsurance && (
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className={`text-2xl font-bold ${colors.accent}`}>{currentBenefits.coberturaKm === 999 ? '∞' : currentBenefits.coberturaKm}</div>
                        <div className="text-xs text-gray-500">{colors.isVial ? 'KM Grúa' : 'KM Cobertura'}</div>
                      </div>
                    )}
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className={`text-2xl font-bold ${colors.accent}`}>{currentBenefits.eventosAnuales}</div>
                      <div className="text-xs text-gray-500">Eventos/Año</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className={`text-2xl font-bold ${colors.accent}`}>{currentBenefits.tiempoRespuesta}</div>
                      <div className="text-xs text-gray-500">Respuesta</div>
                    </div>
                  </div>

              {/* Servicios Incluidos - ABOVE payment button */}
              <div className="mb-6">
                <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Check className="text-green-500" size={20} />
                  Servicios Incluidos
                </h4>
                <div className="grid grid-cols-1 gap-2">
                  {currentBenefits.serviciosIncluidos.map((servicio, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <div className="p-2 bg-blue-50 rounded-lg text-blue-600 flex-shrink-0">
                        {servicio.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 text-sm">{servicio.title}</p>
                        <p className="text-xs text-gray-500 truncate">{servicio.description}</p>
                      </div>
                      {servicio.limit && (
                        <span className="text-xs font-medium bg-green-100 text-green-700 px-2 py-1 rounded-full whitespace-nowrap">
                          {servicio.limit}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Beneficios Premium - ABOVE payment button */}
              <div className="mb-6">
                <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Star className="text-yellow-500" size={20} />
                  Beneficios Premium
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {currentBenefits.beneficiosPremium.map((beneficio, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-3 p-3 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-100 rounded-lg"
                    >
                      <div className="p-2 bg-yellow-100 rounded-lg text-yellow-600 flex-shrink-0">
                        {beneficio.icon}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{beneficio.title}</p>
                        <p className="text-xs text-gray-500">{beneficio.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Payment Button - PAQ Wallet Only */}
              <div className="space-y-3">
                <button
                  onClick={() => openPAQModal(currentPlan)}
                  disabled={purchasing === currentPlan.id}
                  className="w-full py-4 bg-gradient-to-r from-[#00A86B] to-[#00875A] hover:from-[#00875A] hover:to-[#006644] text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-3"
                >
                  {purchasing === currentPlan.id ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Procesando...
                    </>
                  ) : (
                    <>
                      <Wallet size={22} />
                      Suscribirse con PAQ Wallet
                    </>
                  )}
                </button>
                <p className="text-center text-xs text-gray-500">
                  Pago seguro con tu billetera PAQ
                </p>
              </div>

            </div>
              );
            })()}
          </div>
        )}

        {/* Compare Plans Button */}
        <div className="flex justify-center mt-8">
          <button
            onClick={() => setShowComparisonModal(true)}
            className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-800 font-semibold rounded-xl shadow-md hover:shadow-lg transition-all border border-gray-300"
          >
            <Table2 size={22} />
            Ver Tabla Comparativa de Todos los Planes
          </button>
        </div>

        {/* Features Banner */}
        <div className="card bg-gradient-to-r from-blue-900 to-purple-900 text-white">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
            <div>
              <Clock size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">24/7/365</h4>
              <p className="text-sm text-blue-200">Siempre disponibles</p>
            </div>
            <div>
              <Shield size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">Asistencia Profesional</h4>
              <p className="text-sm text-blue-200">Empresa líder en asistencias</p>
            </div>
            <div>
              <MapPin size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">Cobertura Nacional</h4>
              <p className="text-sm text-blue-200">En toda Guatemala</p>
            </div>
            <div>
              <Star size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">+50,000 Servicios</h4>
              <p className="text-sm text-blue-200">Clientes satisfechos</p>
            </div>
          </div>
        </div>
      </div>

      {/* PAQ Wallet Payment Modal with PAYPAQ Flow - SegurifAI Blue */}
      {showPAQModal && selectedPlanForPurchase && (
        <div className="fixed inset-0 bg-blue-900 bg-opacity-60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden">
            {/* PAQ Brand Header - Green PAQ branding */}
            <div className="bg-gradient-to-r from-[#00A86B] to-[#00875A] p-4 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
                    <Wallet className="text-[#00A86B]" size={24} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">
                      {paqStep === 'success' ? '¡Pago Exitoso!' : 'PAQ Wallet'}
                    </h3>
                    <p className="text-xs text-green-100">Pago seguro y rápido</p>
                  </div>
                </div>
                {paqStep !== 'success' && (
                  <button
                    onClick={closePAQModal}
                    className="p-2 hover:bg-white/20 rounded-full transition-colors"
                  >
                    <X size={20} />
                  </button>
                )}
              </div>
            </div>

            <div className="p-6">
            {/* Plan Summary - Always shown except on success */}
            {paqStep !== 'success' && (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-4 rounded-xl mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Plan:</span>
                  <span className="font-bold">{selectedPlanForPurchase.name}</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Período:</span>
                  <span className="font-medium">{billingCycle === 'monthly' ? 'Mensual' : 'Anual'}</span>
                </div>

                {/* Promo Code - LOCKED until e-learning is completed */}
                {elearningChecked && !hasCompletedFirstModule && (
                  <div className="pt-3 border-t border-gray-200 mb-3">
                    <div className="p-3 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-300 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Lock className="text-amber-600" size={18} />
                        <p className="text-sm font-bold text-amber-700">
                          Código Promocional Bloqueado
                        </p>
                      </div>
                      <p className="text-xs text-amber-600">
                        Completa al menos un módulo de e-learning para desbloquear códigos promocionales.
                      </p>
                      <a
                        href="/elearning"
                        className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-amber-700 hover:text-amber-800 underline"
                      >
                        Ir al Centro de Aprendizaje →
                      </a>
                    </div>
                  </div>
                )}

                {/* Promo Code Input - UNLOCKED after e-learning completion */}
                {elearningChecked && hasCompletedFirstModule && (
                  <div className="pt-3 border-t border-gray-200 mb-3">
                    <label className="text-xs font-medium text-gray-600 flex items-center gap-1 mb-2">
                      <Tag size={12} />
                      Código Promocional (opcional)
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={promoCode}
                        onChange={(e) => {
                          setPromoCode(e.target.value.toUpperCase());
                          setPromoDiscount(null);
                          setPromoError('');
                        }}
                        placeholder="Ej: BIENVENIDO20"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 uppercase"
                        disabled={promoValidating}
                      />
                      <button
                        onClick={validatePromoCode}
                        disabled={promoValidating || !promoCode.trim()}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        {promoValidating ? (
                          <Loader2 className="animate-spin" size={16} />
                        ) : (
                          'Aplicar'
                        )}
                      </button>
                    </div>
                    {promoError && (
                      <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                        <AlertCircle size={12} />
                        {promoError}
                      </p>
                    )}
                    {promoDiscount && (
                      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                        <Gift className="text-green-600" size={16} />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-green-700">{promoDiscount.code}</p>
                          <p className="text-xs text-green-600">{promoDiscount.description}</p>
                        </div>
                        <span className="text-green-700 font-bold">-Q{promoDiscount.discount_amount.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Price Summary */}
                {promoDiscount && (
                  <div className="flex justify-between items-center text-sm text-gray-500 mb-1">
                    <span>Subtotal:</span>
                    <span>Q{billingCycle === 'monthly'
                      ? selectedPlanForPurchase.price_monthly
                      : selectedPlanForPurchase.price_yearly}</span>
                  </div>
                )}
                {promoDiscount && (
                  <div className="flex justify-between items-center text-sm text-green-600 mb-2">
                    <span>Descuento:</span>
                    <span>-Q{promoDiscount.discount_amount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between items-center pt-2 border-t border-gray-200">
                  <span className="text-gray-900 font-bold">Total:</span>
                  <span className="text-2xl font-bold text-blue-600">
                    Q{getFinalPrice().toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            {/* Step Indicator - SegurifAI Blue */}
            {paqStep !== 'success' && (
              <div className="flex items-center justify-center gap-2 mb-6">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  paqStep === 'phone' ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
                }`}>
                  {paqStep === 'phone' ? '1' : <Check size={16} />}
                </div>
                <div className={`w-12 h-1 rounded ${paqStep === 'code' ? 'bg-blue-600' : 'bg-gray-300'}`} />
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  paqStep === 'code' ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-500'
                }`}>
                  2
                </div>
              </div>
            )}

            {/* Error Message */}
            {paqError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-center gap-3">
                <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
                <p className="text-red-700 text-sm">{paqError}</p>
              </div>
            )}

            {/* Step 1: Phone Number Input */}
            {paqStep === 'phone' && (
              <>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Número de Teléfono PAQ Wallet
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                    <input
                      type="tel"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      placeholder="Ej: 5555-1234"
                      className="w-full pl-12 pr-4 py-3 border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Ingresa el número asociado a tu cuenta PAQ Wallet. Recibirás un código PAYPAQ por SMS.
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={closePAQModal}
                    className="flex-1 py-3 border-2 border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-all"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={requestPAYPAQCode}
                    disabled={paqLoading || !phoneNumber.trim()}
                    className="flex-1 py-3 bg-gradient-to-r from-[#00A86B] to-[#00875A] text-white font-bold rounded-xl hover:from-[#00875A] hover:to-[#006644] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {paqLoading ? (
                      <>
                        <Loader2 className="animate-spin" size={20} />
                        Enviando...
                      </>
                    ) : (
                      <>
                        <Phone size={20} />
                        Solicitar Código PAYPAQ
                      </>
                    )}
                  </button>
                </div>
              </>
            )}

            {/* Step 2: PAYPAQ Code Input */}
            {paqStep === 'code' && (
              <>
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4">
                  <p className="text-green-800 text-sm">
                    📱 Hemos enviado un <strong>código PAYPAQ</strong> de 5 caracteres a <strong>{phoneNumber}</strong>
                  </p>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Código PAYPAQ
                  </label>
                  <input
                    type="text"
                    value={paypaqCode}
                    onChange={(e) => setPaypaqCode(e.target.value.toUpperCase().slice(0, 6))}
                    placeholder="Ej: A1B2C"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-[#00A86B] focus:ring-2 focus:ring-green-200 transition-all text-center text-2xl tracking-widest font-mono uppercase"
                    maxLength={6}
                    autoFocus
                  />
                  <p className="text-xs text-gray-500 mt-2 text-center">
                    El código tiene 5 caracteres y es válido por 24 horas
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setPaqStep('phone')}
                    className="flex-1 py-3 border-2 border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-all"
                  >
                    Cambiar Número
                  </button>
                  <button
                    onClick={confirmPAYPAQPayment}
                    disabled={paqLoading || paypaqCode.length < 4}
                    className="flex-1 py-3 bg-gradient-to-r from-[#00A86B] to-[#00875A] text-white font-bold rounded-xl hover:from-[#00875A] hover:to-[#006644] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {paqLoading ? (
                      <>
                        <Loader2 className="animate-spin" size={20} />
                        Procesando Pago...
                      </>
                    ) : (
                      <>
                        <Check size={20} />
                        Confirmar Pago
                      </>
                    )}
                  </button>
                </div>

                <button
                  onClick={requestPAYPAQCode}
                  disabled={paqLoading}
                  className="w-full mt-3 py-2 text-[#00A86B] hover:text-[#00875A] font-medium text-sm"
                >
                  ¿No recibiste el código? Solicitar nuevo
                </button>
              </>
            )}

            {/* Success Step */}
            {paqStep === 'success' && (
              <div className="text-center py-6">
                <div className="w-20 h-20 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                  <Check className="text-[#00A86B]" size={40} />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-2">¡Pago Completado!</h4>
                <p className="text-gray-600 mb-6">
                  Tu suscripción al plan <strong>{selectedPlanForPurchase.name}</strong> está ahora activa.
                </p>
                <button
                  onClick={closePAQModal}
                  className="w-full py-3 bg-gradient-to-r from-[#00A86B] to-[#00875A] text-white font-bold rounded-xl hover:from-[#00875A] hover:to-[#006644] transition-all"
                >
                  ¡Entendido!
                </button>
              </div>
            )}
            </div>
          </div>
        </div>
      )}

      {/* Full Comparison Table Modal - FULL SCREEN Design */}
      {showComparisonModal && (
        <div className="fixed inset-0 bg-gray-50 z-50 overflow-y-auto">
          <div className="min-h-screen">
            {/* Modal Header - Cleaner Design */}
            <div className="sticky top-0 bg-white border-b border-gray-200 shadow-sm z-10">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                    <Table2 className="text-white" size={20} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Compara Nuestros Planes</h3>
                    <p className="text-sm text-gray-500">Encuentra el plan perfecto para ti</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowComparisonModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2 text-gray-600"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
              {/* AI Plan Suggestion Section - Redesigned */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                {/* AI Header */}
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
                      <Sparkles className="text-white" size={20} />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">Asistente IA</h4>
                      <p className="text-sm text-white/80">Te ayudamos a elegir el plan ideal</p>
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  {/* AI Prompt Input - Mobile-First with Large Text Area */}
                  <div className="space-y-3 mb-4">
                    <div className="relative">
                      <MessageSquare className="absolute left-4 top-4 text-gray-400" size={18} />
                      <textarea
                        value={aiPrompt}
                        onChange={(e) => setAiPrompt(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && !aiLoading && getAIPlanSuggestion()}
                        placeholder="Cuéntanos sobre tus necesidades de protección. Por ejemplo: 'Tengo un carro nuevo y quiero protegerlo' o 'Busco cobertura médica para mi familia de 4 personas'..."
                        className="w-full pl-11 pr-4 py-4 min-h-[120px] sm:min-h-[100px] border border-gray-300 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-100 transition-all text-gray-700 bg-gray-50 resize-none text-base leading-relaxed"
                        disabled={aiLoading}
                        rows={4}
                      />
                      <p className="absolute bottom-3 right-3 text-xs text-gray-400">Shift+Enter para nueva línea</p>
                    </div>
                    <button
                      onClick={getAIPlanSuggestion}
                      disabled={aiLoading || !aiPrompt.trim()}
                      className="w-full sm:w-auto px-6 py-4 sm:py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {aiLoading ? (
                        <>
                          <Loader2 className="animate-spin" size={18} />
                          <span>Analizando tu situación...</span>
                        </>
                      ) : (
                        <>
                          <Send size={18} />
                          Obtener Recomendación Personalizada
                        </>
                      )}
                    </button>
                  </div>

                  {/* AI Error */}
                  {aiError && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-center gap-3">
                      <AlertCircle className="text-red-500 flex-shrink-0" size={18} />
                      <p className="text-red-700 text-sm">{aiError}</p>
                    </div>
                  )}

                  {/* AI Suggestion Result - Enhanced Card Design */}
                  {aiSuggestion && (
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-5">
                      {/* COMPARISON VIEW */}
                      {aiSuggestion.is_comparison ? (
                        <div>
                          <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center">
                              <BarChart3 className="text-purple-600" size={20} />
                            </div>
                            <div>
                              <h5 className="font-bold text-gray-900">Comparación de Planes</h5>
                              <p className="text-sm text-gray-500">
                                {aiSuggestion.compared_plans?.join(' vs ')}
                              </p>
                            </div>
                          </div>

                          {/* Comparison Table - Cleaner */}
                          {aiSuggestion.comparison_details && aiSuggestion.comparison_details.length > 0 && (
                            <div className="overflow-x-auto mb-4 bg-white rounded-lg border border-gray-200">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b border-gray-200">
                                    <th className="text-left p-3 font-semibold text-gray-700 bg-gray-50">Aspecto</th>
                                    <th className="text-center p-3 font-semibold text-blue-700 bg-blue-50/50">
                                      {aiSuggestion.compared_plans?.[0]}
                                    </th>
                                    <th className="text-center p-3 font-semibold text-pink-700 bg-pink-50/50">
                                      {aiSuggestion.compared_plans?.[1]}
                                    </th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {aiSuggestion.comparison_details.map((detail, idx) => (
                                    <tr key={idx} className="border-b border-gray-100 last:border-0">
                                      <td className="p-3 font-medium text-gray-700">{detail.aspect}</td>
                                      <td className={`p-3 text-center ${detail.winner === aiSuggestion.compared_plans?.[0] ? 'bg-green-50 text-green-700 font-semibold' : 'text-gray-600'}`}>
                                        {detail.plan1}
                                        {detail.winner === aiSuggestion.compared_plans?.[0] && <Check size={14} className="inline ml-1 text-green-600" />}
                                      </td>
                                      <td className={`p-3 text-center ${detail.winner === aiSuggestion.compared_plans?.[1] ? 'bg-green-50 text-green-700 font-semibold' : 'text-gray-600'}`}>
                                        {detail.plan2}
                                        {detail.winner === aiSuggestion.compared_plans?.[1] && <Check size={14} className="inline ml-1 text-green-600" />}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}

                          {/* Key Differences */}
                          {aiSuggestion.key_differences && aiSuggestion.key_differences.length > 0 && (
                            <div className="mb-4 bg-white rounded-lg p-4 border border-purple-100">
                              <p className="text-sm font-semibold text-purple-800 mb-2">Diferencias Clave:</p>
                              <ul className="space-y-1">
                                {aiSuggestion.key_differences.map((diff, idx) => (
                                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                    <span className="text-purple-500 mt-0.5">•</span>
                                    {diff}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* AI Message */}
                          <p className="text-gray-700 text-sm mb-3">{aiSuggestion.message}</p>

                          {/* Recommendation from comparison */}
                          {aiSuggestion.recommendation && (
                            <div className="bg-white border border-green-200 rounded-lg p-3">
                              <p className="text-sm text-green-800">
                                <span className="font-semibold">💡 Recomendación:</span> {aiSuggestion.recommendation}
                              </p>
                            </div>
                          )}
                        </div>
                      ) : (
                        /* RECOMMENDATION VIEW - Enhanced & Organized */
                        <div className="space-y-4">
                          {/* Header Section */}
                          <div className={`p-4 rounded-xl ${
                            aiSuggestion.is_combo ? 'bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200' :
                            aiSuggestion.recommended_plan?.toLowerCase().includes('ruta') ? 'bg-blue-50 border border-blue-200' :
                            aiSuggestion.recommended_plan?.toLowerCase().includes('salud') ? 'bg-pink-50 border border-pink-200' :
                            aiSuggestion.recommended_plan?.toLowerCase().includes('tarjeta') ? 'bg-green-50 border border-green-200' :
                            'bg-purple-50 border border-purple-200'
                          }`}>
                            <div className="flex items-center gap-3">
                              <div className={`w-14 h-14 rounded-xl flex items-center justify-center shadow-sm ${
                                aiSuggestion.is_combo ? 'bg-gradient-to-br from-purple-500 to-blue-500' :
                                aiSuggestion.recommended_plan?.toLowerCase().includes('ruta') ? 'bg-blue-500' :
                                aiSuggestion.recommended_plan?.toLowerCase().includes('salud') ? 'bg-pink-500' :
                                aiSuggestion.recommended_plan?.toLowerCase().includes('tarjeta') ? 'bg-green-500' : 'bg-purple-500'
                              }`}>
                                {aiSuggestion.is_combo ? (
                                  <Sparkles className="text-white" size={28} />
                                ) : aiSuggestion.recommended_plan?.toLowerCase().includes('ruta') ? (
                                  <Car className="text-white" size={28} />
                                ) : aiSuggestion.recommended_plan?.toLowerCase().includes('salud') ? (
                                  <Heart className="text-white" size={28} />
                                ) : aiSuggestion.recommended_plan?.toLowerCase().includes('tarjeta') ? (
                                  <CreditCard className="text-white" size={28} />
                                ) : (
                                  <Shield className="text-white" size={28} />
                                )}
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                                    aiSuggestion.confidence === 'alta' ? 'bg-green-500 text-white' :
                                    aiSuggestion.confidence === 'media' ? 'bg-yellow-500 text-white' : 'bg-gray-500 text-white'
                                  }`}>
                                    {aiSuggestion.confidence === 'alta' ? '✓ RECOMENDADO' :
                                     aiSuggestion.confidence === 'media' ? 'SUGERIDO' : 'OPCIÓN'}
                                  </span>
                                </div>
                                <h4 className="text-xl font-bold text-gray-900 mt-1">{aiSuggestion.recommended_plan}</h4>
                                {aiSuggestion.price_monthly && (
                                  <p className="text-2xl font-bold text-green-600 mt-1">
                                    {aiSuggestion.price_monthly}<span className="text-sm font-normal text-gray-500">/mes</span>
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Combo: Included Plans */}
                          {aiSuggestion.is_combo && aiSuggestion.included_plans && (
                            <div className="bg-white rounded-xl border border-gray-200 p-4">
                              <h5 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                                <Sparkles size={16} className="text-purple-500" />
                                Planes Incluidos en el Combo
                              </h5>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {aiSuggestion.included_plans.map((plan: string, idx: number) => (
                                  <div key={idx} className="flex items-center gap-2 p-2 bg-purple-50 rounded-lg border border-purple-100">
                                    <Check size={16} className="text-purple-600" />
                                    <span className="text-sm font-medium text-purple-800">{plan}</span>
                                  </div>
                                ))}
                              </div>
                              {aiSuggestion.individual_prices && (
                                <p className="text-xs text-gray-500 mt-3 pt-2 border-t border-gray-100">
                                  Precios por separado: {aiSuggestion.individual_prices.join(' + ')}
                                </p>
                              )}
                            </div>
                          )}

                          {/* Why This Plan */}
                          <div className="bg-white rounded-xl border border-gray-200 p-4">
                            <h5 className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                              <MessageSquare size={16} className="text-blue-500" />
                              ¿Por qué este plan?
                            </h5>
                            <p className="text-gray-600 text-sm leading-relaxed">{aiSuggestion.message}</p>
                            {aiSuggestion.reason && (
                              <p className="text-xs text-gray-500 mt-3 pt-3 border-t border-gray-100 italic">
                                💡 {aiSuggestion.reason}
                              </p>
                            )}
                          </div>

                          {/* Key Services */}
                          {aiSuggestion.key_services && aiSuggestion.key_services.length > 0 && (
                            <div className="bg-white rounded-xl border border-gray-200 p-4">
                              <h5 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                                <Check size={16} className="text-green-500" />
                                Servicios Clave Para Ti
                              </h5>
                              <div className="space-y-2">
                                {aiSuggestion.key_services.map((service, idx) => (
                                  <div key={idx} className="flex items-center gap-3 p-2 bg-green-50 rounded-lg">
                                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                                      <Check size={14} className="text-white" />
                                    </div>
                                    <span className="text-sm text-gray-700">{service}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Action Button */}
                          <div className="pt-2">
                            <button
                              onClick={() => setShowComparisonModal(false)}
                              className={`w-full py-3 font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg ${
                                aiSuggestion.is_combo ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white' :
                                aiSuggestion.recommended_plan?.toLowerCase().includes('ruta') ? 'bg-blue-600 hover:bg-blue-700 text-white' :
                                aiSuggestion.recommended_plan?.toLowerCase().includes('salud') ? 'bg-pink-600 hover:bg-pink-700 text-white' :
                                aiSuggestion.recommended_plan?.toLowerCase().includes('tarjeta') ? 'bg-green-600 hover:bg-green-700 text-white' :
                                'bg-purple-600 hover:bg-purple-700 text-white'
                              }`}
                            >
                              {aiSuggestion.is_combo ? 'Ver Todos los Planes' : 'Ver Detalles del Plan'}
                              <ChevronRight size={18} />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Example Prompts - Cleaner Grid */}
                  {!aiSuggestion && !aiLoading && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                      <div>
                        <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Recomendaciones</p>
                        <div className="flex flex-wrap gap-2">
                          {[
                            'Manejo mucho y mi carro es viejo',
                            'Tengo hijos pequeños',
                            'Uso mi tarjeta en internet',
                            'Protección completa'
                          ].map((example, idx) => (
                            <button
                              key={idx}
                              onClick={() => setAiPrompt(example)}
                              className="text-xs bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg hover:bg-purple-100 hover:text-purple-700 transition-colors border border-transparent hover:border-purple-200"
                            >
                              {example}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Comparaciones</p>
                        <div className="flex flex-wrap gap-2">
                          {[
                            'Ruta vs Salud',
                            '¿Qué incluye Combo?',
                            'Tarjeta vs Salud'
                          ].map((example, idx) => (
                            <button
                              key={idx}
                              onClick={() => setAiPrompt(example)}
                              className="text-xs bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg hover:bg-blue-100 hover:text-blue-700 transition-colors border border-transparent hover:border-blue-200"
                            >
                              {example}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Billing Toggle - Improved */}
              <div className="flex justify-center">
                <div className="bg-white border border-gray-200 p-1 rounded-xl inline-flex shadow-sm">
                  <button
                    onClick={() => setBillingCycle('monthly')}
                    className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
                      billingCycle === 'monthly'
                        ? 'bg-gray-900 text-white shadow-md'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    Mensual
                  </button>
                  <button
                    onClick={() => setBillingCycle('yearly')}
                    className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
                      billingCycle === 'yearly'
                        ? 'bg-gray-900 text-white shadow-md'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    Anual
                  </button>
                </div>
              </div>

              {/* Detailed Feature Comparison Table - Redesigned */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                {/* Table Header */}
                <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                      <h4 className="font-bold text-gray-900 text-lg">Tabla Comparativa</h4>
                      <p className="text-sm text-gray-500">Todos los servicios incluidos en cada plan</p>
                    </div>

                    {/* Filter Buttons - Compact */}
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setServiceFilter('all')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                          serviceFilter === 'all'
                            ? 'bg-gray-900 text-white'
                            : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                        }`}
                      >
                        Todos
                      </button>
                      <button
                        onClick={() => setServiceFilter('tarjeta')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
                          serviceFilter === 'tarjeta'
                            ? 'bg-emerald-600 text-white'
                            : 'bg-white text-emerald-600 hover:bg-emerald-50 border border-emerald-200'
                        }`}
                      >
                        <CreditCard size={14} />
                        Tarjeta
                      </button>
                      <button
                        onClick={() => setServiceFilter('salud')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
                          serviceFilter === 'salud'
                            ? 'bg-pink-600 text-white'
                            : 'bg-white text-pink-600 hover:bg-pink-50 border border-pink-200'
                        }`}
                      >
                        <Heart size={14} />
                        Salud
                      </button>
                      <button
                        onClick={() => setServiceFilter('vial')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
                          serviceFilter === 'vial'
                            ? 'bg-blue-600 text-white'
                            : 'bg-white text-blue-600 hover:bg-blue-50 border border-blue-200'
                        }`}
                      >
                        <Car size={14} />
                        Ruta
                      </button>
                    </div>
                  </div>
                </div>

                {/* Mobile scroll hint */}
                <div className="flex items-center justify-center gap-2 py-2 bg-gray-50 text-gray-500 text-xs border-b border-gray-100 md:hidden">
                  <ChevronLeft size={14} className="animate-pulse" />
                  <span>Desliza para ver todos los planes</span>
                  <ChevronRight size={14} className="animate-pulse" />
                </div>

                <div className="relative">
                  <div
                    className="overflow-auto max-h-[450px]"
                    style={{
                      WebkitOverflowScrolling: 'touch',
                      scrollbarWidth: 'thin',
                      scrollbarColor: '#E5E7EB #F9FAFB'
                    }}
                  >
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 z-20">
                        <tr>
                          <th className="text-left p-4 font-semibold text-gray-700 bg-gray-50 min-w-[200px] sticky left-0 z-30 border-b border-gray-200">
                            Servicio
                          </th>
                          {/* Dynamic columns for ALL database plans */}
                          {plans.map((plan) => {
                            const colors = getPlanColors(plan.category_type);
                            const bgColor = colors.isVial ? 'bg-blue-50' : colors.isCardInsurance ? 'bg-emerald-50' : 'bg-pink-50';
                            const iconBg = colors.isVial ? 'bg-blue-100' : colors.isCardInsurance ? 'bg-emerald-100' : 'bg-pink-100';
                            const textColor = colors.isVial ? 'text-blue-900' : colors.isCardInsurance ? 'text-emerald-900' : 'text-pink-900';
                            const iconColor = colors.isVial ? 'text-blue-600' : colors.isCardInsurance ? 'text-emerald-600' : 'text-pink-600';
                            return (
                              <th
                                key={plan.id}
                                className={`text-center p-3 min-w-[130px] border-b border-gray-200 ${bgColor}`}
                              >
                                <div className="flex flex-col items-center gap-1">
                                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconBg}`}>
                                    {colors.isVial ? <Car size={16} className={iconColor} /> : colors.isCardInsurance ? <CreditCard size={16} className={iconColor} /> : <Heart size={16} className={iconColor} />}
                                  </div>
                                  <span className={`text-xs font-bold leading-tight ${textColor}`}>{plan.name}</span>
                                </div>
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {ALL_SERVICES
                          .filter(service => serviceFilter === 'all' || service.category === serviceFilter)
                          .map((service, idx) => (
                          <tr
                            key={service.id}
                            className={`transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} hover:bg-gray-100/50`}
                          >
                            <td className="p-3 text-gray-700 bg-white sticky left-0 z-10">
                              <div className="flex items-center gap-2">
                                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                  service.category === 'vial' ? 'bg-blue-500' :
                                  service.category === 'tarjeta' ? 'bg-emerald-500' : 'bg-pink-500'
                                }`}></span>
                                <span className="text-xs leading-tight">{service.name}</span>
                              </div>
                            </td>
                            {/* Dynamic cells for each database plan */}
                            {plans.map((plan) => {
                              const colors = getPlanColors(plan.category_type);
                              // Determine if this plan has this service
                              const hasService =
                                (colors.isVial && service.category === 'vial') ||
                                (!colors.isVial && !colors.isCardInsurance && service.category === 'salud') ||
                                (colors.isCardInsurance && service.category === 'tarjeta');
                              // Get the appropriate limit based on plan type
                              const limit = colors.isVial
                                ? service.rutaLimit
                                : colors.isCardInsurance
                                  ? service.tarjetaLimit
                                  : service.saludLimit;
                              const checkBg = colors.isVial ? 'bg-blue-100' : colors.isCardInsurance ? 'bg-emerald-100' : 'bg-pink-100';
                              const checkColor = colors.isVial ? 'text-blue-600' : colors.isCardInsurance ? 'text-emerald-600' : 'text-pink-600';
                              const textColor = colors.isVial ? 'text-blue-700' : colors.isCardInsurance ? 'text-emerald-700' : 'text-pink-700';
                              return (
                                <td key={plan.id} className="p-2 text-center">
                                  {hasService && limit !== '-' ? (
                                    <div className="flex flex-col items-center gap-0.5">
                                      <div className={`w-5 h-5 rounded-full flex items-center justify-center ${checkBg}`}>
                                        <Check size={12} className={checkColor} />
                                      </div>
                                      <span className={`text-[10px] font-medium ${textColor}`}>
                                        {limit}
                                      </span>
                                    </div>
                                  ) : (
                                    <Minus className="mx-auto text-gray-300" size={14} />
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                      {/* Footer with prices and CTA */}
                      <tfoot className="sticky bottom-0 z-20">
                        {/* Price Row */}
                        <tr className="bg-gray-100 border-t-2 border-gray-300">
                          <td className="p-4 font-bold text-gray-900 sticky left-0 bg-gray-100">
                            Precio {billingCycle === 'monthly' ? 'Mensual' : 'Anual'}
                          </td>
                          {plans.map((plan) => {
                            const colors = getPlanColors(plan.category_type);
                            const priceColor = colors.isVial ? 'text-blue-700' : colors.isCardInsurance ? 'text-emerald-700' : 'text-pink-700';
                            const price = billingCycle === 'monthly' ? plan.price_monthly : plan.price_yearly;
                            return (
                              <td key={plan.id} className="p-3 text-center bg-gray-100">
                                <div className="flex flex-col items-center">
                                  <span className={`text-xl font-bold ${priceColor}`}>Q{price}</span>
                                  <span className="text-[10px] text-gray-500">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                        {/* CTA Buttons Row */}
                        <tr className="bg-white">
                          <td className="p-4 sticky left-0 bg-white border-t border-gray-200">
                            <span className="text-xs text-gray-500">Selecciona un plan</span>
                          </td>
                          {plans.map((plan) => {
                            const colors = getPlanColors(plan.category_type);
                            const buttonClass = colors.isVial
                              ? 'bg-blue-600 hover:bg-blue-700 text-white'
                              : colors.isCardInsurance
                              ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                              : 'bg-pink-600 hover:bg-pink-700 text-white';
                            return (
                              <td key={plan.id} className="p-3 text-center border-t border-gray-200">
                                <button
                                  onClick={() => {
                                    setShowComparisonModal(false);
                                    const planIndex = plans.findIndex(p => p.id === plan.id);
                                    if (planIndex !== -1) setCurrentPlanIndex(planIndex);
                                    setTimeout(() => openPAQModal(plan), 300);
                                  }}
                                  className={`w-full px-3 py-2 text-xs font-bold rounded-lg transition-all shadow-sm hover:shadow-md ${buttonClass}`}
                                >
                                  <span className="flex items-center justify-center gap-1">
                                    <Wallet size={12} />
                                    Suscribirse
                                  </span>
                                </button>
                              </td>
                            );
                          })}
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>

                {/* Legend - More compact */}
                <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex flex-wrap justify-center gap-4 sm:gap-6 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span className="text-gray-600">Protege tu Tarjeta</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-pink-500"></span>
                    <span className="text-gray-600">Protege tu Salud</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    <span className="text-gray-600">Protege tu Ruta</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check size={12} className="text-green-600" />
                    <span className="text-gray-600">Servicio incluido</span>
                  </div>
                </div>
              </div>

              {/* Trust Badges - Cleaner Design */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 rounded-xl flex items-center justify-center">
                      <Shield className="text-blue-600" size={24} />
                    </div>
                    <h5 className="font-bold text-gray-900 text-sm">Asistencia Profesional</h5>
                    <p className="text-xs text-gray-500 mt-1">Líder en Guatemala</p>
                  </div>
                  <div className="text-center">
                    <div className="w-12 h-12 mx-auto mb-3 bg-green-100 rounded-xl flex items-center justify-center">
                      <Clock className="text-green-600" size={24} />
                    </div>
                    <h5 className="font-bold text-gray-900 text-sm">24/7/365</h5>
                    <p className="text-xs text-gray-500 mt-1">Siempre disponibles</p>
                  </div>
                  <div className="text-center">
                    <div className="w-12 h-12 mx-auto mb-3 bg-purple-100 rounded-xl flex items-center justify-center">
                      <MapPin className="text-purple-600" size={24} />
                    </div>
                    <h5 className="font-bold text-gray-900 text-sm">Cobertura Nacional</h5>
                    <p className="text-xs text-gray-500 mt-1">En toda Guatemala</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
