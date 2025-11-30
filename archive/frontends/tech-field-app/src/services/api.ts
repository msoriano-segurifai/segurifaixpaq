import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8888/api';

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
  login: (email: string, password: string) =>
    api.post('/auth/token/', { email, password }),

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

  getMyProgress: () => api.get('/gamification/progress/'),

  getMyPoints: () => api.get('/gamification/points/'),

  getAchievements: () => api.get('/gamification/achievements/'),

  getMyAchievements: () => api.get('/gamification/achievements/my/'),

  getLeaderboard: () => api.get('/gamification/leaderboard/'),

  getDiscountCredits: () => api.get('/gamification/credits/'),
};

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
// USER WALLET API
// =============================================================================
export const userAPI = {
  getProfile: () => api.get('/users/me/'),

  updateProfile: (data: any) => api.patch('/users/me/', data),

  getFullProfile: () => api.get('/users/full-profile/'),

  getWallet: () => api.get('/paq/wallet/'),

  linkPAQAccount: (data: { bank_name: string; account_number: string; account_type: string }) =>
    api.post('/paq/wallet/link/', data),
};

export default api;
