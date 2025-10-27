import { useState, useMemo } from 'react';
import { mockData } from '../services/mockData';
import { Search, Filter, ChevronDown, ChevronUp, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import type { Session } from '../types';

export function Sessions() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModel, setSelectedModel] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortField, setSortField] = useState<keyof Session>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const allModels = ['all', ...Array.from(new Set(mockData.sessions.map(s => s.model).filter(Boolean)))];

  const filteredAndSortedSessions = useMemo(() => {
    let filtered = mockData.sessions.filter(session => {
      const matchesSearch =
        session.session_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        session.model?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesModel = selectedModel === 'all' || session.model === selectedModel;
      const matchesStatus =
        selectedStatus === 'all' ||
        (selectedStatus === 'success' && session.status_code === 200) ||
        (selectedStatus === 'error' && session.status_code !== 200);

      return matchesSearch && matchesModel && matchesStatus;
    });

    filtered.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      const direction = sortDirection === 'asc' ? 1 : -1;

      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (aVal < bVal) return -1 * direction;
      if (aVal > bVal) return 1 * direction;
      return 0;
    });

    return filtered;
  }, [searchTerm, selectedModel, selectedStatus, sortField, sortDirection]);

  const totalPages = Math.ceil(filteredAndSortedSessions.length / itemsPerPage);
  const paginatedSessions = filteredAndSortedSessions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSort = (field: keyof Session) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Session History</h1>
        <p className="text-muted-foreground mt-2">
          Complete history of all AI-assisted coding sessions
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by session ID or model..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {allModels.map(model => (
            <option key={model} value={model}>
              {model === 'all' ? 'All Models' : model}
            </option>
          ))}
        </select>
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">All Status</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-muted-foreground">
        Showing {paginatedSessions.length} of {filteredAndSortedSessions.length} sessions
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left p-4 text-sm font-medium">
                  <button
                    onClick={() => handleSort('session_id')}
                    className="flex items-center gap-1 hover:text-foreground"
                  >
                    Session ID
                    {sortField === 'session_id' && (
                      sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                    )}
                  </button>
                </th>
                <th className="text-left p-4 text-sm font-medium">
                  <button
                    onClick={() => handleSort('timestamp')}
                    className="flex items-center gap-1 hover:text-foreground"
                  >
                    Timestamp
                    {sortField === 'timestamp' && (
                      sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                    )}
                  </button>
                </th>
                <th className="text-left p-4 text-sm font-medium">Model</th>
                <th className="text-right p-4 text-sm font-medium">
                  <button
                    onClick={() => handleSort('total_tokens')}
                    className="flex items-center gap-1 hover:text-foreground ml-auto"
                  >
                    Tokens
                    {sortField === 'total_tokens' && (
                      sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                    )}
                  </button>
                </th>
                <th className="text-right p-4 text-sm font-medium">
                  <button
                    onClick={() => handleSort('latency_ms')}
                    className="flex items-center gap-1 hover:text-foreground ml-auto"
                  >
                    Duration
                    {sortField === 'latency_ms' && (
                      sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                    )}
                  </button>
                </th>
                <th className="text-center p-4 text-sm font-medium">Status</th>
                <th className="text-center p-4 text-sm font-medium">Accepted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {paginatedSessions.map(session => (
                <tr key={session.id} className="hover:bg-accent/50 transition-colors">
                  <td className="p-4 text-sm font-mono text-muted-foreground">
                    {session.session_id?.substring(0, 12)}...
                  </td>
                  <td className="p-4 text-sm">
                    {format(new Date(session.timestamp), 'MMM d, yyyy h:mm a')}
                  </td>
                  <td className="p-4 text-sm">
                    <span className="px-2 py-1 rounded-full bg-ruddy-blue/10 text-ruddy-blue text-xs">
                      {session.model?.split('-').pop() || 'unknown'}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-right font-mono">
                    {session.total_tokens.toLocaleString()}
                  </td>
                  <td className="p-4 text-sm text-right">
                    {(session.latency_ms / 1000).toFixed(2)}s
                  </td>
                  <td className="p-4 text-center">
                    {session.status_code === 200 ? (
                      <span className="inline-block px-2 py-1 rounded-full bg-picton-blue/10 text-picton-blue text-xs">
                        Success
                      </span>
                    ) : (
                      <span className="inline-block px-2 py-1 rounded-full bg-bittersweet/10 text-bittersweet text-xs">
                        Error
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    {session.accepted_flag ? (
                      <span className="text-picton-blue">✓</span>
                    ) : (
                      <span className="text-muted-foreground">−</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 rounded-lg border border-border bg-card hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 rounded-lg border border-border bg-card hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
