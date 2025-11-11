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
import Settings from './pages/candidate/Settings';
import RecruiterDashboard from './pages/recruiter/Dashboard';
import ResumeAnalyzer from './pages/recruiter/ResumeAnalyzer';
import AdminDashboard from './pages/admin/Dashboard';

// Auth Context
interface User {
  id: string;
  name: string;
  email: string;
  role: 'candidate' | 'recruiter' | 'admin';
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: any) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

// Protected Route Component
function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles: string[] }) {
  const { user } = useAuth();
  
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
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');

    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
      } catch (error) {
        console.error('Failed to parse user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Store user data
      const userData: User = {
        id: data.user.id,
        name: data.user.full_name,
        email: data.user.email,
        role: data.user.role,
        avatar: undefined, // Add avatar support later if needed
      };

      localStorage.setItem('user_data', JSON.stringify(userData));
      setUser(userData);

    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
    setUser(null);
  };

  const register = async (data: any) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: data.email,
          password: data.password,
          full_name: data.name,
          role: data.role || 'candidate',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      // After successful registration, automatically log in
      await login(data.email, data.password);

    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
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
                <Settings />
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

          {/* Admin Routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminDashboard />
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
