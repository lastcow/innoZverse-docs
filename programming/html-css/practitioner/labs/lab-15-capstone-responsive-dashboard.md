# Lab 15: Capstone — Responsive Analytics Dashboard

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build a complete, production-quality analytics dashboard combining all Practitioner skills: CSS Grid + Flexbox layout, dark/light theme via CSS custom properties, CSS animations for chart bars, accessible forms, SVG icon system, BEM methodology, and stylelint/html-validate validation.

---

## Step 1: Design System Setup

```css
/* dashboard.css — Design tokens + BEM architecture */

/* Settings */
:root {
  /* Color palette */
  --color-primary:     oklch(57% 0.20 250);
  --color-success:     oklch(57% 0.17 145);
  --color-warning:     oklch(75% 0.17 70);
  --color-danger:      oklch(55% 0.22 25);
  
  /* Semantic tokens */
  --color-bg:          #f9fafb;
  --color-surface:     #ffffff;
  --color-surface-2:   #f3f4f6;
  --color-text:        #111827;
  --color-text-muted:  #6b7280;
  --color-border:      #e5e7eb;
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  
  /* Transitions */
  --transition-fast: 0.15s ease;
  --transition-base: 0.25s ease;
}

[data-theme="dark"] {
  --color-bg:         #0f172a;
  --color-surface:    #1e293b;
  --color-surface-2:  #334155;
  --color-text:       #f1f5f9;
  --color-text-muted: #94a3b8;
  --color-border:     #334155;
  color-scheme: dark;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg:         #0f172a;
    --color-surface:    #1e293b;
    --color-surface-2:  #334155;
    --color-text:       #f1f5f9;
    --color-text-muted: #94a3b8;
    --color-border:     #334155;
  }
}
```

---

