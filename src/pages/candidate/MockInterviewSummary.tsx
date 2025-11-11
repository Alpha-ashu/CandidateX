import { Link, useParams } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import {
  Trophy,
  TrendingUp,
  TrendingDown,
  Lightbulb,
  Download,
  RefreshCw,
  Home,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';

export default function MockInterviewSummary() {
  const { sessionId } = useParams();

  const overallScore = 78;
  const scores = {
    communication: 82,
    technicalKnowledge: 75,
    problemSolving: 80,
    bodyLanguage: 70
  };

  const radarData = [
    { subject: 'Communication', value: scores.communication, fullMark: 100 },
    { subject: 'Technical', value: scores.technicalKnowledge, fullMark: 100 },
    { subject: 'Problem Solving', value: scores.problemSolving, fullMark: 100 },
    { subject: 'Body Language', value: scores.bodyLanguage, fullMark: 100 },
    { subject: 'Clarity', value: 85, fullMark: 100 },
    { subject: 'Confidence', value: 73, fullMark: 100 },
  ];

  const strengths = [
    'Clear and articulate communication style',
    'Good problem-solving approach with structured thinking',
    'Strong technical foundation and understanding',
    'Effective use of examples to illustrate points',
  ];

  const improvements = [
    'Practice speaking more confidently about your achievements',
    'Include more specific metrics and quantifiable results',
    'Work on maintaining better eye contact with the camera',
    'Reduce filler words (um, uh, like) during responses',
  ];

  const recommendations = [
    {
      title: 'Practice with a timer',
      description: 'Set 2-minute timers for each question to improve pacing and conciseness',
    },
    {
      title: 'Record yourself',
      description: 'Watch your recordings to identify body language and verbal patterns to improve',
    },
    {
      title: 'Master the STAR method',
      description: 'Practice structuring behavioral answers using Situation, Task, Action, Result',
    },
    {
      title: 'Research common questions',
      description: 'Prepare answers for the top 20 most common interview questions in your field',
    },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 90) return { label: 'Excellent', color: 'bg-green-100 text-green-700' };
    if (score >= 80) return { label: 'Very Good', color: 'bg-blue-100 text-blue-700' };
    if (score >= 70) return { label: 'Good', color: 'bg-yellow-100 text-yellow-700' };
    if (score >= 60) return { label: 'Fair', color: 'bg-orange-100 text-orange-700' };
    return { label: 'Needs Work', color: 'bg-red-100 text-red-700' };
  };

  const badge = getScoreBadge(overallScore);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl mb-2">Interview Complete!</h1>
          <p className="text-gray-600">Here's how you performed</p>
        </div>

        {/* Overall Score */}
        <Card className="mb-8 bg-white">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="inline-flex items-baseline gap-2 mb-4">
                <span className="text-6xl">{overallScore}</span>
                <span className="text-3xl text-gray-400">/100</span>
              </div>
              <div className={`inline-block px-4 py-1 rounded-full text-sm mb-4 ${badge.color}`}>
                {badge.label}
              </div>
              <p className="text-gray-600 max-w-2xl mx-auto">
                You performed well overall! With focused practice on the areas below, 
                you can improve your score significantly.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Detailed Breakdown */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Score Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span>Communication</span>
                  <span className={getScoreColor(scores.communication)}>
                    {scores.communication}/100
                  </span>
                </div>
                <Progress value={scores.communication} className="h-2" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span>Technical Knowledge</span>
                  <span className={getScoreColor(scores.technicalKnowledge)}>
                    {scores.technicalKnowledge}/100
                  </span>
                </div>
                <Progress value={scores.technicalKnowledge} className="h-2" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span>Problem Solving</span>
                  <span className={getScoreColor(scores.problemSolving)}>
                    {scores.problemSolving}/100
                  </span>
                </div>
                <Progress value={scores.problemSolving} className="h-2" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span>Body Language</span>
                  <span className={getScoreColor(scores.bodyLanguage)}>
                    {scores.bodyLanguage}/100
                  </span>
                </div>
                <Progress value={scores.bodyLanguage} className="h-2" />
              </div>
            </CardContent>
          </Card>

          {/* Skills Radar */}
          <Card>
            <CardHeader>
              <CardTitle>Skills Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Strengths and Improvements */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Strengths */}
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-900">
                <TrendingUp className="w-5 h-5" />
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

          {/* Areas for Improvement */}
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-amber-900">
                <TrendingDown className="w-5 h-5" />
                Areas for Improvement
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {improvements.map((improvement, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <XCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <span className="text-amber-900">{improvement}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              Personalized Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {recommendations.map((rec, idx) => (
                <div key={idx} className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="mb-2 text-blue-900">{rec.title}</h4>
                  <p className="text-sm text-blue-800">{rec.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button variant="outline" size="lg" className="gap-2">
            <Download className="w-5 h-5" />
            Download PDF Report
          </Button>
          <Link to="/candidate/mock-interview/setup">
            <Button variant="outline" size="lg" className="gap-2 w-full sm:w-auto">
              <RefreshCw className="w-5 h-5" />
              Retake Interview
            </Button>
          </Link>
          <Link to="/candidate/dashboard">
            <Button size="lg" className="gap-2 w-full sm:w-auto">
              <Home className="w-5 h-5" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
