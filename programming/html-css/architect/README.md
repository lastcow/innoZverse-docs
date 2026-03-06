# HTML/CSS Architect Track

**15 Labs | 60 min each | Docker-verified**

Master enterprise CSS engineering: design systems, build pipelines, Web Components, performance, accessibility, theming, and security.

---

## Labs

| # | Lab | Key Skills |
|---|-----|-----------|
| 01 | [Design System Architecture](labs/lab-01-design-system-architecture.md) | Style Dictionary, multi-tier tokens, versioning |
| 02 | [CSS Build Pipeline](labs/lab-02-css-build-pipeline.md) | PostCSS, preset-env, PurgeCSS, custom plugins |
| 03 | [Web Components Architecture](labs/lab-03-web-components-architecture.md) | Shadow DOM, slots, ::part(), registry |
| 04 | [Performance Architecture](labs/lab-04-performance-architecture.md) | CWV, LCP, CLS, INP, content-visibility |
| 05 | [Accessibility Architecture](labs/lab-05-accessibility-architecture.md) | WCAG 2.2 AAA, ARIA, focus trap, axe-core |
| 06 | [CSS-in-JS Architecture](labs/lab-06-css-in-js-architecture.md) | Vanilla Extract, recipe, CSS Modules, Tailwind JIT |
| 07 | [Responsive Architecture](labs/lab-07-responsive-architecture.md) | clamp(), container queries, intrinsic layout |
| 08 | [Animation Architecture](labs/lab-08-animation-architecture.md) | Scroll-driven, View Transitions, FLIP, tokens |
| 09 | [Testing Architecture](labs/lab-09-testing-architecture.md) | Playwright visual, Jest+jsdom, Stylelint plugin |
| 10 | [Internationalization](labs/lab-10-internationalization-architecture.md) | Logical props, RTL, CJK/Arabic fonts, unicode-range |
| 11 | [Theming System](labs/lab-11-theming-system.md) | @layer, oklch(), data-theme, forced-colors |
| 12 | [Component API Design](labs/lab-12-component-api-design.md) | @property, :has(), state machines, slots |
| 13 | [Monorepo CSS](labs/lab-13-monorepo-css.md) | npm workspaces, shared configs, versioning |
| 14 | [Security & CSP](labs/lab-14-security-csp.md) | CSP, nonce/hash, SRI, injection prevention |
| 15 | [Capstone: Design Platform](labs/lab-15-capstone-design-platform.md) | Full platform integration, all techniques |

---

## Prerequisites

- Strong CSS fundamentals (Intermediate + Advanced tracks complete)
- Node.js 20+ and Docker installed
- TypeScript basics (for Vanilla Extract labs)

## Docker Images Used

- `node:20-alpine` — all labs (PostCSS, Style Dictionary, axe-core)

## Key Outcomes

After completing this track you can:
- Architect a multi-tier design token system with Style Dictionary
- Build a zero-runtime CSS-in-JS pipeline with Vanilla Extract
- Engineer Web Components with production-quality Shadow DOM APIs
- Achieve Core Web Vitals targets via CSS-driven optimizations
- Implement WCAG 2.2 AA/AAA with automated axe-core auditing
- Design multi-brand theming with oklch() P3 color palettes
- Build RTL-safe components using CSS logical properties exclusively
- Write custom PostCSS plugins, Stylelint rules, and test utilities
- Secure CSS pipelines with CSP, SRI, and injection prevention
