import axios, { AxiosInstance, AxiosError } from 'axios';

// Use proxy in development (Vite proxy forwards /api to http://localhost:8000)
// In production, set VITE_API_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// =============================================================================
// AUTH API
// =============================================================================
export const authAPI = {
  login: (phone: string, password: string) =>
    api.post('/auth/token/', { phone, password }),

  refreshToken: (refresh: string) =>
    api.post('/auth/token/refresh/', { refresh }),

  verifyToken: (token: string) =>
    api.post('/auth/token/verify/', { token }),

  // PAQ SSO
  paqSSO: (paq_token: string) =>
    api.post('/users/auth/paq/sso/', { paq_token }),

  paqQuickLogin: (paq_wallet_id: string) =>
    api.post('/users/auth/paq/quick-login/', { paq_wallet_id }),

  paqLinkAccount: (paq_wallet_id: string) =>
    api.post('/users/auth/paq/link/', { paq_wallet_id }),
};


// =============================================================================
// ADMIN DASHBOARD API
// =============================================================================
export const adminAPI = {
  // SegurifAI Admin
  getFullDashboard: () => api.get('/admin/dashboard/full/'),
  getRevenueStats: () => api.get('/admin/dashboard/revenue/'),
  getUserStats: () => api.get('/admin/dashboard/users/'),
  getServiceStats: () => api.get('/admin/dashboard/services/'),

  // PAQ Admin
  getPAQDashboard: () => api.get('/admin/dashboard/paq/overview/'),
  getPAQTransactions: (params?: any) => api.get('/admin/dashboard/paq/transactions/', { params }),

  // MAWDY Admin
  getMAWDYOverview: () => api.get('/admin/dashboard/mawdy/overview/'),
  getMAWDYJobs: (params?: any) => api.get('/admin/dashboard/mawdy/jobs/', { params }),
  getMAWDYProviders: () => api.get('/admin/dashboard/mawdy/providers/'),
  getProviderMap: () => api.get('/admin/dashboard/mawdy/live-provider-map/'),
};

// =============================================================================
// ASSISTANCE API
// =============================================================================
export const assistanceAPI = {
  createRequest: (data: any) => api.post('/assistance/requests/', data),

  getMyRequests: () => api.get('/assistance/requests/'),

  getRequest: (id: number) => api.get(`/assistance/requests/${id}/`),

  cancelRequest: (id: number) => api.post(`/assistance/requests/${id}/cancel/`),

  // Vehicle Validation (AI + Human Review) - with Roadside Triage
  validateVehicle: (data: {
    // Vehicle Details
    make: string;
    model: string;
    year: string;
    plate: string;
    color?: string;
    vin?: string;
    // Roadside Emergency Triage
    emergency_type?: string;
    is_safe_location?: boolean;
    traffic_blocked?: boolean;
    hazard_lights_on?: boolean;
    passengers_count?: string;
    // Type-specific details
    tire_position?: string;
    has_spare_tire?: boolean;
    battery_age?: string;
    fuel_type?: string;
    fuel_amount?: string;
    keys_location?: string;
    towing_destination?: string;
    towing_distance?: string;
    additional_details?: string;
  }) => api.post('/assistance/validate-vehicle/', data),

  // Health Questionnaire Validation (AI + Human Review) - SAMPLE Format
  validateHealth: (data: {
    emergency_type: string;
    // S - Signs/Symptoms
    symptoms: string;
    pain_scale?: number;
    // A - Allergies
    has_allergies?: boolean;
    allergies?: string;
    // M - Medications
    is_on_medications?: boolean;
    medications?: string;
    // P - Past Medical History
    has_conditions?: boolean;
    pre_existing_conditions?: string;
    // L - Last Oral Intake
    last_intake_time?: string;
    last_intake?: string;
    // E - Events Leading Up
    events_leading?: string;
    // Patient Demographics
    patient_name?: string;
    patient_relationship?: string;
    patient_age: string;
    patient_gender: string;
    patient_weight?: string;
    // Critical Indicators
    consciousness_level: string;
    breathing_difficulty: boolean;
    chest_pain: boolean;
    bleeding: boolean;
    // Additional
    people_affected?: string;
  }) => api.post('/assistance/validate-health/', data),

  // Generic Service Validation (AI + Human Review for all MAWDY services)
  validateService: (data: {
    service_id: string;
    service_name: string;
    plan_type: 'DRIVE' | 'HEALTH';
    form_type: string;
    description?: string;
    location?: string;
    taxi_info?: {
      pickup_location: string;
      destination: string;
      pickup_time?: string;
      num_passengers?: string;
      special_needs?: string;
    };
    legal_info?: {
      legal_issue_type: string;
      issue_description: string;
      urgency?: string;
      related_to_accident?: boolean;
    };
    generic_info?: {
      service_details: string;
      special_requirements?: string;
    };
  }) => api.post('/assistance/validate-service/', data),

  // Tracking
  getTracking: (id: number) => api.get(`/assistance/tracking/${id}/`),

  getLiveTracking: (id: number) => api.get(`/assistance/live/${id}/`),

  getPublicTracking: (token: string) => api.get(`/assistance/tracking/public/${token}/`),
};

