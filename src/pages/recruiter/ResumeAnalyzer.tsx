import { useState } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import {
  Upload,
  Download,
  Search,
  Filter,
  Mail,
  Calendar,
  Award,
  CheckCircle,
  Star,
  FileText
} from 'lucide-react';

export default function ResumeAnalyzer() {
  const [uploaded, setUploaded] = useState(false);

  const mockCandidates = [
    {
      name: 'Sarah Johnson',
      email: 'sarah.j@email.com',
      match: 95,
      experience: '8 years',
      skills: ['React', 'Node.js', 'Python', 'AWS', 'Docker'],
      score: 92,
      availability: 'Immediate'
    },
    {
      name: 'Mike Chen',
      email: 'mike.c@email.com',
      match: 87,
      experience: '6 years',
      skills: ['React', 'TypeScript', 'GraphQL', 'AWS'],
      score: 88,
      availability: '2 weeks notice'
    },
    {
      name: 'Lisa Wong',
      email: 'lisa.w@email.com',
      match: 82,
      experience: '5 years',
      skills: ['React', 'Node.js', 'MongoDB', 'Kubernetes'],
      score: 85,
      availability: '1 month notice'
    },
    {
      name: 'John Smith',
      email: 'john.s@email.com',
      match: 78,
      experience: '7 years',
      skills: ['JavaScript', 'Angular', 'Python', 'GCP'],
      score: 80,
      availability: 'Immediate'
    },
    {
      name: 'Emma Davis',
      email: 'emma.d@email.com',
      match: 75,
      experience: '4 years',
      skills: ['React', 'Vue.js', 'Node.js', 'PostgreSQL'],
      score: 78,
      availability: '2 weeks notice'
    },
  ];

  const getMatchColor = (match: number) => {
    if (match >= 90) return 'text-green-600';
    if (match >= 80) return 'text-blue-600';
    if (match >= 70) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getMatchBadge = (match: number) => {
    if (match >= 90) return 'bg-green-100 text-green-700';
    if (match >= 80) return 'bg-blue-100 text-blue-700';
    if (match >= 70) return 'bg-yellow-100 text-yellow-700';
    return 'bg-gray-100 text-gray-700';
  };

  return (
    <DashboardLayout role="recruiter">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-3xl mb-2">Resume Analyzer</h2>
          <p className="text-gray-600">
            Upload resumes and get AI-powered candidate rankings
          </p>
        </div>

        {/* Upload Section */}
        {!uploaded ? (
          <Card>
            <CardHeader>
              <CardTitle>Upload Resumes for Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Job Details */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm mb-1 block">Position Title</label>
                    <Input placeholder="e.g., Senior Software Engineer" />
                  </div>
                  <div>
                    <label className="text-sm mb-1 block">Department</label>
                    <Input placeholder="e.g., Engineering" />
                  </div>
                </div>

                {/* Upload Area */}
                <label
                  htmlFor="resume-upload"
                  className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                >
                  <div className="flex flex-col items-center">
                    <Upload className="w-12 h-12 text-gray-400 mb-3" />
                    <p className="text-lg mb-2">Drag & drop files here or click to browse</p>
                    <p className="text-sm text-gray-500 mb-2">Supports: PDF, DOCX, TXT (Max 10MB each)</p>
                    <p className="text-xs text-gray-400">Upload multiple resumes at once</p>
                  </div>
                  <input
                    id="resume-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx,.txt"
                    multiple
                    onChange={() => setUploaded(true)}
                  />
                </label>

                <Button onClick={() => setUploaded(true)} className="w-full" size="lg">
                  Analyze Resumes
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Search and Filter */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input placeholder="Search candidates..." className="pl-10" />
                  </div>
                  <Button variant="outline" className="gap-2">
                    <Filter className="w-4 h-4" />
                    Filters
                  </Button>
                  <Button variant="outline" className="gap-2">
                    <Download className="w-4 h-4" />
                    Export
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Analysis Summary */}
            <div className="grid md:grid-cols-4 gap-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Total Analyzed</p>
                    <p className="text-3xl">{mockCandidates.length}</p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Excellent Match</p>
                    <p className="text-3xl text-green-600">2</p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Good Match</p>
                    <p className="text-3xl text-blue-600">2</p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Avg Score</p>
                    <p className="text-3xl">85</p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Candidate Rankings */}
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Candidate List */}
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Candidate Rankings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {mockCandidates.map((candidate, idx) => (
                        <div
                          key={idx}
                          className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center justify-center w-8 h-8 bg-gray-200 rounded-full">
                                {idx + 1}
                              </div>
                              <div>
                                <h3 className="mb-1">{candidate.name}</h3>
                                <p className="text-sm text-gray-500">{candidate.email}</p>
                              </div>
                            </div>
                            <Badge className={getMatchBadge(candidate.match)}>
                              {candidate.match}% Match
                            </Badge>
                          </div>

                          <div className="grid grid-cols-3 gap-4 mb-3">
                            <div>
                              <p className="text-xs text-gray-500 mb-1">Experience</p>
                              <p className="text-sm">{candidate.experience}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500 mb-1">ATS Score</p>
                              <p className="text-sm">{candidate.score}/100</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500 mb-1">Availability</p>
                              <p className="text-sm">{candidate.availability}</p>
                            </div>
                          </div>

                          <div className="mb-3">
                            <p className="text-xs text-gray-500 mb-2">Key Skills</p>
                            <div className="flex flex-wrap gap-1">
                              {candidate.skills.map((skill, skillIdx) => (
                                <Badge key={skillIdx} variant="outline" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>

                          <div className="flex gap-2">
                            <Button size="sm" className="gap-1">
                              <CheckCircle className="w-4 h-4" />
                              Shortlist
                            </Button>
                            <Button size="sm" variant="outline" className="gap-1">
                              <Mail className="w-4 h-4" />
                              Contact
                            </Button>
                            <Button size="sm" variant="outline" className="gap-1">
                              <Calendar className="w-4 h-4" />
                              Schedule
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Top Match Details */}
              <div>
                <Card className="sticky top-6">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                      <CardTitle>Top Match</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center mb-6">
                      <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl mx-auto mb-3">
                        SJ
                      </div>
                      <h3 className="text-xl mb-1">Sarah Johnson</h3>
                      <p className="text-sm text-gray-500">sarah.j@email.com</p>
                    </div>

                    <div className="space-y-4 mb-6">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm">Match Score</span>
                          <span className="text-sm text-green-600">95%</span>
                        </div>
                        <Progress value={95} className="h-2" />
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm">ATS Score</span>
                          <span className="text-sm">92/100</span>
                        </div>
                        <Progress value={92} className="h-2" />
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm">Skills Match</span>
                          <span className="text-sm">88%</span>
                        </div>
                        <Progress value={88} className="h-2" />
                      </div>
                    </div>

                    <div className="space-y-3 mb-6">
                      <div className="flex items-center gap-2 text-sm">
                        <Award className="w-4 h-4 text-gray-400" />
                        <span>8 years experience</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <FileText className="w-4 h-4 text-gray-400" />
                        <span>Available immediately</span>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-xs text-gray-500 mb-2">Top Skills</p>
                      <div className="flex flex-wrap gap-1">
                        {mockCandidates[0].skills.map((skill, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Button className="w-full gap-2">
                        <Calendar className="w-4 h-4" />
                        Schedule Interview
                      </Button>
                      <Button variant="outline" className="w-full gap-2">
                        <FileText className="w-4 h-4" />
                        View Full Resume
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
