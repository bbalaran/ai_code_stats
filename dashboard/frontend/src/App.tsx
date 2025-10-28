import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './hooks/useTheme';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Profile } from './pages/Profile';
import { Metrics } from './pages/Metrics';
import { Insights } from './pages/Insights';
import { Sessions } from './pages/Sessions';
import { Chat } from './pages/Chat';
import { LiveMonitor } from './pages/LiveMonitor';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
              <Route path="profile" element={<ErrorBoundary><Profile /></ErrorBoundary>} />
              <Route path="metrics" element={<ErrorBoundary><Metrics /></ErrorBoundary>} />
              <Route path="insights" element={<ErrorBoundary><Insights /></ErrorBoundary>} />
              <Route path="sessions" element={<ErrorBoundary><Sessions /></ErrorBoundary>} />
              <Route path="live" element={<ErrorBoundary><LiveMonitor /></ErrorBoundary>} />
              <Route path="chat" element={<ErrorBoundary><Chat /></ErrorBoundary>} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
