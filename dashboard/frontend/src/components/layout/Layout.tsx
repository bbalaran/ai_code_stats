import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

/**
 * Layout Component
 *
 * Main layout wrapper providing the page structure with sidebar and header.
 * Uses React Router's Outlet to render page content.
 *
 * Layout structure:
 * ```
 * ┌─────────────────────────────┐
 * │         Header              │
 * ├──────────┬──────────────────┤
 * │          │                  │
 * │ Sidebar  │   Page Content   │
 * │          │   (Outlet)       │
 * │          │                  │
 * └──────────┴──────────────────┘
 * ```
 *
 * @example
 * ```tsx
 * <Layout>
 *   {/* Pages render here via Outlet */}
 * </Layout>
 * ```
 */
export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
