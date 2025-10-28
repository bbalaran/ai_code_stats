import { Sun, Moon, User, Settings, LogOut } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { useLocation } from 'react-router-dom';
import { useState } from 'react';
import { cn } from '../../lib/utils';
import { mockData } from '../../services/mockData';

/**
 * Page title mapping for different routes
 */
const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/profile': 'Profile',
  '/metrics': 'Metrics',
  '/insights': 'Insights',
  '/sessions': 'Sessions',
  '/live': 'Live Monitor',
  '/chat': 'Chat Assistant',
};

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const { pathname } = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const user = mockData.userProfile;

  // Get the page title based on current route
  const pageTitle = PAGE_TITLES[pathname] || 'Dashboard';

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b border-border bg-card px-6">
      {/* Breadcrumbs / Page Title */}
      <div className="flex-1">
        <h1 className="text-2xl font-semibold">{pageTitle}</h1>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Sun className="h-5 w-5" aria-hidden="true" />
          )}
        </button>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-lg p-2 hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label={`User menu for ${user.name}`}
            aria-expanded={dropdownOpen}
            aria-haspopup="menu"
          >
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-rose-pompadour to-thulian-pink flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user.name.split(' ').map(n => n[0]).join('')}
              </span>
            </div>
            <span className="text-sm font-medium hidden md:block">{user.name}</span>
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setDropdownOpen(false)}
                role="presentation"
              />
              <nav
                className="absolute right-0 mt-2 w-48 rounded-lg border border-border bg-card shadow-lg z-20"
                role="menu"
              >
                <div className="p-2">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      // Navigate to profile page
                      window.location.href = '/profile';
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
                    role="menuitem"
                  >
                    <User className="h-4 w-4" aria-hidden="true" />
                    Profile
                  </button>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      // Settings functionality can be added here
                      alert('Settings coming soon');
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
                    role="menuitem"
                  >
                    <Settings className="h-4 w-4" aria-hidden="true" />
                    Settings
                  </button>
                  <div className="my-1 h-px bg-border" role="separator" />
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      // Sign out functionality
                      alert('Sign out coming soon');
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
                    role="menuitem"
                  >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    Sign out
                  </button>
                </div>
              </nav>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
