# Testing Guide - ProdLens Dashboard

## Overview

This document provides a comprehensive testing guide for the ProdLens Dashboard frontend. It covers manual testing procedures, automated testing setup, and verification checklists.

## Phase 3 Implementation Testing

### Features Implemented

- ✅ Dashboard Homepage (overview metrics, charts, recent sessions)
- ✅ Profile Page (radar chart, skill badges, language distribution)
- ✅ Metrics Dashboard (tabbed interface with multiple analytics)
- ✅ Insights Feed (card-based feed with filtering)
- ✅ Sessions Explorer (data table with search, filtering, pagination)
- ✅ Live Monitoring (real-time session tracking)
- ✅ Chat Interface (AI assistant for data queries)
- ✅ API Integration Layer (with React Query caching)
- ✅ Responsive Design (mobile, tablet, desktop optimized)
- ✅ Dark/Light Theme Toggle (persistent with system preference detection)

## Manual Testing Procedures

### 1. Application Launch

```bash
# Navigate to frontend directory
cd dashboard/frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# The application should be available at http://localhost:5173
```

**Verification Checklist:**
- [ ] App loads without errors
- [ ] No console errors or warnings
- [ ] Theme matches system preference or saved preference
- [ ] All UI elements are visible and properly styled

### 2. Navigation & Routing

Test all navigation items in the sidebar:

```
√ Dashboard (/)
√ Profile (/profile)
√ Metrics (/metrics)
√ Insights (/insights)
√ Sessions (/sessions)
√ Live (/live)
√ Chat (/chat)
```

**Verification Checklist:**
- [ ] Clicking each nav item navigates to correct page
- [ ] Active nav item is highlighted with primary color
- [ ] URL changes appropriately
- [ ] Back button works correctly
- [ ] Page content updates without full page reload

### 3. Theme Functionality

**Light Mode Testing:**

```bash
1. Click theme toggle (sun icon in header)
2. Verify page switches to light mode
3. Check colors match light palette:
   - Background: light gray
   - Cards: white
   - Text: dark gray/black
4. Reload page - light mode should persist
```

**Dark Mode Testing:**

```bash
1. Click theme toggle (moon icon in header)
2. Verify page switches to dark mode
3. Check colors match dark palette:
   - Background: dark gray/black
   - Cards: darker shade
   - Text: light gray/white
4. Reload page - dark mode should persist
```

**System Preference Testing:**

```bash
1. Clear localStorage
2. Change system theme (System Settings)
3. Open application in incognito window
4. Verify app matches system theme
```

**Verification Checklist:**
- [ ] Theme toggle switches dark/light mode
- [ ] All colors update appropriately
- [ ] Text contrast is readable in both themes
- [ ] Charts colors adapt to theme
- [ ] Preference persists on page reload
- [ ] System preference is detected initially

### 4. Dashboard Page Testing

**Metric Cards:**
- [ ] 4 metric cards display with correct values
- [ ] Cards show trends (up/down arrow with percentage)
- [ ] Values are formatted correctly (commas for thousands)
- [ ] Hover effect appears on cards
- [ ] Card colors are from custom palette

**Activity Trend Chart:**
- [ ] 30-day line chart renders correctly
- [ ] X-axis shows dates
- [ ] Y-axis shows session count
- [ ] Tooltip appears on hover
- [ ] Chart responsive to window resize

**Peak Hours Chart:**
- [ ] Bar chart displays 24-hour data
- [ ] X-axis shows hours (0-23)
- [ ] Y-axis shows session count
- [ ] Colors alternate between two shades
- [ ] Hover shows exact values

**Recent Sessions List:**
- [ ] Shows last 10 sessions
- [ ] Displays: timestamp, model, duration, tokens, acceptance rate
- [ ] Hover effect highlights rows
- [ ] Session data is formatted correctly
- [ ] Scrollable if content exceeds height

**Verification Checklist:**
- [ ] All four sections load without errors
- [ ] Data is from mock data service
- [ ] Charts render with correct library (Recharts)
- [ ] Responsive layout on different screen sizes
- [ ] Page loads in under 2 seconds

### 5. Profile Page Testing

**Profile Header:**
- [ ] User avatar displays with initials
- [ ] User name and email shown
- [ ] Join date calculated correctly
- [ ] Days active counter is accurate

