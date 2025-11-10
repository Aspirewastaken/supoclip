# Analytics Dashboard

## Overview

A comprehensive analytics dashboard for tracking clip performance across all social media platforms. Built with React, Next.js 15, Recharts, and ShadCN UI components.

**Location:** `/analytics` (frontend/src/app/analytics/page.tsx)

## Features

### 1. Overview Metrics Cards

Four key metric cards displaying:

- **Total Views**: Total views across all clips with clip count
- **Average Engagement**: Engagement rate percentage with total engagements
- **Best Performing Clip**: Top clip by views with filename and view count
- **Total Watch Time**: Average watch time in seconds with retention rate

Each card includes:
- Icon representation (Eye, Heart, TrendingUp, Clock)
- Large primary metric
- Supporting secondary metric
- Color-coded icons

### 2. Performance Over Time (Line Chart)

**Chart Type:** Dual-axis line chart
**Data Period:** Last 30 days
**Metrics Tracked:**
- Views (left axis, blue line)
- Engagement rate % (right axis, green line)

**Features:**
- Responsive layout
- Grid overlay
- Interactive tooltip
- Legend
- Angled X-axis labels for better readability

### 3. Clips by Platform (Pie Chart)

**Chart Type:** Pie chart with labels
**Data Shown:** Distribution of clips across platforms
**Features:**
- Color-coded segments (6 distinct colors)
- Percentage labels on each segment
- Platform names displayed
- Interactive tooltip

**Supported Platforms:**
- TikTok
- YouTube Shorts
- Instagram Reels
- Facebook
- Twitter
- LinkedIn

### 4. Platform Comparison (Bar Chart)

**Chart Type:** Grouped bar chart
**Metrics Compared:**
- Views (blue bars)
- Engagements (green bars)

**Features:**
- Side-by-side comparison
- Grid overlay
- Interactive tooltip
- Legend
- Y-axis auto-scaling

### 5. Clip Performance Table

Comprehensive data table with the following columns:

| Column | Description | Sortable |
|--------|-------------|----------|
| Clip Name | Filename with duration and relevance score | Yes |
| Views | Total views (formatted: K, M) | Yes |
| Likes | Total likes (formatted) | Yes |
| Comments | Total comments (formatted) | Yes |
| Engagement | Engagement rate % with color-coded badge | Yes |
| Retention | Retention rate % with color-coded badge | Yes |

**Table Features:**
- Click column headers to sort (ascending/descending)
- Sort indicator icon
- Hover effects on rows
- Truncated text with ellipsis for long filenames
- Secondary information (duration, relevance score)
- Color-coded badges:
  - **Green**: High performance (Engagement >10%, Retention >70%)
  - **Yellow**: Medium performance (Engagement >5%, Retention >50%)
  - **Gray**: Low performance

**Filtering & Search:**
- Search input: Filter clips by filename
- Platform selector: Filter by specific platform or "All Platforms"
- Results counter: Shows filtered/total clip count

### 6. Export to CSV

**Button Location:** Top-right of page header
**Functionality:**
- Exports filtered/sorted table data to CSV
- Includes all performance metrics
- Filename format: `supoclip-analytics-YYYY-MM-DD.csv`
- Disabled when no data available

**CSV Columns:**
- Clip ID
- Filename
- Duration
- Views
- Likes
- Comments
- Shares
- Engagement Rate
- Retention Rate
- Relevance Score

### 7. Date Range Support

The dashboard includes date range functionality:
- Default: Last 30 days
- State management for start/end dates
- Used in performance over time chart
- Can be extended with date picker UI

## Technical Implementation

### Dependencies

```json
{
  "recharts": "^2.x",
  "date-fns": "^3.x"
}
```

### API Integration

**Endpoint:** `GET /analytics/dashboard`
**Query Parameters:**
- `user_id`: Filter by user (required, passed via headers)
- `limit`: Number of top clips to return (default: 100)

**Response Structure:**
```typescript
interface DashboardStats {
  total_clips: number;
  total_clips_with_metrics: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_engagements: number;
  avg_engagement_rate: number;
  avg_watch_time: number;
  avg_retention_rate: number;
  top_performing_clips: TopPerformingClip[];
  platform_breakdown: Record<string, PlatformStats>;
}
```

### State Management

The component uses React hooks for state:
- `useState` for data, loading, errors, filters, and sorting
- `useEffect` for data fetching
- `useMemo` for computed values (charts, filtered/sorted data)
- `useSession` for authentication

### Responsive Design

- **Desktop (lg)**: 4-column grid for metrics, 2-column for charts
- **Tablet (md)**: 2-column grid for metrics, full-width charts
- **Mobile**: Single column layout, scrollable table

### Data Formatting

