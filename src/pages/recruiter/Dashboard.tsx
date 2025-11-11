import { Link } from 'react-router-dom';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import {
  Users,
  FileText,
  Calendar,
  TrendingUp,
  Clock,
  CheckCircle,
  Target,
  Award
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function RecruiterDashboard() {
  const interviewData = [
    { date: 'Mon', count: 5 },
    { date: 'Tue', count: 8 },
    { date: 'Wed', count: 6 },
    { date: 'Thu', count: 10 },
    { date: 'Fri', count: 7 },
    { date: 'Sat', count: 3 },
    { date: 'Sun', count: 2 },
  ];

  const candidateQuality = [
    { category: 'Excellent', count: 15 },
    { category: 'Good', count: 28 },
    { category: 'Average', count: 12 },
    { category: 'Below', count: 5 },
  ];

  const upcomingInterviews = [
    { candidate: 'John Smith', position: 'Senior Developer', time: 'Today, 2:00 PM', score: 85 },
    { candidate: 'Sarah Chen', position: 'Product Manager', time: 'Today, 4:00 PM', score: 92 },
    { candidate: 'Mike Johnson', position: 'UX Designer', time: 'Tomorrow, 10:00 AM', score: 78 },
  ];

  const recentActivities = [
    { action: 'Interviewed John Doe', position: 'Senior Developer', result: 'Hired', time: '2 hours ago' },
    { action: 'Analyzed 12 resumes', position: 'Product Manager', result: 'Shortlisted 5', time: '5 hours ago' },
    { action: 'Scheduled interview', position: 'Data Scientist', result: 'Confirmed', time: 'Yesterday' },
  ];

  return (
    <DashboardLayout role="recruiter">
      <div className="space-y-6">
        {/* Welcome Section */}
        <div>
          <h2 className="text-3xl mb-2">Welcome back, Sarah!</h2>
          <p className="text-gray-600">Here's your recruitment overview</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Candidates</p>
                  <p className="text-3xl mt-1">45</p>
                  <p className="text-sm text-green-600 flex items-center gap-1 mt-1">
                    <TrendingUp className="w-4 h-4" />
                    +12 this week
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Interviews Today</p>
                  <p className="text-3xl mt-1">8</p>
                  <p className="text-sm text-gray-500 mt-1">3 completed</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Avg Interview Score</p>
                  <p className="text-3xl mt-1">82/100</p>
                  <p className="text-sm text-gray-500 mt-1">Last 30 days</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Award className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Positions Open</p>
                  <p className="text-3xl mt-1">12</p>
                  <p className="text-sm text-gray-500 mt-1">5 urgent</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Target className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Interview Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Interview Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={interviewData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Candidate Quality */}
          <Card>
            <CardHeader>
              <CardTitle>Candidate Quality Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={candidateQuality}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Upcoming Interviews & Quick Actions */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Upcoming Interviews */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Upcoming Interviews</CardTitle>
                <Button variant="outline" size="sm">View All</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {upcomingInterviews.map((interview, idx) => (
                  <div key={idx} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white">
                      {interview.candidate.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3>{interview.candidate}</h3>
                        <span className="text-sm text-gray-500">• {interview.position}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          <span>{interview.time}</span>
                        </div>
                        <div>Pre-screen score: {interview.score}/100</div>
                      </div>
                    </div>
                    <Button>Join Interview</Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link to="/recruiter/resume-analyzer" className="block">
                <Button className="w-full justify-start gap-3 h-auto py-4">
                  <FileText className="w-5 h-5" />
                  <div className="text-left">
                    <div>Analyze Resumes</div>
                    <div className="text-xs opacity-80">Bulk upload and rank</div>
                  </div>
                </Button>
              </Link>
              <Button variant="outline" className="w-full justify-start gap-3 h-auto py-4">
                <Calendar className="w-5 h-5" />
                <div className="text-left">
                  <div>Schedule Interview</div>
                  <div className="text-xs text-gray-500">Create new session</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start gap-3 h-auto py-4">
                <Users className="w-5 h-5" />
                <div className="text-left">
                  <div>View Candidates</div>
                  <div className="text-xs text-gray-500">Browse pipeline</div>
                </div>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.map((activity, idx) => (
                <div key={idx} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4>{activity.action}</h4>
                      <span className="text-sm text-gray-500">• {activity.position}</span>
                    </div>
                    <p className="text-sm text-gray-600">{activity.result}</p>
                  </div>
                  <span className="text-sm text-gray-500">{activity.time}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
