import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '../../components/ui/radio-group';
import { Slider } from '../../components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Upload, FileText, Lightbulb } from 'lucide-react';

export default function MockInterviewSetup() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    jobTitle: '',
    company: '',
    jobDescription: '',
    interviewType: 'mixed',
    experienceLevel: 'mid',
    questionCount: 10,
    timePerQuestion: 3,
  });

  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const sessionId = Math.random().toString(36).substring(7);
    navigate(`/candidate/mock-interview/precheck/${sessionId}`);
  };

  return (
    <DashboardLayout role="candidate">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h2 className="text-3xl mb-2">Set Up Your Mock Interview</h2>
          <p className="text-gray-600">
            Customize your interview experience to match your target role
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Left Column - Job Details */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Job Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="jobTitle">Job Title *</Label>
                    <Input
                      id="jobTitle"
                      placeholder="e.g., Senior Software Engineer"
                      value={formData.jobTitle}
                      onChange={(e) => setFormData({ ...formData, jobTitle: e.target.value })}
                      required
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      placeholder="e.g., Google, Microsoft"
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="jobDescription">Job Description</Label>
                    <Textarea
                      id="jobDescription"
                      placeholder="Paste the job description here to get more relevant questions..."
                      value={formData.jobDescription}
                      onChange={(e) => setFormData({ ...formData, jobDescription: e.target.value })}
                      rows={6}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="resume">Resume (Optional)</Label>
                    <div className="mt-1">
                      <label
                        htmlFor="resume"
                        className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex flex-col items-center">
                          <Upload className="w-8 h-8 text-gray-400 mb-2" />
                          {file ? (
                            <div className="text-sm text-gray-600">{file.name}</div>
                          ) : (
                            <>
                              <p className="text-sm text-gray-600">Click to upload or drag and drop</p>
                              <p className="text-xs text-gray-500">PDF, DOCX (max 10MB)</p>
                            </>
                          )}
                        </div>
                        <input
                          id="resume"
                          type="file"
                          className="hidden"
                          accept=".pdf,.doc,.docx"
                          onChange={handleFileChange}
                        />
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Interview Preferences */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Interview Preferences</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label>Interview Type *</Label>
                    <RadioGroup
                      value={formData.interviewType}
                      onValueChange={(value) => setFormData({ ...formData, interviewType: value })}
                      className="mt-3 space-y-3"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="behavioral" id="behavioral" />
                        <Label htmlFor="behavioral" className="cursor-pointer flex-1">
                          <div>Behavioral</div>
                          <div className="text-sm text-gray-500">
                            Questions about past experiences and situations
                          </div>
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="technical" id="technical" />
                        <Label htmlFor="technical" className="cursor-pointer flex-1">
                          <div>Technical</div>
                          <div className="text-sm text-gray-500">
                            Domain-specific knowledge and problem-solving
                          </div>
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="mixed" id="mixed" />
                        <Label htmlFor="mixed" className="cursor-pointer flex-1">
                          <div>Mixed</div>
                          <div className="text-sm text-gray-500">
                            Combination of behavioral and technical
                          </div>
                        </Label>
                      </div>
                    </RadioGroup>
                  </div>

                  <div>
                    <Label>Experience Level *</Label>
                    <RadioGroup
                      value={formData.experienceLevel}
                      onValueChange={(value) => setFormData({ ...formData, experienceLevel: value })}
                      className="mt-3 space-y-2"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="entry" id="entry" />
                        <Label htmlFor="entry" className="cursor-pointer">Entry Level (0-2 years)</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="mid" id="mid" />
                        <Label htmlFor="mid" className="cursor-pointer">Mid Level (3-5 years)</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="senior" id="senior" />
                        <Label htmlFor="senior" className="cursor-pointer">Senior Level (6+ years)</Label>
                      </div>
                    </RadioGroup>
                  </div>

                  <div>
                    <Label>Question Count: {formData.questionCount}</Label>
                    <Slider
                      value={[formData.questionCount]}
                      onValueChange={(value) => setFormData({ ...formData, questionCount: value[0] })}
                      min={5}
                      max={20}
                      step={1}
                      className="mt-3"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>5 questions</span>
                      <span>20 questions</span>
                    </div>
                  </div>

                  <div>
                    <Label>Time per Question: {formData.timePerQuestion} min</Label>
                    <Slider
                      value={[formData.timePerQuestion]}
                      onValueChange={(value) => setFormData({ ...formData, timePerQuestion: value[0] })}
                      min={1}
                      max={5}
                      step={1}
                      className="mt-3"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>1 minute</span>
                      <span>5 minutes</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Pro Tip */}
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <div className="flex gap-3">
                    <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm">
                        <strong>Pro tip:</strong> Upload your resume for personalized questions
                        that match your experience and the job description.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Submit Button */}
          <div className="mt-8 flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate('/candidate/dashboard')}>
              Cancel
            </Button>
            <Button type="submit" size="lg" className="min-w-48">
              Start Interview
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
