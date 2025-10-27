import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '../../lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon?: React.ReactNode;
  subtitle?: string;
}

export function MetricCard({ title, value, trend, icon, subtitle }: MetricCardProps) {
  const hasTrend = trend !== undefined && !isNaN(trend);
  const isPositive = trend && trend > 0;
  const isNegative = trend && trend < 0;

  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>

      <div className="mt-3">
        <p className="text-3xl font-bold">{value}</p>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </div>

      {hasTrend && (
        <div className="mt-3 flex items-center gap-1">
          {isPositive && <TrendingUp className="h-4 w-4 text-picton-blue" />}
          {isNegative && <TrendingDown className="h-4 w-4 text-bittersweet" />}
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
    </div>
  );
}
