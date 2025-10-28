import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '../../lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon?: React.ReactNode;
  subtitle?: string;
}

/**
 * Metric Card Component
 *
 * Displays a single metric with optional trend indicator.
 * Accessible with proper ARIA labels and semantic HTML.
 */
export function MetricCard({ title, value, trend, icon, subtitle }: MetricCardProps) {
  const hasTrend = trend !== undefined && !isNaN(trend);
  const isPositive = trend && trend > 0;
  const isNegative = trend && trend < 0;
  const trendLabel = hasTrend
    ? `${isPositive ? 'Up' : isNegative ? 'Down' : 'No change'} ${Math.abs(trend || 0).toFixed(1)}% compared to last week`
    : '';

  return (
    <article
      className="rounded-lg border border-border bg-card p-6 shadow-sm"
      aria-label={title}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        {icon && <div className="text-muted-foreground" aria-hidden="true">{icon}</div>}
      </div>

      <div className="mt-3">
        <p className="text-3xl font-bold" role="status" aria-live="polite">
          {value}
        </p>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1" role="doc-subtitle">
            {subtitle}
          </p>
        )}
      </div>

      {hasTrend && (
        <div className="mt-3 flex items-center gap-1" aria-label={trendLabel}>
          {isPositive && (
            <TrendingUp
              className="h-4 w-4 text-picton-blue"
              aria-hidden="true"
            />
          )}
          {isNegative && (
            <TrendingDown
              className="h-4 w-4 text-bittersweet"
              aria-hidden="true"
            />
          )}
          <span
            className={cn(
              'text-sm font-medium',
              isPositive && 'text-picton-blue',
              isNegative && 'text-bittersweet'
            )}
          >
            {isPositive && '+'}{Math.abs(trend).toFixed(1)}%
          </span>
          <span className="text-sm text-muted-foreground">vs last week</span>
        </div>
      )}
    </article>
  );
}
