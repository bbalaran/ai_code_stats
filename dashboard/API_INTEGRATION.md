# API Integration Guide

## Overview

This document describes the API integration layer for the ProdLens Dashboard frontend. The integration provides a clean abstraction between the React components and backend API endpoints, with built-in fallback to mock data for development.

## Architecture

```
React Components
        ↓
    Hooks (useApi)
        ↓
   API Service Layer (api.ts)
        ↓
   React Query (Caching & State Management)
        ↓
Backend API / Mock Data
```

## Setup

### 1. Environment Configuration

Create a `.env` file in the `dashboard/frontend` directory:

```bash
cp .env.example .env
```

Configure the API endpoints:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws/sessions
VITE_USE_MOCK_DATA=true
```

### 2. Install Dependencies

React Query is already installed. If you need to reinstall:

```bash
npm install @tanstack/react-query
```

## API Service Layer

The `src/services/api.ts` file exports the following modules:

### Metrics API

```typescript
import { api } from './services/api';

// Get overview metrics
const metrics = await api.metrics.getOverviewMetrics();

// Get time-series data
const timeseries = await api.metrics.getTimeSeriesData(30); // 30 days

// Get hourly activity
const hourly = await api.metrics.getHourlyActivity();
```

### Sessions API

```typescript
// List all sessions with filters
const sessions = await api.sessions.listSessions({
  limit: 50,
  offset: 0,
  model: 'sonnet',
  status: 'success'
});

// Get specific session
const session = await api.sessions.getSession('session-id');

// Get recent sessions
const recent = await api.sessions.getRecentSessions(10);
```

### Profile API

```typescript
// Get user profile
const profile = await api.profile.getUserProfile();

// Get proficiency dimensions
const dimensions = await api.profile.getProfileDimensions();

// Get skill badges
const badges = await api.profile.getSkillBadges();

// Get language usage
const languages = await api.profile.getLanguageUsage();
```

### Insights API

```typescript
// Get insights with filters
const insights = await api.insights.getInsights({
  category: 'efficiency',
  limit: 20
});

// Dismiss an insight
await api.insights.dismissInsight('insight-id');
```

### Activity API

```typescript
// Get activity heatmap
const heatmap = await api.activity.getActivityHeatmap();

// Get activity trends
const trends = await api.activity.getActivityTrends(30); // 30 days
```

### Real-time API (WebSocket)

```typescript
// Connect to live session stream
const ws = api.realtime.connectToSessionStream({
  onSessionStarted: (session) => {
    console.log('Session started:', session);
  },
  onSessionCompleted: (session) => {
    console.log('Session completed:', session);
  },
  onError: (error) => {
    console.error('WebSocket error:', error);
  },
  onConnectionEstablished: () => {
    console.log('Connected to live stream');
  }
});

// Don't forget to close the connection when done
// ws?.close();
```

## React Query Hooks

Custom hooks are provided in `src/hooks/useApi.ts` for easy component integration:

### Metrics Hooks

```typescript
import { useOverviewMetrics, useTimeSeriesData, useHourlyActivity } from './hooks/useApi';

function Dashboard() {
  const { data: metrics, isLoading, error } = useOverviewMetrics();
  const { data: timeseries } = useTimeSeriesData(30);
  const { data: hourly } = useHourlyActivity();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Total Sessions: {metrics?.totalSessions}</h1>
      {/* ... */}
    </div>
  );
}
```

### Sessions Hooks

```typescript
import { useSessions, useSession, useRecentSessions } from './hooks/useApi';

function SessionsPage() {
  const { data: sessions } = useSessions({ limit: 50 });
  const { data: recent } = useRecentSessions(10);

  return (
    <div>
      {sessions?.map(session => (
        <div key={session.id}>{session.model}</div>
      ))}
    </div>
  );
}
```

### Profile Hooks

```typescript
import { useUserProfile, useProfileDimensions, useSkillBadges, useLanguageUsage } from './hooks/useApi';

function Profile() {
  const { data: profile } = useUserProfile();
  const { data: dimensions } = useProfileDimensions();
  const { data: badges } = useSkillBadges();
  const { data: languages } = useLanguageUsage();

  return (
    <div>
      <h1>{profile?.name}</h1>
      {/* ... */}
    </div>
  );
}
```

### Insights Hooks

```typescript
import { useInsights, useDismissInsight } from './hooks/useApi';

function InsightsPage() {
  const { data: insights } = useInsights({ category: 'efficiency' });
  const dismissMutation = useDismissInsight();

  const handleDismiss = (insightId: string) => {
    dismissMutation.mutate(insightId);
  };

  return (
    <div>
      {insights?.map(insight => (
        <div key={insight.id}>
          <h3>{insight.title}</h3>
          <button onClick={() => handleDismiss(insight.id)}>Dismiss</button>
        </div>
      ))}
    </div>
  );
}
```

### Activity Hooks

```typescript
import { useActivityHeatmap, useActivityTrends } from './hooks/useApi';

function ActivityPage() {
  const { data: heatmap } = useActivityHeatmap();
  const { data: trends } = useActivityTrends(30);

  return (
    <div>
      {/* ... */}
    </div>
  );
}
```

## Error Handling

All API calls include automatic error handling with fallback to mock data:

```typescript
// If the API call fails, it automatically returns mock data
const { data: metrics, error, isError } = useOverviewMetrics();