**Statistics Cards:**
- [ ] Total sessions count is correct
- [ ] Acceptance rate calculated correctly
- [ ] Lines of code displayed
- [ ] Badge count matches earned badges

**Proficiency Radar Chart:**
- [ ] 6-point radar chart renders
- [ ] All dimensions labeled (e.g., "Prompt Engineering", "Model Selection")
- [ ] Score ranges from 0-100
- [ ] Chart fills appropriately
- [ ] Tooltip shows exact scores

**Language Distribution Pie Chart:**
- [ ] Pie chart shows all languages
- [ ] Percentages add up to 100%
- [ ] Labels show language name and percentage
- [ ] Colors match custom palette
- [ ] Legend shows session count

**Skill Badges:**
- [ ] Earned badges highlighted with blue
- [ ] Unearned badges grayed out
- [ ] Badge icons display
- [ ] Badge names and descriptions readable
- [ ] Earned dates shown for earned badges

**Verification Checklist:**
- [ ] All sections load correctly
- [ ] Data matches mock data
- [ ] Charts render properly
- [ ] Responsive on mobile devices
- [ ] No layout overflow

### 6. Metrics Dashboard Testing

**Tab Navigation:**
- [ ] 4 tabs visible: Productivity, Quality, Usage Patterns, Learning & Growth
- [ ] Clicking tab switches content
- [ ] Active tab is highlighted
- [ ] Tab icons display correctly

**Productivity Tab:**
- [ ] Shows productivity-related charts
- [ ] Code speed metrics displayed
- [ ] Task completion time chart

**Quality Tab:**
- [ ] Shows quality metrics
- [ ] Acceptance rate trends
- [ ] Error rate analysis

**Usage Tab:**
- [ ] Shows usage patterns
- [ ] Model distribution chart
- [ ] Token usage trends

**Learning Tab:**
- [ ] Shows learning metrics
- [ ] Skill progression data
- [ ] Growth indicators

**Verification Checklist:**
- [ ] All tabs load without errors
- [ ] Charts are properly formatted
- [ ] Data is realistic
- [ ] Tab switching is smooth
- [ ] No missing data

### 7. Insights Page Testing

**Insight Cards:**
- [ ] Multiple insight cards display
- [ ] Each card has icon, title, description
- [ ] Impact badges show (high/medium/low)
- [ ] Category colors are distinct

**Category Filtering:**
- [ ] "All Insights" shows all cards
- [ ] Filtering by category works correctly
- [ ] Category counts update
- [ ] No insights lost during filtering

**Insight Actions:**
- [ ] "Dismiss" button removes insight
- [ ] Dismissed insights don't reappear
- [ ] "Learn More" links work (if implemented)

**Verification Checklist:**
- [ ] All insights display correctly
- [ ] Filtering works as expected
- [ ] Dismiss action updates UI
- [ ] Card styling is consistent
- [ ] Icons are clear and recognizable

### 8. Sessions Page Testing

**Search & Filtering:**
- [ ] Search by session ID works
- [ ] Search by model name works
- [ ] Model dropdown filters correctly
- [ ] Status filter (Success/Error) works
- [ ] Multiple filters combined work

**Data Table:**
- [ ] All columns visible on desktop
- [ ] Table scrolls horizontally on mobile
- [ ] Column headers are sortable
- [ ] Sort arrow indicates direction
- [ ] Data types are formatted correctly:
  - Timestamps in readable format
  - Model names abbreviated
  - Token counts with commas
  - Duration in seconds with decimals
  - Status as colored badges

**Pagination:**
- [ ] Shows 20 items per page
- [ ] Previous/Next buttons work
- [ ] Page indicator displays correctly
- [ ] Pagination hidden if < 20 items
- [ ] Page resets on filter change

**Verification Checklist:**
- [ ] All columns sortable
- [ ] Filters work independently and combined
- [ ] Search is case-insensitive
- [ ] Pagination works smoothly
- [ ] No data truncation in columns
- [ ] Responsive on all screen sizes

### 9. Live Monitoring Page Testing

**Quick Stats:**
- [ ] Active sessions counter updates
- [ ] Completed today count correct
- [ ] Success rate percentage accurate
- [ ] Error count reflects

 current state

**System Health:**
- [ ] API Health status shown
- [ ] Database Health status shown
- [ ] Average latency displayed
- [ ] Error rate percentage shown
- [ ] Health indicators animate when healthy

