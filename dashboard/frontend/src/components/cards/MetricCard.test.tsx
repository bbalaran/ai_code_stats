import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MetricCard } from './MetricCard';
import { Activity } from 'lucide-react';

describe('MetricCard', () => {
  it('renders the metric card with title and value', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="100"
        icon={<Activity className="h-5 w-5" />}
      />
    );

    expect(screen.getByText('Test Metric')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="100"
        subtitle="Additional info"
        icon={<Activity className="h-5 w-5" />}
      />
    );

    expect(screen.getByText('Additional info')).toBeInTheDocument();
  });

  it('renders trend indicator when trend is provided', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="100"
        trend={15}
        icon={<Activity className="h-5 w-5" />}
      />
    );

    const trendElement = screen.getByText(/15%/);
    expect(trendElement).toBeInTheDocument();
  });

  it('displays positive trend with correct styling', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="100"
        trend={15}
        icon={<Activity className="h-5 w-5" />}
      />
    );

    const trendElement = screen.getByText(/15%/);
    expect(trendElement).toHaveClass('text-picton-blue');
  });

  it('displays negative trend with correct styling', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="100"
        trend={-10}
        icon={<Activity className="h-5 w-5" />}
      />
    );

    const trendElement = screen.getByText(/-10%/);
    expect(trendElement).toHaveClass('text-bittersweet');
  });

  it('renders icon when provided', () => {
    const { container } = render(
      <MetricCard
        title="Test Metric"
        value="100"
        icon={<Activity className="h-5 w-5" data-testid="metric-icon" />}
      />
    );

    expect(container.querySelector('[data-testid="metric-icon"]')).toBeInTheDocument();
  });
});
