# HTML/CSS Advanced Labs

**Level:** Advanced | **Labs:** 15 | **Total Time:** ~7.5 hours

Deep-dive into cutting-edge HTML/CSS: Houdini, Web Components, container queries, design tokens, PostCSS pipelines, and production-grade design systems.

## Prerequisites

- Complete [Practitioner Labs](../practitioner/README.md) or equivalent experience
- Comfortable with CSS custom properties, Grid, Flexbox
- Node.js + Docker installed
- Familiarity with JavaScript ES6+

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [CSS Houdini](labs/lab-01-css-houdini.md) | `@property` types, animatable custom properties, CSS Typed OM, Paint API | 30 min |
| 02 | [Web Components](labs/lab-02-web-components.md) | Custom Elements lifecycle, Shadow DOM, `<template>/<slot>`, cross-shadow CSS | 30 min |
| 03 | [Container Queries](labs/lab-03-container-queries.md) | `@container`, `container-type`, named containers, style queries, nested containers | 30 min |
| 04 | [Modern CSS Features](labs/lab-04-modern-css-features.md) | CSS nesting, `@scope`, advanced `:has()`, anchor positioning, View Transitions, scroll animations | 30 min |
| 05 | [Design Tokens](labs/lab-05-design-tokens.md) | W3C token format, primitive→semantic→component tiers, Style Dictionary, multi-platform output | 30 min |
| 06 | [CSS-in-JS](labs/lab-06-css-in-js.md) | CSS Modules, Vanilla Extract, styled-components, Tailwind JIT, bundle analysis | 30 min |
| 07 | [PostCSS Pipeline](labs/lab-07-postcss-pipeline.md) | `postcss.config.js`, preset-env, autoprefixer, cssnano, custom plugins | 30 min |
| 08 | [Advanced Accessibility](labs/lab-08-accessibility-advanced.md) | WCAG 2.2 AAA, ARIA live regions, `inert`, skip nav, axe-core | 30 min |
| 09 | [Print & Email CSS](labs/lab-09-print-email-css.md) | `@media print`, `@page`, orphans/widows, HTML email, MJML | 30 min |
| 10 | [CSS Performance Deep](labs/lab-10-css-performance-deep.md) | `contain`, `content-visibility`, `@layer`, selector perf, `will-change`, logical props | 30 min |
| 11 | [Advanced Animations](labs/lab-11-advanced-animations.md) | Scroll-driven animations, View Transitions, motion path, staggered animations | 30 min |
| 12 | [CSS Testing](labs/lab-12-css-testing.md) | Jest + jsdom, @testing-library, BackstopJS, Storybook, Percy | 30 min |
| 13 | [Internationalization](labs/lab-13-internationalization.md) | `dir` attribute, writing modes, logical properties, `:lang()`, CJK/Arabic fonts | 30 min |
| 14 | [Progressive Enhancement](labs/lab-14-progressive-enhancement.md) | `@supports`, CSS fallbacks, Baseline 2024, module/nomodule, polyfills | 30 min |
| 15 | [**Capstone: Design System**](labs/lab-15-capstone-design-system.md) | Style Dictionary + Web Components + PostCSS + 3 themes + WCAG 2.2 AA | 30 min |

## Learning Path

```
Labs 01-04: Modern CSS Power   — Houdini, Web Components, Container Queries, Modern CSS
Labs 05-07: Tooling            — Design Tokens, CSS-in-JS, PostCSS Pipeline
Labs 08-09: Quality & Output   — Advanced A11y, Print/Email
Labs 10-11: Performance & Motion — Perf, Scroll Animations
Labs 12-14: Testing & Global   — Testing, i18n, Progressive Enhancement
Lab  15:    Capstone           — Complete design system
```

## Quick Start

```bash
# Docker environment
docker run -it --rm node:20-alpine sh

# Install pipeline tools
cd /tmp && npm init -y
npm install postcss autoprefixer cssnano postcss-preset-env

# Install testing tools
npm install jsdom @testing-library/dom

# Run PostCSS
npx postcss input.css -o output.css
```

## Advanced Concepts Reference

### @property (Lab 01)
```css
@property --gradient-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}
/* Now --gradient-angle is animatable! */
```

### Container Queries (Lab 03)
```css
.wrapper { container: card / inline-size; }

@container card (min-width: 400px) {
  .card { flex-direction: row; }
}
```

### Scroll-Driven Animations (Lab 11)
```css
.progress {
  animation: grow linear both;
  animation-timeline: scroll(root);
}
```

### Design Tokens (Lab 05)
```
JSON tokens → Style Dictionary → CSS vars + iOS Swift + Android XML
```

### Progressive Enhancement (Lab 14)
```css
@supports (container-type: inline-size) {
  .wrapper { container-type: inline-size; }
}
```

## Tools Reference

| Tool | Install | Purpose |
|------|---------|---------|
| style-dictionary | `npm i style-dictionary` | Token transformation |
| postcss + plugins | `npm i postcss autoprefixer cssnano` | CSS pipeline |
| jsdom | `npm i jsdom` | DOM testing |
| @testing-library/dom | `npm i @testing-library/dom` | Accessible queries |
| html-validate | `npm i -g html-validate` | HTML validation |
| axe-core | `npm i axe-core` | Accessibility audit |
| stylelint | `npm i -g stylelint` | CSS linting |
| backstopjs | `npm i -g backstopjs` | Visual regression |

## Browser Support Strategy

```
Feature                 | @supports guard    | Polyfill
────────────────────────────────────────────────────────
CSS Grid                | Not needed (97%+) | None needed
Container Queries       | Optional (90%)    | JS fallback
scroll-driven animations| Recommended (72%) | IO fallback
View Transitions        | Required (75%)    | No-op fallback
Anchor Positioning      | Required (30%)    | JS tooltip lib
```

---

> Return to [Practitioner Labs](../practitioner/README.md) for foundational skills.
