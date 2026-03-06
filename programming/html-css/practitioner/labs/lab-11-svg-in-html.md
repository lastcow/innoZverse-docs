# Lab 11: SVG in HTML

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master SVG integration in HTML: `viewBox`, inline SVG, symbol/use icon systems, `currentColor` theming, CSS animations on SVG paths, SVG filters, and making SVGs accessible.

---

## Step 1: Inline SVG & viewBox

```html
<!-- Inline SVG: styled via CSS, interactive via JS -->
<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 24 24"
  width="48"
  height="48"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
>
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 6v6l4 2"/>
</svg>
```

**viewBox="minX minY width height":**
- Defines the coordinate system
- `viewBox="0 0 24 24"` = 24×24 unit coordinate space
- SVG scales to fill its container, coordinates remain 0–24
- `preserveAspectRatio` controls alignment and overflow

```html
<!-- preserveAspectRatio examples -->
<svg viewBox="0 0 200 100" preserveAspectRatio="xMidYMid meet">  <!-- center, letterbox -->
<svg viewBox="0 0 200 100" preserveAspectRatio="xMinYMin slice"> <!-- top-left, crop -->
<svg viewBox="0 0 200 100" preserveAspectRatio="none">           <!-- stretch distort -->
```

---

## Step 2: SVG Symbol System (Icon Library)

```html
<!-- Define sprites (hidden) — put near top of <body> -->
<svg xmlns="http://www.w3.org/2000/svg" style="display: none">
  <symbol id="icon-home" viewBox="0 0 24 24">
    <path d="M3 12l9-9 9 9M5 10v10h5v-6h4v6h5V10"/>
  </symbol>
  
  <symbol id="icon-user" viewBox="0 0 24 24">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </symbol>
  
  <symbol id="icon-bell" viewBox="0 0 24 24">
    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 01-3.46 0"/>
  </symbol>
  
  <symbol id="icon-search" viewBox="0 0 24 24">
    <circle cx="11" cy="11" r="8"/>
    <path d="M21 21l-4.35-4.35"/>
  </symbol>
</svg>

<!-- Use icons anywhere in the page -->
<button class="btn btn--icon">
  <svg width="20" height="20" aria-hidden="true" focusable="false">
    <use href="#icon-search"/>
  </svg>
  <span>Search</span>
</button>

<nav>
  <a href="/">
    <svg width="24" height="24" aria-hidden="true">
      <use href="#icon-home"/>
    </svg>
    Home
  </a>
</nav>
```

> 💡 `focusable="false"` prevents SVG from receiving focus in IE/Edge. Always include it on decorative SVG icons.

---

## Step 3: currentColor for Theming

```css
/* currentColor inherits the CSS color property */
/* Perfect for icons that match their context */

.btn {
  color: white;
}

.btn svg {
  fill: currentColor;   /* icon fills white */
  /* or */
  stroke: currentColor; /* icon strokes white */
}

.btn--danger {
  color: white;
  background: #ef4444;
}
/* Icon automatically turns white */

/* In dark mode: */
[data-theme="dark"] .sidebar-icon {
  color: #f0f0f0; /* icon follows text color */
}

/* Example: multi-color icon */
.icon-alert {
  color: #f59e0b; /* warning yellow */
}
.icon-alert .icon-alert__circle { fill: currentColor; }
.icon-alert .icon-alert__mark   { fill: white; } /* hardcoded contrast */
```

---

## Step 4: CSS Animations on SVG

```css
/* Animate SVG path (stroke-dasharray trick for draw-on effect) */
.icon-circle path {
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  animation: draw-path 1s ease forwards;
}

@keyframes draw-path {
  to { stroke-dashoffset: 0; }
}

/* Spin animation */
.spinner {
  animation: spin 1s linear infinite;
  transform-origin: center;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Animate SVG elements via CSS */
.icon-bell {
  transform-origin: 50% 0%; /* pivot at top */
  animation: ring 0.5s ease-in-out infinite alternate;
}

@keyframes ring {
  from { transform: rotate(-15deg); }
  to   { transform: rotate(15deg); }
}

/* Morphing paths — requires same number of path commands */
@keyframes morph {
  0%   { d: path("M5,5 L19,5 L19,19 L5,19 Z"); } /* square */
  100% { d: path("M12,5 L19,12 L12,19 L5,12 Z"); } /* diamond */
}

.morphing { animation: morph 1s ease infinite alternate; }
```

---

## Step 5: SVG Filters

