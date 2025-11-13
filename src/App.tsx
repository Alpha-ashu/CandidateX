import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, createContext, useContext } from 'react';
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
import CandidateProfile from './pages/candidate/Profile';
import RecruiterDashboard from './pages/recruiter/Dashboard';
import ResumeAnalyzer from './pages/recruiter/ResumeAnalyzer';
import RecruiterCandidateProfile from './pages/recruiter/CandidateProfile';
import RecruiterSettings from './pages/recruiter/Settings';
import RecruiterProfile from './pages/recruiter/Profile';
import AdminDashboard from './pages/admin/Dashboard';
import AdminSettings from './pages/admin/Settings';
import AdminProfile from './pages/admin/Profile';

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
  login: (email: string, password: string, role: string) => void;
  logout: () => void;
  register: (data: any) => void;
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

  const login = (email: string, password: string, role: string) => {
    // Mock login
    const mockUser: User = {
      id: '1',
      name: email === 'recruiter@example.com' ? 'Sarah Johnson' : 'Alex Chen',
      email,
      role: role as 'candidate' | 'recruiter' | 'admin',
      avatar: undefined
    };
    setUser(mockUser);
  };

  const logout = () => {
    setUser(null);
  };

  const register = (data: any) => {
    const mockUser: User = {
      id: Math.random().toString(),
      name: data.name,
      email: data.email,
      role: data.role || 'candidate',
      avatar: undefined
    };
    setUser(mockUser);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register }}>
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
          <Route
            path="/candidate/profile"
            element={
              <ProtectedRoute allowedRoles={['candidate']}>
                <CandidateProfile />
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
                <RecruiterCandidateProfile />
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
          <Route
            path="/recruiter/profile"
            element={
              <ProtectedRoute allowedRoles={['recruiter']}>
                <RecruiterProfile />
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
          <Route
            path="/admin/profile"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminProfile />
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