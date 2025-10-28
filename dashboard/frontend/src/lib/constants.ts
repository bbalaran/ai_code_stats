/**
 * Application Constants
 *
 * Centralized location for magic numbers and configuration values
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws/sessions',
  TIMEOUT_MS: 5000,
} as const;

// React Query Cache Configuration
export const REACT_QUERY_CONFIG = {
  STALE_TIME_MS: {
    METRICS: 1000 * 60 * 5, // 5 minutes
    PROFILE: 1000 * 60 * 30, // 30 minutes
    SESSIONS: 1000 * 60 * 2, // 2 minutes
    INSIGHTS: 1000 * 60 * 5, // 5 minutes
    ACTIVITY: 1000 * 60 * 5, // 5 minutes
  },
  GC_TIME_MS: {
    DEFAULT: 1000 * 60 * 30, // 30 minutes
    SHORT: 1000 * 60 * 15, // 15 minutes
  },
  RETRY_ATTEMPTS: 2,
} as const;

// Chart and Visualization
export const CHART_CONFIG = {
  COLORS: {
    PRIMARY: '#66A4E1', // ruddy-blue
    SUCCESS: '#20B6F9', // picton-blue
    SECONDARY: '#E47396', // rose-pompadour
    TERTIARY: '#D77CA6', // thulian-pink
    ERROR: '#F36265', // bittersweet
    CUSTOM_PALETTE: ['#66A4E1', '#E47396', '#D77CA6', '#20B6F9', '#F36265', '#9CA3AF'],
  },
  HEIGHT: {
    LINE_CHART: 300,
    BAR_CHART: 300,
    HEATMAP: 250,
  },
  ANIMATION_DURATION: 200, // ms
} as const;

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;

// Date/Time Formatting
export const DATE_FORMAT = {
  FULL: 'MMM d, yyyy h:mm a',
  DATE_ONLY: 'MMM d, yyyy',
  TIME_ONLY: 'h:mm a',
  SHORT_DATE: 'MMM d',
  ISO: "yyyy-MM-dd'T'HH:mm:ss",
} as const;

// Time Windows (in days)
export const TIME_WINDOWS = {
  WEEK: 7,
  MONTH: 30,
  QUARTER: 90,
  YEAR: 365,
} as const;

// Chat Configuration
export const CHAT_CONFIG = {
  MESSAGE_DELAY_MS: {
    MIN: 1000,
    MAX: 2000,
  },
  MAX_MESSAGE_LENGTH: 10000,
  INITIAL_MESSAGE_ID: 0,
} as const;

// Component Sizing
export const COMPONENT_SIZES = {
  ICON_SM: 'h-4 w-4',
  ICON_MD: 'h-5 w-5',
  ICON_LG: 'h-6 w-6',
  AVATAR_SM: 'h-8 w-8',
  AVATAR_MD: 'h-10 w-10',
  AVATAR_LG: 'h-12 w-12',
} as const;

// Session Status Codes
export const SESSION_STATUS = {
  SUCCESS: 200,
  ERROR: 500,
} as const;

// Time Thresholds (in milliseconds)
export const TIME_THRESHOLDS = {
  FAST: 1000, // 1 second
  MODERATE: 5000, // 5 seconds
  SLOW: 10000, // 10 seconds
} as const;

// Default Limits
export const DEFAULTS = {
  RECENT_SESSIONS_LIMIT: 10,
  INSIGHTS_LIMIT: 10,
  ACTIVITY_HOURS: 24,
  HEATMAP_DAYS: 7,
} as const;

// Accessibility
export const A11Y = {
  FOCUS_RING: 'focus:outline-none focus:ring-2 focus:ring-primary',
  SKIP_LINK: 'sr-only focus:not-sr-only',
} as const;
