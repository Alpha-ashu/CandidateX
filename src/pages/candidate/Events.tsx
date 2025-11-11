import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Calendar, MapPin, Users, Clock, Search, Video, Building } from 'lucide-react';

export default function Events() {
  const upcomingEvents = [
    {
      title: 'Tech Career Workshop',
      date: 'Tomorrow, 2:00 PM',
      duration: '2 hours',
      type: 'Workshop',
      location: 'Online',
      attendees: 245,
      description: 'Learn advanced interview strategies from industry experts. Topics include system design, behavioral questions, and salary negotiation.',
      category: 'workshop',
      featured: true
    },
    {
      title: 'Mock Interview Masterclass',
      date: 'Nov 15, 2025',
      duration: '2 hours',
      type: 'Webinar',
      location: 'Online',
      attendees: 189,
      description: 'Participate in live mock interviews with experienced interviewers and get real-time feedback.',
      category: 'webinar'
    },
    {
      title: 'Startup Networking Mixer',
      date: 'Nov 20, 2025',
      duration: '3 hours',
      type: 'Networking',
      location: 'San Francisco, CA',
      attendees: 78,
      description: 'Connect with founders, investors, and job seekers. Great opportunity to expand your network.',
      category: 'networking'
    },
    {
      title: 'Resume Building Bootcamp',
      date: 'Nov 22, 2025',
      duration: '1.5 hours',
      type: 'Workshop',
      location: 'Online',
      attendees: 156,
      description: 'Create an ATS-optimized resume that gets noticed. Hands-on session with templates and examples.',
      category: 'workshop'
    },
    {
      title: 'Career Fair - Top Tech Companies',
      date: 'Nov 25, 2025',
      duration: '4 hours',
      type: 'Career Fair',
      location: 'Virtual',
      attendees: 523,
      description: 'Meet recruiters from Google, Microsoft, Amazon, and more. Submit your resume and schedule on-site interviews.',
      category: 'career-fair'
    }
  ];

  const getLocationIcon = (location: string) => {
    if (location === 'Online' || location === 'Virtual') {
      return <Video className="w-4 h-4" />;
    }
    return <MapPin className="w-4 h-4" />;
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      workshop: 'bg-blue-100 text-blue-700',
      webinar: 'bg-purple-100 text-purple-700',
      networking: 'bg-green-100 text-green-700',
      'career-fair': 'bg-amber-100 text-amber-700'
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-700';
  };

  return (
    <DashboardLayout role="candidate">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-3xl mb-2">Events & Workshops</h2>
          <p className="text-gray-600">
            Join career development events and connect with industry professionals
          </p>
        </div>

        {/* Search and Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input placeholder="Search events..." className="pl-10" />
              </div>
              <div className="flex gap-2">
                <select className="px-4 py-2 border border-gray-300 rounded-md">
                  <option>All Categories</option>
                  <option>Workshops</option>
                  <option>Webinars</option>
                  <option>Networking</option>
                  <option>Career Fairs</option>
                </select>
                <select className="px-4 py-2 border border-gray-300 rounded-md">
                  <option>All Locations</option>
                  <option>Online</option>
                  <option>San Francisco</option>
                  <option>New York</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Featured Event */}
        {upcomingEvents.filter(e => e.featured).map((event, idx) => (
          <Card key={idx} className="border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <Badge className="mb-2">Featured Event</Badge>
                  <CardTitle className="text-2xl mb-2">{event.title}</CardTitle>
                  <p className="text-gray-600">{event.description}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4 mb-4">
                <div className="flex items-center gap-2 text-gray-700">
                  <Calendar className="w-4 h-4" />
                  <span>{event.date}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-700">
                  {getLocationIcon(event.location)}
                  <span>{event.location}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-700">
                  <Clock className="w-4 h-4" />
                  <span>{event.duration}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-700">
                  <Users className="w-4 h-4" />
                  <span>{event.attendees} registered</span>
                </div>
              </div>
              <Button size="lg">Register Now</Button>
            </CardContent>
          </Card>
        ))}

        {/* Upcoming Events Grid */}
        <div>
          <h3 className="text-xl mb-4">Upcoming Events</h3>
          <div className="grid md:grid-cols-2 gap-6">
            {upcomingEvents.filter(e => !e.featured).map((event, idx) => (
              <Card key={idx} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <Badge className={getCategoryColor(event.category)}>
                      {event.type}
                    </Badge>
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Users className="w-4 h-4" />
                      <span>{event.attendees}</span>
                    </div>
                  </div>
                  <CardTitle className="text-lg">{event.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">{event.description}</p>
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      <Calendar className="w-4 h-4" />
                      <span>{event.date}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      {getLocationIcon(event.location)}
                      <span>{event.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      <Clock className="w-4 h-4" />
                      <span>{event.duration}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button className="flex-1">Register</Button>
                    <Button variant="outline">Learn More</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Calendar View Option */}
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg mb-2">Want to see events in calendar view?</h3>
              <p className="text-gray-600 mb-4">
                View all upcoming events in an interactive calendar format
              </p>
              <Button variant="outline">View Calendar</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