if (isError) {
  console.warn('Using mock data due to API error:', error);
}
```

## Caching Strategy

React Query automatically caches responses based on stale times:

| Resource | Stale Time | Cache Time |
|----------|-----------|-----------|
| Metrics (Overview) | 5 minutes | 30 minutes |
| Metrics (Timeseries) | 5 minutes | 30 minutes |
| Sessions | 2 minutes | 15 minutes |
| Profile | 30 minutes | 60 minutes |
| Insights | 5 minutes | 30 minutes |
| Activity | 5 minutes | 30 minutes |

## Backend API Endpoints

The frontend expects the following API structure (update your backend to match):

### Metrics Endpoints

```
GET /api/metrics/overview              # Dashboard overview metrics
GET /api/metrics/timeseries?days=30    # Time-series data
GET /api/metrics/hourly                # Hourly activity patterns
```

### Sessions Endpoints

```
GET /api/sessions?limit=50&offset=0    # List sessions with pagination
GET /api/sessions/:id                  # Get specific session details
```

### Profile Endpoints

```
GET /api/profile                       # User profile
GET /api/profile/dimensions            # Proficiency dimensions
GET /api/profile/badges                # Skill badges
GET /api/profile/languages             # Language usage
```

### Insights Endpoints

```
GET /api/insights?category=efficiency  # Get insights with filtering
POST /api/insights/:id/dismiss         # Dismiss an insight
```

### Activity Endpoints

```
GET /api/activity/heatmap              # Activity heatmap data
GET /api/activity/trends?days=30       # Activity trends over time
```

### WebSocket Endpoint

```
WS /api/ws/sessions                    # Real-time session stream

# Expected message format:
{
  "type": "session_started" | "session_completed",
  "data": { /* Session object */ }
}
```

## Response Formats

### Session Response

```typescript
interface Session {
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
```

### Dashboard Metrics Response

```typescript
interface DashboardMetrics {
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
```

## Migration Guide

### From Mock Data to API

To convert a component from using mock data to using the API:

**Before:**
```typescript
import { mockData } from '../services/mockData';

export function Dashboard() {
  return (
    <div>
      <h1>Sessions: {mockData.sessions.length}</h1>
    </div>
  );
}
```

**After:**
```typescript
import { useSessions } from '../hooks/useApi';

export function Dashboard() {
  const { data: sessions, isLoading } = useSessions({ limit: 100 });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Sessions: {sessions?.length || 0}</h1>
    </div>
  );
}
```

## Development Mode

During development, the API layer gracefully falls back to mock data if the backend is not running. This allows frontend development to proceed independently.

To use mock data explicitly:

```typescript
import { mockData } from './services/mockData';

// Use mockData directly when needed
const sessions = mockData.sessions;
```

## Query Invalidation

To force a refresh of cached data:

```typescript
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './hooks/useApi';

function MyComponent() {
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    // Invalidate metrics queries
    queryClient.invalidateQueries({ queryKey: queryKeys.metrics.all });

    // Or specific query
    queryClient.invalidateQueries({ queryKey: queryKeys.metrics.overview });
  };

  return <button onClick={handleRefresh}>Refresh</button>;
}
```

## Performance Optimization

### Enable React Query DevTools

For development, you can enable React Query DevTools:

```bash
npm install @tanstack/react-query-devtools
```

Then add to your app:

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <>
      {/* ... */}
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  )
}
```

### Prefetching

Prefetch data before rendering components:

```typescript
import { useQueryClient } from '@tanstack/react-query';

function MyComponent() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Prefetch next page of results
    queryClient.prefetchQuery({
      queryKey: queryKeys.sessions.list({ limit: 50, offset: 50 }),
      queryFn: () => api.sessions.listSessions({ limit: 50, offset: 50 }),
    });
  }, [queryClient]);

  return <div>{/* ... */}</div>;
}
```

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure your backend has CORS configured:

```python
# FastAPI example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WebSocket Connection Issues

Check that:
1. The WebSocket URL is correct in `.env`
2. The backend WebSocket endpoint is running
3. Browser console for any connection errors

### API Timeout

The default timeout is 5 seconds. To increase:

```typescript
// In services/api.ts, change the fetchWithTimeout call:
fetchWithTimeout(url, options, 10000); // 10 seconds
```

## Best Practices

1. **Use hooks for components**: Always use the provided hooks instead of calling the API directly in components.

2. **Handle loading states**: Show loading indicators while data is being fetched.

3. **Handle errors gracefully**: Provide user-friendly error messages.

4. **Avoid over-fetching**: Use query filters to request only needed data.

5. **Cache appropriately**: Use sensible stale times based on data update frequency.

6. **Invalidate cache carefully**: Only invalidate when absolutely necessary.

## Future Enhancements

- [ ] Implement optimistic updates
- [ ] Add retry logic with exponential backoff
- [ ] Implement request deduplication
- [ ] Add request/response logging
- [ ] Implement rate limiting on client side
- [ ] Add offline support with service workers
- [ ] Implement real-time data subscriptions
