import { useState } from 'react';
import { mockData } from '../services/mockData';
import { usePageTitle } from '../hooks/usePageTitle';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, Target, Code, BookOpen, Activity } from 'lucide-react';

type TabType = 'productivity' | 'quality' | 'usage' | 'learning';

const tabs = [
  { id: 'productivity' as TabType, label: 'Productivity', icon: TrendingUp },
  { id: 'quality' as TabType, label: 'Quality', icon: Target },
  { id: 'usage' as TabType, label: 'Usage Patterns', icon: Activity },
  { id: 'learning' as TabType, label: 'Learning & Growth', icon: BookOpen },
];

/**
 * Metrics Page Component
 *
 * Displays detailed analytics across productivity, quality, usage, and learning dimensions
 */

export function Metrics() {
  usePageTitle('Metrics', 'Deep Analytics');
  const [activeTab, setActiveTab] = useState<TabType>('productivity');

  // Productivity metrics
  const codeSpeedData = mockData.sessions
    .slice(0, 30)
    .map((s, i) => ({
      day: `Day ${i + 1}`,
      speed: Math.round((s.tokens_out / s.latency_ms) * 1000 * 60), // Lines per minute estimate
    }));

  const taskCompletionData = [
    { task: 'Bug Fix', time: 12.5, color: '#66A4E1' },
    { task: 'Feature', time: 45.3, color: '#20B6F9' },
    { task: 'Refactor', time: 28.7, color: '#E47396' },
    { task: 'Test', time: 18.2, color: '#D77CA6' },
    { task: 'Docs', time: 8.9, color: '#F36265' },
  ];

  const acceptanceRateData = mockData.sessions
    .slice(0, 30)
    .reduce((acc: any[], session, i) => {
      if (i % 3 === 0) {
        const recent = mockData.sessions.slice(Math.max(0, i - 10), i + 1);
        const rate = (recent.filter(s => s.accepted_flag).length / recent.length) * 100;
        acc.push({ day: `Day ${Math.floor(i / 3) + 1}`, rate: Math.round(rate) });
      }
      return acc;
    }, []);

  // Quality metrics
  const testCoverageData = [
    { name: 'Before AI', coverage: 62, fill: '#F36265' },
    { name: 'After AI', coverage: 84, fill: '#66A4E1' },
  ];

  const docQualityData = [
    { project: 'API Service', score: 88 },
    { project: 'Frontend', score: 92 },
    { project: 'Backend', score: 79 },
    { project: 'Mobile App', score: 85 },
    { project: 'CLI Tool', score: 91 },
  ];

  const qualityGauges = [
    { name: 'Code Quality', score: 88, max: 100, fill: '#66A4E1' },
    { name: 'Test Coverage', score: 84, max: 100, fill: '#20B6F9' },
    { name: 'Documentation', score: 91, max: 100, fill: '#E47396' },
  ];

  // Usage pattern metrics
  const taskDistribution = [
    { name: 'Feature Development', value: 35, color: '#66A4E1' },
    { name: 'Bug Fixes', value: 25, color: '#20B6F9' },
    { name: 'Refactoring', value: 20, color: '#E47396' },
    { name: 'Testing', value: 12, color: '#D77CA6' },
    { name: 'Documentation', value: 8, color: '#F36265' },
  ];

  const languageUsage = [
    { language: 'TypeScript', sessions: 45 },
    { language: 'Python', sessions: 38 },
    { language: 'JavaScript', sessions: 32 },
    { language: 'Go', sessions: 18 },
    { language: 'Rust', sessions: 12 },
  ];

  const modelUsageData = mockData.sessions
    .slice(0, 30)
    .reduce((acc: any[], session, i) => {
      if (i % 2 === 0) {
        const recent = mockData.sessions.slice(Math.max(0, i - 5), i + 1);
        const sonnet = recent.filter(s => s.model?.includes('sonnet')).length;
        const haiku = recent.filter(s => s.model?.includes('haiku')).length;
        const opus = recent.filter(s => s.model?.includes('opus')).length;
        acc.push({
          day: `Day ${Math.floor(i / 2) + 1}`,
          Sonnet: sonnet,
          Haiku: haiku,
          Opus: opus,
        });
      }
      return acc;
    }, []);

  // Learning metrics
  const skillProgressionData = [
    { month: 'Jan', promptEngineering: 45, modelSelection: 50, codeQuality: 60 },
    { month: 'Feb', promptEngineering: 55, modelSelection: 58, codeQuality: 65 },
    { month: 'Mar', promptEngineering: 62, modelSelection: 65, codeQuality: 72 },
    { month: 'Apr', promptEngineering: 70, modelSelection: 75, codeQuality: 80 },
    { month: 'May', promptEngineering: 75, modelSelection: 82, codeQuality: 88 },
  ];

  const knowledgeGaps = [
    { area: 'Advanced Prompting', size: 45, color: '#F36265' },
    { area: 'Cost Optimization', size: 32, color: '#E47396' },
    { area: 'Model Selection', size: 28, color: '#D77CA6' },
    { area: 'Context Management', size: 38, color: '#66A4E1' },
    { area: 'Best Practices', size: 25, color: '#20B6F9' },
  ];

  const improvementAreas = [
    { area: 'Prompt Engineering', improvement: '+30%', icon: Code },
    { area: 'Test Coverage', improvement: '+22%', icon: Target },
    { area: 'Documentation Quality', improvement: '+18%', icon: BookOpen },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Metrics Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Deep dive into productivity, quality, usage patterns, and learning progress
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-primary text-primary font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Productivity Tab */}
      {activeTab === 'productivity' && (
        <div className="space-y-6">
          {/* Code Generation Speed */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Code Generation Speed Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={codeSpeedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="speed"
                  stroke="#66A4E1"
                  strokeWidth={2}
                  dot={{ fill: '#66A4E1', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-sm text-muted-foreground mt-2">
              Average lines per minute generated with AI assistance
            </p>
          </div>

          {/* Time to Completion by Task Type */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Time to Completion by Task Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={taskCompletionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="task" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="time" radius={[8, 8, 0, 0]}>
                  {taskCompletionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-muted-foreground mt-2">
              Average minutes to complete each task type
            </p>
          </div>

          {/* Acceptance Rate Trend */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Acceptance Rate Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={acceptanceRateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="rate"
                  stroke="#20B6F9"
                  fill="#20B6F9"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
            <p className="text-sm text-muted-foreground mt-2">
              Percentage of AI-generated code accepted over time
            </p>
          </div>
        </div>
      )}

      {/* Quality Tab */}
      {activeTab === 'quality' && (
        <div className="space-y-6">
          {/* Test Coverage Comparison */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">Test Coverage Impact</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={testCoverageData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis type="number" stroke="hsl(var(--muted-foreground))" />
                  <YAxis type="category" dataKey="name" stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="coverage" radius={[0, 8, 8, 0]}>
                    {testCoverageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Quality Gauge Charts */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">Quality Metrics</h3>
              <div className="space-y-4">
                {qualityGauges.map((gauge) => (
                  <div key={gauge.name}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{gauge.name}</span>
                      <span className="text-sm font-bold" style={{ color: gauge.fill }}>
                        {gauge.score}%
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-3">
                      <div
                        className="h-3 rounded-full transition-all"
                        style={{
                          width: `${gauge.score}%`,
                          backgroundColor: gauge.fill,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Documentation Quality by Project */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Documentation Quality by Project</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={docQualityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="project" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="score" fill="#E47396" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-muted-foreground mt-2">
              Documentation quality score (0-100) by project
            </p>
          </div>
        </div>
      )}

      {/* Usage Patterns Tab */}
      {activeTab === 'usage' && (
        <div className="space-y-6">
          {/* Task Type Distribution */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">Task Type Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={taskDistribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, value }) => `${name}: ${value}%`}
                    labelLine={{ stroke: 'hsl(var(--muted-foreground))' }}
                  >
                    {taskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Language Usage */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">Language/Framework Usage</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={languageUsage}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="language" stroke="hsl(var(--muted-foreground))" />
                  <YAxis stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="sessions" fill="#66A4E1" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model Usage Distribution */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Model Usage Distribution Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={modelUsageData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="Sonnet"
                  stackId="1"
                  stroke="#66A4E1"
                  fill="#66A4E1"
                />
                <Area
                  type="monotone"
                  dataKey="Haiku"
                  stackId="1"
                  stroke="#20B6F9"
                  fill="#20B6F9"
                />
                <Area
                  type="monotone"
                  dataKey="Opus"
                  stackId="1"
                  stroke="#E47396"
                  fill="#E47396"
                />
              </AreaChart>
            </ResponsiveContainer>
            <p className="text-sm text-muted-foreground mt-2">
              Stacked area chart showing which models you use over time
            </p>
          </div>
        </div>
      )}

      {/* Learning & Growth Tab */}
      {activeTab === 'learning' && (
        <div className="space-y-6">
          {/* Skill Progression Timeline */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Skill Progression Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={skillProgressionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="promptEngineering"
                  stroke="#66A4E1"
                  strokeWidth={2}
                  name="Prompt Engineering"
                />
                <Line
                  type="monotone"
                  dataKey="modelSelection"
                  stroke="#20B6F9"
                  strokeWidth={2}
                  name="Model Selection"
                />
                <Line
                  type="monotone"
                  dataKey="codeQuality"
                  stroke="#E47396"
                  strokeWidth={2}
                  name="Code Quality"
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-sm text-muted-foreground mt-2">
              Your skill scores improving over time (0-100 scale)
            </p>
          </div>

          {/* Most Improved Areas */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Most Improved Areas</h3>
            <div className="grid gap-4 md:grid-cols-3">
              {improvementAreas.map((area) => {
                const Icon = area.icon;
                return (
                  <div
                    key={area.area}
                    className="rounded-lg border border-border bg-muted/50 p-4"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className="rounded-lg p-2 bg-picton-blue/10 border border-picton-blue">
                        <Icon className="h-5 w-5 text-picton-blue" />
                      </div>
                      <span className="text-2xl font-bold text-picton-blue">
                        {area.improvement}
                      </span>
                    </div>
                    <p className="text-sm font-medium">{area.area}</p>
                    <p className="text-xs text-muted-foreground mt-1">vs. last month</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Knowledge Gaps Bubble Chart */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Knowledge Gaps to Address</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {knowledgeGaps.map((gap) => (
                <div
                  key={gap.area}
                  className="flex flex-col items-center justify-center rounded-lg border border-border p-4 hover:shadow-md transition-shadow"
                  style={{
                    height: `${gap.size + 100}px`,
                    backgroundColor: `${gap.color}10`,
                    borderColor: gap.color,
                  }}
                >
                  <div
                    className="rounded-full flex items-center justify-center text-white font-bold mb-2"
                    style={{
                      width: `${gap.size + 20}px`,
                      height: `${gap.size + 20}px`,
                      backgroundColor: gap.color,
                    }}
                  >
                    {gap.size}
                  </div>
                  <p className="text-xs text-center font-medium">{gap.area}</p>
                </div>
              ))}
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              Bubble size represents the potential impact of addressing each knowledge gap
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
