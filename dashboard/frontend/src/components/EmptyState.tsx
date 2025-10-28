import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  /** Optional icon component from lucide-react */
  icon?: LucideIcon;
  /** Main title/heading for the empty state */
  title: string;
  /** Optional description text */
  description?: string;
  /**
   * Optional action button configuration
   * @property label - Button text
   * @property onClick - Click handler function
   */
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Empty State Component
 *
 * Displays a user-friendly message when no data is available.
 * Commonly used to indicate empty tables, lists, or search results.
 *
 * @example
 * ```tsx
 * <EmptyState
 *   icon={Database}
 *   title="No data found"
 *   description="Try adjusting your filters"
 *   action={{
 *     label: "Clear filters",
 *     onClick: () => setFilters({})
 *   }}
 * />
 * ```
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-6">
      {Icon && <Icon className="h-12 w-12 text-muted-foreground mb-4" />}
      <h3 className="text-lg font-semibold mb-2 text-center">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground text-center mb-4 max-w-sm">
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
