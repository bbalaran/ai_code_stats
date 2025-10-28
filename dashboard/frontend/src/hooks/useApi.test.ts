import { describe, it, expect } from 'vitest';
import { queryKeys } from './useApi';

describe('useApi - Query Keys', () => {
  it('creates correct metric query keys', () => {
    expect(queryKeys.metrics.all).toEqual(['metrics']);
    expect(queryKeys.metrics.overview).toEqual(['metrics', 'overview']);
    expect(queryKeys.metrics.timeseries(30)).toEqual(['metrics', 'timeseries', 30]);
    expect(queryKeys.metrics.hourly).toEqual(['metrics', 'hourly']);
  });

  it('creates correct session query keys', () => {
    expect(queryKeys.sessions.all).toEqual(['sessions']);
    expect(queryKeys.sessions.list()).toEqual(['sessions', 'list', undefined]);
    expect(queryKeys.sessions.list({ limit: 10 })).toEqual([
      'sessions',
      'list',
      { limit: 10 },
    ]);
    expect(queryKeys.sessions.detail('123')).toEqual([
      'sessions',
      'detail',
      '123',
    ]);
    expect(queryKeys.sessions.recent(10)).toEqual(['sessions', 'recent', 10]);
  });

  it('creates correct profile query keys', () => {
    expect(queryKeys.profile.all).toEqual(['profile']);
    expect(queryKeys.profile.user).toEqual(['profile', 'user']);
    expect(queryKeys.profile.dimensions).toEqual(['profile', 'dimensions']);
    expect(queryKeys.profile.badges).toEqual(['profile', 'badges']);
    expect(queryKeys.profile.languages).toEqual(['profile', 'languages']);
  });

  it('creates correct insight query keys', () => {
    expect(queryKeys.insights.all).toEqual(['insights']);
    expect(queryKeys.insights.list()).toEqual(['insights', 'list', undefined]);
    expect(queryKeys.insights.list({ category: 'efficiency' })).toEqual([
      'insights',
      'list',
      { category: 'efficiency' },
    ]);
  });

  it('creates correct activity query keys', () => {
    expect(queryKeys.activity.all).toEqual(['activity']);
    expect(queryKeys.activity.heatmap).toEqual(['activity', 'heatmap']);
    expect(queryKeys.activity.trends(30)).toEqual(['activity', 'trends', 30]);
  });

  it('handles typed filter objects correctly', () => {
    const sessionFilters = { limit: 20, offset: 0, model: 'claude-3-sonnet' };
    const result = queryKeys.sessions.list(sessionFilters);

    expect(result[0]).toBe('sessions');
    expect(result[1]).toBe('list');
    expect(result[2]).toEqual(sessionFilters);
  });
});
