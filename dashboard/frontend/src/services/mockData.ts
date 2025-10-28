import type {
  Session,
  DashboardMetrics,
  RecentSession,
  ProfileDimension,
  SkillBadge,
  LanguageUsage,
  MetricTrend,
  Insight,
  UserProfile,
  TaskType,
} from '../types';

// Define ActivityHeatmap inline to avoid import issues
interface ActivityHeatmap {
  day: number;
  hour: number;
  value: number;
}

const MODELS = ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'];
const TASK_TYPES: TaskType[] = [
  'code_generation',
  'refactoring',
  'debugging',
  'documentation',
  'testing',
  'code_review',
];

// Helper to generate random date within last N days
function randomDate(daysAgo: number): Date {
  const now = new Date();
  const start = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
  return new Date(start.getTime() + Math.random() * (now.getTime() - start.getTime()));
}

// Generate 30 days of session data
export function generateMockSessions(count: number = 150): Session[] {
  const sessions: Session[] = [];

  for (let i = 0; i < count; i++) {
    const timestamp = randomDate(30);
    const model = MODELS[Math.floor(Math.random() * MODELS.length)];
    const tokensIn = Math.floor(Math.random() * 5000) + 500;
    const tokensOut = Math.floor(Math.random() * 3000) + 200;
    const totalTokens = tokensIn + tokensOut;
    const acceptedFlag = Math.random() > 0.3; // 70% acceptance rate

    // Cost estimation based on model (rough approximation)
    let costPer1M = 0;
    if (model.includes('opus')) {
      costPer1M = 15; // $15 per 1M tokens for input
    } else if (model.includes('sonnet')) {
      costPer1M = 3; // $3 per 1M tokens
    } else {
      costPer1M = 0.8; // Haiku
    }
    const costUsd = (totalTokens / 1_000_000) * costPer1M;

    sessions.push({
      id: i + 1,
      session_id: `session_${i + 1}`,
      developer_id: 'dev_001',
      timestamp: timestamp.toISOString(),
      model,
      tokens_in: tokensIn,
      tokens_out: tokensOut,
      latency_ms: Math.random() * 5000 + 500,
      status_code: Math.random() > 0.95 ? 500 : 200, // 5% error rate
      accepted_flag: acceptedFlag,
      repo_slug: 'company/project',
      event_date: timestamp.toISOString().split('T')[0],
      total_tokens: totalTokens,
      cost_usd: costUsd,
      diff_ratio: acceptedFlag ? Math.random() * 0.5 + 0.5 : Math.random() * 0.3,
      accepted_lines: acceptedFlag ? Math.floor(Math.random() * 100) + 10 : 0,
    });
  }

  return sessions.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export function calculateDashboardMetrics(sessions: Session[]): DashboardMetrics {
  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

  const thisWeek = sessions.filter(s => new Date(s.timestamp) >= weekAgo);
  const lastWeek = sessions.filter(
    s => new Date(s.timestamp) >= twoWeeksAgo && new Date(s.timestamp) < weekAgo
  );

  const totalSessions = thisWeek.length;
  const totalSessionsLast = lastWeek.length;
  const totalSessionsTrend = totalSessionsLast > 0
    ? ((totalSessions - totalSessionsLast) / totalSessionsLast) * 100
    : 0;

  const linesOfCode = thisWeek.reduce((sum, s) => sum + (s.accepted_lines || 0), 0);
  const linesOfCodeLast = lastWeek.reduce((sum, s) => sum + (s.accepted_lines || 0), 0);
  const linesOfCodeTrend = linesOfCodeLast > 0
    ? ((linesOfCode - linesOfCodeLast) / linesOfCodeLast) * 100
    : 0;

  const acceptedThisWeek = thisWeek.filter(s => s.accepted_flag).length;
  const acceptanceRate = totalSessions > 0 ? (acceptedThisWeek / totalSessions) * 100 : 0;

  const acceptedLastWeek = lastWeek.filter(s => s.accepted_flag).length;
  const acceptanceRateLast = totalSessionsLast > 0 ? (acceptedLastWeek / totalSessionsLast) * 100 : 0;
  const acceptanceRateTrend = acceptanceRateLast > 0
    ? ((acceptanceRate - acceptanceRateLast) / acceptanceRateLast) * 100
    : 0;

  const tokenUsage = thisWeek.reduce((sum, s) => sum + s.total_tokens, 0);
  const estimatedCost = thisWeek.reduce((sum, s) => sum + s.cost_usd, 0);

  const costLast = lastWeek.reduce((sum, s) => sum + s.cost_usd, 0);
  const costTrend = costLast > 0 ? ((estimatedCost - costLast) / costLast) * 100 : 0;

  return {
    totalSessions,
    totalSessionsTrend,
    linesOfCode,
    linesOfCodeTrend,
    acceptanceRate,
    acceptanceRateTrend,
    tokenUsage,
    estimatedCost,
    costTrend,
  };
}

export function generateActivityHeatmap(sessions: Session[]): ActivityHeatmap[] {
  const heatmap: ActivityHeatmap[] = [];

  for (let day = 0; day < 7; day++) {
    for (let hour = 0; hour < 24; hour++) {
      const count = sessions.filter(s => {
        const date = new Date(s.timestamp);
        return date.getDay() === day && date.getHours() === hour;
      }).length;

      heatmap.push({ day, hour, value: count });
    }
  }

  return heatmap;
}

export function generateRecentSessions(sessions: Session[]): RecentSession[] {
  return sessions.slice(0, 10).map(s => ({
    id: s.id,
    timestamp: s.timestamp,
    model: s.model || 'Unknown',
    duration: s.latency_ms,
    tokensUsed: s.total_tokens,
    acceptanceRate: s.accepted_flag ? 100 : 0,
    taskType: TASK_TYPES[Math.floor(Math.random() * TASK_TYPES.length)],
  }));
}

export function generateProfileDimensions(): ProfileDimension[] {
  return [
    { dimension: 'Prompt Engineering', score: 75 },
    { dimension: 'Model Selection', score: 82 },
    { dimension: 'Code Quality', score: 88 },
    { dimension: 'Productivity', score: 91 },
    { dimension: 'Learning Curve', score: 78 },
    { dimension: 'Cost Efficiency', score: 85 },
  ];
}

export function generateSkillBadges(): SkillBadge[] {
  return [
    {
      id: 'test-champion',
      name: 'Test Champion',
      description: 'Generated over 100 test cases with AI assistance',
      earned: true,
      earnedDate: '2024-10-15',
    },
    {
      id: 'doc-pro',
      name: 'Documentation Pro',
      description: 'Maintained 90%+ documentation coverage',
      earned: true,
      earnedDate: '2024-10-10',
    },
    {
      id: 'cost-optimizer',
      name: 'Cost Optimizer',
      description: 'Reduced token costs by 30% through efficient model selection',
      earned: false,
    },
    {
      id: 'speed-demon',
      name: 'Speed Demon',
      description: 'Completed 50+ sessions in a single week',
      earned: true,
      earnedDate: '2024-10-20',
    },
  ];
}

export function generateLanguageUsage(): LanguageUsage[] {
  return [
    { language: 'TypeScript', percentage: 35, sessionCount: 52 },
    { language: 'Python', percentage: 28, sessionCount: 42 },
    { language: 'JavaScript', percentage: 15, sessionCount: 22 },
    { language: 'Go', percentage: 12, sessionCount: 18 },
    { language: 'Rust', percentage: 7, sessionCount: 11 },
    { language: 'Java', percentage: 3, sessionCount: 5 },
  ];
}

export function generateMetricTrends(days: number = 30): MetricTrend[] {
  const trends: MetricTrend[] = [];
  const now = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    // Simulate a generally increasing trend with some variance
    const baseValue = 50 + (days - i) * 2;
    const variance = (Math.random() - 0.5) * 20;
    const value = Math.max(0, baseValue + variance);

    trends.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(value),
    });
  }

  return trends;
}

