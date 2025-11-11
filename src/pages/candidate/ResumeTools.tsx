import { useState } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import { Badge } from '../../components/ui/badge';
import {
  Upload,
  FileText,
  Download,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Target
} from 'lucide-react';

export default function ResumeTools() {
  const [uploadedFile, setUploadedFile] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(true);
    }
  };

  const atsScore = 78;
  const strengths = [
    'Clear contact information with email and phone',
    'Well-structured experience section with job titles and dates',
    'Quantifiable achievements with specific metrics',
    'Appropriate use of industry keywords',
  ];

  const improvements = [
    'Add a professional summary at the top',
    'Include more technical skills keywords',
    'Use stronger action verbs (achieved, implemented, led)',
    'Add certifications section',
  ];

  const missingKeywords = [
    'Leadership',
    'Project Management',
    'Agile Methodology',
    'Cloud Computing',
    'CI/CD',
    'Docker',
    'Kubernetes',
    'AWS'
  ];

  return (
    <DashboardLayout role="candidate">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-3xl mb-2">Resume Tools</h2>
          <p className="text-gray-600">
            Optimize your resume for Applicant Tracking Systems (ATS)
          </p>
        </div>

        {/* Upload Section */}
        {!uploadedFile ? (
          <Card>
            <CardContent className="pt-6">
              <label
                htmlFor="resume-upload"
                className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex flex-col items-center">
                  <Upload className="w-16 h-16 text-gray-400 mb-4" />
                  <p className="text-xl mb-2">Upload Your Resume</p>
                  <p className="text-sm text-gray-500 mb-4">Drag and drop or click to browse</p>
                  <p className="text-xs text-gray-400">PDF, DOCX, TXT (max 10MB)</p>
                </div>
                <input
                  id="resume-upload"
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileUpload}
                />
              </label>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* ATS Score */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>ATS Score Analysis</CardTitle>
                  <Button variant="outline" size="sm" onClick={() => setUploadedFile(false)}>
                    Upload New Resume
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-8 mb-6">
                  <div className="flex-shrink-0">
                    <div className="relative w-32 h-32">
                      <svg className="w-full h-full" viewBox="0 0 100 100">
                        <circle
                          className="text-gray-200"
                          strokeWidth="10"
                          stroke="currentColor"
                          fill="transparent"
                          r="40"
                          cx="50"
                          cy="50"
                        />
                        <circle
                          className="text-blue-600"
                          strokeWidth="10"
                          strokeDasharray={`${2 * Math.PI * 40}`}
                          strokeDashoffset={`${2 * Math.PI * 40 * (1 - atsScore / 100)}`}
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="transparent"
                          r="40"
                          cx="50"
                          cy="50"
                          transform="rotate(-90 50 50)"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-3xl">{atsScore}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl mb-2">Good Score!</h3>
                    <p className="text-gray-600 mb-4">
                      Your resume has a solid ATS score. With a few improvements, you can
                      boost it to excellent and increase your chances of getting interviews.
                    </p>
                    <div className="flex gap-2">
                      <Badge className="bg-green-100 text-green-700">
                        ATS Friendly
                      </Badge>
                      <Badge className="bg-blue-100 text-blue-700">
                        Good Structure
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-4 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Format Score</p>
                    <div className="flex items-center gap-2">
                      <Progress value={90} className="h-2 flex-1" />
                      <span>90%</span>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Keywords</p>
                    <div className="flex items-center gap-2">
                      <Progress value={75} className="h-2 flex-1" />
                      <span>75%</span>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Experience</p>
                    <div className="flex items-center gap-2">
                      <Progress value={85} className="h-2 flex-1" />
                      <span>85%</span>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Education</p>
                    <div className="flex items-center gap-2">
                      <Progress value={80} className="h-2 flex-1" />
                      <span>80%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Strengths and Improvements */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Strengths */}
              <Card className="border-green-200 bg-green-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-900">
                    <CheckCircle className="w-5 h-5" />
                    Strengths
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {strengths.map((strength, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span className="text-green-900">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Improvements */}
              <Card className="border-amber-200 bg-amber-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-amber-900">
                    <TrendingUp className="w-5 h-5" />
                    Suggested Improvements
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {improvements.map((improvement, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <span className="text-amber-900">{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>

            {/* Keyword Optimization */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Keyword Optimization
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  These high-value keywords are missing from your resume. Consider adding
                  them where relevant to improve your ATS score.
                </p>
                <div className="flex flex-wrap gap-2">
                  {missingKeywords.map((keyword, idx) => (
                    <Badge key={idx} variant="outline" className="px-3 py-1">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex gap-4">
              <Button className="gap-2">
                <Download className="w-5 h-5" />
                Download Optimized Resume
              </Button>
              <Button variant="outline" className="gap-2">
                <FileText className="w-5 h-5" />
                View Detailed Report
              </Button>
            </div>
          </>
        )}

        {/* Tools Menu */}
        <div className="grid md:grid-cols-3 gap-4">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardContent className="pt-6">
              <FileText className="w-8 h-8 text-blue-600 mb-3" />
              <h3 className="mb-2">Resume Builder</h3>
              <p className="text-sm text-gray-600">
                Create a professional resume with our ATS-optimized templates
              </p>
            </CardContent>
          </Card>
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardContent className="pt-6">
              <Target className="w-8 h-8 text-green-600 mb-3" />
              <h3 className="mb-2">Cover Letter Generator</h3>
              <p className="text-sm text-gray-600">
                Generate tailored cover letters for specific job applications
              </p>
            </CardContent>
          </Card>
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardContent className="pt-6">
              <CheckCircle className="w-8 h-8 text-purple-600 mb-3" />
              <h3 className="mb-2">Resume Checklist</h3>
              <p className="text-sm text-gray-600">
                Ensure your resume has all the essential elements
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