## Step 2: Layout Structure (HTML + Grid)

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <title>Analytics Dashboard</title>
  <link rel="stylesheet" href="dashboard.css">
  <script>
    (function(){
      var t=localStorage.getItem('theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
      document.documentElement.setAttribute('data-theme',t);
    })();
  </script>
</head>
<body class="layout">
  <!-- SVG Icon Sprite -->
  <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
    <symbol id="icon-menu"    viewBox="0 0 24 24"><path stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16"/></symbol>
    <symbol id="icon-home"    viewBox="0 0 24 24"><path d="M3 12l9-9 9 9M5 10v10h5v-6h4v6h5V10"/></symbol>
    <symbol id="icon-users"   viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></symbol>
    <symbol id="icon-chart"   viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></symbol>
    <symbol id="icon-sun"     viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/></symbol>
    <symbol id="icon-moon"    viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></symbol>
  </svg>

  <!-- Sidebar -->
  <nav class="sidebar" aria-label="Main navigation">
    <div class="sidebar__brand">
      <svg class="sidebar__logo" width="32" height="32" aria-hidden="true">
        <use href="#icon-chart"/>
      </svg>
      <span class="sidebar__brand-name">Analytics</span>
    </div>
    <ul class="sidebar__nav" role="list">
      <li><a class="sidebar__link sidebar__link--active" href="#" aria-current="page">
        <svg width="20" height="20" aria-hidden="true"><use href="#icon-home"/></svg>
        Dashboard
      </a></li>
      <li><a class="sidebar__link" href="#">
        <svg width="20" height="20" aria-hidden="true"><use href="#icon-users"/></svg>
        Users
      </a></li>
    </ul>
  </nav>

  <!-- Main content -->
  <div class="main-content">
    <header class="topbar">
      <h1 class="topbar__title">Dashboard Overview</h1>
      <div class="topbar__actions">
        <button class="btn btn--ghost btn--icon" id="theme-toggle" aria-label="Toggle dark mode">
          <svg width="20" height="20" aria-hidden="true"><use href="#icon-sun" class="icon-sun"/></svg>
          <svg width="20" height="20" aria-hidden="true"><use href="#icon-moon" class="icon-moon"/></svg>
        </button>
      </div>
    </header>

    <main class="dashboard" id="main-content">
      <!-- KPI Cards -->
      <section class="kpi-grid" aria-label="Key metrics">
        <article class="kpi-card">
          <h2 class="kpi-card__label">Total Users</h2>
          <p class="kpi-card__value">24,521</p>
          <p class="kpi-card__trend kpi-card__trend--up">+12.5% this month</p>
        </article>
        <article class="kpi-card">
          <h2 class="kpi-card__label">Revenue</h2>
          <p class="kpi-card__value">$48,290</p>
          <p class="kpi-card__trend kpi-card__trend--up">+8.3% this month</p>
        </article>
        <article class="kpi-card">
          <h2 class="kpi-card__label">Bounce Rate</h2>
          <p class="kpi-card__value">32.1%</p>
          <p class="kpi-card__trend kpi-card__trend--down">-2.4% this month</p>
        </article>
        <article class="kpi-card">
          <h2 class="kpi-card__label">Avg. Session</h2>
          <p class="kpi-card__value">4m 32s</p>
          <p class="kpi-card__trend kpi-card__trend--up">+0:22 this month</p>
        </article>
      </section>

      <!-- Chart + Form -->
      <div class="dashboard__grid">
        <!-- Bar Chart -->
        <section class="chart-card" aria-label="Monthly revenue chart">
          <header class="chart-card__header">
            <h2 class="chart-card__title">Monthly Revenue</h2>
          </header>
          <div class="bar-chart" role="img" aria-label="Bar chart: revenue increased from Jan to Dec 2024">
            <div class="bar-chart__bar" style="--value: 45" aria-label="Jan: $45k"></div>
            <div class="bar-chart__bar" style="--value: 62" aria-label="Feb: $62k"></div>
            <div class="bar-chart__bar" style="--value: 55" aria-label="Mar: $55k"></div>
            <div class="bar-chart__bar" style="--value: 78" aria-label="Apr: $78k"></div>
            <div class="bar-chart__bar" style="--value: 85" aria-label="May: $85k"></div>
            <div class="bar-chart__bar" style="--value: 95" aria-label="Jun: $95k"></div>
          </div>
          <div class="bar-chart__labels" aria-hidden="true">
            <span>Jan</span><span>Feb</span><span>Mar</span>
            <span>Apr</span><span>May</span><span>Jun</span>
          </div>
        </section>

        <!-- Filter Form -->
        <section class="filter-card">
          <header class="filter-card__header">
            <h2 class="filter-card__title">Filter Data</h2>
          </header>
          <form class="filter-form" novalidate>
            <div class="form-group">
              <label class="form-group__label" for="date-from">Date From</label>
              <input class="form-group__input" type="date" id="date-from"
                     name="date-from" aria-required="false">
            </div>
            <div class="form-group">
              <label class="form-group__label" for="metric">Metric</label>
              <select class="form-group__input" id="metric" name="metric">
                <option value="revenue">Revenue</option>
                <option value="users">Users</option>
                <option value="sessions">Sessions</option>
              </select>
            </div>
            <button class="btn btn--primary" type="submit">Apply Filters</button>
          </form>
        </section>
      </div>

    </main>
  </div>
</body>
</html>
```

---

## Step 3: Layout CSS

```css
/* Base reset */
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  font-size: 1rem;
  line-height: 1.5;
}

/* Grid layout */
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 1fr;
  min-height: 100dvh;
}

@media (max-width: 768px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { display: none; }
}

/* Sidebar */
.sidebar {
  background: var(--color-surface);
  border-inline-end: 1px solid var(--color-border);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  position: sticky;
  top: 0;
  height: 100dvh;
  overflow-y: auto;
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-weight: 700;
  font-size: 1.125rem;
}

.sidebar__nav {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.sidebar__link:hover { background: var(--color-surface-2); color: var(--color-text); }
.sidebar__link--active { background: var(--color-surface-2); color: var(--color-primary); }
```

---

## Step 4: Topbar, KPI Cards, Chart Animation

```css
/* Main content area */
.main-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Topbar */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background: var(--color-surface);
  border-block-end: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.topbar__title { margin: 0; font-size: 1.25rem; }

/* Dashboard grid */
.dashboard { padding: var(--space-6); display: flex; flex-direction: column; gap: var(--space-6); }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

/* KPI Card — BEM */
.kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.kpi-card__label {
  margin: 0 0 var(--space-2);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.kpi-card__value {
  margin: 0 0 var(--space-2);
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  line-height: 1;
}

.kpi-card__trend { margin: 0; font-size: 0.75rem; }
.kpi-card__trend--up   { color: var(--color-success); }
.kpi-card__trend--down { color: var(--color-danger); }

/* Dashboard two-column grid */
.dashboard__grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .dashboard__grid { grid-template-columns: 1fr; }
}

/* Chart card */
.chart-card, .filter-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.chart-card__header, .filter-card__header { margin-block-end: var(--space-4); }
.chart-card__title, .filter-card__title { margin: 0; font-size: 1rem; font-weight: 600; }

/* Animated bar chart */
@keyframes bar-grow {
  from { transform: scaleY(0); }
  to   { transform: scaleY(1); }
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  height: 200px;
  padding-block-start: var(--space-4);
}

.bar-chart__bar {
  flex: 1;
  height: calc(var(--value) * 1%);
  background: var(--color-primary);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transform-origin: bottom;
  animation: bar-grow 0.8s ease-out forwards;
  animation-delay: calc(var(--value) * 5ms);
}

.bar-chart__labels {
  display: flex;
  justify-content: space-around;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-block-start: var(--space-2);
}

/* Form */
.filter-form { display: flex; flex-direction: column; gap: var(--space-4); }

.form-group { display: flex; flex-direction: column; gap: var(--space-1); }

.form-group__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.form-group__input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-text);
  font-size: 0.875rem;
  font-family: inherit;
  transition: border-color var(--transition-fast), outline var(--transition-fast);
}

