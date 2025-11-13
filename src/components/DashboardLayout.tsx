import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Avatar, AvatarFallback } from './ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import {
  Home,
  FileText,
  Bot,
  Calendar,
  Settings,
  Bell,
  LogOut,
  User,
  BarChart3,
  Briefcase,
  Users,
  Shield,
  DollarSign,
  FileBarChart
} from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
  role: 'candidate' | 'recruiter' | 'admin';
}

export default function DashboardLayout({ children, role }: DashboardLayoutProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const candidateNav = [
    { icon: Home, label: 'Dashboard', path: '/candidate/dashboard' },
    { icon: FileText, label: 'Mock Interviews', path: '/candidate/mock-interview/setup' },
    { icon: FileBarChart, label: 'Resume Tools', path: '/candidate/resume-tools' },
    { icon: Bot, label: 'AI Assistant', path: '/candidate/ai-assistant' },
    { icon: Calendar, label: 'Events', path: '/candidate/events' },
    { icon: Settings, label: 'Settings', path: '/candidate/settings' },
  ];

  const recruiterNav = [
    { icon: Home, label: 'Dashboard', path: '/recruiter/dashboard' },
    { icon: FileBarChart, label: 'Resume Analyzer', path: '/recruiter/resume-analyzer' },
    { icon: Users, label: 'Live Interviews', path: '/recruiter/live-interviews' },
    { icon: Bot, label: 'AI Assistant', path: '/recruiter/ai-assistant' },
    { icon: Calendar, label: 'Events', path: '/recruiter/events' },
    { icon: Settings, label: 'Settings', path: '/recruiter/settings' },
  ];

  const adminNav = [
    { icon: Home, label: 'Dashboard', path: '/admin/dashboard' },
    { icon: Users, label: 'User Management', path: '/admin/users' },
    { icon: Shield, label: 'Audit Logs', path: '/admin/audit-logs' },
    { icon: FileText, label: 'Policies', path: '/admin/policies' },
    { icon: DollarSign, label: 'Billing', path: '/admin/billing' },
    { icon: Settings, label: 'Settings', path: '/admin/settings' },
  ];

  const navItems = role === 'candidate' ? candidateNav : role === 'recruiter' ? recruiterNav : adminNav;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r hidden md:flex flex-col fixed h-screen">
        {/* Logo */}
        <div className="p-6 border-b">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm">CX</span>
            </div>
            <span className="text-lg">CandidateX</span>
          </Link>
        </div>

        {/* User Profile */}
        <div className="p-6 border-b">
          <Link to={`/${role}/profile`} className="block">
            <div className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer">
              <Avatar>
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                  {user?.name.split(' ').map(n => n[0]).join('') || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="truncate">{user?.name}</div>
                <div className="text-sm text-gray-500 capitalize">{role}</div>
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t">
          <Button variant="ghost" className="w-full justify-start gap-3" onClick={handleLogout}>
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 md:ml-64">
        {/* Header */}
        <header className="bg-white border-b sticky top-0 z-40">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl">
                {role === 'candidate' ? 'Candidate' : role === 'recruiter' ? 'Recruiter' : 'Admin'} Portal
              </h1>
            </div>
            <div className="flex items-center gap-4">
              {/* Notifications */}
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </Button>

              {/* Profile Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="gap-2">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                        {user?.name.split(' ').map(n => n[0]).join('') || 'U'}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col">
                      <span>{user?.name}</span>
                      <span className="text-xs text-gray-500 font-normal">{user?.email}</span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to={`/${role}/profile`} className="cursor-pointer">
                      <User className="w-4 h-4 mr-2" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to={`/${role}/settings`} className="cursor-pointer">
                      <Settings className="w-4 h-4 mr-2" />
                      Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}