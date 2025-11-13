/**
 * Frontend-Backend API Integration Layer
 * Handles all communication with the CandidateX backend API
 */

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_BASE_PATH = '/api/v1';

// HTTP client configuration
const apiClient = {
  baseURL: `${API_BASE_URL}${API_BASE_PATH}`,
  headers: {
    'Content-Type': 'application/json',
  },
};

// API endpoints
export const API_ENDPOINTS = {
  // Authentication
  REGISTER: '/auth/register',
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  REFRESH: '/auth/refresh-token',
  ME: '/auth/me',
  
  // User management
  USERS: '/users',
  USER_PROFILE: '/users/me',
  USER_UPDATE: '/users/me',
  
  // Interview management
  INTERVIEWS: '/interviews',
  INTERVIEW_BY_ID: '/interviews',
  INTERVIEW_QUESTIONS: '/interviews',
  
  // Dashboard
  DASHBOARD_STATS: '/dashboard/stats',
  DASHBOARD_OVERVIEW: '/dashboard',
  
  // AI services
  AI_CHAT: '/ai/chat',
  AI_GENERATE_QUESTIONS: '/ai/generate-questions',
  AI_ANALYZE_RESPONSE: '/ai/analyze-response',
  
  // Admin functions
  ADMIN_STATS: '/admin/stats',
  ADMIN_USERS: '/admin/users',

  // Feedback
  FEEDBACK: '/feedback',
  FEEDBACK_STATS: '/feedback/stats/summary',

  // Health
  HEALTH: '/health',
};

// Helper function to get auth headers
const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// API response types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: 'success' | 'error';
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'candidate' | 'recruiter' | 'admin';
  status: string;
  avatar_url?: string;
  phone?: string;
  location?: string;
  bio?: string;
  linkedin_url?: string;
  github_url?: string;
  email_verified: boolean;
  two_factor_enabled: boolean;
  preferred_language: string;
  timezone: string;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role: 'candidate' | 'recruiter' | 'admin';
}

// Generic API request function
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${apiClient.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        ...apiClient.headers,
        ...options.headers,
        ...getAuthHeaders(),
      },
      ...options,
    };

    const response = await fetch(url, config);
    const contentType = response.headers.get('content-type');
    
    if (!response.ok) {
      // Handle different error types
      if (response.status === 401) {
        // Unauthorized - clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
        return { status: 'error', error: 'Authentication required' };
      }
      
      if (contentType?.includes('application/json')) {
        const errorData = await response.json();
        return { 
          status: 'error', 
          error: errorData.detail || errorData.message || 'API request failed' 
        };
      } else {
        return { 
          status: 'error', 
          error: `HTTP ${response.status}: ${response.statusText}` 
        };
      }
    }

    // Handle empty responses (like 204 No Content)
    if (response.status === 204) {
      return { status: 'success', data: undefined as T };
    }

    // Parse JSON response
    const data = contentType?.includes('application/json') 
      ? await response.json() 
      : await response.text();
    
    return { 
      status: 'success', 
      data 
    };
    
  } catch (error) {
    console.error('API request failed:', error);
    return { 
      status: 'error', 
      error: error instanceof Error ? error.message : 'Network request failed' 
    };
  }
}

// Authentication API functions
export const authApi = {
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthResponse>> {
    return apiRequest<AuthResponse>(API_ENDPOINTS.LOGIN, {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  async register(userData: RegisterRequest): Promise<ApiResponse<AuthResponse>> {
    return apiRequest<AuthResponse>(API_ENDPOINTS.REGISTER, {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  async logout(): Promise<ApiResponse<void>> {
    return apiRequest<void>(API_ENDPOINTS.LOGOUT, {
      method: 'POST',
    });
  },

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return apiRequest<User>(API_ENDPOINTS.ME);
  },

  async refreshToken(refreshToken: string): Promise<ApiResponse<AuthResponse>> {
    return apiRequest<AuthResponse>(API_ENDPOINTS.REFRESH, {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },
};

// User API functions
export const userApi = {
  async getProfile(): Promise<ApiResponse<User>> {
    return apiRequest<User>(API_ENDPOINTS.USER_PROFILE);
  },

  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    return apiRequest<User>(API_ENDPOINTS.USER_UPDATE, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },
};

// Interview API functions
export const interviewApi = {
  async createInterview(interviewData: any): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.INTERVIEWS, {
      method: 'POST',
      body: JSON.stringify(interviewData),
    });
  },

  async getInterview(id: string): Promise<ApiResponse<any>> {
    return apiRequest(`${API_ENDPOINTS.INTERVIEW_BY_ID}/${id}`);
  },

  async getUserInterviews(): Promise<ApiResponse<any[]>> {
    return apiRequest(API_ENDPOINTS.INTERVIEWS);
  },
};

// AI API functions
export const aiApi = {
  async generateQuestions(params: any): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.AI_GENERATE_QUESTIONS, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async chat(message: string, context?: any): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.AI_CHAT, {
      method: 'POST',
      body: JSON.stringify({ message, context }),
    });
  },

  async analyzeResponse(response: any): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.AI_ANALYZE_RESPONSE, {
      method: 'POST',
      body: JSON.stringify(response),
    });
  },
};

// Dashboard API functions
export const dashboardApi = {
  async getStats(): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.DASHBOARD_STATS);
  },

  async getOverview(): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.DASHBOARD_OVERVIEW);
  },
};

