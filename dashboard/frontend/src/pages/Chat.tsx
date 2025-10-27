import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, TrendingUp, Calendar, Code } from 'lucide-react';
import { mockData } from '../services/mockData';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const exampleQueries = [
  {
    icon: TrendingUp,
    text: 'What was my productivity trend this week?',
    color: 'text-ruddy-blue',
  },
  {
    icon: Calendar,
    text: 'Show me my most active coding hours',
    color: 'text-picton-blue',
  },
  {
    icon: Code,
    text: 'Which AI model do I use most often?',
    color: 'text-rose-pompadour',
  },
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hi! I'm your AI coding insights assistant. Ask me anything about your development patterns, AI usage, productivity metrics, or trends. I can help you understand your data better!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    // Productivity trends
    if (lowerQuery.includes('productivity') || lowerQuery.includes('trend')) {
      const sessions = mockData.sessions.slice(0, 7).length;
      return `Based on your recent activity, you've had ${sessions} AI-assisted coding sessions in the past week. Your acceptance rate is around ${mockData.dashboardMetrics.acceptanceRate}%, which is excellent! Your productivity has been trending upward with consistent daily engagement.`;
    }

    // Active hours
    if (lowerQuery.includes('active') || lowerQuery.includes('hours') || lowerQuery.includes('when')) {
      return `Your most productive coding hours are between 9 AM - 12 PM and 2 PM - 5 PM. You tend to have longer, more focused sessions in the morning with an average of 45 minutes per session. Evening sessions (6-9 PM) are shorter but more frequent for quick fixes and reviews.`;
    }

    // Model usage
    if (lowerQuery.includes('model') || lowerQuery.includes('which ai')) {
      const sonnetCount = mockData.sessions.filter((s) => s.model?.includes('sonnet')).length;
      const haikuCount = mockData.sessions.filter((s) => s.model?.includes('haiku')).length;
      return `You primarily use Claude Sonnet (${sonnetCount} sessions), which is great for complex coding tasks. You also use Claude Haiku (${haikuCount} sessions) for quicker, simpler requests. This shows good model selection strategy - using powerful models when needed and faster ones for routine tasks.`;
    }

    // Token usage and cost
    if (lowerQuery.includes('token') || lowerQuery.includes('cost') || lowerQuery.includes('spend')) {
      return `Your total token usage this month is approximately ${mockData.dashboardMetrics.tokenUsage.toLocaleString()} tokens, costing around $${mockData.dashboardMetrics.estimatedCost.toFixed(2)}. You're averaging about ${Math.round(mockData.sessions.reduce((acc, s) => acc + s.total_tokens, 0) / mockData.sessions.length)} tokens per session. Your cost efficiency is good, with a ${mockData.dashboardMetrics.costTrend > 0 ? 'slight increase' : 'decrease'} from last month.`;
    }

    // Acceptance rate
    if (lowerQuery.includes('acceptance') || lowerQuery.includes('accept')) {
      return `Your code acceptance rate is ${mockData.dashboardMetrics.acceptanceRate}%, which is above average! This indicates that the AI-generated code aligns well with your needs. The trend shows ${mockData.dashboardMetrics.acceptanceRateTrend > 0 ? 'improvement' : 'consistency'} over time. Keep refining your prompts to maintain this high quality.`;
    }

    // Lines of code
    if (lowerQuery.includes('lines') || lowerQuery.includes('code generated')) {
      return `You've generated ${mockData.dashboardMetrics.linesOfCode.toLocaleString()} lines of code with AI assistance this month. That's a ${Math.abs(mockData.dashboardMetrics.linesOfCodeTrend)}% ${mockData.dashboardMetrics.linesOfCodeTrend > 0 ? 'increase' : 'decrease'} from last month. Your average session produces around ${Math.round(mockData.sessions.reduce((acc, s) => acc + (s.accepted_lines || 0), 0) / mockData.sessions.length)} lines of accepted code.`;
    }

    // Language usage
    if (lowerQuery.includes('language') || lowerQuery.includes('typescript') || lowerQuery.includes('python')) {
      return `Based on your session patterns, you're working primarily with TypeScript (35%) and Python (28%). JavaScript accounts for about 20%, with Go and Rust making up the remainder. Your TypeScript sessions tend to have higher acceptance rates, suggesting strong familiarity with the language.`;
    }

    // Improvement suggestions
    if (lowerQuery.includes('improve') || lowerQuery.includes('better') || lowerQuery.includes('tip')) {
      return `Here are some personalized tips: 1) Your morning sessions have 15% higher acceptance rates - consider tackling complex tasks then. 2) You could explore using more specific prompts for documentation tasks to boost that quality score. 3) Your cost efficiency is good, but using Haiku for routine refactoring could save 20-30% on costs.`;
    }

    // Default response
    return `That's an interesting question! While I don't have specific data on that yet, I can tell you that your overall AI coding metrics look great. You have ${mockData.sessions.length} sessions tracked with a ${mockData.dashboardMetrics.acceptanceRate}% acceptance rate. Feel free to ask about productivity trends, model usage, costs, or coding patterns!`;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI thinking time
    setTimeout(() => {
      const response = generateResponse(input);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const handleExampleClick = (text: string) => {
    setInput(text);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-8 w-8 text-ruddy-blue" />
          <h1 className="text-3xl font-bold">AI Chat Assistant</h1>
        </div>
        <p className="text-muted-foreground mt-2">
          Ask questions about your coding patterns, AI usage, and productivity metrics
        </p>
      </div>

      {/* Example Queries */}
      {messages.length <= 1 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">Try asking:</h3>
          <div className="grid gap-3 md:grid-cols-3">
            {exampleQueries.map((example, index) => {
              const Icon = example.icon;
              return (
                <button
                  key={index}
                  onClick={() => handleExampleClick(example.text)}
                  className="flex items-start gap-3 p-4 rounded-lg border border-border bg-card hover:bg-accent transition-colors text-left"
                >
                  <Icon className={`h-5 w-5 mt-0.5 ${example.color}`} />
                  <span className="text-sm">{example.text}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-6 mb-4">
        <div className="space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-ruddy-blue text-white'
                    : 'bg-muted text-foreground'
                }`}
              >
                <div className="flex items-start gap-2">
                  {message.role === 'assistant' && (
                    <Sparkles className="h-4 w-4 text-ruddy-blue mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    <p
                      className={`text-xs mt-2 ${
                        message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg p-4 bg-muted text-foreground">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-ruddy-blue" />
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" />
                    <div
                      className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                    <div
                      className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                      style={{ animationDelay: '0.4s' }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your coding metrics, AI usage, or productivity..."
            className="w-full p-4 pr-12 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            rows={2}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={!input.trim() || isTyping}
          className="px-6 py-2 rounded-lg bg-ruddy-blue text-white hover:bg-ruddy-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          <Send className="h-4 w-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>
    </div>
  );
}
