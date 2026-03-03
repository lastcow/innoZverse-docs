# HTML/CSS

> **The universal language of the web.** Every website you've ever visited is built with HTML and CSS. Master these two foundational technologies and you can build anything — from simple landing pages to complex, accessible, animated user interfaces.

***

## 🗺️ Learning Path

<table data-view="cards">
  <thead>
    <tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🌱 Foundations</strong></td>
      <td>15 labs covering HTML semantics through CSS animations, Grid, Flexbox, accessibility, and a full portfolio capstone.</td>
      <td><a href="foundations/">foundations/</a></td>
    </tr>
    <tr>
      <td><strong>⚙️ Practitioner</strong></td>
      <td>CSS preprocessors (Sass), CSS Modules, design systems, component-driven development, CSS-in-JS, build tools.</td>
      <td><a href="practitioner/">practitioner/</a></td>
    </tr>
    <tr>
      <td><strong>🚀 Advanced</strong></td>
      <td>CSS architecture at scale, design tokens, container queries, CSS nesting, view transitions, performance optimization.</td>
      <td><a href="advanced/">advanced/</a></td>
    </tr>
    <tr>
      <td><strong>🎓 Expert</strong></td>
      <td>CSS Houdini, custom properties API, paint worklets, layout algorithms, browser rendering pipeline, animation performance.</td>
      <td><a href="expert/">expert/</a></td>
    </tr>
  </tbody>
</table>

***

## ⚡ Modern CSS & HTML5 Highlights

{% hint style="info" %}
All labs use **modern HTML5 and CSS3** — including features that have transformed frontend development in the last 5 years.
{% endhint %}

| Feature | Status | Used In |
|---------|--------|---------|
| **HTML5 Semantic Elements** | Baseline | Labs 1, 13, 15 |
| **CSS Grid** | Widely Supported | Labs 8, 15 |
| **CSS Flexbox** | Widely Supported | Labs 7, 15 |
| **CSS Custom Properties** | Widely Supported | Labs 12, 14, 15 |
| **CSS Animations & Keyframes** | Widely Supported | Lab 10, 15 |
| **Media Queries & Responsive** | Widely Supported | Labs 9, 15 |
| **ARIA & Accessibility** | Standard | Lab 13, 15 |
| **CSS Cascade Layers (@layer)** | Widely Supported | Lab 14 |
| **Container Queries** | Newly Baseline | Practitioner |
| **CSS Nesting** | Newly Baseline | Advanced |

***

## 🐳 Docker Setup

{% tabs %}
{% tab title="Ubuntu / Debian" %}
```bash
# Install Docker
sudo apt-get update && sudo apt-get install -y docker.io
sudo systemctl start docker

# Pull the HTML/CSS lab image
docker pull zchencow/innozverse-htmlcss:latest

# Run a lab verification
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "console.log('HTML/CSS lab ready!')"
```
{% endtab %}

{% tab title="macOS" %}
```bash
# Install Docker Desktop from https://docker.com/products/docker-desktop
# Or via Homebrew:
brew install --cask docker

# Pull the HTML/CSS lab image
docker pull zchencow/innozverse-htmlcss:latest

# Verify node is available
docker run --rm zchencow/innozverse-htmlcss:latest node -v
```
{% endtab %}

{% tab title="Windows" %}
```powershell
# Install Docker Desktop from https://docker.com/products/docker-desktop
# Enable WSL2 backend recommended

# Pull the HTML/CSS lab image
docker pull zchencow/innozverse-htmlcss:latest

# Run interactive session
docker run --rm -it -v C:\tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```
{% endtab %}

{% tab title="Alpine Linux" %}
```bash
# Install Docker
apk add docker docker-cli
rc-service docker start
rc-update add docker default

# Pull the HTML/CSS lab image
docker pull zchencow/innozverse-htmlcss:latest

# Quick test
docker run --rm zchencow/innozverse-htmlcss:latest node -v
```
{% endtab %}
{% endtabs %}

### Image Contents

The `zchencow/innozverse-htmlcss:latest` image includes:

| Tool | Purpose |
|------|---------|
| **Node.js 20** | Lab verification scripts |
| **live-server** | Local dev server with hot reload |
| **prettier** | Code formatting |
| **stylelint** | CSS linting |
| **html-validator-cli** | HTML validation |

```bash
# Start a live dev server for your HTML file
docker run --rm -it -p 8080:8080 -v /tmp:/workspace zchencow/innozverse-htmlcss:latest \
  live-server /workspace --port=8080 --host=0.0.0.0

# Validate HTML
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest \
  html-validator --file=/workspace/index.html

# Format CSS with Prettier
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest \
  prettier --write /workspace/style.css
```

***

## 📚 What You'll Learn

### 🌱 Foundations (15 Labs)

Build the solid foundation every web developer needs:

- **HTML Structure** — Document outline, semantic elements, accessibility attributes
- **CSS Selectors** — Combinators, pseudo-classes, pseudo-elements, specificity rules
- **Box Model** — Margin, padding, border, display modes, box-sizing
- **Typography** — Font stacks, `@font-face`, `clamp()`, fluid text scales
- **Positioning** — Static, relative, absolute, fixed, sticky, z-index stacking
- **Flexbox** — 1D layouts, alignment, flex items, the holy grail layout
- **CSS Grid** — 2D layouts, named areas, auto-fit/auto-fill, magazine layouts
- **Responsive Design** — Mobile-first, media queries, `srcset`, fluid grids
- **Animations** — `@keyframes`, transitions, 3D transforms, loading spinners
- **Forms** — All input types, validation states, custom checkboxes, accessible forms
- **CSS Variables** — Design tokens, dark mode, component theming, JS integration
- **Accessibility** — WCAG AA, ARIA, keyboard nav, skip links, screen readers
- **CSS Architecture** — BEM, `@layer`, cascade, logical properties, print styles
- **Capstone** — Complete responsive developer portfolio with all techniques combined

### ⚙️ Practitioner (Coming Soon)

Elevate to professional-grade CSS development:

- Sass/SCSS — variables, mixins, functions, partials, `@each`, `@for`
- PostCSS — autoprefixer, CSS nesting, custom plugins
- CSS Modules — scoped styles, composition, composes keyword
- Design Systems — tokens, component APIs, theming architecture
- Build Tools — Vite, Webpack, CSS optimization and code splitting
- CSS-in-JS — styled-components, Emotion, vanilla-extract
- Testing CSS — Percy visual regression, Chromatic, accessibility audits

***

{% hint style="success" %}
**Start Here:** Begin with [Foundations Lab 1](foundations/labs/lab-01-html-document-structure.md) if you're new to HTML/CSS, or jump to any lab that covers a topic you want to learn.
{% endhint %}

{% hint style="warning" %}
**Prerequisites:** Basic computer skills and a text editor. No programming experience required for Foundations. A modern browser (Chrome, Firefox, or Edge) is all you need to view your work.
{% endhint %}
