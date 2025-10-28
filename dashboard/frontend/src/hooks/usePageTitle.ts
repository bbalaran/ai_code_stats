import { useEffect } from 'react';

/**
 * Hook to dynamically set the page title
 *
 * Updates the browser's document title and returns the title information.
 * Automatically appends "AI Code Stats" to the page title.
 *
 * @param title - The main title to display in the browser tab
 * @param subtitle - Optional subtitle to append to the title with a dash separator
 * @returns Object containing the title and subtitle for reference
 *
 * @example
 * ```tsx
 * function Dashboard() {
 *   usePageTitle('Dashboard', 'Overview');
 *   // Browser tab will show: "Dashboard - Overview | AI Code Stats"
 *   return <div>...</div>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * function Profile() {
 *   usePageTitle('Profile');
 *   // Browser tab will show: "Profile | AI Code Stats"
 *   return <div>...</div>;
 * }
 * ```
 */
export function usePageTitle(title: string, subtitle?: string) {
  useEffect(() => {
    const fullTitle = subtitle ? `${title} - ${subtitle}` : title;
    document.title = `${fullTitle} | AI Code Stats`;
  }, [title, subtitle]);

  return { title, subtitle };
}