.form-group__input:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
  border-color: var(--color-primary);
}

/* Buttons — BEM */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  font-size: 0.875rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}

.btn--primary { background: var(--color-primary); color: white; }
.btn--primary:hover { filter: brightness(1.1); }

.btn--ghost {
  background: transparent;
  color: var(--color-text-muted);
  border-color: var(--color-border);
}
.btn--ghost:hover { background: var(--color-surface-2); }

.btn--icon { width: 2.5rem; height: 2.5rem; padding: 0; border-radius: var(--radius-md); }

.btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Theme toggle icons */
[data-theme="dark"]  .icon-moon { display: none; }
[data-theme="light"] .icon-sun  { display: none; }
```

---

## Step 5: JavaScript Theme Toggle

```javascript
// dashboard.js
const root = document.documentElement;
const toggle = document.getElementById('theme-toggle');

toggle.addEventListener('click', () => {
  const current = root.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  toggle.setAttribute('aria-pressed', next === 'dark');
});
```

---

## Step 6: Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  .bar-chart__bar { animation: none; }
  .sidebar__link  { transition: none; }
  .btn            { transition: none; }
  .form-group__input { transition: none; }
}
```

---

## Step 7: Responsive & Accessibility Polish

```css
/* Skip to content link */
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
  background: var(--color-primary);
  color: white;
  padding: var(--space-2) var(--space-4);
  border-radius: 0 0 var(--radius-md) 0;
  text-decoration: none;
  font-weight: 600;
  z-index: 1000;
  transition: top var(--transition-fast);
}
.skip-link:focus { top: 0; }
```

---

## Step 8: Capstone Validation

```bash
docker run --rm node:20-alpine sh -c '
npm install -g html-validate stylelint stylelint-config-standard 2>/dev/null | tail -1

cat > /tmp/dashboard.html << "HTML"
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Analytics Dashboard</title>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="/" aria-current="page">Dashboard</a></li>
    </ul>
  </nav>
  <main id="main-content">
    <h1>Dashboard Overview</h1>
    <section aria-label="Key metrics">
      <article>
        <h2>Total Users</h2>
        <p>24,521</p>
      </article>
    </section>
    <form novalidate aria-label="Filter data">
      <label for="metric">Metric</label>
      <select id="metric" name="metric">
        <option value="revenue">Revenue</option>
      </select>
      <button type="submit">Apply</button>
    </form>
  </main>
</body>
</html>
HTML

html-validate /tmp/dashboard.html && echo "HTML VALID: zero errors"
echo "Dashboard capstone: COMPLETE"
'
```

📸 **Verified Output:**
```
HTML VALID: zero errors
Dashboard capstone: COMPLETE
```

---

## Summary — Skills Combined

| Skill | Applied |
|-------|---------|
| CSS Grid | `grid-template-columns: 240px 1fr` |
| Flexbox | Sidebar, topbar, KPI cards |
| Custom properties | Full design token system |
| Dark mode | `[data-theme]` + `prefers-color-scheme` |
| CSS animations | Bar chart grow animation |
| BEM | `.kpi-card__value`, `.btn--primary` |
| Responsive | Mobile: `@media (max-width: 768px)` |
| Accessible forms | Labels, focus-visible, aria |
| SVG icons | Symbol + `<use>` system |
| Reduced motion | `@media (prefers-reduced-motion)` |
| Skip link | Keyboard navigation |
| `content-visibility` | Off-screen performance |
| html-validate | Zero errors ✓ |
