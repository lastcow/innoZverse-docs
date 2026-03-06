# HTML/CSS Practitioner Labs

**Level:** Practitioner | **Labs:** 15 | **Total Time:** ~7.5 hours

Master production-quality HTML and CSS with hands-on labs. Each lab includes Docker-verified examples, real terminal output, and a capstone exercise.

## Prerequisites

- Basic HTML/CSS knowledge (selectors, box model, basic layout)
- Docker installed for verification
- Text editor or IDE

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [Advanced CSS Selectors](labs/lab-01-advanced-selectors.md) | Attribute selectors, `:nth-child`, `:has()`, specificity, `@layer`, logical properties | 30 min |
| 02 | [Flexbox Deep Dive](labs/lab-02-flexbox-deep-dive.md) | `flex` shorthand, alignment axes, `order`, Holy Grail layout, sticky footer, card grid | 30 min |
| 03 | [CSS Grid Advanced](labs/lab-03-css-grid-advanced.md) | Template areas, auto-placement, `minmax()`, `subgrid`, named lines, magazine layout | 30 min |
| 04 | [CSS Custom Properties](labs/lab-04-css-custom-properties.md) | `var()`, scoping, JS theming, `@property`, design token patterns | 30 min |
| 05 | [Responsive Design](labs/lab-05-responsive-design.md) | Mobile-first, `clamp()`, container queries, viewport units, responsive images | 30 min |
| 06 | [CSS Animations](labs/lab-06-css-animations.md) | `@keyframes`, animation shorthand, transitions, `will-change`, motion path, easing | 30 min |
| 07 | [Forms & Accessibility](labs/lab-07-forms-accessibility.md) | Input types, Constraint Validation API, ARIA, `:focus-visible`, WCAG 2.2 | 30 min |
| 08 | [HTML5 APIs](labs/lab-08-html5-apis.md) | Intersection Observer, Resize Observer, MutationObserver, Web Storage, Custom Elements | 30 min |
| 09 | [CSS Typography](labs/lab-09-css-typography.md) | Variable fonts, `font-display`, system stacks, fluid type scale, `text-wrap: balance` | 30 min |
| 10 | [Dark Mode & Theming](labs/lab-10-dark-mode-theming.md) | `prefers-color-scheme`, CSS tokens, `color-scheme`, `oklch()`, JS theme switcher | 30 min |
| 11 | [SVG in HTML](labs/lab-11-svg-in-html.md) | Inline SVG, symbol/use system, `currentColor`, CSS animations on SVG, SVG filters | 30 min |
| 12 | [CSS Architecture](labs/lab-12-css-architecture.md) | BEM, ITCSS, Tailwind concepts, CSS Modules, stylelint | 30 min |
| 13 | [Performance Optimization](labs/lab-13-performance-optimization.md) | Critical CSS, resource hints, Core Web Vitals, `content-visibility`, lazy loading | 30 min |
| 14 | [Modern HTML Semantics](labs/lab-14-modern-html-semantics.md) | Semantic elements, JSON-LD, Open Graph, Twitter Cards, canonical links | 30 min |
| 15 | [**Capstone: Responsive Dashboard**](labs/lab-15-capstone-responsive-dashboard.md) | Grid + Flex layout, dark mode, bar chart animations, accessible forms, SVG icons | 30 min |

## Learning Path

```
Labs 01-04: Foundation         — Selectors, Flexbox, Grid, Custom Properties
Labs 05-06: Layout & Motion    — Responsive, Animations
Labs 07-08: HTML5 Depth        — Accessibility, Browser APIs
Labs 09-11: Visual Polish      — Typography, Theming, SVG
Labs 12-14: Architecture & SEO — BEM/ITCSS, Performance, Semantics
Lab  15:    Capstone           — Everything combined
```

## Quick Start

```bash
# Docker environment for all labs
docker run -it --rm node:20-alpine sh

# Install common tools inside container
npm install -g html-validate stylelint stylelint-config-standard

# Validate HTML
html-validate index.html

# Lint CSS
stylelint "**/*.css"
```

## Key Concepts by Lab

### Selectors & Cascade (Lab 01)
```css
/* Specificity: (ID, Class, Element) */
#nav .link:hover  /* (1,1,1) */
:where(h1,h2,h3) /* (0,0,0) — zero specificity */

@layer reset, base, components, utilities;
```

### Responsive Typography (Lab 05)
```css
h1 { font-size: clamp(28px, 21.65px + 1.98vw, 56px); }
```

### Dark Mode (Lab 10)
```css
:root { --color-bg: #fff; --color-text: #111; }
[data-theme="dark"] { --color-bg: #0d0d0d; --color-text: #f0f0f0; }
```

### BEM Naming (Lab 12)
```
.card                — Block
.card__title         — Element
.card--featured      — Modifier
```

## Tools Reference

| Tool | Install | Use |
|------|---------|-----|
| html-validate | `npm i -g html-validate` | Validate HTML |
| stylelint | `npm i -g stylelint` | Lint CSS |
| jsdom | `npm i jsdom` | DOM testing |
| postcss | `npm i postcss` | CSS transforms |

---

> Continue to [Advanced Labs](../advanced/README.md) when ready.