export function generateInsights(): Insight[] {
  return [
    {
      id: 'insight-1',
      category: 'efficiency',
      title: 'Model Selection Opportunity',
      description: "You're using Opus for simple tasks 40% of the time. Consider using Haiku to save tokens.",
      impact: 'high',
      actionable: true,
      timestamp: new Date().toISOString(),
    },
    {
      id: 'insight-2',
      category: 'quality',
      title: 'Test Coverage Improvement',
      description: 'Your test coverage increased 15% when using AI for test generation.',
      impact: 'high',
      actionable: false,
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'insight-3',
      category: 'efficiency',
      title: 'Peak Productivity Hours',
      description: 'Your most productive hours are 9-11 AM and 2-4 PM. Consider scheduling complex tasks during these windows.',
      impact: 'medium',
      actionable: true,
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'insight-4',
      category: 'cost',
      title: 'Token Usage Spike',
      description: 'Token usage increased by 35% this week. Review recent sessions for optimization opportunities.',
      impact: 'medium',
      actionable: true,
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'insight-5',
      category: 'learning',
      title: 'Prompt Engineering Progress',
      description: 'Your prompt iteration count decreased by 25% - sign of improving AI collaboration skills.',
      impact: 'low',
      actionable: false,
      timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    },
  ];
}

export function getUserProfile(): UserProfile {
  return {
    id: 'dev_001',
    name: 'Alex Chen',
    email: 'alex.chen@company.com',
    avatar: undefined,
    joinDate: '2024-09-15',
  };
}

// Export all mock data
export const mockData = {
  sessions: generateMockSessions(),
  get dashboardMetrics() {
    return calculateDashboardMetrics(this.sessions);
  },
  get activityHeatmap() {
    return generateActivityHeatmap(this.sessions);
  },
  get recentSessions() {
    return generateRecentSessions(this.sessions);
  },
  profileDimensions: generateProfileDimensions(),
  skillBadges: generateSkillBadges(),
  languageUsage: generateLanguageUsage(),
  metricTrends: generateMetricTrends(),
  insights: generateInsights(),
  userProfile: getUserProfile(),
};
