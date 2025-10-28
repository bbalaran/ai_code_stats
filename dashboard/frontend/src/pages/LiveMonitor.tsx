import { useState, useEffect, useRef } from 'react';
import { mockData } from '../services/mockData';
import { usePageTitle } from '../hooks/usePageTitle';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Radio,
  TrendingUp,
  Zap,
  Users,
  Eye,
  Server,
  Gauge,
} from 'lucide-react';
import { format } from 'date-fns';
import type { Session } from '../types';

/**
 * Live Monitor Page Component
 *
 * Real-time monitoring of active coding sessions
 */

interface LiveSession extends Session {
  status: 'active' | 'completed' | 'error';
  progress?: number;
}

export function LiveMonitor() {
  usePageTitle('Live Monitor', 'Real-time Sessions');
  const [liveSessions, setLiveSessions] = useState<LiveSession[]>([]);
  const [activeSessionCount, setActiveSessionCount] = useState(0);
  const [totalToday, setTotalToday] = useState(0);
  const [systemHealth, setSystemHealth] = useState({
    apiHealth: 'healthy',
    databaseHealth: 'healthy',
    avgLatency: 245,
    errorRate: 1.2,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Initialize with some sessions
    const today = new Date();
    const todaySessionsData = mockData.sessions.filter(s => {
      const sessionDate = new Date(s.timestamp);
      return sessionDate.toDateString() === today.toDateString();
    });

    setTotalToday(todaySessionsData.length);

    // Simulate real-time session updates
    const updateSessions = () => {
      const randomSessionCount = Math.floor(Math.random() * 8) + 2; // 2-9 active sessions
      const newSessions: LiveSession[] = [];

      // Create active sessions
      for (let i = 0; i < randomSessionCount; i++) {
        const baseSession = mockData.sessions[Math.floor(Math.random() * mockData.sessions.length)];
        const isError = Math.random() < 0.05; // 5% error rate
        const status = isError ? 'error' : Math.random() < 0.3 ? 'completed' : 'active';

        newSessions.push({
          ...baseSession,
          id: i,
          status: status as 'active' | 'completed' | 'error',
          progress: status === 'active' ? Math.floor(Math.random() * 100) : 100,
        });
      }

      setLiveSessions(newSessions);
      setActiveSessionCount(newSessions.filter(s => s.status === 'active').length);

      // Update system health metrics
      setSystemHealth({
        apiHealth: Math.random() > 0.02 ? 'healthy' : 'degraded',
        databaseHealth: Math.random() > 0.01 ? 'healthy' : 'degraded',
        avgLatency: Math.floor(Math.random() * 200) + 100,
        errorRate: (Math.random() * 3).toFixed(2) as unknown as number,
      });
    };

    updateSessions();
    intervalRef.current = setInterval(updateSessions, 2000); // Update every 2 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const successCount = liveSessions.filter(s => s.status === 'completed').length;
  const errorCount = liveSessions.filter(s => s.status === 'error').length;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-amber-500';
      case 'completed':
        return 'text-picton-blue';
      case 'error':
        return 'text-bittersweet';
      default:
        return 'text-muted-foreground';
    }
  };

  const getStatusBgColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-amber-500/10';
      case 'completed':
        return 'bg-picton-blue/10';
      case 'error':
        return 'bg-bittersweet/10';
      default:
        return 'bg-muted/10';
    }
  };

  const getHealthColor = (health: string) => {
    return health === 'healthy'
      ? 'text-picton-blue bg-picton-blue/10'
      : 'text-bittersweet bg-bittersweet/10';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Radio className="h-8 w-8 text-amber-500 animate-pulse" />
            Live Monitoring
          </h1>
          <p className="text-muted-foreground mt-2">
            Real-time tracking of active AI coding sessions
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/10 border border-picton-blue/30">
          <Activity className="h-5 w-5 text-picton-blue animate-pulse" />
          <span className="text-sm font-semibold">{activeSessionCount} Active</span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Activity className="h-4 w-4" />
            <span className="text-sm">Active Sessions</span>
          </div>
          <p className="text-3xl font-bold">{activeSessionCount}</p>
          <p className="text-xs text-muted-foreground mt-1">Currently running</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-sm">Completed Today</span>
          </div>
          <p className="text-3xl font-bold">{totalToday}</p>
          <p className="text-xs text-muted-foreground mt-1">In last 24 hours</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Success Rate</span>
          </div>
          <p className="text-3xl font-bold">
            {liveSessions.length > 0
              ? ((successCount / liveSessions.length) * 100).toFixed(0)
              : '0'}
            %
          </p>
          <p className="text-xs text-muted-foreground mt-1">{successCount} successful</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <TrendingUp className="h-4 w-4" />
            <span className="text-sm">Errors</span>
          </div>
          <p className="text-3xl font-bold text-bittersweet">{errorCount}</p>
          <p className="text-xs text-muted-foreground mt-1">In progress</p>
        </div>
      </div>

      {/* System Health */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Server className="h-5 w-5" />
            System Health
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">API Health</span>
              <span
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${getHealthColor(
                  systemHealth.apiHealth
                )}`}
              >
                <div
                  className={`h-2 w-2 rounded-full ${
                    systemHealth.apiHealth === 'healthy'
                      ? 'bg-picton-blue animate-pulse'
                      : 'bg-bittersweet'
                  }`}
                />
                {systemHealth.apiHealth === 'healthy' ? 'Healthy' : 'Degraded'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Database Health</span>
              <span
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${getHealthColor(
                  systemHealth.databaseHealth
                )}`}
              >
                <div
                  className={`h-2 w-2 rounded-full ${
                    systemHealth.databaseHealth === 'healthy'
                      ? 'bg-picton-blue animate-pulse'
                      : 'bg-bittersweet'
                  }`}
                />
                {systemHealth.databaseHealth === 'healthy' ? 'Healthy' : 'Degraded'}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-border">
              <span className="text-sm font-medium">Avg Latency</span>
              <div className="flex items-center gap-2">
                <Gauge className="h-4 w-4 text-muted-foreground" />
                <span className="font-mono text-sm">{systemHealth.avgLatency}ms</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Error Rate</span>
              <span className="font-mono text-sm text-bittersweet">
                {systemHealth.errorRate}%
              </span>
            </div>
          </div>
        </div>

        {/* Activity Summary */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Users className="h-5 w-5" />
            Activity Summary
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Active Sessions</span>
                <span className="text-sm font-bold text-amber-500">{activeSessionCount}</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-amber-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min((activeSessionCount / 10) * 100, 100)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Success Rate</span>
                <span className="text-sm font-bold text-picton-blue">
                  {liveSessions.length > 0
                    ? ((successCount / liveSessions.length) * 100).toFixed(0)
                    : '0'}
                  %
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-picton-blue h-2 rounded-full transition-all"
                  style={{
                    width: `${
                      liveSessions.length > 0
                        ? ((successCount / liveSessions.length) * 100)
                        : 0
                    }%`
                  }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Error Rate</span>
                <span className="text-sm font-bold text-bittersweet">
                  {liveSessions.length > 0 ? ((errorCount / liveSessions.length) * 100).toFixed(0) : '0'}%
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-bittersweet h-2 rounded-full transition-all"
                  style={{
                    width: `${
                      liveSessions.length > 0 ? ((errorCount / liveSessions.length) * 100) : 0
                    }%`
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Session Feed */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Eye className="h-5 w-5" />
          Live Session Feed
        </h3>

        {liveSessions.length === 0 ? (
          <div className="py-8 text-center">
            <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground">No active sessions at the moment</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {liveSessions.map((session, index) => (
              <div
                key={index}
                className={`flex items-center gap-4 p-4 rounded-lg border ${
                  session.status === 'active'
                    ? 'border-amber-500/50 bg-amber-500/5'
                    : session.status === 'completed'
                    ? 'border-picton-blue/50 bg-picton-blue/5'
                    : 'border-bittersweet/50 bg-bittersweet/5'
                } transition-all`}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {session.status === 'active' ? (
                    <Radio className={`h-5 w-5 ${getStatusColor(session.status)} animate-pulse flex-shrink-0`} />
                  ) : session.status === 'completed' ? (
                    <CheckCircle2 className={`h-5 w-5 ${getStatusColor(session.status)} flex-shrink-0`} />
                  ) : (
                    <AlertCircle className={`h-5 w-5 ${getStatusColor(session.status)} flex-shrink-0`} />
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold truncate">
                        {session.model?.split('-').pop() || 'Unknown Model'}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                        {format(new Date(session.timestamp), 'h:mm a')}
                      </span>
                    </div>
                    {session.status === 'active' && session.progress !== undefined && (
                      <div>
                        <div className="w-full bg-muted rounded-full h-1.5">
                          <div
                            className="bg-amber-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${session.progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {session.progress}% complete · {session.total_tokens} tokens
                        </p>
                      </div>
                    )}
                    {session.status !== 'active' && (
                      <p className="text-xs text-muted-foreground">
                        {(session.latency_ms / 1000).toFixed(2)}s · {session.total_tokens} tokens · Cost: ${session.cost_usd.toFixed(4)}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`inline-flex px-2.5 py-1.5 rounded text-xs font-medium ${getStatusBgColor(session.status)} ${getStatusColor(session.status)}`}>
                    {session.status === 'active' ? (
                      <span className="flex items-center gap-1">
                        <Zap className="h-3 w-3" />
                        Active
                      </span>
                    ) : session.status === 'completed' ? (
                      'Completed'
                    ) : (
                      'Error'
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Connection Status */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-picton-blue animate-pulse" />
            <span className="text-sm text-muted-foreground">
              Connected to live stream · Last update: just now
            </span>
          </div>
          <span className="text-xs text-muted-foreground font-mono">ws://api/traces</span>
        </div>
      </div>
    </div>
  );
}
