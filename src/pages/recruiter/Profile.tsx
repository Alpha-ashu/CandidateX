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
import { Mail, MapPin, Phone, Briefcase, Building, Users, Award, Edit, Save, X, Calendar } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

export default function RecruiterProfile() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Mock profile data
  const [profileData, setProfileData] = useState({
    name: user?.name || 'Sarah Johnson',
    email: user?.email || 'sarah.johnson@example.com',
    phone: '+1 (555) 987-6543',
    location: 'New York, NY',
    bio: 'Experienced technical recruiter specializing in engineering and product roles. Passionate about connecting talented individuals with great opportunities.',
    title: 'Senior Technical Recruiter',
    company: 'Tech Solutions Inc.',
    department: 'Talent Acquisition',
    experience: '7 years',
    specializations: ['Software Engineering', 'Product Management', 'Data Science', 'DevOps'],
  });

  const stats = [
    { label: 'Candidates Interviewed', value: '347', icon: Users },
    { label: 'Successful Placements', value: '89', icon: Award },
    { label: 'Active Positions', value: '12', icon: Briefcase },
    { label: 'Member Since', value: 'Sep 2022', icon: Calendar },
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
    <DashboardLayout role="recruiter">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl mb-2">My Profile</h1>
            <p className="text-gray-600">Manage your professional information and recruiting details</p>
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
          <div className="h-32 bg-gradient-to-r from-purple-500 via-pink-500 to-red-500"></div>
          <CardContent className="relative pt-0 pb-6">
            <div className="flex flex-col md:flex-row gap-6 -mt-16 md:-mt-12">
              {/* Avatar */}
              <div className="relative">
                <Avatar className="w-32 h-32 border-4 border-white shadow-lg">
                  <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-600 text-white text-4xl">
                    {profileData.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                {isEditing && (
                  <Button size="sm" variant="outline" className="absolute bottom-0 right-0 rounded-full">
                    <Edit className="w-3 h-3" />
                  </Button>
                )}
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
                        <p className="text-lg text-gray-600 mb-3">{profileData.title} at {profileData.company}</p>
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
                      <Badge className="bg-blue-100 text-blue-700">Verified Recruiter</Badge>
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
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Icon className="w-5 h-5 text-purple-600" />
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
              <CardTitle>About Me</CardTitle>
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

          {/* Professional Info */}
          <Card>
            <CardHeader>
              <CardTitle>Professional Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isEditing ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="title">Job Title</Label>
                    <Input 
                      id="title" 
                      value={profileData.title}
                      onChange={(e) => setProfileData({...profileData, title: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input 
                      id="company" 
                      value={profileData.company}
                      onChange={(e) => setProfileData({...profileData, company: e.target.value})}
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
                  <div className="space-y-2">
                    <Label htmlFor="experience">Years of Experience</Label>
                    <Input 
                      id="experience" 
                      value={profileData.experience}
                      onChange={(e) => setProfileData({...profileData, experience: e.target.value})}
                    />
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-start gap-3">
                    <Briefcase className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm text-gray-500">Current Position</div>
                      <div>{profileData.title}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Building className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm text-gray-500">Company</div>
                      <div>{profileData.company}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Users className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm text-gray-500">Department</div>
                      <div>{profileData.department}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm text-gray-500">Experience</div>
                      <div>{profileData.experience} in recruiting</div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Specializations */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recruiting Specializations</CardTitle>
              <CardDescription>Areas you typically recruit for</CardDescription>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <div className="space-y-2">
                  <Label htmlFor="specializations">Specializations (comma separated)</Label>
                  <Textarea 
                    id="specializations" 
                    rows={3}
                    value={profileData.specializations.join(', ')}
                    onChange={(e) => setProfileData({...profileData, specializations: e.target.value.split(',').map(s => s.trim())})}
                  />
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {profileData.specializations.map((spec, idx) => (
                    <Badge key={idx} variant="secondary" className="text-sm px-4 py-2">{spec}</Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { action: 'Interviewed', candidate: 'John Doe', position: 'Senior Frontend Developer', time: '2 hours ago' },
                  { action: 'Shortlisted', candidate: 'Jane Smith', position: 'Product Manager', time: '5 hours ago' },
                  { action: 'Posted', candidate: null, position: 'DevOps Engineer', time: '1 day ago' },
                  { action: 'Hired', candidate: 'Mike Johnson', position: 'UX Designer', time: '2 days ago' },
                ].map((activity, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b last:border-b-0">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">{activity.action}</Badge>
                        <span>
                          {activity.candidate ? (
                            <>
                              <span>{activity.candidate}</span> for <span>{activity.position}</span>
                            </>
                          ) : (
                            <span>{activity.position}</span>
                          )}
                        </span>
                      </div>
                    </div>
                    <span className="text-sm text-gray-500">{activity.time}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
