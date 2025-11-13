import { useState } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Avatar, AvatarFallback } from '../../components/ui/avatar';
import { Textarea } from '../../components/ui/textarea';
import { useAuth } from '../../App';
import { Mail, MapPin, Phone, Shield, Calendar, Activity, Users, Database, Edit, Save, X } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

export default function AdminProfile() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Mock profile data
  const [profileData, setProfileData] = useState({
    name: user?.name || 'Admin User',
    email: user?.email || 'admin@candidatex.com',
    phone: '+1 (555) 000-1234',
    location: 'San Francisco, CA',
    bio: 'Platform administrator with full system access. Responsible for managing users, system configuration, and ensuring platform security.',
    role: 'System Administrator',
    department: 'IT Operations',
    permissions: ['Full System Access', 'User Management', 'Security Configuration', 'Audit Logs', 'Billing Management'],
  });

  const stats = [
    { label: 'Total Users', value: '2,847', icon: Users },
    { label: 'System Uptime', value: '99.9%', icon: Activity },
    { label: 'Active Sessions', value: '342', icon: Database },
    { label: 'Admin Since', value: 'Jan 2023', icon: Calendar },
  ];

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setIsEditing(false);
      toast.success('Profile updated successfully!');
    }, 1000);
  };

  return (
    <DashboardLayout role="admin">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl mb-2">Admin Profile</h1>
            <p className="text-gray-600">Manage your administrator information and permissions</p>
          </div>
          {!isEditing ? (
            <Button onClick={() => setIsEditing(true)}>
              <Edit className="w-4 h-4 mr-2" />
              Edit Profile
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          )}
        </div>

        {/* Profile Card */}
        <Card>
          <div className="h-32 bg-gradient-to-r from-gray-700 via-gray-800 to-black"></div>
          <CardContent className="relative pt-0 pb-6">
            <div className="flex flex-col md:flex-row gap-6 -mt-16 md:-mt-12">
              {/* Avatar */}
              <div className="relative">
                <Avatar className="w-32 h-32 border-4 border-white shadow-lg">
                  <AvatarFallback className="bg-gradient-to-br from-gray-700 to-gray-900 text-white text-4xl">
                    {profileData.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                {isEditing && (
                  <Button size="sm" variant="outline" className="absolute bottom-0 right-0 rounded-full">
                    <Edit className="w-3 h-3" />
                  </Button>
                )}
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2">
                  <Badge className="bg-red-600 text-white">
                    <Shield className="w-3 h-3 mr-1" />
                    Admin
                  </Badge>
                </div>
              </div>

              {/* Profile Info */}
              <div className="flex-1 mt-16 md:mt-0">
                {isEditing ? (
                  <div className="space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="name">Full Name</Label>
                        <Input 
                          id="name" 
                          value={profileData.name}
                          onChange={(e) => setProfileData({...profileData, name: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input 
                          id="email" 
                          type="email"
                          value={profileData.email}
                          onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                        />
                      </div>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone</Label>
                        <Input 
                          id="phone" 
                          value={profileData.phone}
                          onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="location">Location</Label>
                        <Input 
                          id="location" 
                          value={profileData.location}
                          onChange={(e) => setProfileData({...profileData, location: e.target.value})}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-2xl mb-1">{profileData.name}</h2>
                        <p className="text-lg text-gray-600 mb-3">{profileData.role} • {profileData.department}</p>
                        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            <span>{profileData.email}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Phone className="w-4 h-4" />
                            <span>{profileData.phone}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            <span>{profileData.location}</span>
                          </div>
                        </div>
                      </div>
                      <Badge className="bg-green-100 text-green-700">Active</Badge>
                    </div>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <Card key={idx}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Icon className="w-5 h-5 text-gray-700" />
                    </div>
                    <div>
                      <div className="text-2xl">{stat.value}</div>
                      <div className="text-xs text-gray-600">{stat.label}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* About */}
          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea 
                    id="bio" 
                    rows={6}
                    value={profileData.bio}
                    onChange={(e) => setProfileData({...profileData, bio: e.target.value})}
                  />
                </div>
              ) : (
                <p className="text-gray-700">{profileData.bio}</p>
              )}
            </CardContent>
          </Card>

          {/* Role Info */}
          <Card>
            <CardHeader>
              <CardTitle>Role Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isEditing ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="role">Role</Label>
                    <Input 
                      id="role" 
                      value={profileData.role}
                      onChange={(e) => setProfileData({...profileData, role: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Input 
                      id="department" 
                      value={profileData.department}
                      onChange={(e) => setProfileData({...profileData, department: e.target.value})}
                    />
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm text-gray-500">Admin Role</div>
                      <div>{profileData.role}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Users className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm text-gray-500">Department</div>
                      <div>{profileData.department}</div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Permissions */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Admin Permissions</CardTitle>
              <CardDescription>Your current system permissions and access levels</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-3">
                {profileData.permissions.map((permission, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <Shield className="w-5 h-5 text-green-600" />
                    <span>{permission}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Actions */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recent Admin Actions</CardTitle>
              <CardDescription>Your latest administrative activities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { action: 'User Created', details: 'Created new recruiter account for john.smith@company.com', time: '1 hour ago', type: 'success' },
                  { action: 'Settings Updated', details: 'Modified email notification settings', time: '3 hours ago', type: 'info' },
                  { action: 'Security Alert', details: 'Reviewed failed login attempts', time: '5 hours ago', type: 'warning' },
                  { action: 'System Maintenance', details: 'Completed database backup', time: '1 day ago', type: 'success' },
                ].map((activity, idx) => (
                  <div key={idx} className="flex items-start justify-between py-3 border-b last:border-b-0">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${
                            activity.type === 'success' ? 'border-green-600 text-green-700' :
                            activity.type === 'warning' ? 'border-yellow-600 text-yellow-700' :
                            'border-blue-600 text-blue-700'
                          }`}
                        >
                          {activity.action}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">{activity.details}</p>
                    </div>
                    <span className="text-sm text-gray-500 whitespace-nowrap ml-4">{activity.time}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Security Info */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Security Information</CardTitle>
              <CardDescription>Your account security details</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-5 h-5 text-green-600" />
                    <span className="text-sm">Two-Factor Auth</span>
                  </div>
                  <div className="text-xs text-gray-600">Enabled</div>
                </div>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="w-5 h-5 text-blue-600" />
                    <span className="text-sm">Last Login</span>
                  </div>
                  <div className="text-xs text-gray-600">Today at 9:23 AM</div>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="w-5 h-5 text-purple-600" />
                    <span className="text-sm">Session Status</span>
                  </div>
                  <div className="text-xs text-gray-600">Active (3 devices)</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
