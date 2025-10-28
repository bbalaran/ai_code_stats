/**
 * React Query Hooks for API Integration
 *
 * Provides type-safe hooks for fetching data with caching, background refetching,
 * and automatic error handling.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Session, DashboardMetrics, Insight, UserProfile, ProfileDimension, SkillBadge, LanguageUsage } from '../types';

// Query key factory for cache management
interface SessionFilters {
  limit?: number;
  offset?: number;
  model?: string;
  status?: string;
}

interface InsightFilters {
  category?: string;
  limit?: number;
}

export const queryKeys = {
  metrics: {
    all: ['metrics'] as const,
    overview: ['metrics', 'overview'] as const,
    timeseries: (days: number) => ['metrics', 'timeseries', days] as const,
    hourly: ['metrics', 'hourly'] as const,
  },
  sessions: {
    all: ['sessions'] as const,
    list: (filters?: SessionFilters) => ['sessions', 'list', filters] as const,
    detail: (id: string) => ['sessions', 'detail', id] as const,
    recent: (limit: number) => ['sessions', 'recent', limit] as const,
  },
  profile: {
    all: ['profile'] as const,
    user: ['profile', 'user'] as const,
    dimensions: ['profile', 'dimensions'] as const,
    badges: ['profile', 'badges'] as const,
    languages: ['profile', 'languages'] as const,
  },
  insights: {
    all: ['insights'] as const,
    list: (filters?: InsightFilters) => ['insights', 'list', filters] as const,
  },
  activity: {
    all: ['activity'] as const,
    heatmap: ['activity', 'heatmap'] as const,
    trends: (days: number) => ['activity', 'trends', days] as const,
  },
};

/**
 * Metrics Hooks
 */
export function useOverviewMetrics() {
  return useQuery({
    queryKey: queryKeys.metrics.overview,
    queryFn: () => api.metrics.getOverviewMetrics(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
    retry: 2,
  });
}

export function useTimeSeriesData(days: number = 30) {
  return useQuery({
    queryKey: queryKeys.metrics.timeseries(days),
    queryFn: () => api.metrics.getTimeSeriesData(days),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

export function useHourlyActivity() {
  return useQuery({
    queryKey: queryKeys.metrics.hourly,
    queryFn: () => api.metrics.getHourlyActivity(),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

/**
 * Sessions Hooks
 */
export function useSessions(filters?: { limit?: number; offset?: number; model?: string; status?: string }) {
  return useQuery({
    queryKey: queryKeys.sessions.list(filters),
    queryFn: () => api.sessions.listSessions(filters),
    staleTime: 1000 * 60 * 2, // 2 minutes (more frequent updates for sessions)
    gcTime: 1000 * 60 * 15,
    retry: 2,
  });
}

export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: sessionId ? queryKeys.sessions.detail(sessionId) : null,
    queryFn: () => (sessionId ? api.sessions.getSession(sessionId) : null),
    enabled: !!sessionId,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

export function useRecentSessions(limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.sessions.recent(limit),
    queryFn: () => api.sessions.getRecentSessions(limit),
    staleTime: 1000 * 60 * 2,
    gcTime: 1000 * 60 * 15,
    retry: 2,
  });
}

/**
 * Profile Hooks
 */
export function useUserProfile() {
  return useQuery({
    queryKey: queryKeys.profile.user,
    queryFn: () => api.profile.getUserProfile(),
    staleTime: 1000 * 60 * 30, // 30 minutes (profile doesn't change often)
    gcTime: 1000 * 60 * 60,
    retry: 2,
  });
}

export function useProfileDimensions() {
  return useQuery({
    queryKey: queryKeys.profile.dimensions,
    queryFn: () => api.profile.getProfileDimensions(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

export function useSkillBadges() {
  return useQuery({
    queryKey: queryKeys.profile.badges,
    queryFn: () => api.profile.getSkillBadges(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

export function useLanguageUsage() {
  return useQuery({
    queryKey: queryKeys.profile.languages,
    queryFn: () => api.profile.getLanguageUsage(),
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

/**
 * Insights Hooks
 */
export function useInsights(filters?: { category?: string; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.insights.list(filters),
    queryFn: () => api.insights.getInsights(filters),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

/**
 * Activity Hooks
 */
export function useActivityHeatmap() {
  return useQuery({
    queryKey: queryKeys.activity.heatmap,
    queryFn: () => api.activity.getActivityHeatmap(),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

export function useActivityTrends(days: number = 30) {
  return useQuery({
    queryKey: queryKeys.activity.trends(days),
    queryFn: () => api.activity.getActivityTrends(days),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    retry: 2,
  });
}

/**
 * Mutation Hooks
 */
export function useDismissInsight() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (insightId: string) => api.insights.dismissInsight(insightId),
    onSuccess: () => {
      // Invalidate insights query to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.insights.all });
    },
  });
}