// =============================================================================
// DISPATCH API (Field Tech)
// =============================================================================
export const dispatchAPI = {
  getMyProfile: () => api.get('/providers/dispatch/my-profile/'),

  goOnline: (latitude: number, longitude: number) =>
    api.post('/providers/dispatch/online/', { latitude, longitude }),

  goOffline: () => api.post('/providers/dispatch/offline/'),

  updateLocation: (data: { latitude: number; longitude: number; heading?: number; speed?: number }) =>
    api.post('/providers/dispatch/location/', data),

  getAvailableJobs: () => api.get('/assistance/dispatch/available/'),

  getMyActiveJobs: () => api.get('/assistance/dispatch/my-jobs/'),

  acceptJob: (requestId: number) =>
    api.post(`/assistance/dispatch/${requestId}/accept/`),

  departForJob: (requestId: number) =>
    api.post(`/assistance/dispatch/${requestId}/depart/`),

  markArrived: (requestId: number) =>
    api.post(`/assistance/tracking/${requestId}/arrived/`),

  startService: (requestId: number) =>
    api.post(`/assistance/tracking/${requestId}/start/`),

  completeService: (requestId: number, data?: any) =>
    api.post(`/assistance/tracking/${requestId}/completed/`, data),

  getJobHistory: () => api.get('/providers/dispatch/jobs/history/'),

  getEarnings: () => api.get('/providers/dispatch/earnings/'),
};

// =============================================================================
// SERVICES & SUBSCRIPTIONS API
// =============================================================================
export const servicesAPI = {
  getCategories: () => api.get('/services/categories/'),

  getPlans: () => api.get('/services/plans/'),

  getPlanServices: (planType: string) =>
    api.get(`/providers/mawdy/plans/${planType}/services/`),

  getMyUsage: (planType: string) =>
    api.get(`/providers/mawdy/plans/${planType}/my-usage/`),

  // Subscriptions
  getMySubscriptions: () => api.get('/services/subscriptions/my/'),

  purchaseSubscription: (planId: number, billingCycle: 'monthly' | 'yearly') =>
    api.post('/services/subscriptions/purchase/', { plan_id: planId, billing_cycle: billingCycle }),

  // PAQ Payment Flow
  purchaseWithPAQ: (data: { plan_id: number; billing_cycle: string; phone_number: string }) =>
    api.post('/services/subscriptions/purchase-with-paq/', data),

  confirmPAQPayment: (data: { paypaq_code: string; phone_number: string; pending_data?: any }) =>
    api.post('/services/subscriptions/confirm-paq-payment/', data),

  // Subscription Management
  cancelSubscription: (subscriptionId: number) =>
    api.post(`/services/subscriptions/${subscriptionId}/cancel/`),

  deleteSubscription: (subscriptionId: number) =>
    api.delete(`/services/subscriptions/${subscriptionId}/`),

  // Renewal
  getRenewalStatus: (subscriptionId: number) =>
    api.get(`/services/renewal/${subscriptionId}/status/`),

  initiateRenewal: (subscriptionId: number) =>
    api.post(`/services/renewal/${subscriptionId}/renew/`),
};

// =============================================================================
// E-LEARNING / GAMIFICATION API
// =============================================================================
export const elearningAPI = {
  getModules: () => api.get('/gamification/modules/'),

  getModule: (id: number) => api.get(`/gamification/modules/${id}/`),

  startModule: (id: number) => api.post(`/gamification/modules/${id}/start/`),

  completeModule: (id: number, quizScore?: number) =>
    api.post(`/gamification/modules/${id}/complete/`, { quiz_score: quizScore }),

  submitQuiz: (moduleId: number, answers: any) =>
    api.post(`/gamification/modules/${moduleId}/complete/`, answers),

  getMyProgress: () => api.get('/gamification/progress/'),

  getMyPoints: () => api.get('/gamification/points/'),

  getAchievements: () => api.get('/gamification/achievements/'),

  getMyAchievements: () => api.get('/gamification/achievements/my/'),

  getLeaderboard: () => api.get('/gamification/leaderboard/'),

  getDiscountCredits: () => api.get('/gamification/credits/'),

  // Claim all available rewards (backend uses /rewards/claim/ for all at once)
  claimRewards: () =>
    api.post('/gamification/rewards/claim/'),

  // Alias for backwards compatibility - redirects to claim all
  redeemReward: (_rewardId: number) =>
    api.post('/gamification/rewards/claim/'),

  // Get rewards tiers and status
  getRewardsTiers: () =>
    api.get('/gamification/rewards/tiers/'),

  getMyRewards: () =>
    api.get('/gamification/rewards/'),
};

