import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI, userAPI, promoCodesAPI, elearningAPI, aiAPI } from '../../services/api';
import {
  Check, Star, Shield, Truck, Heart, Clock, Wallet,
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

// MAWDY Benefits Data - Based on official MAWDY PAQ Wallet document (Oct 2025)
// Prices in GTQ (Quetzales guatemaltecos)
// Plan Drive: Q24.41/month (Q292.86/year) | Plan Health: Q22.48/month (Q269.70/year)

// Complete service list for comparison table - matching PDF exactly
// Now includes Combo plan (Drive + Health combined)
interface ServiceItem {
  id: string;
  name: string;
  category: 'vial' | 'salud' | 'both';
  driveLimit: string;
  driveValue: string;
  healthLimit: string;
  healthValue: string;
  comboLimit: string;
  comboValue: string;
}

const ALL_SERVICES: ServiceItem[] = [
  // VIAL SERVICES (Plan Asistencia Vial MAPFRE) - Values in USD
  // Combo plan includes ALL Vial services
  { id: 'muerte_vial', name: 'Seguro Muerte Accidental', category: 'vial', driveLimit: 'Incluido', driveValue: 'Q3,000', healthLimit: '-', healthValue: '-', comboLimit: 'Incluido', comboValue: 'Q6,000' },
  { id: 'grua', name: 'Grua del Vehiculo (Accidente o falla mecanica)', category: 'vial', driveLimit: '3/año', driveValue: '$150 USD', healthLimit: '-', healthValue: '-', comboLimit: '3/año', comboValue: '$150 USD' },
  { id: 'combustible', name: 'Abasto de Combustible (1 galon)', category: 'vial', driveLimit: '3/año', driveValue: '$150 comb.', healthLimit: '-', healthValue: '-', comboLimit: '3/año', comboValue: '$150 comb.' },
  { id: 'neumaticos', name: 'Cambio de Neumaticos', category: 'vial', driveLimit: '3/año', driveValue: '$150 comb.', healthLimit: '-', healthValue: '-', comboLimit: '3/año', comboValue: '$150 comb.' },
  { id: 'corriente', name: 'Paso de Corriente', category: 'vial', driveLimit: '3/año', driveValue: '$150 comb.', healthLimit: '-', healthValue: '-', comboLimit: '3/año', comboValue: '$150 comb.' },
  { id: 'cerrajeria', name: 'Cerrajeria Vehicular', category: 'vial', driveLimit: '3/año', driveValue: '$150 comb.', healthLimit: '-', healthValue: '-', comboLimit: '3/año', comboValue: '$150 comb.' },
  { id: 'ambulancia_vial', name: 'Ambulancia por Accidente', category: 'vial', driveLimit: '1/año', driveValue: '$100 USD', healthLimit: '-', healthValue: '-', comboLimit: '3/año', comboValue: '$250 USD' },
  { id: 'conductor', name: 'Conductor Profesional (enfermedad/embriaguez)', category: 'vial', driveLimit: '1/año', driveValue: '$60 USD', healthLimit: '-', healthValue: '-', comboLimit: '1/año', comboValue: '$60 USD' },
  { id: 'taxi_aeropuerto', name: 'Taxi al Aeropuerto (viaje al extranjero)', category: 'vial', driveLimit: '1/año', driveValue: '$60 USD', healthLimit: '-', healthValue: '-', comboLimit: '1/año', comboValue: '$60 USD' },
  { id: 'legal', name: 'Asistencia Legal Telefonica', category: 'vial', driveLimit: '1/año', driveValue: '$200 USD', healthLimit: '-', healthValue: '-', comboLimit: '1/año', comboValue: '$200 USD' },
  { id: 'emergencia_hospital', name: 'Apoyo Emergencia Hospital', category: 'vial', driveLimit: '1/año', driveValue: '$1,000 USD', healthLimit: '-', healthValue: '-', comboLimit: '1/año', comboValue: '$1,000 USD' },
  { id: 'rayos_x', name: 'Rayos X', category: 'vial', driveLimit: '1/año', driveValue: '$300 USD', healthLimit: '-', healthValue: '-', comboLimit: '1/año', comboValue: '$300 USD' },
  { id: 'descuentos', name: 'Descuentos en Red de Proveedores', category: 'vial', driveLimit: 'Incluido', driveValue: 'Hasta 20%', healthLimit: '-', healthValue: '-', comboLimit: 'Incluido', comboValue: 'Hasta 20%' },
  { id: 'asistentes', name: 'Asistentes Telefonicos (Cotizacion, Referencias)', category: 'vial', driveLimit: 'Incluido', driveValue: 'Incluido', healthLimit: '-', healthValue: '-', comboLimit: 'Incluido', comboValue: 'Incluido' },

  // SALUD SERVICES (Plan Asistencia Medica MAPFRE) - Values in USD
  // Combo plan includes ALL Medica services with enhanced limits
  { id: 'muerte_medica', name: 'Seguro Muerte Accidental', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: 'Incluido', healthValue: 'Q3,000', comboLimit: 'Incluido', comboValue: 'Q6,000' },
  { id: 'orientacion_medica', name: 'Orientacion Medica Telefonica 24/7', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: 'Ilimitado', healthValue: 'Incluido', comboLimit: 'Ilimitado', comboValue: 'Incluido' },
  { id: 'especialistas', name: 'Conexion con Especialistas', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: 'Ilimitado', healthValue: 'Incluido', comboLimit: 'Ilimitado', comboValue: 'Incluido' },
  { id: 'medicamentos', name: 'Coordinacion Medicamentos a Domicilio', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: 'Ilimitado', healthValue: 'Incluido', comboLimit: 'Ilimitado', comboValue: 'Incluido' },
  { id: 'consulta_presencial', name: 'Consulta Presencial (General/Ginecologo/Pediatra)', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '3/año', healthValue: '$150 USD', comboLimit: '6/año', comboValue: '$300 USD' },
  { id: 'enfermera', name: 'Cuidados Post-Op Enfermera', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '1/año', healthValue: '$100 USD', comboLimit: '1/año', comboValue: '$100 USD' },
  { id: 'aseo', name: 'Articulos de Aseo Hospitalizacion', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '1/año', healthValue: '$100 USD', comboLimit: '1/año', comboValue: '$100 USD' },
  { id: 'lab_basico', name: 'Examenes Lab Basicos (Heces, Orina, Hematologia)', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '2/año', healthValue: '$100 USD', comboLimit: '2/año', comboValue: '$100 USD' },
  { id: 'lab_especial', name: 'Examenes Especializados (Papanicolau/Mamografia/Antigeno)', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '2/año', healthValue: '$100 USD', comboLimit: '2/año', comboValue: '$100 USD' },
  { id: 'nutricionista', name: 'Nutricionista Video Consulta (Grupo Familiar)', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '4/año', healthValue: '$150 USD', comboLimit: '8/año', comboValue: '$300 USD' },
  { id: 'psicologia', name: 'Psicologia Video Consulta (Nucleo Familiar)', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '4/año', healthValue: '$150 USD', comboLimit: '8/año', comboValue: '$300 USD' },
  { id: 'mensajeria', name: 'Mensajeria Hospitalizacion', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '2/año', healthValue: '$60 USD', comboLimit: '2/año', comboValue: '$60 USD' },
  { id: 'taxi_familiar', name: 'Taxi Familiar Hospitalizacion', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '2/año', healthValue: '$100 USD', comboLimit: '2/año', comboValue: '$100 USD' },
  { id: 'ambulancia_salud', name: 'Ambulancia Accidente', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '2/año', healthValue: '$150 USD', comboLimit: '2/año', comboValue: '$150 USD' },
  { id: 'taxi_alta', name: 'Taxi Post-Alta (al domicilio)', category: 'salud', driveLimit: '-', driveValue: '-', healthLimit: '1/año', healthValue: '$100 USD', comboLimit: '1/año', comboValue: '$100 USD' },
];

const MAWDY_BENEFITS: Record<string, {
  serviciosIncluidos: Array<{ icon: React.ReactNode; title: string; description: string; limit?: string }>;
  beneficiosPremium: Array<{ icon: React.ReactNode; title: string; description: string }>;
  coberturaKm: number;
  eventosAnuales: number | string;
  tiempoRespuesta: string;
  planType: 'vial' | 'salud';
}> = {
  // Plan Asistencia Vial MAPFRE (Q36.88/mes Inclusion, Q38.93/mes Opcional)
  'Drive': {
    planType: 'vial',
    serviciosIncluidos: [
      { icon: <Shield size={20} />, title: 'Seguro Muerte Accidental', description: 'Cobertura por fallecimiento', limit: 'Q3,000' },
      { icon: <Truck size={20} />, title: 'Grua del Vehiculo', description: 'Por accidente o falla mecanica', limit: '3/año - $150 USD' },
      { icon: <Fuel size={20} />, title: 'Abasto de Combustible', description: '1 galon de emergencia', limit: '3/año - $150 comb.' },
      { icon: <Car size={20} />, title: 'Cambio de Neumaticos', description: 'Instalacion de llanta de repuesto', limit: '3/año - $150 comb.' },
      { icon: <Zap size={20} />, title: 'Paso de Corriente', description: 'Servicio de arranque de bateria', limit: '3/año - $150 comb.' },
      { icon: <Key size={20} />, title: 'Cerrajeria Vehicular', description: 'Apertura de vehiculo 24/7', limit: '3/año - $150 comb.' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia por Accidente', description: 'Traslado medico de emergencia', limit: '1/año - $100 USD' },
      { icon: <Users size={20} />, title: 'Conductor Profesional', description: 'Por enfermedad o embriaguez', limit: '1/año - $60 USD' },
      { icon: <Car size={20} />, title: 'Taxi al Aeropuerto', description: 'Por viaje del titular al extranjero', limit: '1/año - $60 USD' },
      { icon: <Scale size={20} />, title: 'Asistencia Legal Telefonica', description: 'Asesoria legal por accidente', limit: '1/año - $200 USD' },
      { icon: <Heart size={20} />, title: 'Apoyo Emergencia Hospital', description: 'Pago directo al hospital por accidente', limit: '1/año - $1,000 USD' },
      { icon: <FileText size={20} />, title: 'Rayos X', description: 'Servicio de radiografia', limit: '1/año - $300 USD' },
    ],
    beneficiosPremium: [
      { icon: <Star size={20} />, title: 'Descuentos en Red', description: 'Hasta 20% en proveedores asociados' },
      { icon: <Phone size={20} />, title: 'Asistentes Telefonicos', description: 'Cotizacion repuestos y referencias medicas' },
      { icon: <Clock size={20} />, title: 'Disponibilidad 24/7', description: 'Central telefonica siempre disponible' },
      { icon: <Shield size={20} />, title: 'Proveedor MAPFRE', description: 'Respaldado por MAPFRE Guatemala' },
    ],
    coberturaKm: 150,
    eventosAnuales: '14+',
    tiempoRespuesta: '30 min'
  },
  // Plan Asistencia Medica MAPFRE (Q34.26/mes Inclusion, Q36.31/mes Opcional)
  'Health': {
    planType: 'salud',
    serviciosIncluidos: [
      { icon: <Shield size={20} />, title: 'Seguro Muerte Accidental', description: 'Cobertura por fallecimiento', limit: 'Q3,000' },
      { icon: <Phone size={20} />, title: 'Orientacion Medica Telefonica', description: 'Consulta medica por telefono 24/7', limit: 'Ilimitado' },
      { icon: <Users size={20} />, title: 'Conexion con Especialistas', description: 'Referencia a medicos de la red', limit: 'Ilimitado' },
      { icon: <Truck size={20} />, title: 'Medicamentos a Domicilio', description: 'Coordinacion de envio de medicamentos', limit: 'Ilimitado' },
      { icon: <Heart size={20} />, title: 'Consulta Presencial', description: 'Medico general, ginecologo o pediatra', limit: '3/año - $150 USD' },
      { icon: <Home size={20} />, title: 'Cuidados Post-Op Enfermera', description: 'Enfermera a domicilio', limit: '1/año - $100 USD' },
      { icon: <FileText size={20} />, title: 'Articulos de Aseo', description: 'Envio por hospitalizacion', limit: '1/año - $100 USD' },
      { icon: <FileText size={20} />, title: 'Examenes Lab Basicos', description: 'Heces, orina y hematologia', limit: '2/año - $100 USD' },
      { icon: <FileText size={20} />, title: 'Examenes Especializados', description: 'Papanicolau, mamografia, antigeno', limit: '2/año - $100 USD' },
      { icon: <Users size={20} />, title: 'Nutricionista Video', description: 'Video consulta (grupo familiar)', limit: '4/año - $150 USD' },
      { icon: <Heart size={20} />, title: 'Psicologia Video', description: 'Video consulta (nucleo familiar)', limit: '4/año - $150 USD' },
      { icon: <Truck size={20} />, title: 'Mensajeria Hospitalizacion', description: 'Servicio de mensajeria por emergencia', limit: '2/año - $60 USD' },
      { icon: <Car size={20} />, title: 'Taxi Familiar', description: 'Por hospitalizacion del titular', limit: '2/año - $100 USD' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia por Accidente', description: 'Traslado del titular', limit: '2/año - $150 USD' },
      { icon: <Car size={20} />, title: 'Taxi Post Alta', description: 'Traslado al domicilio', limit: '1/año - $100 USD' },
    ],
    beneficiosPremium: [
      { icon: <Users size={20} />, title: 'Cobertura Familiar', description: 'Incluye grupo familiar y nucleo familiar' },
      { icon: <Clock size={20} />, title: 'Disponibilidad 24/7', description: 'Orientacion medica siempre disponible' },
      { icon: <MapPin size={20} />, title: 'Cobertura Nacional', description: 'Valido en toda Guatemala' },
      { icon: <Shield size={20} />, title: 'Proveedor MAPFRE', description: 'Respaldado por MAPFRE Guatemala' },
    ],
    coberturaKm: 15,
    eventosAnuales: '15+',
    tiempoRespuesta: '24hrs'
  },
  // Plan Combo - Vial + Medica MAPFRE
  'Combo': {
    planType: 'vial',
    serviciosIncluidos: [
      { icon: <Shield size={20} />, title: 'Seguro Muerte Accidental', description: 'Doble cobertura combinada', limit: 'Q6,000' },
      { icon: <Truck size={20} />, title: 'Grua del Vehiculo', description: 'Por accidente o falla mecanica', limit: '3/año - $150 USD' },
      { icon: <Fuel size={20} />, title: 'Abasto de Combustible', description: '1 galon de emergencia', limit: '3/año - $150 comb.' },
      { icon: <Car size={20} />, title: 'Cambio de Neumaticos', description: 'Instalacion de llanta', limit: '3/año - $150 comb.' },
      { icon: <Zap size={20} />, title: 'Paso de Corriente', description: 'Arranque de bateria', limit: '3/año - $150 comb.' },
      { icon: <Key size={20} />, title: 'Cerrajeria Vehicular', description: 'Apertura de vehiculo', limit: '3/año - $150 comb.' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia', description: 'Por accidente vial o medico', limit: '3/año - $250 USD' },
      { icon: <Heart size={20} />, title: 'Consultas Medicas', description: 'Presencial y video (grupo familiar)', limit: '6/año - $300 USD' },
      { icon: <Scale size={20} />, title: 'Asistencia Legal', description: 'Asesoria telefonica', limit: '1/año - $200 USD' },
      { icon: <Heart size={20} />, title: 'Apoyo Hospitalario', description: 'Pago directo al hospital', limit: '1/año - $1,000 USD' },
      { icon: <Users size={20} />, title: 'Psicologia y Nutricion', description: 'Video consultas familiares', limit: '8/año - Q2,325' },
    ],
    beneficiosPremium: [
      { icon: <Star size={20} />, title: 'Mejor Valor', description: 'Ahorra combinando ambos planes' },
      { icon: <Users size={20} />, title: 'Cobertura Familiar Completa', description: 'Vial + Salud para toda la familia' },
      { icon: <Clock size={20} />, title: '24/7/365', description: 'Asistencia permanente' },
      { icon: <Shield size={20} />, title: 'Proteccion Integral', description: 'Vehiculo y salud en un solo plan' },
    ],
    coberturaKm: 150,
    eventosAnuales: '25+',
    tiempoRespuesta: '30 min'
  }
};

// Map plan names to benefit keys based on MAWDY products
const getPlanBenefitKey = (planName: string): string => {
  const name = planName.toLowerCase();
  if (name.includes('combo') || name.includes('completo') || name.includes('integral')) return 'Combo';
  if (name.includes('health') || name.includes('salud') || name.includes('médic')) return 'Health';
  if (name.includes('drive') || name.includes('vial') || name.includes('vehicul') || name.includes('road')) return 'Drive';
  // Default to Drive for roadside plans
  return 'Drive';
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
  const [serviceFilter, setServiceFilter] = useState<'all' | 'vial' | 'salud'>('all');

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
    message: string;
    // Recommendation fields
    recommended_plan?: string;
    confidence?: string;
    reason?: string;
    key_services?: string[];
    price_monthly?: string;
    price_yearly?: string;
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
      // Filter out CARD_INSURANCE plans - only show ROADSIDE and HEALTH
      const allPlans = plansRes.data.plans || plansRes.data || [];
      const filteredPlans = allPlans.filter((p: Plan) =>
        p.category_type !== 'CARD_INSURANCE'
      );
      setPlans(filteredPlans);
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
                 (recommended === 'drive' && name.includes('vial')) ||
                 (recommended === 'health' && name.includes('salud')) ||
                 (recommended === 'combo' && (name.includes('combo') || name.includes('completo')));
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

  const getIcon = (categoryType: string) => {
    switch (categoryType?.toUpperCase()) {
      case 'ROADSIDE': return <Truck className="text-red-500" size={32} />;
      case 'HEALTH': return <Heart className="text-pink-500" size={32} />;
      default: return <Star className="text-yellow-500" size={32} />;
    }
  };

  const nextPlan = () => {
    setCurrentPlanIndex((prev) => (prev + 1) % plans.length);
  };

  const prevPlan = () => {
    setCurrentPlanIndex((prev) => (prev - 1 + plans.length) % plans.length);
  };

  const currentPlan = plans[currentPlanIndex];
  const benefitKey = currentPlan ? getPlanBenefitKey(currentPlan.name) : 'Basico';
  const currentBenefits = MAWDY_BENEFITS[benefitKey];
  const yearlyDiscount = 20;

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
          <h1 className="text-3xl font-bold text-gray-900">Planes MAWDY</h1>
          <p className="text-gray-500 mt-2">Asistencia vial, médica y en hogar respaldada por MAWDY</p>
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
              className={`px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                billingCycle === 'yearly'
                  ? 'bg-white shadow text-blue-900'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Anual
              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                -{yearlyDiscount}%
              </span>
            </button>
          </div>
        </div>

        {/* Plan Carousel */}
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

            {/* Current Plan Card */}
            <div className={`card relative mx-auto max-w-2xl transition-all duration-300 ${
              currentPlan.is_featured ? 'border-2 border-blue-500 shadow-xl' : 'shadow-lg'
            }`}>
              {currentPlan.is_featured && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg">
                    ⭐ Más Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-6 pt-4">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                  {getIcon(currentPlan.category_type)}
                </div>
                <h3 className="text-2xl font-bold text-gray-900">{currentPlan.name}</h3>
                <p className="text-gray-500 mt-1">{currentPlan.description}</p>
              </div>

              {/* Price Display */}
              <div className="text-center mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-5xl font-bold text-blue-900">
                    Q{billingCycle === 'monthly' ? currentPlan.price_monthly : currentPlan.price_yearly}
                  </span>
                  <span className="text-gray-500 text-lg">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                </div>
                {billingCycle === 'yearly' && (
                  <p className="text-sm text-green-600 mt-2 font-medium">
                    Q{(parseFloat(String(currentPlan.price_yearly)) / 12).toFixed(2)}/mes · Ahorras Q{(parseFloat(String(currentPlan.price_monthly)) * 12 - parseFloat(String(currentPlan.price_yearly))).toFixed(0)} al año
                  </p>
                )}
              </div>

              {/* Coverage Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{currentBenefits.coberturaKm === 999 ? '∞' : currentBenefits.coberturaKm}</div>
                  <div className="text-xs text-gray-500">KM Grúa</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{currentBenefits.eventosAnuales}</div>
                  <div className="text-xs text-gray-500">Eventos/Año</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{currentBenefits.tiempoRespuesta}</div>
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
              <h4 className="font-bold">Respaldo MAWDY</h4>
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
        <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
          <div className="min-h-screen">
            {/* Modal Header - Full Width */}
            <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 flex items-center justify-between z-10 shadow-lg">
              <div>
                <h3 className="text-3xl font-bold">Compara Nuestros Planes MAWDY</h3>
                <p className="text-blue-100 mt-1">Encuentra el plan perfecto para tus necesidades</p>
              </div>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="p-3 hover:bg-white/20 rounded-full transition-colors flex items-center gap-2 bg-white/10"
              >
                <X size={28} />
                <span className="font-medium">Cerrar</span>
              </button>
            </div>

            <div className="p-6 space-y-8">
              {/* AI Plan Suggestion Section */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                    <Sparkles className="text-white" size={24} />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 text-lg">Asistente IA para elegir tu plan</h4>
                    <p className="text-sm text-gray-600">Describe tus necesidades y te recomendaremos el mejor plan</p>
                  </div>
                </div>

                {/* AI Prompt Input */}
                <div className="flex gap-3 mb-4">
                  <div className="flex-1 relative">
                    <MessageSquare className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                    <input
                      type="text"
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !aiLoading && getAIPlanSuggestion()}
                      placeholder="Ej: Manejo mucho y necesito grua, o tengo familia y quiero consultas medicas..."
                      className="w-full pl-12 pr-4 py-3 border-2 border-purple-200 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all text-gray-700"
                      disabled={aiLoading}
                    />
                  </div>
                  <button
                    onClick={getAIPlanSuggestion}
                    disabled={aiLoading || !aiPrompt.trim()}
                    className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {aiLoading ? (
                      <>
                        <Loader2 className="animate-spin" size={20} />
                        Analizando...
                      </>
                    ) : (
                      <>
                        <Send size={20} />
                        Recomendar
                      </>
                    )}
                  </button>
                </div>

                {/* AI Error */}
                {aiError && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-center gap-3">
                    <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
                    <p className="text-red-700 text-sm">{aiError}</p>
                  </div>
                )}

                {/* AI Suggestion Result - Handles both recommendations and comparisons */}
                {aiSuggestion && (
                  <div className="bg-white border-2 border-green-200 rounded-xl p-5 shadow-lg">
                    {/* COMPARISON VIEW */}
                    {aiSuggestion.is_comparison ? (
                      <div>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-100 to-pink-100 flex items-center justify-center">
                            <BarChart3 className="text-purple-600" size={24} />
                          </div>
                          <div>
                            <h5 className="font-bold text-gray-900 text-lg">Comparación de Planes</h5>
                            <p className="text-sm text-gray-500">
                              {aiSuggestion.compared_plans?.join(' vs ')}
                            </p>
                          </div>
                        </div>

                        {/* Comparison Table */}
                        {aiSuggestion.comparison_details && aiSuggestion.comparison_details.length > 0 && (
                          <div className="overflow-x-auto mb-4">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="bg-gray-100">
                                  <th className="text-left p-3 font-semibold text-gray-700 rounded-tl-lg">Aspecto</th>
                                  <th className="text-center p-3 font-semibold text-blue-700 bg-blue-50">
                                    {aiSuggestion.compared_plans?.[0]}
                                  </th>
                                  <th className="text-center p-3 font-semibold text-pink-700 bg-pink-50 rounded-tr-lg">
                                    {aiSuggestion.compared_plans?.[1]}
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                {aiSuggestion.comparison_details.map((detail, idx) => (
                                  <tr key={idx} className="border-b border-gray-200">
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
                          <div className="mb-4 bg-purple-50 rounded-lg p-4">
                            <p className="text-sm font-semibold text-purple-800 mb-2">Diferencias Clave:</p>
                            <ul className="space-y-1">
                              {aiSuggestion.key_differences.map((diff, idx) => (
                                <li key={idx} className="text-sm text-purple-700 flex items-start gap-2">
                                  <span className="text-purple-500 mt-1">•</span>
                                  {diff}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* AI Message */}
                        <p className="text-gray-700 mb-3">{aiSuggestion.message}</p>

                        {/* Recommendation from comparison */}
                        {aiSuggestion.recommendation && (
                          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mt-3">
                            <p className="text-sm text-green-800">
                              <span className="font-semibold">💡 Recomendación:</span> {aiSuggestion.recommendation}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      /* RECOMMENDATION VIEW */
                      <div>
                        <div className="flex items-start gap-4">
                          <div className={`w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 ${
                            aiSuggestion.recommended_plan?.includes('Drive') ? 'bg-blue-100' :
                            aiSuggestion.recommended_plan?.includes('Health') ? 'bg-pink-100' : 'bg-purple-100'
                          }`}>
                            {aiSuggestion.recommended_plan?.includes('Drive') ? (
                              <Car className="text-blue-600" size={28} />
                            ) : aiSuggestion.recommended_plan?.includes('Health') ? (
                              <Heart className="text-pink-600" size={28} />
                            ) : (
                              <Shield className="text-purple-600" size={28} />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <h5 className="font-bold text-gray-900 text-lg">Plan Recomendado: {aiSuggestion.recommended_plan}</h5>
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                aiSuggestion.confidence === 'alta' ? 'bg-green-100 text-green-700' :
                                aiSuggestion.confidence === 'media' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'
                              }`}>
                                {aiSuggestion.confidence === 'alta' ? 'Alta confianza' :
                                 aiSuggestion.confidence === 'media' ? 'Confianza media' : 'Sugerencia'}
                              </span>
                            </div>
                            {/* Price display */}
                            {aiSuggestion.price_monthly && (
                              <p className="text-lg font-bold text-green-600 mb-2">
                                {aiSuggestion.price_monthly}/mes
                                {aiSuggestion.price_yearly && <span className="text-sm font-normal text-gray-500 ml-2">({aiSuggestion.price_yearly}/año)</span>}
                              </p>
                            )}
                            <p className="text-gray-700 mb-3">{aiSuggestion.message}</p>
                            {aiSuggestion.key_services && aiSuggestion.key_services.length > 0 && (
                              <div className="mb-3">
                                <p className="text-sm font-medium text-gray-600 mb-2">Servicios clave para ti:</p>
                                <div className="flex flex-wrap gap-2">
                                  {aiSuggestion.key_services.map((service, idx) => (
                                    <span key={idx} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                                      <Check size={14} />
                                      {service}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            <p className="text-sm text-gray-500 italic">{aiSuggestion.reason}</p>
                          </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end">
                          <button
                            onClick={() => setShowComparisonModal(false)}
                            className={`px-6 py-2 font-bold rounded-lg transition-all flex items-center gap-2 ${
                              aiSuggestion.recommended_plan?.includes('Drive') ? 'bg-blue-600 hover:bg-blue-700 text-white' :
                              aiSuggestion.recommended_plan?.includes('Health') ? 'bg-pink-600 hover:bg-pink-700 text-white' :
                              'bg-purple-600 hover:bg-purple-700 text-white'
                            }`}
                          >
                            Ver Planes
                            <ChevronRight size={18} />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Example Prompts */}
                {!aiSuggestion && !aiLoading && (
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Ejemplos de lo que puedes preguntar:</p>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {[
                        'Manejo mucho y mi carro es viejo',
                        'Tengo hijos pequeños y quiero consultas médicas',
                        'Quiero protección completa para mi familia'
                      ].map((example, idx) => (
                        <button
                          key={idx}
                          onClick={() => setAiPrompt(example)}
                          className="text-xs bg-white border border-purple-200 text-purple-700 px-3 py-1.5 rounded-full hover:bg-purple-50 transition-colors"
                        >
                          "{example}"
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-gray-500 mb-2">O compara planes específicos:</p>
                    <div className="flex flex-wrap gap-2">
                      {[
                        'Compara Drive Inclusión vs Drive Opcional',
                        'Diferencia entre Health Inclusión y Opcional',
                        'Compara Plan Drive vs Plan Health',
                        '¿Qué incluye el Plan Combo?'
                      ].map((example, idx) => (
                        <button
                          key={idx}
                          onClick={() => setAiPrompt(example)}
                          className="text-xs bg-white border border-blue-200 text-blue-700 px-3 py-1.5 rounded-full hover:bg-blue-50 transition-colors"
                        >
                          "{example}"
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Billing Toggle */}
              <div className="flex justify-center">
                <div className="bg-gray-100 p-1.5 rounded-xl inline-flex shadow-inner">
                  <button
                    onClick={() => setBillingCycle('monthly')}
                    className={`px-8 py-2.5 rounded-lg font-semibold transition-all ${
                      billingCycle === 'monthly'
                        ? 'bg-white shadow-md text-blue-900'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Mensual
                  </button>
                  <button
                    onClick={() => setBillingCycle('yearly')}
                    className={`px-8 py-2.5 rounded-lg font-semibold transition-all flex items-center gap-2 ${
                      billingCycle === 'yearly'
                        ? 'bg-white shadow-md text-blue-900'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Anual
                    <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full font-bold">-20%</span>
                  </button>
                </div>
              </div>

              {/* Detailed Feature Comparison Table - ALL MAWDY Plans */}
              <div className="bg-gray-50 rounded-2xl p-6">
                <h4 className="font-bold text-gray-900 mb-4 text-center text-xl">Comparación de Todos los Planes MAWDY</h4>
                <p className="text-center text-gray-500 text-sm mb-6">Compara los servicios incluidos en cada plan</p>

                {/* Filter Buttons */}
                <div className="flex justify-center gap-2 mb-6">
                  <button
                    onClick={() => setServiceFilter('all')}
                    className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                      serviceFilter === 'all'
                        ? 'bg-gray-800 text-white shadow-md'
                        : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    Todos los Servicios
                  </button>
                  <button
                    onClick={() => setServiceFilter('vial')}
                    className={`px-6 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 ${
                      serviceFilter === 'vial'
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-white text-blue-600 hover:bg-blue-50 border border-blue-300'
                    }`}
                  >
                    <Car size={18} />
                    Servicios Viales
                  </button>
                  <button
                    onClick={() => setServiceFilter('salud')}
                    className={`px-6 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 ${
                      serviceFilter === 'salud'
                        ? 'bg-pink-600 text-white shadow-md'
                        : 'bg-white text-pink-600 hover:bg-pink-50 border border-pink-300'
                    }`}
                  >
                    <Heart size={18} />
                    Servicios de Salud
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 border-gray-300">
                        <th className="text-left p-3 font-semibold text-gray-700 bg-gray-100 rounded-tl-lg min-w-[220px] sticky left-0 z-10">
                          Servicio
                        </th>
                        {/* Dynamic columns for ALL database plans */}
                        {plans.map((plan) => {
                          const isVial = plan.category_type === 'ROADSIDE';
                          return (
                            <th
                              key={plan.id}
                              className={`text-center p-3 font-bold min-w-[140px] ${
                                isVial ? 'bg-blue-100 text-blue-900' : 'bg-pink-100 text-pink-900'
                              } ${plan.is_featured ? 'ring-2 ring-yellow-400' : ''}`}
                            >
                              <div className="flex flex-col items-center">
                                {isVial ? <Car size={18} className="mb-1" /> : <Heart size={18} className="mb-1" />}
                                <span className="text-xs leading-tight">{plan.name}</span>
                                {plan.is_featured && (
                                  <span className="text-[10px] bg-yellow-400 text-yellow-900 px-1 rounded mt-1">⭐</span>
                                )}
                              </div>
                            </th>
                          );
                        })}
                        {/* Combo Plan Column */}
                        <th className="text-center p-3 font-bold bg-purple-100 text-purple-900 min-w-[140px] rounded-tr-lg">
                          <div className="flex flex-col items-center">
                            <Shield size={18} className="mb-1" />
                            <span className="text-xs leading-tight">Plan Combo</span>
                            <span className="text-[10px] bg-green-500 text-white px-1 rounded mt-1">Ahorra</span>
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {ALL_SERVICES
                        .filter(service => serviceFilter === 'all' || service.category === serviceFilter)
                        .map((service) => (
                        <tr
                          key={service.id}
                          className={`border-b border-gray-200 ${
                            service.category === 'vial'
                              ? 'bg-blue-50/30 hover:bg-blue-100/50'
                              : 'bg-pink-50/30 hover:bg-pink-100/50'
                          }`}
                        >
                          <td className="p-3 text-gray-700 font-medium bg-white sticky left-0 z-10 border-r border-gray-200">
                            <div className="flex items-center gap-2">
                              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${service.category === 'vial' ? 'bg-blue-500' : 'bg-pink-500'}`}></span>
                              <span className="text-xs">{service.name}</span>
                            </div>
                          </td>
                          {/* Dynamic cells for each database plan */}
                          {plans.map((plan) => {
                            const isVial = plan.category_type === 'ROADSIDE';
                            const hasService = (isVial && service.category === 'vial') || (!isVial && service.category === 'salud');
                            const limit = isVial ? service.driveLimit : service.healthLimit;
                            const value = isVial ? service.driveValue : service.healthValue;
                            return (
                              <td key={plan.id} className={`p-2 text-center ${hasService ? (isVial ? 'text-blue-700' : 'text-pink-700') : 'text-gray-300'}`}>
                                {hasService && limit !== '-' ? (
                                  <div className="flex flex-col items-center">
                                    <Check size={16} className={isVial ? 'text-blue-600' : 'text-pink-600'} />
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full mt-0.5 ${isVial ? 'bg-blue-100' : 'bg-pink-100'}`}>
                                      {limit}
                                    </span>
                                  </div>
                                ) : (
                                  <Minus className="mx-auto text-gray-300" size={14} />
                                )}
                              </td>
                            );
                          })}
                          {/* Combo Plan Cell */}
                          <td className={`p-2 text-center ${service.comboLimit !== '-' ? 'text-purple-700' : 'text-gray-300'}`}>
                            {service.comboLimit !== '-' ? (
                              <div className="flex flex-col items-center">
                                <Check size={16} className="text-purple-600" />
                                <span className="text-[10px] bg-purple-100 px-1.5 py-0.5 rounded-full mt-0.5">
                                  {service.comboLimit}
                                </span>
                              </div>
                            ) : (
                              <Minus className="mx-auto text-gray-300" size={14} />
                            )}
                          </td>
                        </tr>
                      ))}
                      {/* Price Row */}
                      <tr className="bg-gradient-to-r from-gray-100 to-gray-200 font-bold border-t-2 border-gray-400">
                        <td className="p-3 text-gray-900 rounded-bl-lg sticky left-0 bg-gray-100 border-r border-gray-300">
                          Precio {billingCycle === 'monthly' ? 'Mensual' : 'Anual'}
                        </td>
                        {plans.map((plan) => {
                          const isVial = plan.category_type === 'ROADSIDE';
                          const price = billingCycle === 'monthly' ? plan.price_monthly : plan.price_yearly;
                          return (
                            <td key={plan.id} className={`p-3 text-center ${isVial ? 'text-blue-700' : 'text-pink-700'}`}>
                              <div className="flex flex-col items-center">
                                <span className="text-lg font-bold">Q{price}</span>
                                <span className="text-[10px] text-gray-500">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                              </div>
                            </td>
                          );
                        })}
                        <td className="p-3 text-center text-purple-700 rounded-br-lg">
                          <div className="flex flex-col items-center">
                            <span className="text-lg font-bold">Q{billingCycle === 'monthly' ? '42.89' : '514.68'}</span>
                            <span className="text-[10px] text-green-600 bg-green-100 px-2 py-0.5 rounded-full">
                              Ahorra Q{billingCycle === 'monthly' ? '4' : '48'}
                            </span>
                          </div>
                        </td>
                      </tr>
                      {/* Service Count Row */}
                      <tr className="bg-gray-50">
                        <td className="p-3 text-gray-700 font-medium sticky left-0 bg-gray-50 border-r border-gray-200">
                          Total Servicios Incluidos
                        </td>
                        {plans.map((plan) => {
                          const isVial = plan.category_type === 'ROADSIDE';
                          const serviceCount = ALL_SERVICES.filter(s =>
                            (isVial && s.category === 'vial' && s.driveLimit !== '-') ||
                            (!isVial && s.category === 'salud' && s.healthLimit !== '-')
                          ).length;
                          return (
                            <td key={plan.id} className={`p-3 text-center font-bold ${isVial ? 'text-blue-600' : 'text-pink-600'}`}>
                              {serviceCount} servicios
                            </td>
                          );
                        })}
                        <td className="p-3 text-center font-bold text-purple-600">
                          {ALL_SERVICES.filter(s => s.comboLimit !== '-').length} servicios
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Legend */}
                <div className="mt-4 flex flex-wrap justify-center gap-4 md:gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                    <span className="text-gray-600">Servicios Viales (Plan Drive)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-pink-500"></span>
                    <span className="text-gray-600">Servicios de Salud (Plan Health)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                    <span className="text-gray-600">Plan Combo (Drive + Health)</span>
                  </div>
                </div>
              </div>

              {/* Trust Badges - Enhanced */}
              <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-2xl p-6 text-white">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                  <div>
                    <Shield className="mx-auto mb-2 opacity-90" size={28} />
                    <h5 className="font-bold text-sm">Respaldo MAWDY</h5>
                    <p className="text-xs text-blue-200 mt-1">Lider en asistencias</p>
                  </div>
                  <div>
                    <Clock className="mx-auto mb-2 opacity-90" size={28} />
                    <h5 className="font-bold text-sm">24/7/365</h5>
                    <p className="text-xs text-blue-200 mt-1">Siempre disponibles</p>
                  </div>
                  <div>
                    <MapPin className="mx-auto mb-2 opacity-90" size={28} />
                    <h5 className="font-bold text-sm">Cobertura Nacional</h5>
                    <p className="text-xs text-blue-200 mt-1">En toda Guatemala</p>
                  </div>
                  <div>
                    <Wallet className="mx-auto mb-2 opacity-90" size={28} />
                    <h5 className="font-bold text-sm">Pago PAQ Wallet</h5>
                    <p className="text-xs text-blue-200 mt-1">Seguro y facil</p>
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
