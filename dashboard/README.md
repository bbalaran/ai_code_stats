# AI Coding Assistant Telemetry Dashboard

A modern, responsive Single Page Application for visualizing AI coding assistant telemetry and insights. Built with React, TypeScript, and Tailwind CSS.

## Features

### Implemented (Phase 1)
✅ **Modern Tech Stack**: React 18 + TypeScript + Vite
✅ **Responsive Layout**: Sidebar navigation, header with user dropdown
✅ **Dark/Light Theme**: Toggle between themes with persistence
✅ **Dashboard Home**: Metric cards, activity charts, recent sessions
✅ **Mock Data Service**: 30 days of realistic telemetry data
✅ **Custom Color Palette**: Professional color scheme with dark mode support

### In Progress
🔧 **AI Engineer Profile**: Radar chart showing proficiency dimensions
🔧 **Metrics Dashboard**: Tabbed views for Productivity, Quality, Usage, Learning
🔧 **Insights Feed**: AI-generated actionable recommendations
🔧 **Session History**: Searchable table with detailed session views
🔧 **Chat Interface**: Natural language queries about metrics

## Quick Start

```bash
# Install dependencies
cd dashboard/frontend
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The app will be available at [http://localhost:5173](http://localhost:5173)

## Project Structure

```
dashboard/frontend/
├── src/
│   ├── components/
│   │   ├── layout/         # Sidebar, Header, Layout
│   │   ├── cards/          # MetricCard, InsightCard
│   │   ├── charts/         # Chart wrappers (planned)
│   │   └── ui/             # Reusable UI components
│   ├── pages/              # Dashboard, Profile, Metrics, etc.
│   ├── services/
│   │   └── mockData.ts     # Mock telemetry data generator
│   ├── types/              # TypeScript definitions
│   ├── hooks/              # useTheme, custom hooks
│   ├── lib/                # Utility functions
│   └── theme/              # Theme configuration
├── public/
└── package.json
```

## Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom theme
- **Charts**: Recharts
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Color Palette

### Light Mode
- **Primary**: #66A4E1 (ruddy-blue) - Interactive elements
- **Error/Alert**: #F36265 (bittersweet) - Negative trends
- **Secondary**: #E47396 (rose-pompadour) - Highlights
- **Tertiary**: #D77CA6 (thulian-pink) - Tags
- **Success**: #20B6F9 (picton-blue) - Positive trends

### Dark Mode
Automatically adjusted versions maintaining contrast and semantic meaning.

## Dashboard Features

### Metric Cards
- Total AI Sessions (with week-over-week trend)
- Lines of Code Generated (with trend)
- Average Acceptance Rate (with trend)
- Token Usage & Estimated Cost (with trend)

### Activity Visualization
- 30-day activity trend line chart
- Peak activity hours bar chart
- Recent sessions list with quick stats

### Navigation
- Dashboard: Overview and key metrics
- Profile: Engineer profile with skill radar
- Metrics: Detailed analytics with tabs
- Insights: AI-generated recommendations
- Sessions: Full session history
- Chat: Natural language query interface

## Mock Data

The app includes a comprehensive mock data generator that simulates:
- 150 sessions over 30 days
- Multiple models (Sonnet, Haiku, Opus)
- Varied acceptance rates and token usage
- Realistic cost calculations
- Different task types and languages
- Error scenarios (5% error rate)

## Development

### Adding New Pages
1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/layout/Sidebar.tsx`

### Customizing Theme
Edit `tailwind.config.js` and `src/index.css` to adjust colors and styling.

### Data Integration
To connect to real ProdLens backend:
1. Create API client in `src/services/api.ts`
2. Replace mock data calls with API calls
3. Add React Query for caching and state management

## Next Steps

1. **Profile Page**: Implement radar chart with proficiency dimensions
2. **Metrics Page**: Add tabbed views with various chart types
3. **Insights Page**: Card-based feed with filtering
4. **Sessions Page**: Data table with search, sort, and filters
5. **Chat Interface**: Natural language query system
6. **Backend Integration**: Connect to ProdLens Python backend

## Contributing

This is part of the ProdLens AI observability project. See main project README for contribution guidelines.

## License

See main project for license information.
