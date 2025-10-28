# Responsive Design Guide

## Overview

The ProdLens Dashboard is built with a mobile-first approach using Tailwind CSS responsive utilities. This guide documents the responsive design patterns and breakpoints used throughout the application.

## Breakpoints

The application uses Tailwind's default breakpoints:

| Size | Breakpoint | Device |
|------|-----------|--------|
| Mobile | None (base) | < 640px |
| Small | `sm:` | ≥ 640px |
| Medium | `md:` | ≥ 768px |
| Large | `lg:` | ≥ 1024px |
| Extra Large | `xl:` | ≥ 1280px |
| 2XL | `2xl:` | ≥ 1536px |

## Layout Architecture

### Mobile-First Approach

All styles start with mobile-optimized defaults. Breakpoint utilities are used to progressively enhance layouts for larger screens.

```typescript
// Example: Grid that starts as 1 column, then 2, then 3, then 4
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  {/* Items */}
</div>
```

### Main Layout Structure

```
Mobile (<768px):
┌─────────────────────┐
│  Sidebar (collapsed)│
│  or hamburger menu  │
├─────────────────────┤
│                     │
│   Main Content      │
│   (full width)      │
│                     │
└─────────────────────┘

Tablet (≥768px):
┌──────┬──────────────┐
│      │              │
│ Side │   Main       │
│ bar  │  Content     │
│      │              │
└──────┴──────────────┘

Desktop (≥1024px):
┌──────┬──────────────────┐
│      │                  │
│ Side │   Main Content   │
│ bar  │   (optimized)    │
│ (64) │                  │
│      │                  │
└──────┴──────────────────┘
```

## Component Responsive Patterns

### 1. Navigation Sidebar

**Mobile**: Collapsible hamburger menu (implement if needed)
**Tablet+**: Fixed sidebar with 256px width

```typescript
// Sidebar is always visible in current implementation
<div className="flex h-full w-64 flex-col bg-card">
  {/* Navigation items stack vertically */}
</div>
```

### 2. Grid Cards

**Mobile**: Single column (100% width)
**Tablet**: 2 columns
**Desktop**: 3-4 columns

```typescript
// Dashboard metric cards
<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
  {/* Cards */}
</div>

// Profile sections
<div className="grid gap-6 md:grid-cols-2">
  {/* Two column layouts */}
</div>

// Insights feed
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
  {/* Responsive grid */}
</div>
```

### 3. Data Tables

**Mobile**: Scrollable horizontal table (or stacked rows)
**Tablet+**: Standard table with horizontal scroll on overflow

```typescript
<div className="overflow-x-auto">
  <table className="w-full">
    <thead>
      <tr>
        <th>Column 1</th>
        <th className="hidden md:table-cell">Column 2</th>
        <th className="hidden lg:table-cell">Column 3</th>
      </tr>
    </thead>
  </table>
</div>
```

### 4. Charts and Visualizations

**Mobile**: Single column (stacked)
**Tablet+**: Side-by-side layouts with responsive heights

```typescript
<div className="grid gap-6 md:grid-cols-2">
  {/* Charts stack on mobile, side-by-side on tablet+ */}
</div>
```

### 5. Filter and Search Controls

**Mobile**: Full-width inputs stacked vertically
**Tablet+**: Flexbox row layout

```typescript
<div className="flex flex-col md:flex-row gap-4">
  <input className="flex-1" />
  <select className="md:w-48" />
  <select className="md:w-48" />
</div>
```

## Responsive Typography

Text sizes scale based on screen size:

```typescript
<h1 className="text-2xl md:text-3xl lg:text-4xl">Large Heading</h1>
<p className="text-sm md:text-base">Body text</p>
<span className="text-xs md:text-sm">Small text</span>
```

## Padding and Spacing

Responsive spacing utilities are used throughout:

```typescript
<div className="p-4 md:p-6 lg:p-8">
  {/* Padding scales from 16px to 32px based on screen size */}
</div>

<div className="gap-2 md:gap-4 lg:gap-6">
  {/* Gap scales responsively */}
</div>
```

## Responsive Features

### Visible/Hidden Elements

Hide elements on certain screen sizes:

```typescript
{/* Hidden on mobile, visible on tablet+ */}
<div className="hidden md:block">
  {/* Content */}
</div>

{/* Visible on mobile, hidden on tablet+ */}
<div className="md:hidden">
  {/* Mobile-only content */}
</div>
```

### Responsive Display

```typescript
{/* Different displays at different breakpoints */}
<div className="block md:flex lg:grid">
  {/* Display type changes based on screen size */}
</div>
```

## Mobile Optimization Checklist

- [x] **Touch-friendly sizes**: Buttons and clickable elements are ≥44px minimum
- [x] **Readable text**: Font sizes are ≥16px on mobile to prevent zoom
- [x] **Proper spacing**: Adequate padding/margins on mobile
- [x] **Scrollable tables**: Horizontal scroll for data tables on mobile
- [x] **Full-width inputs**: Form inputs stretch to full width on mobile
- [x] **Stack layouts**: Multi-column layouts stack on mobile
- [x] **Hide non-essential elements**: Hide complex charts/tables on mobile when appropriate
- [x] **Responsive images**: Images scale with container width

