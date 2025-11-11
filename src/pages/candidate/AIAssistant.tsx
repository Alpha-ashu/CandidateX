import { useState, useEffect, useRef } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Badge } from '../../components/ui/badge';
import { Bot, Send, Lightbulb, BookOpen, Target, TrendingUp, Sparkles, Brain, Zap, Loader2, type LucideIcon } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface AIModel {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  available: boolean;
}

interface QuickAction {
  icon: LucideIcon;
  label: string;
  prompt: string;
}

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI Interview Assistant. I can help you with interview preparation, answer questions about common interview techniques, provide feedback on your responses, and more. How can I help you today?',
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('grok');
  const [models, setModels] = useState<AIModel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [quickActions, setQuickActions] = useState<QuickAction[]>([]);
  const [suggestedTopics, setSuggestedTopics] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load available models
    fetchModels();
    fetchQuickActions();
    fetchSuggestedTopics();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/v1/ai/models', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setModels(data.models);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchQuickActions = async () => {
    try {
      const response = await fetch('/api/v1/ai/quick-actions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setQuickActions(data.quick_actions.map((action: any) => ({
          icon: getIconForCategory(action.category),
          label: action.label,
          prompt: action.prompt
        })));
      } else {
        setQuickActions([]);
      }
    } catch (error) {
      console.error('Failed to fetch quick actions:', error);
      setQuickActions([]);
    }
  };

  const fetchSuggestedTopics = async () => {
    try {
      const response = await fetch('/api/v1/ai/suggested-topics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSuggestedTopics(data.topics);
      } else {
        setSuggestedTopics([]);
      }
    } catch (error) {
      console.error('Failed to fetch suggested topics:', error);
      setSuggestedTopics([]);
    }
  };

  const getIconForCategory = (category: string): LucideIcon => {
    const iconMap: { [key: string]: LucideIcon } = {
      'interview_technique': Lightbulb,
      'interview_prep': BookOpen,
      'practice': Target,
      'career_advice': TrendingUp,
      'default': Sparkles
    };
    return iconMap[category] || iconMap.default;
  };

  const getModelIcon = (modelId: string): LucideIcon => {
    const iconMap: { [key: string]: LucideIcon } = {
      'grok': Sparkles,
      'gemini': Brain,
      'gpt-4': Zap,
      'claude': Bot
    };
    return iconMap[modelId] || Bot;
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages((prev: Message[]) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          message: input,
          model: selectedModel,
          context: messages.slice(-5) // Send last 5 messages for context
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage: Message = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        };
        setMessages((prev: Message[]) => [...prev, aiMessage]);
      } else {
        const aiMessage: Message = {
          role: 'assistant',
          content: 'Sorry, I\'m having trouble connecting right now. Please try again in a moment.',
          timestamp: new Date().toISOString()
        };
        setMessages((prev: Message[]) => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('AI chat error:', error);
      const aiMessage: Message = {
        role: 'assistant',
        content: 'I\'m experiencing some technical difficulties. Please try again later.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (prompt: string) => {
    setInput(prompt);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <DashboardLayout role="candidate">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h2 className="text-3xl mb-2">AI Interview Assistant</h2>
          <p className="text-gray-600">
            Get personalized help with your interview preparation using advanced AI models
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Chat Area */}
          <div className="lg:col-span-2">
            <Card className="h-[calc(100vh-16rem)] flex flex-col">
              <CardHeader className="border-b">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    AI Assistant
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {models.map((model) => {
                          const Icon = getModelIcon(model.id);
                          return (
                            <SelectItem key={model.id} value={model.id} disabled={!model.available}>
                              <div className="flex items-center gap-2">
                                <Icon className="w-4 h-4" />
                                <span>{model.name}</span>
                                {!model.available && <Badge variant="secondary" className="text-xs">Soon</Badge>}
                              </div>
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
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
                            <span className="text-sm font-medium">AI Assistant</span>
                            <Badge variant="outline" className="text-xs">
                              {models.find(m => m.id === selectedModel)?.name || 'AI'}
                            </Badge>
                          </div>
                        )}
                        <p className="whitespace-pre-line">{message.content}</p>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg p-4 max-w-[80%]">
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="w-4 h-4" />
                          <span className="text-sm font-medium">AI Assistant</span>
                          <Badge variant="outline" className="text-xs">
                            {models.find(m => m.id === selectedModel)?.name || 'AI'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="text-sm text-gray-600">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div ref={messagesEndRef} />
              </CardContent>
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about interview preparation..."
                    className="flex-1"
                    disabled={isLoading}
                  />
                  <Button onClick={handleSend} disabled={isLoading || !input.trim()} className="gap-2">
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
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
                      disabled={isLoading}
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
                      disabled={isLoading}
                    >
                      {topic}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Model Info */}
            <Card className="border-purple-200 bg-purple-50">
              <CardContent className="pt-6">
                <h3 className="mb-3 text-purple-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Current AI Model
                </h3>
                {models.find(m => m.id === selectedModel) && (
                  <div className="text-sm text-purple-800">
                    <p className="font-medium mb-1">
                      {models.find(m => m.id === selectedModel)?.name}
                    </p>
                    <p className="mb-2">
                      {models.find(m => m.id === selectedModel)?.description}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {models.find(m => m.id === selectedModel)?.capabilities.map((cap, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {cap.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
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
