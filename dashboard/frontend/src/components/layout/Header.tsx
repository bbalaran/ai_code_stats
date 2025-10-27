import { Sun, Moon, User, Settings, LogOut } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { useState } from 'react';
import { cn } from '../../lib/utils';
import { mockData } from '../../services/mockData';

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const user = mockData.userProfile;

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b border-border bg-card px-6">
      {/* Breadcrumbs / Page Title */}
      <div className="flex-1">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 hover:bg-accent transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </button>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-lg p-2 hover:bg-accent transition-colors"
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
              />
              <div className="absolute right-0 mt-2 w-48 rounded-lg border border-border bg-card shadow-lg z-20">
                <div className="p-2">
                  <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent transition-colors">
                    <User className="h-4 w-4" />
                    Profile
                  </button>
                  <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent transition-colors">
                    <Settings className="h-4 w-4" />
                    Settings
                  </button>
                  <div className="my-1 h-px bg-border" />
                  <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-accent transition-colors">
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
