import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI, userAPI, promoCodesAPI, elearningAPI } from '../../services/api';
import {
  Check, Star, Shield, Truck, Heart, Clock, Wallet,
  ChevronLeft, ChevronRight, Phone, MapPin,
  Ambulance, Home, Scale, Car, Fuel, Key,
  Users, FileText, Zap, Loader2, X, AlertCircle, Table2, Minus, Tag, Gift
} from 'lucide-react';

interface Plan {
  id: number;
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  is_featured: boolean;
  category: string;
}

// MAWDY Benefits Data - Based on official MAWDY PAQ Wallet document (Oct 2025)
// Prices converted from USD to GTQ (Exchange rate: 1 USD ≈ 7.75 GTQ)
const MAWDY_BENEFITS: Record<string, {
  serviciosIncluidos: Array<{ icon: React.ReactNode; title: string; description: string; limit?: string }>;
  beneficiosPremium: Array<{ icon: React.ReactNode; title: string; description: string }>;
  coberturaKm: number;
  eventosAnuales: number | string;
  tiempoRespuesta: string;
  planType: 'vial' | 'salud';
}> = {
  // Plan Drive - Asistencia Vial (Q24.41/mes)
  'Drive': {
    planType: 'vial',
    serviciosIncluidos: [
      { icon: <Truck size={20} />, title: 'Grúa del Vehículo', description: 'Por accidente o falla mecánica', limit: '3/año - Q1,163' },
      { icon: <Fuel size={20} />, title: 'Abasto de Combustible', description: '1 galón (demostrar con imagen)', limit: 'Incluido' },
      { icon: <Car size={20} />, title: 'Cambio de Neumáticos', description: 'Instalación de llanta de repuesto', limit: '3/año - Q1,163' },
      { icon: <Zap size={20} />, title: 'Paso de Corriente', description: 'Servicio de arranque de batería', limit: 'Incluido' },
      { icon: <Key size={20} />, title: 'Emergencia de Cerrajería', description: 'Apertura de vehículo 24/7', limit: 'Incluido' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia por Accidente', description: 'Traslado médico de emergencia', limit: '1/año - Q775' },
      { icon: <Users size={20} />, title: 'Conductor Profesional', description: 'Por enfermedad o embriaguez (5hrs anticipación)', limit: '1/año - Q465' },
      { icon: <Car size={20} />, title: 'Taxi al Aeropuerto', description: 'Por viaje del titular al extranjero', limit: '1/año - Q465' },
      { icon: <Scale size={20} />, title: 'Asistencia Legal Telefónica', description: 'Asesoría legal por accidente', limit: '1/año - Q1,550' },
      { icon: <Heart size={20} />, title: 'Apoyo Económico Emergencia', description: 'Pago directo al hospital por accidente', limit: '1/año - Q7,750' },
      { icon: <FileText size={20} />, title: 'Rayos X', description: 'Servicio de radiografía', limit: '1/año - Q2,325' },
    ],
    beneficiosPremium: [
      { icon: <Star size={20} />, title: 'Descuentos en Red', description: 'Hasta 20% en proveedores asociados' },
      { icon: <Phone size={20} />, title: 'Cotización de Repuestos', description: 'Asistente telefónico para cotizaciones' },
      { icon: <Heart size={20} />, title: 'Referencias Médicas', description: 'Asistente para referencias por accidente' },
      { icon: <Clock size={20} />, title: 'Disponibilidad 24/7', description: 'Central telefónica siempre disponible' },
    ],
    coberturaKm: 150,
    eventosAnuales: '3-6',
    tiempoRespuesta: '30 min'
  },
  // Plan Health - Asistencia Salud (Q22.48/mes)
  'Health': {
    planType: 'salud',
    serviciosIncluidos: [
      { icon: <Phone size={20} />, title: 'Orientación Médica Telefónica', description: 'Consulta médica por teléfono 24/7', limit: 'Ilimitado' },
      { icon: <Users size={20} />, title: 'Conexión con Especialistas', description: 'Referencia a médicos de la red', limit: 'Ilimitado' },
      { icon: <Heart size={20} />, title: 'Consulta Presencial', description: 'Médico general, ginecólogo o pediatra (grupo familiar)', limit: '3/año - Q1,163' },
      { icon: <Truck size={20} />, title: 'Medicamentos a Domicilio', description: 'Coordinación de envío de medicamentos', limit: 'Incluido' },
      { icon: <Home size={20} />, title: 'Cuidados Post Operatorios', description: 'Enfermera para el titular', limit: '1/año - Q775' },
      { icon: <FileText size={20} />, title: 'Artículos de Aseo', description: 'Envío por hospitalización', limit: '1/año - Q775' },
      { icon: <FileText size={20} />, title: 'Exámenes de Laboratorio', description: 'Heces, orina y hematología (grupo familiar)', limit: '2/año - Q775' },
      { icon: <FileText size={20} />, title: 'Exámenes Especializados', description: 'Papanicolau, mamografía o antígeno prostático', limit: '2/año - Q775' },
      { icon: <Users size={20} />, title: 'Nutricionista Video', description: 'Video consulta (grupo familiar)', limit: '4/año - Q1,163' },
      { icon: <Heart size={20} />, title: 'Psicología Video', description: 'Video consulta (núcleo familiar)', limit: '4/año - Q1,163' },
      { icon: <Truck size={20} />, title: 'Mensajería Hospitalización', description: 'Servicio de mensajería por emergencia', limit: '2/año - Q465' },
      { icon: <Car size={20} />, title: 'Taxi Familiar', description: 'Por hospitalización del titular (15km)', limit: '2/año - Q775' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia por Accidente', description: 'Traslado del titular', limit: '2/año - Q1,163' },
      { icon: <Car size={20} />, title: 'Taxi Post Alta', description: 'Traslado al domicilio tras hospitalización', limit: '1/año - Q775' },
    ],
    beneficiosPremium: [
      { icon: <Users size={20} />, title: 'Cobertura Familiar', description: 'Incluye grupo familiar y núcleo familiar' },
      { icon: <Clock size={20} />, title: 'Disponibilidad 24/7', description: 'Orientación médica siempre disponible' },
      { icon: <MapPin size={20} />, title: 'Cobertura Nacional', description: 'Válido en toda Guatemala' },
      { icon: <Shield size={20} />, title: 'Red de Especialistas', description: 'Acceso a red médica MAWDY' },
    ],
    coberturaKm: 15,
    eventosAnuales: '14+',
    tiempoRespuesta: '24hrs'
  },
  // Combined Plan - Drive + Health
  'Combo': {
    planType: 'vial',
    serviciosIncluidos: [
      { icon: <Truck size={20} />, title: 'Grúa del Vehículo', description: 'Por accidente o falla mecánica', limit: '3/año - Q1,163' },
      { icon: <Fuel size={20} />, title: 'Abasto de Combustible', description: '1 galón con imagen', limit: 'Incluido' },
      { icon: <Car size={20} />, title: 'Cambio de Neumáticos', description: 'Instalación de llanta', limit: '3/año - Q1,163' },
      { icon: <Zap size={20} />, title: 'Paso de Corriente', description: 'Arranque de batería', limit: 'Incluido' },
      { icon: <Key size={20} />, title: 'Cerrajería Automotriz', description: 'Apertura de vehículo', limit: 'Incluido' },
      { icon: <Ambulance size={20} />, title: 'Ambulancia', description: 'Por accidente vial o médico', limit: '3/año - Q1,938' },
      { icon: <Heart size={20} />, title: 'Consultas Médicas', description: 'Presencial y video (grupo familiar)', limit: '6/año - Q2,325' },
      { icon: <Scale size={20} />, title: 'Asistencia Legal', description: 'Asesoría telefónica', limit: '1/año - Q1,550' },
      { icon: <Heart size={20} />, title: 'Apoyo Hospitalario', description: 'Pago directo al hospital', limit: '1/año - Q7,750' },
      { icon: <Users size={20} />, title: 'Psicología y Nutrición', description: 'Video consultas familiares', limit: '8/año - Q2,325' },
    ],
    beneficiosPremium: [
      { icon: <Star size={20} />, title: 'Mejor Valor', description: 'Ahorra combinando ambos planes' },
      { icon: <Users size={20} />, title: 'Cobertura Familiar Completa', description: 'Vial + Salud para toda la familia' },
      { icon: <Clock size={20} />, title: '24/7/365', description: 'Asistencia permanente' },
      { icon: <Shield size={20} />, title: 'Protección Integral', description: 'Vehículo y salud en un solo plan' },
    ],
    coberturaKm: 150,
    eventosAnuales: '20+',
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
  const [mySubscriptions, setMySubscriptions] = useState<any[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [currentPlanIndex, setCurrentPlanIndex] = useState(0);
  const [showPAQModal, setShowPAQModal] = useState(false);
  const [selectedPlanForPurchase, setSelectedPlanForPurchase] = useState<Plan | null>(null);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

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
      const [plansRes, subsRes] = await Promise.all([
        servicesAPI.getPlans(),
        servicesAPI.getMySubscriptions()
      ]);
      setPlans(plansRes.data.plans || plansRes.data || []);
      setMySubscriptions(subsRes.data.subscriptions || subsRes.data || []);
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
          ? selectedPlanForPurchase?.price_monthly || 0
          : selectedPlanForPurchase?.price_yearly || 0;

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
  const getFinalPrice = () => {
    if (!selectedPlanForPurchase) return 0;
    const basePrice = billingCycle === 'monthly'
      ? selectedPlanForPurchase.price_monthly
      : selectedPlanForPurchase.price_yearly;

    if (promoDiscount) {
      return Math.max(0, basePrice - promoDiscount.discount_amount);
    }
    return basePrice;
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
      const response = await servicesAPI.purchaseWithPAQ({
        plan_id: selectedPlanForPurchase.id,
        billing_cycle: billingCycle,
        phone_number: phoneNumber.trim()
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
      await servicesAPI.confirmPAQPayment({
        paypaq_code: paypaqCode.trim().toUpperCase(),  // PAYPAQ codes are uppercase
        phone_number: phoneNumber.trim(),
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

  const getIcon = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'vehicular': return <Truck className="text-red-500" size={32} />;
      case 'health': return <Heart className="text-pink-500" size={32} />;
      case 'home': return <Shield className="text-blue-500" size={32} />;
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

        {/* My Active Subscriptions */}
        {mySubscriptions.length > 0 && (
          <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Check className="text-green-500" />
              Mis Suscripciones Activas
            </h3>
            <div className="space-y-3">
              {mySubscriptions.map((sub: any) => (
                <div key={sub.id} className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm">
                  <div>
                    <p className="font-medium">{sub.plan_name}</p>
                    <p className="text-sm text-gray-500">
                      Vence: {new Date(sub.end_date).toLocaleDateString()}
                      {sub.days_remaining > 0 && ` (${sub.days_remaining} días restantes)`}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      sub.status === 'ACTIVE' ? 'bg-green-100 text-green-700' :
                      sub.status === 'CANCELLED' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {sub.status === 'ACTIVE' ? 'Activo' :
                       sub.status === 'CANCELLED' ? 'Cancelado' : sub.status}
                    </span>
                    {sub.status === 'ACTIVE' && sub.days_remaining <= 7 && (
                      <button
                        onClick={async () => {
                          try {
                            await servicesAPI.initiateRenewal(sub.id);
                            alert('Renovación iniciada. Por favor completa el pago.');
                            await loadData();
                          } catch (error: any) {
                            alert(error.response?.data?.error || 'Error al renovar suscripción');
                          }
                        }}
                        className="btn btn-primary btn-sm"
                      >
                        Renovar
                      </button>
                    )}
                    {sub.status === 'ACTIVE' && (
                      <button
                        onClick={async () => {
                          if (confirm('¿Estás seguro que deseas cancelar esta suscripción?')) {
                            try {
                              await servicesAPI.cancelSubscription(sub.id);
                              alert('Suscripción cancelada exitosamente');
                              await loadData();
                            } catch (error: any) {
                              alert(error.response?.data?.error || 'Error al cancelar suscripción');
                            }
                          }
                        }}
                        className="btn btn-outline btn-sm text-red-600 border-red-300 hover:bg-red-50"
                      >
                        Cancelar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
                  {getIcon(currentPlan.category)}
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
                    Q{(currentPlan.price_yearly / 12).toFixed(2)}/mes · Ahorras Q{(currentPlan.price_monthly * 12 - currentPlan.price_yearly).toFixed(0)} al año
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
                  className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-3"
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

      {/* PAQ Wallet Payment Modal with PAYPAQ Flow - PAQ Brand Colors */}
      {showPAQModal && selectedPlanForPurchase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden">
            {/* PAQ Brand Header */}
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
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 p-4 rounded-xl mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Plan:</span>
                  <span className="font-bold">{selectedPlanForPurchase.name}</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Período:</span>
                  <span className="font-medium">{billingCycle === 'monthly' ? 'Mensual' : 'Anual'}</span>
                </div>

                {/* Promo Code Input - Only available until first e-learning module is completed */}
                {elearningChecked && !hasCompletedFirstModule && (
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

                {/* Message for users who have completed e-learning */}
                {elearningChecked && hasCompletedFirstModule && (
                  <div className="pt-3 border-t border-gray-200 mb-3">
                    <div className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Gift className="text-purple-600" size={18} />
                        <p className="text-sm text-purple-700">
                          <span className="font-bold">¡Gana códigos promocionales!</span>
                        </p>
                      </div>
                      <p className="text-xs text-purple-600 mt-1">
                        Completa más módulos de e-learning para obtener códigos de descuento exclusivos.
                      </p>
                    </div>
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

            {/* Step Indicator - PAQ Green */}
            {paqStep !== 'success' && (
              <div className="flex items-center justify-center gap-2 mb-6">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  paqStep === 'phone' ? 'bg-[#00A86B] text-white' : 'bg-[#00A86B] text-white'
                }`}>
                  {paqStep === 'phone' ? '1' : <Check size={16} />}
                </div>
                <div className={`w-12 h-1 rounded ${paqStep === 'code' ? 'bg-[#00A86B]' : 'bg-gray-300'}`} />
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  paqStep === 'code' ? 'bg-[#00A86B] text-white' : 'bg-gray-300 text-gray-500'
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

              {/* Plan Cards Side by Side - Enhanced */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {plans.map((plan, planIndex) => {
                  const benefits = MAWDY_BENEFITS[getPlanBenefitKey(plan.name)];
                  const isVial = benefits.planType === 'vial';
                  const colorTheme = plan.is_featured
                    ? { bg: 'bg-gradient-to-b from-purple-50 to-blue-50', border: 'border-purple-400', accent: 'purple' }
                    : isVial
                      ? { bg: 'bg-white', border: 'border-blue-200', accent: 'blue' }
                      : { bg: 'bg-white', border: 'border-pink-200', accent: 'pink' };

                  return (
                    <div
                      key={plan.id}
                      className={`rounded-2xl border-2 ${colorTheme.border} ${colorTheme.bg} p-6 transition-all hover:shadow-xl ${
                        plan.is_featured ? 'shadow-xl ring-2 ring-purple-300 ring-offset-2' : 'hover:border-gray-400'
                      }`}
                    >
                      {/* Plan Header */}
                      {plan.is_featured && (
                        <div className="text-center -mt-9 mb-4">
                          <span className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-bold px-4 py-1.5 rounded-full shadow-lg inline-flex items-center gap-1">
                            <Star size={14} className="fill-current" /> Recomendado
                          </span>
                        </div>
                      )}

                      {/* Plan Type Badge */}
                      <div className="flex justify-center mb-3">
                        <span className={`text-xs font-medium px-3 py-1 rounded-full ${
                          getPlanBenefitKey(plan.name) === 'Combo'
                            ? 'bg-purple-100 text-purple-700'
                            : isVial
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-pink-100 text-pink-700'
                        }`}>
                          {getPlanBenefitKey(plan.name) === 'Combo' ? 'Vial + Salud' : isVial ? 'Asistencia Vial' : 'Asistencia Salud'}
                        </span>
                      </div>

                      <div className="text-center mb-5">
                        <div className={`w-16 h-16 mx-auto mb-3 rounded-2xl flex items-center justify-center ${
                          plan.is_featured
                            ? 'bg-gradient-to-br from-purple-100 to-blue-100'
                            : isVial
                              ? 'bg-gradient-to-br from-blue-100 to-cyan-100'
                              : 'bg-gradient-to-br from-pink-100 to-rose-100'
                        }`}>
                          {getIcon(plan.category)}
                        </div>
                        <h4 className="text-2xl font-bold text-gray-900">{plan.name}</h4>
                        <p className="text-sm text-gray-500 mt-1">{plan.description}</p>

                        {/* Price */}
                        <div className="mt-4 p-3 bg-white rounded-xl shadow-sm">
                          <div className="flex items-baseline justify-center gap-1">
                            <span className="text-4xl font-bold text-gray-900">
                              Q{billingCycle === 'monthly' ? plan.price_monthly : plan.price_yearly}
                            </span>
                            <span className="text-gray-500">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                          </div>
                          {billingCycle === 'yearly' && (
                            <p className="text-xs text-green-600 mt-1 font-medium">
                              Equivale a Q{(plan.price_yearly / 12).toFixed(2)}/mes
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Quick Stats - Enhanced */}
                      <div className="grid grid-cols-3 gap-2 mb-5">
                        <div className="bg-white p-3 rounded-xl text-center shadow-sm border border-gray-100">
                          <div className="text-xl font-bold text-blue-600">{benefits.coberturaKm}</div>
                          <div className="text-xs text-gray-500 font-medium">KM Cobertura</div>
                        </div>
                        <div className="bg-white p-3 rounded-xl text-center shadow-sm border border-gray-100">
                          <div className="text-xl font-bold text-purple-600">{benefits.eventosAnuales}</div>
                          <div className="text-xs text-gray-500 font-medium">Eventos/Año</div>
                        </div>
                        <div className="bg-white p-3 rounded-xl text-center shadow-sm border border-gray-100">
                          <div className="text-xl font-bold text-green-600">{benefits.tiempoRespuesta}</div>
                          <div className="text-xs text-gray-500 font-medium">Respuesta</div>
                        </div>
                      </div>

                      {/* Services List - All services shown */}
                      <div className="space-y-2 mb-5 max-h-64 overflow-y-auto pr-1">
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                          {benefits.serviciosIncluidos.length} Servicios Incluidos:
                        </p>
                        {benefits.serviciosIncluidos.map((service, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-sm bg-white p-2 rounded-lg border border-gray-100">
                            <Check className="text-green-500 flex-shrink-0 mt-0.5" size={16} />
                            <div className="flex-1 min-w-0">
                              <span className="text-gray-800 font-medium">{service.title}</span>
                              {service.limit && (
                                <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                  {service.limit.split(' - ')[0]}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Value Highlight */}
                      <div className={`p-3 rounded-xl mb-4 ${
                        plan.is_featured
                          ? 'bg-gradient-to-r from-purple-100 to-blue-100 border border-purple-200'
                          : 'bg-gray-50 border border-gray-200'
                      }`}>
                        <p className="text-xs text-center font-medium text-gray-700">
                          Valor total de servicios: <span className="text-green-600 font-bold">Q{
                            benefits.serviciosIncluidos.reduce((acc, s) => {
                              const match = s.limit?.match(/Q([\d,]+)/);
                              return acc + (match ? parseInt(match[1].replace(',', '')) : 0);
                            }, 0).toLocaleString()
                          }+</span>/año
                        </p>
                      </div>

                      {/* CTA Button */}
                      <button
                        onClick={() => {
                          setShowComparisonModal(false);
                          openPAQModal(plan);
                        }}
                        className={`w-full py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-xl ${
                          plan.is_featured
                            ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white'
                            : 'bg-gray-900 hover:bg-gray-800 text-white'
                        }`}
                      >
                        <Wallet size={20} />
                        Contratar Ahora
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Detailed Feature Comparison Table */}
              <div className="bg-gray-50 rounded-2xl p-6">
                <h4 className="font-bold text-gray-900 mb-6 text-center text-xl">Comparacion Detallada de Servicios</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 border-gray-300">
                        <th className="text-left p-4 font-semibold text-gray-700 bg-gray-100 rounded-tl-lg">Servicio</th>
                        {plans.map((plan, idx) => (
                          <th key={plan.id} className={`text-center p-4 font-bold ${
                            plan.is_featured ? 'bg-purple-100 text-purple-900' : 'bg-gray-100 text-gray-900'
                          } ${idx === plans.length - 1 ? 'rounded-tr-lg' : ''}`}>
                            {plan.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { name: 'Grua del Vehiculo', key: 'grua' },
                        { name: 'Ambulancia', key: 'ambulancia' },
                        { name: 'Abasto Combustible', key: 'combustible' },
                        { name: 'Cerrajeria Automotriz', key: 'cerrajeria' },
                        { name: 'Paso de Corriente', key: 'corriente' },
                        { name: 'Consulta Medica', key: 'consulta' },
                        { name: 'Orientacion Medica 24/7', key: 'orientacion' },
                        { name: 'Asistencia Legal', key: 'legal' },
                        { name: 'Psicologia/Nutricion', key: 'psicolog' },
                        { name: 'Exámenes Lab', key: 'laboratorio' },
                      ].map((service, rowIdx) => (
                        <tr key={service.key} className={`border-b border-gray-200 ${rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                          <td className="p-4 text-gray-700 font-medium">{service.name}</td>
                          {plans.map((plan) => {
                            const benefits = MAWDY_BENEFITS[getPlanBenefitKey(plan.name)];
                            const found = benefits.serviciosIncluidos.find(s =>
                              s.title.toLowerCase().includes(service.key.toLowerCase())
                            );
                            return (
                              <td key={plan.id} className={`p-4 text-center ${plan.is_featured ? 'bg-purple-50/50' : ''}`}>
                                {found ? (
                                  <div className="flex flex-col items-center">
                                    <Check className="text-green-500" size={20} />
                                    {found.limit && (
                                      <span className="text-xs text-gray-500 mt-1">
                                        {found.limit.split(' - ')[0]}
                                      </span>
                                    )}
                                  </div>
                                ) : (
                                  <Minus className="text-gray-300 mx-auto" size={20} />
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                      {/* Price Row */}
                      <tr className="bg-gray-100 font-bold">
                        <td className="p-4 text-gray-900 rounded-bl-lg">Precio {billingCycle === 'monthly' ? 'Mensual' : 'Anual'}</td>
                        {plans.map((plan, idx) => (
                          <td key={plan.id} className={`p-4 text-center text-xl ${
                            plan.is_featured ? 'text-purple-600' : 'text-blue-600'
                          } ${idx === plans.length - 1 ? 'rounded-br-lg' : ''}`}>
                            Q{billingCycle === 'monthly' ? plan.price_monthly : plan.price_yearly}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
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
