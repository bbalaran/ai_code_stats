/**
 * API Integration Layer
 *
 * This service provides a centralized interface for all API calls to the backend.
 * Currently using mock data, but can be easily switched to real API endpoints.
 */

import { mockData } from './mockData';
import type { Session, DashboardMetrics, Insight, UserProfile, ProfileDimension, SkillBadge, LanguageUsage } from '../types';

// Define ActivityHeatmap type for API
interface ActivityHeatmap {
  day: number;
  hour: number;
  value: number;
}

// API Base URL - configure this based on environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Fetch with error handling and timeout
 */
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Metrics API
 */
export const metricsAPI = {
  /**
   * Get dashboard overview metrics
   */
  async getOverviewMetrics(): Promise<DashboardMetrics> {
    try {
      // Try to fetch from API
      const response = await fetchWithTimeout(`${API_BASE_URL}/metrics/overview`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch overview metrics from API, using mock data:', error);
      return mockData.dashboardMetrics;
    }
  },

  /**
   * Get time-series data for charts
   */
  async getTimeSeriesData(days: number = 30): Promise<Array<{ date: string; value: number }>> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/metrics/timeseries?days=${days}`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch time-series data from API, using mock data:', error);
      return mockData.metricTrends;
    }
  },

  /**
   * Get hourly activity data
   */
  async getHourlyActivity(): Promise<Array<{ hour: number; sessions: number }>> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/metrics/hourly`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch hourly activity from API, using mock data:', error);
      // Generate hourly data from activity heatmap
      const hourlyMap = new Map<number, number>();
      for (let hour = 0; hour < 24; hour++) {
        hourlyMap.set(hour, Math.floor(Math.random() * 20) + 5);
      }
      return Array.from(hourlyMap, ([hour, sessions]) => ({ hour, sessions }));
    }
  },
};

/**
 * Sessions API
 */
export const sessionsAPI = {
  /**
   * Get list of sessions with optional filters
   */
  async listSessions(filters?: {
    limit?: number;
    offset?: number;
    model?: string;
    status?: string;
  }): Promise<Session[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.limit) params.append('limit', filters.limit.toString());
      if (filters?.offset) params.append('offset', filters.offset.toString());
      if (filters?.model) params.append('model', filters.model);
      if (filters?.status) params.append('status', filters.status);

      const response = await fetchWithTimeout(
        `${API_BASE_URL}/sessions${params.toString() ? `?${params.toString()}` : ''}`
      );
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch sessions from API, using mock data:', error);
      return mockData.sessions;
    }
  },

  /**
   * Get detailed information about a specific session
   */
  async getSession(sessionId: string): Promise<Session | null> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/sessions/${sessionId}`);
      return response.json();
    } catch (error) {
      console.warn(`Failed to fetch session ${sessionId} from API:`, error);
      return mockData.sessions.find((s: Session) => s.session_id === sessionId) || null;
    }
  },

  /**
   * Get recent sessions
   */
  async getRecentSessions(limit: number = 10): Promise<Session[]> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/sessions?limit=${limit}&sort=timestamp&order=desc`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch recent sessions from API, using mock data:', error);
      return mockData.sessions.slice(0, limit);
    }
  },
};

/**
 * Profile API
 */
export const profileAPI = {
  /**
   * Get current user profile
   */
  async getUserProfile(): Promise<UserProfile> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/profile`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch user profile from API, using mock data:', error);
      return mockData.userProfile;
    }
  },

  /**
   * Get proficiency dimensions
   */
  async getProfileDimensions(): Promise<ProfileDimension[]> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/profile/dimensions`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch profile dimensions from API, using mock data:', error);
      return mockData.profileDimensions;
    }
  },

  /**
   * Get skill badges
   */
  async getSkillBadges(): Promise<SkillBadge[]> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/profile/badges`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch skill badges from API, using mock data:', error);
      return mockData.skillBadges;
    }
  },

  /**
   * Get language usage data
   */
  async getLanguageUsage(): Promise<LanguageUsage[]> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/profile/languages`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch language usage from API, using mock data:', error);
      return mockData.languageUsage;
    }
  },
};

/**
 * Insights API
 */
export const insightsAPI = {
  /**
   * Get insights with optional filtering
   */
  async getInsights(filters?: {
    category?: string;
    limit?: number;
  }): Promise<Insight[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.category) params.append('category', filters.category);
      if (filters?.limit) params.append('limit', filters.limit.toString());

      const response = await fetchWithTimeout(
        `${API_BASE_URL}/insights${params.toString() ? `?${params.toString()}` : ''}`
      );
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch insights from API, using mock data:', error);
      return mockData.insights;
    }
  },

  /**
   * Dismiss an insight
   */
  async dismissInsight(insightId: string): Promise<boolean> {
    try {
      await fetchWithTimeout(`${API_BASE_URL}/insights/${insightId}/dismiss`, {
        method: 'POST',
      });
      return true;
    } catch (error) {
      console.warn(`Failed to dismiss insight ${insightId}:`, error);
      return false;
    }
  },
};

/**
 * Activity API
 */
export const activityAPI = {
  /**
   * Get activity heatmap data
   */
  async getActivityHeatmap(): Promise<ActivityHeatmap[]> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/activity/heatmap`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch activity heatmap from API, using mock data:', error);
      return mockData.activityHeatmap;
    }
  },

  /**
   * Get activity trends over time
   */
  async getActivityTrends(days: number = 30): Promise<Array<{ date: string; value: number }>> {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/activity/trends?days=${days}`);
      return response.json();
    } catch (error) {
      console.warn('Failed to fetch activity trends from API, using mock data:', error);
      return mockData.metricTrends;
    }
  },
};

/**
 * Real-time API (WebSocket)
 */
export const realtimeAPI = {
  /**
   * Connect to WebSocket for real-time session updates
   * Returns WebSocket connection that can be used to listen to events
   */
  connectToSessionStream(callbacks: {
    onSessionStarted?: (session: Session) => void;
    onSessionCompleted?: (session: Session) => void;
    onError?: (error: string) => void;
    onConnectionEstablished?: () => void;
  }): WebSocket | null {
    try {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws/sessions';
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Connected to WebSocket');
        callbacks.onConnectionEstablished?.();
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'session_started') {
          callbacks.onSessionStarted?.(message.data);
        } else if (message.type === 'session_completed') {
          callbacks.onSessionCompleted?.(message.data);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        callbacks.onError?.('WebSocket connection error');
      };

      return ws;
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      callbacks.onError?.('Failed to establish WebSocket connection');
      return null;
    }
  },
};

/**
 * Export all API modules
 */
export const api = {
  metrics: metricsAPI,
  sessions: sessionsAPI,
  profile: profileAPI,
  insights: insightsAPI,
  activity: activityAPI,
  realtime: realtimeAPI,
};

export default api;
