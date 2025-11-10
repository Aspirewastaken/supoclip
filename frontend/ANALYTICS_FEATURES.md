# Analytics Dashboard - Feature Overview

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back                           ANALYTICS DASHBOARD            │
│                                                   [Export CSV]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │ 👁 Total     │  │ ❤️ Avg       │  │ 📈 Best      │  │ 🕐 Watch││
│  │    Views    │  │  Engagement │  │  Performing │  │   Time  ││
│  │   125.0K    │  │    13.2%    │  │  clip_1...  │  │   11.5s ││
│  │  45 clips   │  │  16.5K eng. │  │  15K views  │  │  76% ret││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
│                                                                   │
│  ┌────────────────────────────┐  ┌──────────────────────────┐  │
│  │ Performance Over Time      │  │ Clips by Platform        │  │
│  │ ─────────────────────────  │  │                          │  │
│  │     [Line Chart]           │  │      [Pie Chart]         │  │
│  │  Views & Engagement        │  │   Platform Distribution  │  │
│  │  Last 30 Days              │  │                          │  │
│  └────────────────────────────┘  └──────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Platform Comparison                                         ││
│  │ ───────────────────────────────────────────────────────────││
│  │              [Bar Chart]                                    ││
│  │   Views & Engagements by Platform                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Clip Performance                                            ││
│  │ ───────────────────────────────────────────────────────────││
│  │  [Search: ________] [Platform: All ▼]                      ││
│  │                                                             ││
│  │  Clip Name ↕ │ Views ↕ │ Likes ↕ │ Comments ↕ │ Eng ↕ │... ││
│  │  ─────────────────────────────────────────────────────────││
│  │  clip_1.mp4  │  15.0K  │  1.8K   │    120     │ 15.8% │... ││
│  │  clip_2.mp4  │  12.5K  │  1.5K   │     95     │ 12.1% │... ││
│  │  clip_3.mp4  │  10.2K  │  1.2K   │     78     │ 11.8% │... ││
│  │                                                             ││
│  │  Showing 25 of 45 clips                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Feature Breakdown

### 1. Overview Metrics (Top Row)

**Total Views Card**
```
┌──────────────┐
│ 👁 Total Views│
│   125,000    │  ← Large primary metric
│ 45 clips     │  ← Supporting metric
└──────────────┘
```

**Average Engagement Card**
```
┌──────────────────┐
│ ❤️ Avg Engagement │
│      13.2%       │
│ 16.5K eng.       │
└──────────────────┘
```

**Best Performing Card**
```
┌──────────────────┐
│ 📈 Best Perform. │
│  clip_1_tran...  │
│   15,000 views   │
└──────────────────┘
```

**Total Watch Time Card**
```
┌──────────────┐
│ 🕐 Watch Time│
│    11.5s     │
│  76.8% ret.  │
└──────────────┘
```

### 2. Performance Over Time Chart

**Type:** Dual-axis line chart
**Period:** 30 days

```
Views     │                              Engagement %
15000 ────┤     ╱╲    ╱╲                     25%
          │    ╱  ╲  ╱  ╲
12500 ────┤   ╱    ╲╱    ╲   ╱╲              20%
          │  ╱            ╲ ╱  ╲
10000 ────┤ ╱              ╲    ╲            15%
          │╱                     ╲
 7500 ────┤                       ╲╱╲        10%
          │                           ╲
 5000 ────┤                            ╲╱    5%
          └──────────────────────────────────
           Oct 11  Oct 18  Oct 25  Nov 01

          ──── Views    ──── Engagement %
```

### 3. Clips by Platform Chart

**Type:** Pie chart with percentages

```
          TikTok (40%)
              ╱╲
         ╱╲╱    ╲╱╲
        │          │
        │  YouTube │  Instagram
        │  Shorts  │  Reels
        │  (35%)   │  (25%)
         ╲        ╱
          ╲╱╲  ╱╲╱
```

### 4. Platform Comparison Chart

**Type:** Grouped bar chart

```
Views/Eng
 75000 ┤
       │  ■■
 50000 │  ■■  ■■  ■■
       │  ■■  ■■  ■■
 25000 │  ■■  ■■  ■■  ■■
       │  ■■  ■■  ■■  ■■  ■■
     0 └────────────────────
        TikTok YouTube Instagram
               Shorts  Reels

        ■ Views    ■ Engagements
```

### 5. Clip Performance Table

**Interactive Features:**
- ✓ Sortable columns
- ✓ Search filter
- ✓ Platform filter
- ✓ Color-coded badges
- ✓ Hover effects

**Example Rows:**
```
┌──────────────┬──────────┬────────┬──────────┬────────────┬────────────┐
│ Clip Name    │ Views    │ Likes  │ Comments │ Engagement │ Retention  │
├──────────────┼──────────┼────────┼──────────┼────────────┼────────────┤
│ clip_1.mp4   │  15.0K   │  1.8K  │   120    │  [15.8% ✓] │  [82.5% ✓] │
│ 15.5s • 0.95 │          │        │          │   Green    │   Green    │
├──────────────┼──────────┼────────┼──────────┼────────────┼────────────┤
│ clip_2.mp4   │  12.5K   │  1.5K  │    95    │  [12.1% ✓] │  [71.3% ⚠] │
│ 18.2s • 0.92 │          │        │          │   Green    │   Yellow   │
├──────────────┼──────────┼────────┼──────────┼────────────┼────────────┤
│ clip_3.mp4   │  10.2K   │  1.2K  │    78    │  [ 8.5% ⚠] │  [65.1% ⚠] │
│ 12.8s • 0.88 │          │        │          │   Yellow   │   Yellow   │
└──────────────┴──────────┴────────┴──────────┴────────────┴────────────┘

↑ Click headers to sort
```

