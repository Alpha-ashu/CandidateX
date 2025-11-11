import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Progress } from '../../components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar';
import {
  ChevronLeft,
  Mail,
  Calendar,
  MapPin,
  Clock,
  ChevronDown,
  CheckCircle,
  Trophy,
  Target,
  History
} from 'lucide-react';

export default function CandidateProfile() {
  const { id } = useParams();
  const [showAllApplications, setShowAllApplications] = useState(false);
  const [showAllExperience, setShowAllExperience] = useState(false);

  const candidate = {
    name: 'Jake Richards',
    role: 'Developer',
    verified: true,
    avatar: null,
    skills: ['Angular', 'Javascript', 'Tailwind', 'React', 'Node.js'],
    positionType: ['Remote', 'Full-time'],
    location: 'Manchester, UK',
    timezone: 'UTC+1 (BST)',
    metrics: {
      abilityTest: 91,
      availability: 90,
      leadership: 87,
      communication: 61,
      responsibility: 96,
      loyalty: 45
    },
    aspectScore: 86,
    overallScore: 'High Potential'
  };

  const insights = [
    {
      icon: Trophy,
      title: 'Top of class',
      description: 'This candidate is in the top 10',
      color: 'text-yellow-600'
    },
    {
      icon: Target,
      title: 'Leadership',
      description: 'Leadership score is below your benchmark',
      color: 'text-gray-600'
    },
    {
      icon: History,
      title: 'Interview history',
      description: 'You interviewed 10 candidates like this before',
      color: 'text-gray-600'
    }
  ];

  const jobApplications = [
    {
      position: 'Senior Product Designer',
      company: 'GE Austin',
      logo: null,
      logoColor: 'bg-blue-600'
    },
    {
      position: 'Senior Frontend Angular Developer',
      company: 'Diffco LLC',
      logo: null,
      logoColor: 'bg-red-600'
    },
    {
      position: 'Uber',
      company: 'Front end developer',
      year: '2019-2020',
      logo: null,
      logoColor: 'bg-gray-900'
    },
    {
      position: 'Additional Position 1',
      company: 'Company Name',
      logo: null,
      logoColor: 'bg-green-600'
    },
    {
      position: 'Additional Position 2',
      company: 'Company Name',
      logo: null,
      logoColor: 'bg-purple-600'
    }
  ];

  const experience = [
    {
      company: 'Sincron Software',
      position: 'Lead - Front end developer',
      period: '2020-2023',
      logo: null,
      logoColor: 'bg-gray-600'
    },
    {
      company: 'Zass Software',
      position: 'Front end developer',
      period: '2019-2020',
      logo: null,
      logoColor: 'bg-green-500'
    },
    {
      company: 'DoorDash',
      position: 'Senior Front end developer',
      period: '2017-2018',
      logo: null,
      logoColor: 'bg-red-500'
    },
    {
      company: 'Previous Company 1',
      position: 'Developer',
      period: '2016-2017',
      logo: null,
      logoColor: 'bg-blue-500'
    },
    {
      company: 'Previous Company 2',
      position: 'Junior Developer',
      period: '2015-2016',
      logo: null,
      logoColor: 'bg-purple-500'
    }
  ];

  const activeInterviews = [
    {
      position: 'React Developer',
      company: 'Saasify',
      stages: {
        all: 72,
        new: 45,
        screening: 0,
        phone: 0,
        technical: 0,
        final: 0,
        hired: 0
      },
      progress: 62
    },
    {
      position: 'Senior Frontend Angular Developer',
      company: 'Diffco LLC',
      stages: {
        all: 75,
        new: 22,
        screening: 15,
        phone: 11,
        technical: 5,
        final: 0,
        hired: 0
      },
      progress: 71
    },
    {
      position: 'Senior Product Designer',
      company: 'Saasify',
      stages: {
        all: 153,
        new: 124,
        screening: 68,
        phone: 0,
        technical: 0,
        final: 0,
        hired: 0
      },
      progress: 44
    },
    {
      position: 'Senior Frontend Developer',
      company: 'Zass Software',
      stages: {
        all: 45,
        new: 12,
        screening: 8,
        phone: 5,
        technical: 3,
        final: 1,
        hired: 0
      },
      progress: 82
    }
  ];

  const displayedApplications = showAllApplications ? jobApplications : jobApplications.slice(0, 3);
  const displayedExperience = showAllExperience ? experience : experience.slice(0, 3);

  return (
    <DashboardLayout role="recruiter">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Link to="/recruiter/dashboard" className="hover:text-gray-900">
            Candidates
          </Link>
          <ChevronLeft className="w-4 h-4 rotate-180" />
          <span className="text-gray-900">{candidate.name}</span>
        </div>

        {/* Top Metrics */}
        <div className="grid grid-cols-6 gap-4">
          {[
            { label: 'Ability Test', value: candidate.metrics.abilityTest },
            { label: 'Availability', value: candidate.metrics.availability },
            { label: 'Leadership', value: candidate.metrics.leadership },
            { label: 'Communication', value: candidate.metrics.communication },
            { label: 'Responsibility', value: candidate.metrics.responsibility },
            { label: 'Loyalty', value: candidate.metrics.loyalty }
          ].map((metric, idx) => (
            <Card key={idx}>
              <CardContent className="pt-6 text-center">
                <div className="text-3xl mb-1">{metric.value}%</div>
                <div className="text-sm text-gray-600">{metric.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-12 gap-6">
          {/* Left Sidebar */}
          <div className="lg:col-span-3 space-y-6">
            {/* Profile Card */}
            <Card className="overflow-hidden">
              <div className="h-24 bg-gradient-to-r from-purple-400 via-blue-400 to-purple-300"></div>
              <CardContent className="pt-0">
                <div className="relative -mt-12 mb-4">
                  <Avatar className="w-24 h-24 border-4 border-white">
                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-2xl">
                      JR
                    </AvatarFallback>
                  </Avatar>
                  {candidate.verified && (
                    <div className="absolute bottom-0 right-0 bg-blue-500 text-white rounded-full p-1">
                      <CheckCircle className="w-5 h-5" />
                    </div>
                  )}
                </div>

                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <h2 className="text-xl">{candidate.name}</h2>
                    <Badge variant="secondary">{candidate.role}</Badge>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm mb-2">Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {candidate.skills.map((skill, idx) => (
                        <Badge key={idx} variant="outline">{skill}</Badge>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm mb-2">Position type</h3>
                    <div className="flex gap-2">
                      {candidate.positionType.map((type, idx) => (
                        <Badge key={idx} variant="outline">{type}</Badge>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Location</div>
                      <div className="text-sm">{candidate.location}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Timezone</div>
                      <div className="text-sm">{candidate.timezone}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Job Applications */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Job Applications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {displayedApplications.map((app, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${app.logoColor} rounded-lg flex items-center justify-center text-white flex-shrink-0`}>
                      {app.company.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">{app.position}</div>
                      <div className="text-xs text-gray-500 truncate">{app.company}</div>
                      {app.year && <div className="text-xs text-gray-400">{app.year}</div>}
                    </div>
                  </div>
                ))}
                {jobApplications.length > 3 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAllApplications(!showAllApplications)}
                    className="w-full text-blue-600"
                  >
                    See {showAllApplications ? 'less' : `${jobApplications.length - 3} more`}
                    <ChevronDown className={`w-4 h-4 ml-1 transition-transform ${showAllApplications ? 'rotate-180' : ''}`} />
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Experience */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Experience</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {displayedExperience.map((exp, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <div className={`w-10 h-10 ${exp.logoColor} rounded-lg flex items-center justify-center text-white flex-shrink-0`}>
                      {exp.company.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm">{exp.company}</div>
                      <div className="text-xs text-gray-500">{exp.position}</div>
                      <div className="text-xs text-gray-400">{exp.period}</div>
                    </div>
                  </div>
                ))}
                {experience.length > 3 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAllExperience(!showAllExperience)}
                    className="w-full text-blue-600"
                  >
                    See {showAllExperience ? 'less' : `${experience.length - 3} more`}
                    <ChevronDown className={`w-4 h-4 ml-1 transition-transform ${showAllExperience ? 'rotate-180' : ''}`} />
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button className="flex-1 bg-gray-900 hover:bg-gray-800">
                <Mail className="w-4 h-4 mr-2" />
                Contact Jake
              </Button>
              <Button className="flex-1">
                <Calendar className="w-4 h-4 mr-2" />
                Invite to Interview
              </Button>
            </div>
          </div>

          {/* Middle Content */}
          <div className="lg:col-span-6 space-y-6">
            {/* Aspect Score */}
            <Card>
              <CardHeader>
                <CardTitle>Aspect Score</CardTitle>
              </CardHeader>
              <CardContent className="flex justify-center">
                <div className="relative w-48 h-48">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      className="text-gray-200"
                      strokeWidth="16"
                      stroke="currentColor"
                      fill="transparent"
                      r="70"
                      cx="96"
                      cy="96"
                    />
                    <circle
                      className="text-blue-600"
                      strokeWidth="16"
                      strokeDasharray={`${2 * Math.PI * 70}`}
                      strokeDashoffset={`${2 * Math.PI * 70 * (1 - candidate.aspectScore / 100)}`}
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="transparent"
                      r="70"
                      cx="96"
                      cy="96"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-5xl">{candidate.aspectScore}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Active Interviews */}
            <Card>
              <CardHeader>
                <CardTitle>Jake's active Interviews</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {activeInterviews.map((interview, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div>{interview.position}</div>
                        <div className="text-sm text-gray-500">{interview.company}</div>
                      </div>
                      <Button variant="link" className="text-blue-600">View</Button>
                    </div>

                    <div className="grid grid-cols-7 gap-2 mb-2">
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.all}</div>
                        <div className="text-xs text-gray-500">All</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.new}</div>
                        <div className="text-xs text-gray-500">New</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.screening}</div>
                        <div className="text-xs text-gray-500">Screening</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.phone}</div>
                        <div className="text-xs text-gray-500">Phone Interview</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.technical}</div>
                        <div className="text-xs text-gray-500">Technical Interview</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.final}</div>
                        <div className="text-xs text-gray-500">Final Decision</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl mb-1">{interview.stages.hired}</div>
                        <div className="text-xs text-gray-500">Hired</div>
                      </div>
                    </div>

                    <Progress value={interview.progress} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-3 space-y-6">
            {/* Overall Score */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Overall Score</CardTitle>
                  <Badge className="bg-green-100 text-green-700">{candidate.overallScore}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {insights.map((insight, idx) => {
                  const Icon = insight.icon;
                  return (
                    <div key={idx} className="flex gap-3">
                      <div className={`w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0`}>
                        <Icon className={`w-5 h-5 ${insight.color}`} />
                      </div>
                      <div>
                        <div className="text-sm mb-1">{insight.title}</div>
                        <div className="text-xs text-gray-500">{insight.description}</div>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Hiring History */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Hiring History</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="text-sm mb-2">Jake Richards</div>
                  <Progress value={92} className="h-2 bg-gray-200" style={{ 
                    ['--tw-bg-opacity' as any]: 1 
                  }}>
                    <div className="h-full bg-blue-600 rounded-full" style={{ width: '92%' }}></div>
                  </Progress>
                </div>
                <div>
                  <div className="text-sm mb-2">Other candidates</div>
                  <Progress value={65} className="h-2 bg-gray-200">
                    <div className="h-full bg-pink-500 rounded-full" style={{ width: '65%' }}></div>
                  </Progress>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