**Activity Summary:**
- [ ] Progress bars render correctly
- [ ] Active sessions bar reflects count
- [ ] Success rate bar shows percentage
- [ ] Error rate bar shows percentage

**Live Session Feed:**
- [ ] Sessions display in real-time
- [ ] Status icons (active/completed/error) show correctly
- [ ] Progress bars animate for active sessions
- [ ] Session details visible on hover
- [ ] Auto-scrolls to latest
- [ ] Max height with scroll container

**Connection Status:**
- [ ] Shows "Connected" status
- [ ] WebSocket URL displayed
- [ ] Updates show "Last update: just now"

**Verification Checklist:**
- [ ] Real-time updates work (refreshes every 2 seconds)
- [ ] All metrics update correctly
- [ ] Status colors are distinct
- [ ] Layout is readable under stress
- [ ] No memory leaks from interval

### 10. Chat Interface Testing

**Chat Display:**
- [ ] Initial assistant message loads
- [ ] Messages display in chronological order
- [ ] User messages appear on right
- [ ] Assistant messages appear on left
- [ ] Messages scroll to bottom automatically

**Message Input:**
- [ ] Input field is focused initially
- [ ] Can type messages
- [ ] Enter key sends message
- [ ] Send button works
- [ ] Input clears after sending

**Example Queries:**
- [ ] Click example query buttons
- [ ] Selected query populates input
- [ ] Submitting shows loading state
- [ ] Assistant responds

**Verification Checklist:**
- [ ] Chat UI is intuitive
- [ ] Messages format correctly
- [ ] Input/output works smoothly
- [ ] No visual glitches
- [ ] Scrolling works on mobile

### 11. Responsive Design Testing

**Mobile (375px - iPhone SE):**
```
✓ Layout stacks vertically
✓ Navigation remains accessible
✓ Charts are readable
✓ Tables scroll horizontally
✓ Touch targets are ≥44px
✓ Text is readable (≥16px)
```

**Tablet (768px - iPad):**
```
✓ 2-column layouts work
✓ Sidebar is visible
✓ Charts are optimized
✓ Table columns appropriate
✓ Touch/mouse inputs work
```

**Desktop (1024px+):**
```
✓ 3-4 column layouts work
✓ Full sidebar visible
✓ All charts fully featured
✓ Table fully readable
✓ Mouse interactions smooth
```

**Ultra-wide (1920px+):**
```
✓ Layouts don't look stretched
✓ Content width capped if needed
✓ Spacing is proportional
✓ No horizontal scroll needed
```

**Verification Checklist:**
- [ ] Test on Chrome DevTools mobile view
- [ ] Test on actual devices if possible
- [ ] Landscape and portrait orientations
- [ ] No content overflow
- [ ] Spacing is proportional
- [ ] All interactions work on touch

### 12. API Integration Testing

**Mock Data Fallback:**
```bash
1. Start the development server
2. Verify data loads from mock service
3. No API errors in console
4. All pages load correctly
```

**With Backend API (when available):**
```bash
1. Start backend API server
2. Configure API_BASE_URL in .env
3. Restart frontend dev server
4. Verify real data loads
5. Check network tab for API calls
```

**Error Handling:**
```bash
1. Temporarily disable network (DevTools)
2. Verify fallback to mock data works
3. Check console for warning messages
4. UI should remain functional
```

**Caching:**
```bash
1. Open Network tab in DevTools
2. Navigate between pages
3. Verify same queries aren't called twice
4. Cache indicators show in React Query DevTools (if enabled)
```

**Verification Checklist:**
- [ ] Mock data loads correctly
- [ ] API calls work with backend
- [ ] Error fallbacks work smoothly
- [ ] Data is cached appropriately
- [ ] No console errors

### 13. Performance Testing

**Build Size:**
```bash
npm run build
# Check output:
# - HTML: < 1KB
# - CSS: < 50KB gzipped
# - JS: < 300KB gzipped
```

**Load Time:**
```bash
1. Open DevTools Performance tab
2. Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
3. Check metrics:
   - First Contentful Paint (FCP): < 2s
   - Largest Contentful Paint (LCP): < 2.5s
   - Time to Interactive (TTI): < 3s
```

