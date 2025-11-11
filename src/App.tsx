import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, createContext, useContext, useEffect } from 'react';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CandidateDashboard from './pages/candidate/Dashboard';
import MockInterviewSetup from './pages/candidate/MockInterviewSetup';
import MockInterviewPreCheck from './pages/candidate/MockInterviewPreCheck';
import MockInterviewSession from './pages/candidate/MockInterviewSession';
import MockInterviewSummary from './pages/candidate/MockInterviewSummary';
import ResumeTools from './pages/candidate/ResumeTools';
import AIAssistant from './pages/candidate/AIAssistant';
import Events from './pages/candidate/Events';
import CandidateSettings from './pages/candidate/Settings';
import RecruiterDashboard from './pages/recruiter/Dashboard';
import ResumeAnalyzer from './pages/recruiter/ResumeAnalyzer';
import CandidateProfile from './pages/recruiter/CandidateProfile';
import RecruiterSettings from './pages/recruiter/Settings';
import AdminDashboard from './pages/admin/Dashboard';
import AdminSettings from './pages/admin/Settings';
import { authApi, authHelpers, User } from './lib/api';

// Auth Context
interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: { email: string; password: string; full_name: string; role: 'candidate' | 'recruiter' | 'admin' }) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

// Protected Route Component
function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles: string[] }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={`/${user.role}/dashboard`} />;
  }
  
  return <>{children}</>;
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user from localStorage on app start
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (authHelpers.isAuthenticated()) {
          const { data, status } = await authApi.getCurrentUser();
          if (status === 'success' && data) {
            setUser(data);
            authHelpers.setUserData(data);
          } else {
            // Token might be invalid, clear it
            authHelpers.clearTokens();
          }
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        authHelpers.clearTokens();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const { data, status, error } = await authApi.login({ email, password });
      
      if (status === 'success' && data) {
        // Store tokens
        authHelpers.setTokens(data.access_token, data.refresh_token);
        authHelpers.setUserData(data.user);
        setUser(data.user);
      } else {
        throw new Error(error || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    authHelpers.clearTokens();
    setUser(null);
  };

  const register = async (data: { email: string; password: string; full_name: string; role: 'candidate' | 'recruiter' | 'admin' }) => {
    try {
      const { data: authData, status, error } = await authApi.register(data);
      
      if (status === 'success' && authData) {
        // Store tokens
        authHelpers.setTokens(authData.access_token, authData.refresh_token);
        authHelpers.setUserData(authData.user);
        setUser(authData.user);
      } else {
        throw new Error(error || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const refreshUser = async () => {
    try {
      if (authHelpers.isAuthenticated()) {
        const { data, status } = await authApi.getCurrentUser();
        if (status === 'success' && data) {
          setUser(data);
          authHelpers.setUserData(data);
        }
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, refreshUser }}>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Candidate Routes */}
          <Route
            path="/candidate/dashboard"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <CandidateDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/mock-interview/setup"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <MockInterviewSetup />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/mock-interview/precheck/:sessionId"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <MockInterviewPreCheck />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/mock-interview/session/:sessionId"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <MockInterviewSession />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/mock-interview/summary/:sessionId"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <MockInterviewSummary />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/resume-tools"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <ResumeTools />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/ai-assistant"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <AIAssistant />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/events"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <Events />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/settings"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <CandidateSettings />
              </ProtectedRoute>
            }
          />

          {/* Recruiter Routes */}
          <Route
            path="/recruiter/dashboard"
            element={
              <ProtectedRoute allowedRoles={['recruiter']}>
                <RecruiterDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/resume-analyzer"
            element={
              <ProtectedRoute allowedRoles={['recruiter']}>
                <ResumeAnalyzer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/candidate-profile/:candidateId"
            element={
              <ProtectedRoute allowedRoles={['recruiter']}>
                <CandidateProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/settings"
            element={
              <ProtectedRoute allowedRoles={['recruiter']}>
                <RecruiterSettings />
              </ProtectedRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminSettings />
              </ProtectedRoute>
            }
          />

          {/* Redirect based on role */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthContext.Provider>
  );
}