## Implementation Examples

### Example 1: Dashboard Page

```typescript
export function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Header - responsive text sizing */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm md:text-base">Overview of your AI usage</p>
      </div>

      {/* Metric cards - responsive grid */}
      <div className="grid gap-4 md:gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* 1 column on mobile, 2 on tablet, 4 on desktop */}
      </div>

      {/* Charts - responsive layout */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* 1 column on mobile, 2 on tablet */}
      </div>

      {/* Sessions list - scrollable on mobile */}
      <div className="overflow-x-auto">
        <div className="space-y-2">
          {/* List of sessions */}
        </div>
      </div>
    </div>
  );
}
```

### Example 2: Session Table with Responsive Columns

```typescript
export function Sessions() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            {/* Always visible columns */}
            <th className="text-left p-2 md:p-4">Session</th>
            <th className="text-left p-2 md:p-4">Model</th>

            {/* Hidden on mobile */}
            <th className="hidden md:table-cell p-4">Timestamp</th>
            <th className="hidden lg:table-cell p-4">Tokens</th>
            <th className="hidden xl:table-cell p-4">Cost</th>
          </tr>
        </thead>
        <tbody>
          {/* Rows */}
        </tbody>
      </table>
    </div>
  );
}
```

### Example 3: Profile Card with Responsive Grid

```typescript
export function Profile() {
  return (
    <div className="space-y-6">
      {/* Profile header - responsive flex direction */}
      <div className="rounded-lg border border-border bg-card p-4 md:p-6">
        <div className="flex flex-col md:flex-row items-center gap-4 md:gap-6">
          <div className="h-20 w-20 md:h-24 md:w-24 rounded-full">
            {/* Avatar */}
          </div>
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-xl md:text-3xl font-bold">{name}</h1>
          </div>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Cards */}
      </div>

      {/* Charts - 1 column on mobile, 2 on tablet */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Charts */}
      </div>
    </div>
  );
}
```

## Common Responsive Patterns

### Pattern 1: Two-Column Desktop, One-Column Mobile

```typescript
<div className="grid gap-6 md:grid-cols-2">
  <Card>Left Column</Card>
  <Card>Right Column</Card>
</div>
```

### Pattern 2: Three-Column Desktop, One-Column Mobile

```typescript
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  {items.map(item => <Card key={item.id}>{item}</Card>)}
</div>
```

### Pattern 3: Responsive Flex Row

```typescript
<div className="flex flex-col md:flex-row gap-4">
  <div className="flex-1">Left</div>
  <div className="flex-1">Right</div>
</div>
```

### Pattern 4: Hide/Show Based on Screen Size

```typescript
<div>
  {/* Simple view on mobile */}
  <div className="md:hidden">Mobile View</div>

  {/* Complex view on desktop */}
  <div className="hidden md:block">Desktop View</div>
</div>
```

### Pattern 5: Responsive Padding

```typescript
<div className="p-4 md:p-6 lg:p-8">
  Content with responsive padding
</div>
```

## Testing Responsive Design

### Browser Dev Tools

Use Chrome DevTools to test responsive layouts:

1. Open DevTools (F12)
2. Click "Toggle device toolbar" (Ctrl+Shift+M)
3. Select different device presets
4. Manually resize the viewport

### Testing Checklist

- [ ] Test on mobile (375px width)
- [ ] Test on tablet (768px width)
- [ ] Test on desktop (1024px+ width)
- [ ] Test on large desktop (1920px width)
- [ ] Test text readability at all sizes
- [ ] Test button/input sizes for touch
- [ ] Test table scrolling on mobile
- [ ] Test chart responsiveness
- [ ] Test image scaling
- [ ] Test navigation on mobile

### Devices to Test

- iPhone SE (375px)
- iPhone 12/13 (390px)
- iPad (768px)
- iPad Pro (1024px)
- Desktop 1280px
- Desktop 1920px
- Ultra-wide 2560px

## Performance Considerations

### CSS Performance

- Tailwind CSS is production-optimized
- Unused styles are purged in production build
- Critical CSS is inlined in the HTML

### Image Optimization

Use responsive images:

```typescript
<img
  src="image.jpg"
  alt="Description"
  className="w-full h-auto"
/>
```

### Lazy Loading

For charts and heavy components:

```typescript
const HeavyChart = lazy(() => import('./HeavyChart'));

<Suspense fallback={<Skeleton />}>
  <HeavyChart />
</Suspense>
```

## Accessibility & Responsiveness

- Use semantic HTML (header, nav, main, section, article)
- Ensure sufficient color contrast in all themes
- Use proper heading hierarchy
- Provide alt text for images
- Test with keyboard navigation
- Test with screen readers

## Browser Support

The dashboard supports:

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Resources

- [Tailwind CSS Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [Mobile-First Approach](https://www.nngroup.com/articles/mobile-first-responsive-web-design/)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
