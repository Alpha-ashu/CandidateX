import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Textarea } from '../../components/ui/textarea';
import { Progress } from '../../components/ui/progress';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';
import {
  Camera,
  Mic,
  MicOff,
  AlertTriangle,
  Clock,
  ChevronLeft,
  ChevronRight,
  Lightbulb,
  Shield
} from 'lucide-react';

const mockQuestions = [
  {
    id: 1,
    question: "Tell me about yourself and your background in software development.",
    type: "Behavioral"
  },
  {
    id: 2,
    question: "Describe a challenging project you worked on and how you overcame the difficulties.",
    type: "Behavioral"
  },
  {
    id: 3,
    question: "How do you handle conflicts with team members when working on a project?",
    type: "Behavioral"
  },
  {
    id: 4,
    question: "Explain the difference between REST and GraphQL APIs. When would you use each?",
    type: "Technical"
  },
  {
    id: 5,
    question: "What is your approach to debugging a production issue?",
    type: "Technical"
  },
];

export default function MockInterviewSession() {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<string[]>(Array(mockQuestions.length).fill(''));
  const [timeRemaining, setTimeRemaining] = useState(180); // 3 minutes
  const [isRecording, setIsRecording] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [aiFeedback, setAiFeedback] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentQuestion]);

  useEffect(() => {
    // Simulate AI feedback after typing
    const timeout = setTimeout(() => {
      if (answers[currentQuestion].length > 50) {
        setAiFeedback('Good structure! Consider adding specific metrics or results to strengthen your answer.');
      } else if (answers[currentQuestion].length > 20) {
        setAiFeedback('Keep going! Try to provide more detail and specific examples.');
      }
    }, 2000);

    return () => clearTimeout(timeout);
  }, [answers, currentQuestion]);

  // Simulate random anti-cheat warnings
  useEffect(() => {
    const warningTimeout = setTimeout(() => {
      if (Math.random() > 0.7) {
        setShowWarning(true);
        setTimeout(() => setShowWarning(false), 5000);
      }
    }, 15000);

    return () => clearTimeout(warningTimeout);
  }, [currentQuestion]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleNext = () => {
    if (currentQuestion < mockQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setTimeRemaining(180);
      setAiFeedback('');
    } else {
      navigate(`/candidate/mock-interview/summary/${sessionId}`);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
      setTimeRemaining(180);
      setAiFeedback('');
    }
  };

  const handleAnswerChange = (value: string) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = value;
    setAnswers(newAnswers);
  };

  const progress = ((currentQuestion + 1) / mockQuestions.length) * 100;
  const question = mockQuestions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge variant="destructive" className="gap-1">
                <Shield className="w-3 h-3" />
                Anti-Cheat Active
              </Badge>
              <span className="text-gray-600">
                Question {currentQuestion + 1} of {mockQuestions.length}
              </span>
              <Badge variant="outline">{question.type}</Badge>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-gray-600" />
                <span className={`text-lg ${timeRemaining < 60 ? 'text-red-600 ' : ''}`}>
                  {formatTime(timeRemaining)}
                </span>
              </div>
            </div>
          </div>
          <Progress value={progress} className="mt-4" />
        </div>
      </div>

      {/* Anti-Cheat Warning */}
      {showWarning && (
        <div className="container mx-auto px-4 pt-4">
          <Alert variant="destructive">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>
              <strong>Warning:</strong> Multiple faces detected. Please ensure only you are visible in the camera.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Question and Response */}
          <div className="lg:col-span-2 space-y-6">
            {/* Question */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl mb-4">Question:</h2>
              <p className="text-lg text-gray-700 leading-relaxed">
                {question.question}
              </p>
            </div>

            {/* Response Area */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg">Your Response:</h3>
                <div className="flex items-center gap-2">
                  <Button
                    variant={isRecording ? "destructive" : "outline"}
                    size="sm"
                    onClick={() => setIsRecording(!isRecording)}
                    className="gap-2"
                  >
                    {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    {isRecording ? 'Stop Recording' : 'Voice Response'}
                  </Button>
                </div>
              </div>
              <Textarea
                value={answers[currentQuestion]}
                onChange={(e) => handleAnswerChange(e.target.value)}
                placeholder="Type your answer here or use voice recording..."
                rows={12}
                className="resize-none"
              />
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm text-gray-500">
                  {answers[currentQuestion].length} characters
                </span>
                {isRecording && (
                  <Badge variant="destructive" className="animate-pulse">
                    Recording...
                  </Badge>
                )}
              </div>
            </div>

            {/* Navigation */}
            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentQuestion === 0}
                className="gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </Button>
              <Button
                onClick={handleNext}
                className="flex-1 gap-2"
              >
                {currentQuestion === mockQuestions.length - 1 ? 'Finish Interview' : 'Next Question'}
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Video Feed */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="mb-3">Camera Feed</h3>
              <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center">
                <Camera className="w-12 h-12 text-white opacity-50" />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Your camera is being monitored for anti-cheat purposes
              </p>
            </div>

            {/* AI Feedback */}
            {aiFeedback && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-2 mb-2">
                  <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <h3 className="text-blue-900">AI Feedback:</h3>
                </div>
                <p className="text-sm text-blue-800">{aiFeedback}</p>
              </div>
            )}

            {/* Tips */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="mb-3">Interview Tips</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                  <span>Use the STAR method for behavioral questions</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                  <span>Be specific with examples and metrics</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                  <span>Take a moment to think before answering</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                  <span>Maintain eye contact with the camera</span>
                </li>
              </ul>
            </div>

            {/* Question Navigation */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="mb-3">Questions</h3>
              <div className="grid grid-cols-5 gap-2">
                {mockQuestions.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentQuestion(idx)}
                    className={`aspect-square rounded flex items-center justify-center text-sm transition-colors ${
                      idx === currentQuestion
                        ? 'bg-blue-600 text-white'
                        : answers[idx]
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
