import { Activity, Code2, CheckCircle2, DollarSign } from 'lucide-react';
import { MetricCard } from '../components/cards/MetricCard';
import { mockData } from '../services/mockData';
import { usePageTitle } from '../hooks/usePageTitle';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

/**
 * Dashboard Page Component
 *
 * Displays overview metrics, activity trends, and recent sessions
 */
export function Dashboard() {
  usePageTitle('Dashboard', 'AI Coding Statistics');
  const metrics = mockData.dashboardMetrics;
  const recentSessions = mockData.recentSessions;
  const trends = mockData.metricTrends;

  // Prepare heatmap data for activity visualization
  const heatmapData = mockData.activityHeatmap.filter(d => d.value > 0);
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="AI Sessions This Week"
          value={metrics.totalSessions}
          trend={metrics.totalSessionsTrend}
          icon={<Activity className="h-5 w-5" />}
        />
        <MetricCard
          title="Lines of Code Generated"
          value={metrics.linesOfCode.toLocaleString()}
          trend={metrics.linesOfCodeTrend}
          icon={<Code2 className="h-5 w-5" />}
        />
        <MetricCard
          title="Average Acceptance Rate"
          value={`${metrics.acceptanceRate.toFixed(1)}%`}
          trend={metrics.acceptanceRateTrend}
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
        <MetricCard
          title="Estimated Cost"
          value={`$${metrics.estimatedCost.toFixed(2)}`}
          trend={metrics.costTrend}
          icon={<DollarSign className="h-5 w-5" />}
          subtitle={`${(metrics.tokenUsage / 1000).toFixed(1)}K tokens`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Activity Trend */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Activity Trend (30 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => format(new Date(date), 'MMM d')}
                className="text-xs"
              />
              <YAxis className="text-xs" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#66A4E1"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Sessions by Hour */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Peak Activity Hours</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={Array.from({ length: 24 }, (_, hour) => ({
                hour,
                count: heatmapData.filter(d => d.hour === hour).reduce((sum, d) => sum + d.value, 0),
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="hour"
                tickFormatter={(hour) => `${hour}:00`}
                className="text-xs"
              />
              <YAxis className="text-xs" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
              />
              <Bar dataKey="count" fill="#20B6F9" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="rounded-lg border border-border bg-card">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Recent Sessions</h3>
        </div>
        <div className="divide-y divide-border">
          {recentSessions.map((session) => (
            <div key={session.id} className="p-4 hover:bg-accent/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">
                      {format(new Date(session.timestamp), 'MMM d, h:mm a')}
                    </span>
                    <span className="text-xs px-2 py-1 rounded-full bg-ruddy-blue/10 text-ruddy-blue">
                      {session.model.split('-').pop()}
                    </span>
                    <span className="text-xs text-muted-foreground capitalize">
                      {session.taskType.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{session.tokensUsed.toLocaleString()} tokens</span>
                    <span>{(session.duration / 1000).toFixed(1)}s</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-picton-blue">
                    {session.acceptanceRate}% accepted
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
