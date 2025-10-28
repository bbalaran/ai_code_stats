export interface Session {
  id: number;
  session_id: string | null;
  developer_id: string | null;
  timestamp: string;
  model: string | null;
  tokens_in: number;
  tokens_out: number;
  latency_ms: number;
  status_code: number | null;
  accepted_flag: boolean;
  repo_slug: string | null;
  event_date: string;
  total_tokens: number;
  cost_usd: number;
  diff_ratio: number | null;
  accepted_lines: number | null;
}

export interface DashboardMetrics {
  totalSessions: number;
  totalSessionsTrend: number;
  linesOfCode: number;
  linesOfCodeTrend: number;
  acceptanceRate: number;
  acceptanceRateTrend: number;
  tokenUsage: number;
  estimatedCost: number;
  costTrend: number;
}

export interface ActivityHeatmap {
  day: number; // 0-6 (Sun-Sat)
  hour: number; // 0-23
  value: number; // session count
}

export interface RecentSession {
  id: number;
  timestamp: string;
  model: string;
  duration: number; // latency_ms
  tokensUsed: number;
  acceptanceRate: number;
  taskType: string;
}

export interface ProfileDimension {
  dimension: string;
  score: number; // 0-100
}

export interface SkillBadge {
  id: string;
  name: string;
  description: string;
  earned: boolean;
  earnedDate?: string;
}

export interface LanguageUsage {
  language: string;
  percentage: number;
  sessionCount: number;
}

export interface MetricTrend {
  date: string;
  value: number;
}

export interface Insight {
  id: string;
  category: 'efficiency' | 'quality' | 'cost' | 'learning';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  actionable: boolean;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  data?: any; // For inline charts/data
}

export interface TimeRange {
  label: string;
  days: number;
}

export const TIME_RANGES: TimeRange[] = [
  { label: 'Today', days: 1 },
  { label: 'Week', days: 7 },
  { label: 'Month', days: 30 },
  { label: 'Quarter', days: 90 },
  { label: 'Year', days: 365 },
];

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  joinDate: string;
}

export type TaskType =
  | 'code_generation'
  | 'refactoring'
  | 'debugging'
  | 'documentation'
  | 'testing'
  | 'code_review'
  | 'architecture';