### 6. CSV Export

**Exported Data:**
```csv
Clip ID,Filename,Duration,Views,Likes,Comments,Shares,Engagement Rate,Retention Rate,Relevance Score
abc-123,clip_1_transition.mp4,15.50,15000,1800,120,450,15.80,82.50,0.95
def-456,clip_2_transition.mp4,18.20,12500,1500,95,380,12.10,71.30,0.92
ghi-789,clip_3_transition.mp4,12.80,10200,1200,78,320,8.50,65.10,0.88
```

## Color Coding System

### Badges

**Engagement Rate:**
- 🟢 Green: > 10% (High engagement)
- 🟡 Yellow: 5-10% (Medium engagement)
- ⚪ Gray: < 5% (Low engagement)

**Retention Rate:**
- 🟢 Green: > 70% (High retention)
- 🟡 Yellow: 50-70% (Medium retention)
- ⚪ Gray: < 50% (Low retention)

### Chart Colors
- 🔵 Blue (#3b82f6): Primary metric (Views)
- 🟢 Green (#10b981): Success metric (Engagement)
- 🟠 Orange (#f59e0b): Warning/Medium
- 🔴 Red (#ef4444): Alert/Low
- 🟣 Purple (#8b5cf6): Platform color 1
- 🩷 Pink (#ec4899): Platform color 2

## Responsive Breakpoints

### Desktop (1024px+)
```
┌─────────────────────────────────────┐
│  [Card] [Card] [Card] [Card]        │  ← 4 columns
│  [Chart        ] [Chart        ]    │  ← 2 columns
│  [Full Width Chart              ]   │
│  [Full Width Table              ]   │
└─────────────────────────────────────┘
```

### Tablet (768px-1023px)
```
┌──────────────────────┐
│  [Card]    [Card]    │  ← 2 columns
│  [Card]    [Card]    │
│  [Full Width Chart]  │  ← 1 column
│  [Full Width Chart]  │
│  [Full Width Table]  │
└──────────────────────┘
```

### Mobile (<768px)
```
┌──────────┐
│  [Card]  │  ← 1 column
│  [Card]  │
│  [Card]  │
│  [Card]  │
│  [Chart] │
│  [Chart] │
│  [Table] │  ← Horizontal scroll
└──────────┘
```

## Interaction Examples

### Sorting Table
```
Click "Views" header once:  ↓ Descending (15K → 1K)
Click "Views" header again: ↑ Ascending (1K → 15K)
```

### Filtering
```
Search: "transition"
Result: Shows only clips with "transition" in filename

Platform: "TikTok"
Result: Shows only clips posted to TikTok
```

### Export
```
Click "Export CSV" → Downloads: supoclip-analytics-2025-11-10.csv
```

## Data Flow

```
User Login
    ↓
Navigate to /analytics
    ↓
Fetch data: GET /analytics/dashboard?user_id={id}
    ↓
Backend queries:
  - Aggregate view metrics
  - Calculate performance metrics
  - Get top clips
  - Platform breakdown
    ↓
Frontend receives JSON
    ↓
Process & compute:
  - Performance over time (30 days)
  - Platform distribution
  - Filtered/sorted clips
    ↓
Render dashboard with:
  - Metric cards
  - Charts (Recharts)
  - Interactive table
    ↓
User interactions:
  - Sort columns
  - Filter/search
  - Export CSV
```

## Key Statistics Display

### Number Formatting
```
Raw Number    →  Displayed As
─────────────────────────────
1,500,000     →  1.5M
125,000       →  125.0K
15,000        →  15.0K
2,500         →  2.5K
850           →  850
```

### Percentage Formatting
```
Raw Number    →  Displayed As
─────────────────────────────
0.13245678    →  13.2%
0.05876543    →  5.9%
0.76543210    →  76.5%
```

### Duration Formatting
```
Raw Seconds   →  Displayed As
─────────────────────────────
15.5          →  15.5s
8.3           →  8.3s
122.7         →  122.7s
```

## Empty States

### No Analytics Data
```
┌─────────────────────────┐
│       📊                │
│  No Analytics Data      │
│                         │
│  Start generating clips │
│  to see your analytics. │
│                         │
│  [Create First Clip]    │
└─────────────────────────┘
```

### Loading State
```
┌─────────────────────────┐
│  ▓▓▓▓░░░░░░  Loading... │
│  ▓▓▓░░░░░░░░            │
│  ▓▓▓▓▓░░░░░             │
└─────────────────────────┘
```

### Error State
```
┌─────────────────────────┐
│  ⚠️ Error               │
│  Failed to load         │
│  analytics data         │
└─────────────────────────┘
```

## Usage Tips

1. **Sorting**: Click any column header to sort. Click again to reverse.
2. **Best Performance**: Look for green badges in the table.
3. **Trends**: Use the line chart to identify growth patterns.
4. **Platform Focus**: Use pie chart to see where most clips are posted.
5. **Comparison**: Bar chart shows which platform performs best.
6. **Export**: Save data for external analysis or reporting.
7. **Search**: Quickly find specific clips by name.
8. **Mobile**: Table scrolls horizontally on small screens.

## Quick Actions

```
┌────────────────────────────────────┐
│ Want to...              Do this... │
├────────────────────────────────────┤
│ Find best clip          Sort by Views ↓      │
│ See low engagement      Sort by Engagement ↑ │
│ Check TikTok only       Filter: TikTok       │
│ Save data               Export CSV           │
│ Find specific clip      Use search box       │
│ See trends              View line chart      │
│ Compare platforms       View bar chart       │
└────────────────────────────────────┘
```
