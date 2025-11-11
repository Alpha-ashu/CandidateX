import { Link } from 'react-router-dom';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import {
  TrendingUp,
  Calendar,
  FileText,
  Bot,
  Award,
  Clock,
  Target,
  CheckCircle,
  Upload
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function CandidateDashboard() {
  const scoreData = [
    { date: 'Mon', score: 65 },
    { date: 'Tue', score: 68 },
    { date: 'Wed', score: 72 },
    { date: 'Thu', score: 75 },
    { date: 'Fri', score: 78 },
    { date: 'Sat', score: 80 },
    { date: 'Sun', score: 82 },
  ];

  const upcomingInterviews = [
    { title: 'Technical Mock Interview', date: 'Tomorrow, 2:00 PM', type: 'mock' },
    { title: 'Career Workshop: Resume Tips', date: 'Friday, 10:00 AM', type: 'event' },
  ];

  const recentActivity = [
    { title: 'Completed Technical Interview', score: 82, date: '2 days ago', icon: CheckCircle, color: 'text-green-600' },
    { title: 'Resume ATS Score', score: 85, date: '3 days ago', icon: FileText, color: 'text-blue-600' },
    { title: 'Joined Career Workshop', score: null, date: '5 days ago', icon: Calendar, color: 'text-purple-600' },
  ];

  return (
    <DashboardLayout role="candidate">
      <div className="space-y-6">
        {/* Welcome Section */}
        <div>
          <h2 className="text-3xl mb-2">Welcome back, Alex!</h2>
          <p className="text-gray-600">Here's your interview preparation progress</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Overall Score</p>
                  <p className="text-3xl mt-1">78/100</p>
                  <p className="text-sm text-green-600 flex items-center gap-1 mt-1">
                    <TrendingUp className="w-4 h-4" />
                    +5 this week
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Target className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Interviews Done</p>
                  <p className="text-3xl mt-1">12</p>
                  <p className="text-sm text-gray-500 mt-1">This month</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Practice Time</p>
                  <p className="text-3xl mt-1">18h</p>
                  <p className="text-sm text-gray-500 mt-1">This week</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Rank</p>
                  <p className="text-3xl mt-1">Top 15%</p>
                  <p className="text-sm text-gray-500 mt-1">Among peers</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Award className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Score Trend */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Your Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={scoreData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Weekly Goal Progress</span>
                  <span className="text-sm">8/10 interviews</span>
                </div>
                <Progress value={80} className="h-2" />
              </div>
            </CardContent>
          </Card>

          {/* Upcoming */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Upcoming
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {upcomingInterviews.map((item, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        item.type === 'mock' ? 'bg-blue-500' : 'bg-purple-500'
                      }`}></div>
                      <div className="flex-1">
                        <p className="text-sm mb-1">{item.title}</p>
                        <p className="text-xs text-gray-500">{item.date}</p>
                      </div>
                    </div>
                  </div>
                ))}
                <Link to="/candidate/events">
                  <Button variant="outline" className="w-full">
                    View All Events
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions & Recent Activity */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <Link to="/candidate/mock-interview/setup" className="block">
                  <Button className="w-full h-24 flex flex-col gap-2">
                    <FileText className="w-6 h-6" />
                    <span className="text-sm">Start Mock Interview</span>
                  </Button>
                </Link>
                <Link to="/candidate/resume-tools" className="block">
                  <Button variant="outline" className="w-full h-24 flex flex-col gap-2">
                    <Upload className="w-6 h-6" />
                    <span className="text-sm">Upload Resume</span>
                  </Button>
                </Link>
                <Link to="/candidate/events" className="block">
                  <Button variant="outline" className="w-full h-24 flex flex-col gap-2">
                    <Calendar className="w-6 h-6" />
                    <span className="text-sm">Join Event</span>
                  </Button>
                </Link>
                <Link to="/candidate/ai-assistant" className="block">
                  <Button variant="outline" className="w-full h-24 flex flex-col gap-2">
                    <Bot className="w-6 h-6" />
                    <span className="text-sm">AI Assistant</span>
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.map((activity, idx) => {
                  const Icon = activity.icon;
                  return (
                    <div key={idx} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        activity.color === 'text-green-600' ? 'bg-green-100' :
                        activity.color === 'text-blue-600' ? 'bg-blue-100' :
                        'bg-purple-100'
                      }`}>
                        <Icon className={`w-5 h-5 ${activity.color}`} />
                      </div>
                      <div className="flex-1">
                        <p>{activity.title}</p>
                        {activity.score && (
                          <p className="text-sm text-gray-600">Score: {activity.score}/100</p>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">{activity.date}</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI Insights */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Bot className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="mb-2">AI Insights</h3>
                <p className="text-gray-700 mb-4">
                  Based on your recent interviews, we recommend focusing on leadership questions and
                  system design scenarios. Your communication skills are strong, but practicing
                  STAR method responses will help you score even higher.
                </p>
                <Link to="/candidate/ai-assistant">
                  <Button variant="outline" size="sm">
                    Get Personalized Tips
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