```html
<!-- Define filters in SVG defs -->
<svg style="display: none">
  <defs>
    <!-- Blur filter -->
    <filter id="blur">
      <feGaussianBlur stdDeviation="4"/>
    </filter>
    
    <!-- Drop shadow -->
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="2" dy="4" stdDeviation="3" flood-color="#00000040"/>
    </filter>
    
    <!-- Color matrix: convert to grayscale -->
    <filter id="grayscale">
      <feColorMatrix type="saturate" values="0"/>
    </filter>
    
    <!-- Sepia tone -->
    <filter id="sepia">
      <feColorMatrix type="matrix" values="
        0.393 0.769 0.189 0 0
        0.349 0.686 0.168 0 0
        0.272 0.534 0.131 0 0
        0     0     0     1 0
      "/>
    </filter>
    
    <!-- Glow effect -->
    <filter id="glow">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
</svg>
```

```css
/* Apply via CSS filter property */
.photo-card img { filter: url(#grayscale); }
.photo-card:hover img { filter: none; transition: filter 0.3s; }

/* Or via CSS filters directly */
.card:hover {
  filter: drop-shadow(0 8px 16px rgba(0,0,0,0.2));
}
```

---

## Step 6: SVG Accessibility

```html
<!-- Decorative SVG: hide from screen readers -->
<svg aria-hidden="true" focusable="false">
  <path d="..."/>
</svg>

<!-- Meaningful SVG: provide accessible name -->
<!-- Method 1: role + aria-label -->
<svg role="img" aria-label="Heart: add to favorites">
  <path d="..."/>
</svg>

<!-- Method 2: title element (referenced) -->
<svg role="img" aria-labelledby="heart-title heart-desc">
  <title id="heart-title">Heart icon</title>
  <desc id="heart-desc">Click to add this item to your favorites list</desc>
  <path d="..."/>
</svg>

<!-- Interactive SVG icon button -->
<button type="button" aria-label="Add to favorites">
  <svg width="24" height="24" aria-hidden="true" focusable="false">
    <use href="#icon-heart"/>
  </svg>
</button>

<!-- SVG chart: provide text alternative -->
<figure>
  <svg role="img" aria-labelledby="chart-title" aria-describedby="chart-desc">
    <title id="chart-title">Monthly Revenue 2024</title>
    <desc id="chart-desc">Bar chart showing revenue increased from $10k in January to $45k in December</desc>
    <!-- chart content -->
  </svg>
  <figcaption>Monthly Revenue 2024 — showing consistent growth</figcaption>
</figure>
```

---

## Step 7: Responsive SVG

```css
/* SVG as background image */
.hero {
  background-image: url("data:image/svg+xml,%3Csvg...%3E");
  background-size: cover;
}

/* Inline SVG responsive sizing */
.icon-wrapper svg {
  width: 1em;     /* scales with font-size */
  height: 1em;
  display: inline-block;
  vertical-align: -0.125em; /* align with text baseline */
}

/* Fluid SVG illustration */
.illustration {
  width: 100%;
  max-width: 600px;
  height: auto;  /* SVG height scales with width if viewBox set */
}
```

---

## Step 8: Capstone — SVG Generator + Validator

```bash
docker run --rm node:20-alpine node -e "
var icons = {
  home: 'M3 12l9-9 9 9M5 10v10h5v-6h4v6h5V10',
  user: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8',
  bell: 'M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0'
};
var svg = '<svg xmlns=\"http://www.w3.org/2000/svg\" style=\"display:none\">';
Object.keys(icons).forEach(function(name){
  svg += '<symbol id=\"' + name + '\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\">';
  svg += '<path d=\"' + icons[name] + '\"/>';
  svg += '</symbol>';
});
svg += '</svg>';
console.log('Generated SVG symbol sprite:');
console.log(svg.substring(0,100) + '...');
console.log('');
console.log('Validation - xmlns: ' + svg.includes('xmlns'));
console.log('Validation - viewBox: ' + svg.includes('viewBox'));
console.log('Validation - symbol count: ' + (svg.match(/<symbol/g)||[]).length);
console.log('All required attributes present: ' + (svg.includes('xmlns') && svg.includes('viewBox') && svg.includes('symbol')));
"
```

📸 **Verified Output:**
```
Generated SVG symbol sprite:
<svg xmlns="http://www.w3.org/2000/svg" style="display:none"><symbol id="home" viewBox="0 0 24 24" f...

Validation - xmlns: true
Validation - viewBox: true
Validation - symbol count: 3
All required attributes present: true
```

---

## Summary

| Feature | Technique | Purpose |
|---------|-----------|---------|
| viewBox | `"0 0 24 24"` | Scalable coordinate system |
| Icon system | `<symbol>` + `<use href>` | Reusable icon library |
| Theming | `stroke: currentColor` | Inherit text color |
| Draw animation | `stroke-dasharray/offset` | Path draw effect |
| Blur filter | `<feGaussianBlur>` | CSS-accessible blur |
| Decorative | `aria-hidden="true"` | Hide from screen readers |
| Meaningful | `role="img" aria-label` | Accessible SVG |
| Responsive | `width: 100%; height: auto` | Fluid SVG |
| CSS animation | `@keyframes` on SVG elements | Animated icons |
| Drop shadow | `filter: drop-shadow()` | CSS filter on SVG |
