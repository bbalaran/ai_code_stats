import { useState } from 'react';
import { mockData } from '../services/mockData';
import { AlertCircle, TrendingUp, DollarSign, Lightbulb, X, ChevronRight, Filter } from 'lucide-react';
import type { Insight } from '../types';

const categoryIcons = {
  efficiency: TrendingUp,
  quality: AlertCircle,
  cost: DollarSign,
  learning: Lightbulb,
};

const categoryColors = {
  efficiency: 'text-picton-blue bg-picton-blue/10 border-picton-blue',
  quality: 'text-bittersweet bg-bittersweet/10 border-bittersweet',
  cost: 'text-rose-pompadour bg-rose-pompadour/10 border-rose-pompadour',
  learning: 'text-thulian-pink bg-thulian-pink/10 border-thulian-pink',
};

const impactColors = {
  high: 'bg-bittersweet text-white',
  medium: 'bg-rose-pompadour text-white',
  low: 'bg-muted text-foreground',
};

export function Insights() {
  const [insights, setInsights] = useState<Insight[]>(mockData.insights);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredInsights = selectedCategory
    ? insights.filter(i => i.category === selectedCategory)
    : insights;

  const categories = [
    { id: 'all', label: 'All Insights', count: insights.length },
    { id: 'efficiency', label: 'Efficiency', count: insights.filter(i => i.category === 'efficiency').length },
    { id: 'quality', label: 'Quality', count: insights.filter(i => i.category === 'quality').length },
    { id: 'cost', label: 'Cost', count: insights.filter(i => i.category === 'cost').length },
    { id: 'learning', label: 'Learning', count: insights.filter(i => i.category === 'learning').length },
  ];

  const handleDismiss = (id: string) => {
    setInsights(insights.filter(i => i.id !== id));
  };

  const getRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">AI Insights</h1>
        <p className="text-muted-foreground mt-2">
          Actionable recommendations to improve your AI-assisted development workflow
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border overflow-x-auto">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id === 'all' ? null : cat.id)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors whitespace-nowrap ${
              (cat.id === 'all' && selectedCategory === null) || selectedCategory === cat.id
                ? 'border-primary text-primary font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Filter className="h-4 w-4" />
            {cat.label}
            <span className="text-xs px-2 py-0.5 rounded-full bg-muted">
              {cat.count}
            </span>
          </button>
        ))}
      </div>

      {/* Insights Grid */}
      <div className="grid gap-4">
        {filteredInsights.length === 0 ? (
          <div className="rounded-lg border border-border bg-card p-12 text-center">
            <Lightbulb className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No insights available</h3>
            <p className="text-muted-foreground">
              {selectedCategory ? 'Try selecting a different category' : 'Check back later for new insights'}
            </p>
          </div>
        ) : (
          filteredInsights.map(insight => {
            const CategoryIcon = categoryIcons[insight.category];
            return (
              <div
                key={insight.id}
                className="rounded-lg border border-border bg-card p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className={`rounded-lg p-3 border ${categoryColors[insight.category]}`}>
                    <CategoryIcon className="h-5 w-5" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-lg font-semibold">{insight.title}</h3>
                          <span className={`text-xs px-2 py-1 rounded-full ${impactColors[insight.impact]}`}>
                            {insight.impact} impact
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground capitalize">
                          {insight.category} • {getRelativeTime(insight.timestamp)}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDismiss(insight.id)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label="Dismiss insight"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>

                    <p className="text-foreground mb-4">{insight.description}</p>

                    {/* Actions */}
                    <div className="flex items-center gap-3">
                      {insight.actionable && (
                        <button className="flex items-center gap-1 text-sm text-primary hover:underline">
                          Take Action
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      )}
                      <button className="text-sm text-muted-foreground hover:text-foreground">
                        Learn More
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Summary Stats */}
      {filteredInsights.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Insight Summary</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Total Insights</p>
              <p className="text-2xl font-bold">{filteredInsights.length}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Actionable</p>
              <p className="text-2xl font-bold">
                {filteredInsights.filter(i => i.actionable).length}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">High Impact</p>
              <p className="text-2xl font-bold">
                {filteredInsights.filter(i => i.impact === 'high').length}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