// Admin API functions
export const adminApi = {
  async getStats(): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.ADMIN_STATS);
  },

  async getUsers(): Promise<ApiResponse<any[]>> {
    return apiRequest(API_ENDPOINTS.ADMIN_USERS);
  },
};

// Feedback API functions
export const feedbackApi = {
  async submitFeedback(feedbackData: {
    feedback_type: string;
    subject: string;
    message: string;
    rating?: number;
    page_url?: string;
  }): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.FEEDBACK, {
      method: 'POST',
      body: JSON.stringify(feedbackData),
    });
  },

  async getFeedback(params?: {
    feedback_type?: string;
    status?: string;
  }): Promise<ApiResponse<any[]>> {
    const queryParams = params ? new URLSearchParams(params).toString() : '';
    const endpoint = queryParams ? `${API_ENDPOINTS.FEEDBACK}?${queryParams}` : API_ENDPOINTS.FEEDBACK;
    return apiRequest(endpoint);
  },

  async getFeedbackById(id: string): Promise<ApiResponse<any>> {
    return apiRequest(`${API_ENDPOINTS.FEEDBACK}/${id}`);
  },

  async updateFeedbackStatus(id: string, status: string): Promise<ApiResponse<any>> {
    return apiRequest(`${API_ENDPOINTS.FEEDBACK}/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  },

  async deleteFeedback(id: string): Promise<ApiResponse<any>> {
    return apiRequest(`${API_ENDPOINTS.FEEDBACK}/${id}`, {
      method: 'DELETE',
    });
  },

  async getFeedbackStats(): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.FEEDBACK_STATS);
  },
};

// Health check
export const healthApi = {
  async check(): Promise<ApiResponse<any>> {
    return apiRequest(API_ENDPOINTS.HEALTH);
  },
};

// Auth helper functions
export const authHelpers = {
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  },

  getAccessToken: (): string | null => {
    return localStorage.getItem('access_token');
  },

  getRefreshToken: (): string | null => {
    return localStorage.getItem('refresh_token');
  },

  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token');
  },

  setUserData: (user: User) => {
    localStorage.setItem('user_data', JSON.stringify(user));
  },

  getUserData: (): User | null => {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  },
};

// Auto-refresh token on 401 errors
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
};

const addAuthInterceptor = () => {
  const originalFetch = window.fetch;
  
  window.fetch = async (...args) => {
    const [url, config] = args;
    
    let response: Response;
    
    try {
      // Check if this is an API request
      if (typeof url === 'string' && url.startsWith(apiClient.baseURL)) {
        response = await originalFetch(url, config);
        
        if (response.status === 401 && !isRefreshing) {
          isRefreshing = true;
          
          const refreshToken = authHelpers.getRefreshToken();
          if (refreshToken) {
            try {
              const { data } = await authApi.refreshToken(refreshToken);
              if (data) {
                authHelpers.setTokens(data.access_token, data.refresh_token);
                onRefreshed(data.access_token);
                
                // Retry original request with new token
                const newConfig = {
                  ...config,
                  headers: {
                    ...(config?.headers || {}),
                    Authorization: `Bearer ${data.access_token}`,
                  },
                };
                
                return originalFetch(url, newConfig);
              }
            } catch (error) {
              authHelpers.clearTokens();
              window.location.href = '/login';
              return new Response(JSON.stringify({ error: 'Authentication failed' }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
              });
            } finally {
              isRefreshing = false;
            }
          } else {
            authHelpers.clearTokens();
            window.location.href = '/login';
          }
        }
      } else {
        response = await originalFetch(url, config);
      }
      
      return response;
    } catch (error) {
      console.error('Fetch error:', error);
      throw error;
    }
  };
};

// Initialize auth interceptor
addAuthInterceptor();

// Export everything
export default {
  auth: authApi,
  user: userApi,
  interview: interviewApi,
  ai: aiApi,
  dashboard: dashboardApi,
  admin: adminApi,
  feedback: feedbackApi,
  health: healthApi,
  helpers: authHelpers,
  endpoints: API_ENDPOINTS,
  baseURL: apiClient.baseURL,
};
