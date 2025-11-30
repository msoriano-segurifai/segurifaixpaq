import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/shared/Layout';
import { servicesAPI } from '../../services/api';
import { Check, Star, Shield, Truck, Heart, Clock, CreditCard } from 'lucide-react';

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

export const Subscriptions: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [mySubscriptions, setMySubscriptions] = useState<any[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, []);

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

  const handlePurchase = async (planId: number) => {
    setPurchasing(planId);
    try {
      await servicesAPI.purchaseSubscription(planId, billingCycle);
      await loadData();
      alert('Suscripcion comprada exitosamente!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al procesar la compra');
    } finally {
      setPurchasing(null);
    }
  };

  const getIcon = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'vehicular': return <Truck className="text-red-500" />;
      case 'health': return <Heart className="text-pink-500" />;
      case 'home': return <Shield className="text-blue-500" />;
      default: return <Star className="text-yellow-500" />;
    }
  };

  const yearlyDiscount = 20; // 20% off for yearly

  return (
    <Layout variant="user">
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Planes de Suscripcion</h1>
          <p className="text-gray-500 mt-2">Elige el plan que mejor se adapte a tus necesidades</p>
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
          <div className="card bg-gradient-to-r from-blue-50 to-purple-50">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Check className="text-green-500" />
              Mis Suscripciones Activas
            </h3>
            <div className="space-y-3">
              {mySubscriptions.map((sub: any) => (
                <div key={sub.id} className="flex items-center justify-between bg-white p-4 rounded-lg">
                  <div>
                    <p className="font-medium">{sub.plan_name}</p>
                    <p className="text-sm text-gray-500">
                      Vence: {new Date(sub.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`badge ${sub.status === 'ACTIVE' ? 'badge-success' : 'badge-warning'}`}>
                      {sub.status}
                    </span>
                    {sub.days_remaining <= 7 && (
                      <button className="btn btn-primary btn-sm">Renovar</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const price = billingCycle === 'monthly' ? plan.price_monthly : plan.price_yearly;
            const monthlyEquivalent = billingCycle === 'yearly' ? (price / 12).toFixed(2) : price;

            return (
              <div
                key={plan.id}
                className={`card relative ${
                  plan.is_featured ? 'border-2 border-blue-500 shadow-lg' : ''
                }`}
              >
                {plan.is_featured && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                      Mas Popular
                    </span>
                  </div>
                )}

                <div className="text-center mb-6">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 flex items-center justify-center">
                    {getIcon(plan.category)}
                  </div>
                  <h3 className="text-xl font-bold">{plan.name}</h3>
                  <p className="text-gray-500 text-sm mt-1">{plan.description}</p>
                </div>

                <div className="text-center mb-6">
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold">Q{price}</span>
                    <span className="text-gray-500">/{billingCycle === 'monthly' ? 'mes' : 'ano'}</span>
                  </div>
                  {billingCycle === 'yearly' && (
                    <p className="text-sm text-green-600 mt-1">
                      Q{monthlyEquivalent}/mes (ahorras Q{(plan.price_monthly * 12 - price).toFixed(0)})
                    </p>
                  )}
                </div>

                <ul className="space-y-3 mb-6">
                  {(plan.features || []).map((feature: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check size={18} className="text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handlePurchase(plan.id)}
                  disabled={purchasing === plan.id}
                  className={`w-full btn ${
                    plan.is_featured ? 'btn-primary' : 'btn-outline'
                  } flex items-center justify-center gap-2`}
                >
                  {purchasing === plan.id ? (
                    'Procesando...'
                  ) : (
                    <>
                      <CreditCard size={18} />
                      Suscribirse
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Features Banner */}
        <div className="card bg-gradient-to-r from-blue-900 to-purple-900 text-white">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <Clock size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">Asistencia 24/7</h4>
              <p className="text-sm text-blue-200">Disponible cuando lo necesites</p>
            </div>
            <div>
              <Shield size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">Cobertura Nacional</h4>
              <p className="text-sm text-blue-200">En toda Guatemala</p>
            </div>
            <div>
              <Star size={32} className="mx-auto mb-2 opacity-80" />
              <h4 className="font-bold">Tecnicos Certificados</h4>
              <p className="text-sm text-blue-200">Profesionales capacitados</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