// =============================================================================
// PROMO CODES API
// =============================================================================
export const promoCodesAPI = {
  validatePromoCode: (code: string) =>
    api.post('/promotions/validate/', { code }),

  applyPromoCode: (code: string) =>
    api.post('/promotions/apply/', { code }),

  getAvailableCodes: () =>
    api.get('/promotions/available/'),

  getMyUsageHistory: () =>
    api.get('/promotions/my-usage/'),
};

// Alias for backwards compatibility
export const gamificationAPI = promoCodesAPI;

// =============================================================================
// MAPS API
// =============================================================================
export const mapsAPI = {
  geocode: (address: string) =>
    api.get('/maps/geocode/', { params: { address } }),

  reverseGeocode: (lat: number, lng: number) =>
    api.get('/maps/reverse-geocode/', { params: { lat, lng } }),

  getETA: (providerLat: number, providerLng: number, userLat: number, userLng: number) =>
    api.get('/maps/eta/', {
      params: { provider_lat: providerLat, provider_lng: providerLng, user_lat: userLat, user_lng: userLng }
    }),

  autocomplete: (query: string) =>
    api.get('/maps/autocomplete/', { params: { query } }),
};

// =============================================================================
// AI DOCUMENT REVIEW API
// =============================================================================
export const documentAPI = {
  // Upload document with AI review
  uploadDocument: (requestId: number, documentType: string, file: File) => {
    const formData = new FormData();
    formData.append('request_id', requestId.toString());
    formData.append('document_type', documentType);
    formData.append('file', file);
    return api.post('/assistance/docs/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Get documents for a request
  getRequestDocuments: (requestId: number) =>
    api.get(`/assistance/docs/${requestId}/`),

  // Get required documents
  getRequiredDocuments: (requestId: number) =>
    api.get(`/assistance/docs/${requestId}/required/`),

  // Check documents status
  checkDocumentsComplete: (requestId: number) =>
    api.get(`/assistance/docs/${requestId}/status/`),

  // Get document types
  getDocumentTypes: () =>
    api.get('/assistance/docs/types/'),

  // Delete document
  deleteDocument: (documentId: number) =>
    api.delete(`/assistance/docs/${documentId}/delete/`),

  // Trigger AI review
  aiReviewDocument: (documentId: number) =>
    api.post(`/assistance/docs/${documentId}/ai-review/`),
};

// =============================================================================
// EVIDENCE FORM API (AI-powered forms)
// =============================================================================
export const evidenceAPI = {
  // Get evidence options for a request
  getEvidenceOptions: (requestId: number) =>
    api.get(`/assistance/evidence/options/${requestId}/`),

  // Get evidence status
  getEvidenceStatus: (requestId: number) =>
    api.get(`/assistance/evidence/status/${requestId}/`),

  // Get form template
  getFormTemplate: (formType: string) =>
    api.get(`/assistance/evidence/template/${formType}/`),

  // Create evidence form
  createEvidenceForm: (data: any) =>
    api.post('/assistance/evidence/forms/', data),

  // Update evidence form
  updateEvidenceForm: (formId: number, data: any) =>
    api.put(`/assistance/evidence/forms/${formId}/`, data),

  // Submit form for AI review
  submitEvidenceForm: (formId: number, declarationAccepted: boolean) =>
    api.post(`/assistance/evidence/forms/${formId}/submit/`, {
      declaration_accepted: declarationAccepted
    }),

  // Get my forms
  getMyForms: () =>
    api.get('/assistance/evidence/forms/'),

  // Get specific form
  getForm: (formId: number) =>
    api.get(`/assistance/evidence/forms/${formId}/`),
};

// =============================================================================
// AI PLAN SUGGESTION API
// =============================================================================
export const aiAPI = {
  // Get AI-powered plan suggestions based on user's needs
  getPlanSuggestion: (prompt: string) =>
    api.post('/services/ai/plan-suggestion/', { prompt }),
};

// =============================================================================
// USER / PROFILE API
// =============================================================================
export const userAPI = {
  getProfile: () => api.get('/users/me/'),

  updateProfile: (data: any) => api.patch('/users/me/', data),

  getFullProfile: () => api.get('/users/full-profile/'),

  // Emergency contacts
  addEmergencyContact: (data: { name: string; phone: string; relationship: string }) =>
    api.post('/users/emergency-contacts/', data),

  deleteEmergencyContact: (id: number) =>
    api.delete(`/users/emergency-contacts/${id}/`),

  // Password
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/users/change-password/', data),

  // PAQ Wallet endpoints
  getWalletBalance: () => api.get('/wallet/balance/'),

  getWalletHistory: () => api.get('/wallet/history/'),

  generatePaymentToken: (data: { amount: number; reference: string; description?: string }) =>
    api.post('/wallet/generate-token/', data),
};

export default api;