**Runtime Performance:**
```bash
1. Open DevTools Performance tab
2. Record while interacting
3. Check frame rate (target 60fps)
4. Look for dropped frames during:
   - Tab switching
   - Page navigation
   - Chart rendering
   - Data loading
```

**Memory Usage:**
```bash
1. Open DevTools Memory tab
2. Take heap snapshot
3. Interact with all pages
4. Take another snapshot
5. Compare growth (should be minimal)
```

**Verification Checklist:**
- [ ] Build size is optimized
- [ ] Initial load < 2 seconds
- [ ] Interactions are smooth (60fps)
- [ ] Memory usage is stable
- [ ] No memory leaks

## Automated Testing

### Unit Tests (Future Implementation)

```bash
npm install --save-dev vitest @testing-library/react
npm run test
```

### E2E Tests (Future Implementation)

```bash
npm install --save-dev playwright
npm run test:e2e
```

## CI/CD Pipeline Testing

- [ ] Automated build passes
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Production build succeeds
- [ ] Deployed version matches local

## Browser Compatibility

### Tested Browsers:
- [ ] Chrome 120+
- [ ] Firefox 121+
- [ ] Safari 17+
- [ ] Edge 120+

### Mobile Browsers:
- [ ] Safari iOS 17+
- [ ] Chrome Mobile
- [ ] Firefox Mobile

## Accessibility Testing

- [ ] Tab navigation works throughout app
- [ ] All buttons are keyboard accessible
- [ ] Color contrast meets WCAG AA
- [ ] Form inputs have labels
- [ ] Images have alt text
- [ ] Screen reader compatible (test with NVDA/JAWS)

## Sign-off Checklist

Before marking Phase 3 as complete:

- [ ] All 13 feature categories tested
- [ ] Responsive design verified
- [ ] Theme functionality working
- [ ] API integration tested
- [ ] Performance acceptable
- [ ] No console errors
- [ ] Mobile-friendly
- [ ] Accessible
- [ ] Browser compatible
- [ ] Build successful
- [ ] Production build tested

## Known Issues & Limitations

### Current Limitations:
1. Real-time data updates are simulated (not from actual WebSocket)
2. Chat responses are mocked (not AI-powered yet)
3. Session data is generated mock data
4. Insights are static suggestions

### Future Enhancements:
- [ ] Real WebSocket integration
- [ ] AI-powered chat with actual backend
- [ ] Real session data from production
- [ ] Dynamic insight generation
- [ ] Performance monitoring dashboard
- [ ] Advanced filtering options
- [ ] Export functionality
- [ ] User preferences/settings page

## Troubleshooting

### Issue: Blank white screen

```bash
# Solution:
1. Check browser console for errors
2. Clear cache: Cmd+Shift+Delete / Ctrl+Shift+Delete
3. Restart dev server: npm run dev
4. Check that port 5173 is available
```

### Issue: Slow loading

```bash
# Solution:
1. Check Network tab in DevTools
2. Verify no large files being downloaded
3. Check if CPU is throttled in DevTools
4. Restart dev server with clean cache
```

### Issue: Theme not persisting

```bash
# Solution:
1. Check if localStorage is enabled
2. Check browser's privacy settings
3. Try in incognito window (temporary storage only)
4. Clear site data and refresh
```

### Issue: Charts not rendering

```bash
# Solution:
1. Check browser console for Recharts errors
2. Verify window size (need minimum width)
3. Check if data is loading (Network tab)
4. Try zooming out (Cmd+- / Ctrl+-)
```

## Test Results Template

Document your testing results:

```markdown
## Test Date: [DATE]
## Tester: [NAME]

### Summary
- Build: ✓ Pass / ✗ Fail
- Navigation: ✓ Pass / ✗ Fail
- Theme: ✓ Pass / ✗ Fail
- Dashboard: ✓ Pass / ✗ Fail
- [Other features...]

### Issues Found
1. [Issue description] - Severity: High/Medium/Low
2. [Issue description] - Severity: High/Medium/Low

### Recommendations
1. [Recommendation]
2. [Recommendation]

### Sign-off
- [ ] All critical issues resolved
- [ ] Ready for deployment
```

## Resources

- [React Testing Library](https://testing-library.com/react)
- [Vitest](https://vitest.dev/)
- [Playwright](https://playwright.dev/)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/)
- [WCAG Accessibility](https://www.w3.org/WAI/WCAG21/quickref/)
