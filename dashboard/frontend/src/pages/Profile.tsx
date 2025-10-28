import { mockData } from '../services/mockData';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import { Award, Calendar, Code, TrendingUp } from 'lucide-react';

export function Profile() {
  const user = mockData.userProfile;
  const dimensions = mockData.profileDimensions;
  const badges = mockData.skillBadges;
  const languages = mockData.languageUsage;
  const metrics = mockData.dashboardMetrics;

  const COLORS = ['#66A4E1', '#E47396', '#D77CA6', '#20B6F9', '#F36265', '#9CA3AF'];

  const joinDate = new Date(user.joinDate);
  const daysSinceJoin = Math.floor(
    (new Date().getTime() - joinDate.getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center gap-6">
          <div className="h-24 w-24 rounded-full bg-gradient-to-br from-rose-pompadour to-thulian-pink flex items-center justify-center">
            <span className="text-white text-4xl font-bold">
              {user.name.split(' ').map(n => n[0]).join('')}
            </span>
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{user.name}</h1>
            <p className="text-muted-foreground mt-1">{user.email}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Joined {joinDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
              </span>
              <span>•</span>
              <span>{daysSinceJoin} days active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Code className="h-4 w-4" />
            <span className="text-sm">Total Sessions</span>
          </div>
          <p className="text-2xl font-bold">{mockData.sessions.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <TrendingUp className="h-4 w-4" />
            <span className="text-sm">Acceptance Rate</span>
          </div>
          <p className="text-2xl font-bold">{metrics.acceptanceRate.toFixed(1)}%</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Code className="h-4 w-4" />
            <span className="text-sm">Lines Generated</span>
          </div>
          <p className="text-2xl font-bold">{metrics.linesOfCode.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Award className="h-4 w-4" />
            <span className="text-sm">Badges Earned</span>
          </div>
          <p className="text-2xl font-bold">{badges.filter(b => b.earned).length}/{badges.length}</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Proficiency Radar Chart */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">AI Engineering Proficiency</h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={dimensions}>
              <PolarGrid stroke="hsl(var(--border))" />
              <PolarAngleAxis
                dataKey="dimension"
                tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              />
              <Radar
                name="Proficiency"
                dataKey="score"
                stroke="#66A4E1"
                fill="#66A4E1"
                fillOpacity={0.6}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-muted-foreground">
            <p>Proficiency scores are calculated based on your AI-assisted development patterns, acceptance rates, and code quality metrics.</p>
          </div>
        </div>

        {/* Language Distribution */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Language Distribution</h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={languages as any}
                dataKey="percentage"
                nameKey="language"
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={({ language, percentage }) => `${language} ${percentage}%`}
              >
                {languages.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-2">
            {languages.map((lang, index) => (
              <div key={lang.language} className="flex items-center gap-2 text-sm">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-muted-foreground">
                  {lang.language}: {lang.sessionCount} sessions
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Skill Badges */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-4">Achievements</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {badges.map((badge) => (
            <div
              key={badge.id}
              className={`rounded-lg border p-4 transition-all ${
                badge.earned
                  ? 'border-picton-blue bg-picton-blue/10'
                  : 'border-border bg-muted/50 opacity-60'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`rounded-full p-2 ${
                  badge.earned ? 'bg-picton-blue/20' : 'bg-muted'
                }`}>
                  <Award className={`h-5 w-5 ${
                    badge.earned ? 'text-picton-blue' : 'text-muted-foreground'
                  }`} />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold">{badge.name}</h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    {badge.description}
                  </p>
                  {badge.earned && badge.earnedDate && (
                    <p className="text-xs text-picton-blue mt-2">
                      Earned {new Date(badge.earnedDate).toLocaleDateString()}
                    </p>
                  )}
                  {!badge.earned && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Not yet earned
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
