import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { CheckCircle, XCircle, AlertCircle, Camera, Mic, Monitor, Wifi } from 'lucide-react';

export default function MockInterviewPreCheck() {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [checks, setChecks] = useState({
    camera: 'checking',
    microphone: 'checking',
    internet: 'checking',
    browser: 'checking',
  });

  useEffect(() => {
    // Simulate system checks
    const checkSystems = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setChecks(prev => ({ ...prev, camera: 'success' }));
      
      await new Promise(resolve => setTimeout(resolve, 500));
      setChecks(prev => ({ ...prev, microphone: 'success' }));
      
      await new Promise(resolve => setTimeout(resolve, 500));
      setChecks(prev => ({ ...prev, internet: 'success' }));
      
      await new Promise(resolve => setTimeout(resolve, 500));
      setChecks(prev => ({ ...prev, browser: 'success' }));
    };

    checkSystems();
  }, []);

  const allChecksPass = Object.values(checks).every(status => status === 'success');

  const CheckItem = ({ icon: Icon, title, description, status }: any) => {
    const getStatusIcon = () => {
      if (status === 'checking') return <AlertCircle className="w-5 h-5 text-yellow-600 animate-pulse" />;
      if (status === 'success') return <CheckCircle className="w-5 h-5 text-green-600" />;
      return <XCircle className="w-5 h-5 text-red-600" />;
    };

    const getStatusColor = () => {
      if (status === 'checking') return 'border-yellow-200 bg-yellow-50';
      if (status === 'success') return 'border-green-200 bg-green-50';
      return 'border-red-200 bg-red-50';
    };

    return (
      <div className={`border-2 rounded-lg p-4 ${getStatusColor()}`}>
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center flex-shrink-0">
            <Icon className="w-6 h-6 text-gray-700" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3>{title}</h3>
              {getStatusIcon()}
            </div>
            <p className="text-sm text-gray-600">{description}</p>
            {status === 'checking' && (
              <p className="text-sm text-yellow-600 mt-2">Testing...</p>
            )}
            {status === 'success' && (
              <p className="text-sm text-green-600 mt-2">Ready</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-3xl">
        <CardContent className="pt-6">
          <div className="text-center mb-8">
            <h1 className="text-3xl mb-2">System Check</h1>
            <p className="text-gray-600">
              We're testing your system to ensure the best interview experience
            </p>
          </div>

          {/* Video Preview */}
          <div className="mb-8">
            <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center overflow-hidden">
              <div className="text-center text-white">
                <Camera className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Camera Preview</p>
                <p className="text-sm text-gray-400 mt-2">Your camera feed will appear here</p>
              </div>
            </div>
          </div>

          {/* System Checks */}
          <div className="space-y-4 mb-8">
            <CheckItem
              icon={Camera}
              title="Camera Access"
              description="Required for facial recognition and anti-cheat monitoring"
              status={checks.camera}
            />
            <CheckItem
              icon={Mic}
              title="Microphone Access"
              description="Required for voice responses (optional)"
              status={checks.microphone}
            />
            <CheckItem
              icon={Wifi}
              title="Internet Connection"
              description="Stable connection required for real-time feedback"
              status={checks.internet}
            />
            <CheckItem
              icon={Monitor}
              title="Browser Compatibility"
              description="Your browser supports all required features"
              status={checks.browser}
            />
          </div>

          {/* Anti-Cheat Warning */}
          <Alert className="mb-6">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              <strong>Anti-cheat system will be active.</strong> Tab switching, multiple faces,
              or looking away frequently will trigger warnings. This simulates real interview conditions.
            </AlertDescription>
          </Alert>

          {/* Tips */}
          <Card className="border-blue-200 bg-blue-50 mb-6">
            <CardContent className="pt-6">
              <h3 className="mb-3">Interview Tips</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>Find a quiet, well-lit room</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>Position your camera at eye level</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>Close unnecessary browser tabs and applications</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>Use the STAR method (Situation, Task, Action, Result) for behavioral questions</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button
              variant="outline"
              onClick={() => navigate('/candidate/dashboard')}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={() => navigate(`/candidate/mock-interview/session/${sessionId}`)}
              disabled={!allChecksPass}
              className="flex-1"
            >
              {allChecksPass ? 'Begin Interview' : 'Running Checks...'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
