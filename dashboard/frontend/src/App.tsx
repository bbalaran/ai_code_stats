import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './hooks/useTheme';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Profile } from './pages/Profile';
import { Metrics } from './pages/Metrics';
import { Insights } from './pages/Insights';
import { Sessions } from './pages/Sessions';
import { Chat } from './pages/Chat';

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="profile" element={<Profile />} />
            <Route path="metrics" element={<Metrics />} />
            <Route path="insights" element={<Insights />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="chat" element={<Chat />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
