import { useState } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Bot, Send, Lightbulb, BookOpen, Target, TrendingUp } from 'lucide-react';

export default function AIAssistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI Interview Assistant. I can help you with interview preparation, answer questions about common interview techniques, provide feedback on your responses, and more. How can I help you today?'
    }
  ]);
  const [input, setInput] = useState('');

  const quickActions = [
    { icon: Lightbulb, label: 'STAR Method Tips', prompt: 'How do I use the STAR method effectively?' },
    { icon: BookOpen, label: 'Common Questions', prompt: 'What are the most common interview questions?' },
    { icon: Target, label: 'Mock Interview', prompt: 'Can you give me a practice interview question?' },
    { icon: TrendingUp, label: 'Improvement Tips', prompt: 'How can I improve my interview performance?' },
  ];

  const suggestedTopics = [
    'STAR Method Practice',
    'Technical Interview Prep',
    'Behavioral Questions',
    'Salary Negotiation',
    'Body Language Tips',
    'Follow-up Questions'
  ];

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        role: 'assistant',
        content: 'That\'s a great question! The STAR method is a structured approach to answering behavioral interview questions. Here\'s how it works:\n\n• **Situation**: Describe the context or challenge\n• **Task**: Explain your responsibility\n• **Action**: Detail the steps you took\n• **Result**: Share the outcome and what you learned\n\nWould you like to practice with a specific example?'
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleQuickAction = (prompt: string) => {
    setInput(prompt);
  };

  return (
    <DashboardLayout role="candidate">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h2 className="text-3xl mb-2">AI Interview Assistant</h2>
          <p className="text-gray-600">
            Get personalized help with your interview preparation
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Chat Area */}
          <div className="lg:col-span-2">
            <Card className="h-[calc(100vh-16rem)] flex flex-col">
              <CardHeader className="border-b">
                <CardTitle className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  AI Assistant
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-6">
                <div className="space-y-4">
                  {messages.map((message, idx) => (
                    <div
                      key={idx}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-4 ${
                          message.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        {message.role === 'assistant' && (
                          <div className="flex items-center gap-2 mb-2">
                            <Bot className="w-4 h-4" />
                            <span className="text-sm">AI Assistant</span>
                          </div>
                        )}
                        <p className="whitespace-pre-line">{message.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type your question..."
                    className="flex-1"
                  />
                  <Button onClick={handleSend} className="gap-2">
                    <Send className="w-4 h-4" />
                    Send
                  </Button>
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {quickActions.map((action, idx) => {
                  const Icon = action.icon;
                  return (
                    <Button
                      key={idx}
                      variant="outline"
                      className="w-full justify-start gap-3 h-auto py-3"
                      onClick={() => handleQuickAction(action.prompt)}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span className="text-left">{action.label}</span>
                    </Button>
                  );
                })}
              </CardContent>
            </Card>

            {/* Suggested Topics */}
            <Card>
              <CardHeader>
                <CardTitle>Suggested Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {suggestedTopics.map((topic, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => setInput(`Tell me about ${topic}`)}
                    >
                      {topic}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Help Tips */}
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="pt-6">
                <h3 className="mb-3 text-blue-900">How to use the AI Assistant</h3>
                <ul className="space-y-2 text-sm text-blue-800">
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                    <span>Ask specific questions about interview techniques</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                    <span>Request practice questions for your role</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                    <span>Get feedback on your sample answers</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
                    <span>Learn about industry-specific interview styles</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