**Number Formatting:**
- 1,000,000+ → "1.0M"
- 1,000+ → "1.0K"
- <1,000 → Raw number

**Percentage Formatting:**
- Fixed to 1 decimal place
- Example: 12.5%

**Date Formatting:**
- Chart: "MMM dd" (e.g., "Nov 10")
- CSV: "yyyy-MM-dd" (e.g., "2025-11-10")

## Usage

### Accessing the Dashboard

1. Navigate to `/analytics` in your browser
2. Must be signed in (redirects to `/sign-in` if not authenticated)
3. Data loads automatically for the current user

### Interacting with the Dashboard

**Sorting:**
- Click any column header in the table
- Click again to reverse sort direction
- Arrow icon indicates current sort

**Filtering:**
- Type in search box to filter by clip name
- Select platform from dropdown to filter by platform
- Filters apply in real-time

**Exporting:**
- Click "Export CSV" button in header
- Downloads immediately as CSV file
- Includes only filtered/visible clips

### Empty States

The dashboard handles three states:

1. **Loading**: Skeleton loaders for all components
2. **No Data**: Friendly message with "Create First Clip" CTA
3. **Error**: Alert message with error details

## Chart Customization

All charts use consistent styling:

**Colors:**
- Primary blue: `#3b82f6`
- Success green: `#10b981`
- Warning orange: `#f59e0b`
- Danger red: `#ef4444`
- Purple: `#8b5cf6`
- Pink: `#ec4899`

**Chart Settings:**
- Height: 300px (responsive container)
- Grid: Dashed lines (#3 3 pattern)
- Font size: 12px for axis labels
- Stroke width: 2px for lines

## Performance Considerations

**Optimizations:**
- `useMemo` for expensive calculations
- Conditional rendering to avoid unnecessary updates
- Efficient filtering and sorting algorithms
- Table virtualization ready (can add react-window)

**Data Limits:**
- Default: 100 top clips from API
- Can be adjusted via API `limit` parameter
- Client-side filtering for instant results

## Future Enhancements

Potential improvements:

1. **Date Range Picker**: Interactive calendar widget
2. **Real-time Updates**: WebSocket connection for live data
3. **Custom Reports**: Save and share custom views
4. **Comparison Mode**: Compare time periods or platforms
5. **Goal Tracking**: Set and track performance goals
6. **Export Options**: PDF reports, scheduled exports
7. **Table Virtualization**: Handle 1000+ clips efficiently
8. **Advanced Filters**: Date range, engagement threshold, duration
9. **Annotations**: Add notes to specific dates/events
10. **Platform-specific Metrics**: Platform-unique KPIs

## Troubleshooting

### No Data Displayed

**Check:**
- User is authenticated
- Analytics tables exist in database (run migration)
- Clips have recorded metrics (use `/analytics/record` endpoint)

### Charts Not Rendering

**Check:**
- Recharts is installed: `npm list recharts`
- Browser console for errors
- Data structure matches expected format

### CSV Export Not Working

**Check:**
- Browser allows downloads
- Data exists in filtered results
- Pop-up blocker not interfering

## Code Structure

```
frontend/src/app/analytics/page.tsx
├── Imports (libraries, components, types)
├── Type Definitions
│   ├── DashboardStats
│   ├── TopPerformingClip
│   └── PlatformStats
├── Constants
│   ├── COLORS (chart colors)
│   └── PLATFORM_NAMES (display names)
├── Component: AnalyticsPage
│   ├── State Management
│   ├── Data Fetching (useEffect)
│   ├── Computed Values (useMemo)
│   │   ├── performanceOverTime
│   │   ├── platformComparisonData
│   │   ├── clipsByPlatform
│   │   └── filteredAndSortedClips
│   ├── Event Handlers
│   │   ├── handleSort
│   │   └── exportToCSV
│   ├── Utility Functions
│   │   └── formatNumber
│   └── Render
│       ├── Loading State
│       ├── Auth Check
│       ├── Header
│       ├── Overview Cards
│       ├── Charts (Line, Pie, Bar)
│       └── Table with Filters
```

## Accessibility

**Keyboard Navigation:**
- All interactive elements are keyboard accessible
- Tab order follows logical flow
- Focus indicators visible

**Screen Readers:**
- Semantic HTML structure
- ARIA labels where appropriate
- Alternative text for visual elements

**Color Contrast:**
- Meets WCAG 2.1 AA standards
- Badge colors have sufficient contrast
- Chart colors distinguishable

## Browser Support

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Related Files

- Backend API: `backend/src/api/routes/analytics.py`
- Database Schema: `backend/migrations/001_add_analytics_tables.sql`
- Backend Docs: `backend/ANALYTICS_README.md`

## License

Part of the SupoClip project - MIT License
