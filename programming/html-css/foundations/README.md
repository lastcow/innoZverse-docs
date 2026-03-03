# HTML/CSS Foundations

> **15 hands-on labs** taking you from HTML document structure to a complete, responsive, accessible portfolio page. Every lab uses Docker for consistent verification — no local setup headaches.

***

## 🐳 Quick Start

```bash
# Pull the lab image
docker pull zchencow/innozverse-htmlcss:latest

# Run an interactive session
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash

# Verify a lab file
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest \
  node -e "const fs=require('fs'); console.log(fs.readFileSync('/workspace/index.html','utf8').length + ' bytes')"
```

***

## 📋 Lab Overview

{% tabs %}
{% tab title="Labs 1–5: HTML Core" %}
| # | Lab | Key Topics | Time |
|---|-----|------------|------|
| 1 | [HTML Structure & Semantics](labs/lab-01-html-document-structure.md) | DOCTYPE, html/head/body, semantic elements, attributes | 20 min |
| 2 | [CSS Selectors & Specificity](labs/lab-02-text-elements.md) | Type, class, ID, combinators, pseudo-classes, cascade | 25 min |
| 3 | [Box Model & Layout](labs/lab-03-links-and-images.md) | margin, padding, border, display, box-sizing | 25 min |
| 4 | [Typography & Colors](labs/lab-04-lists.md) | font-family, text properties, color systems, web fonts | 25 min |
| 5 | [Positioning & Z-index](labs/lab-05-tables.md) | static, relative, absolute, fixed, sticky, z-index | 30 min |
{% endtab %}

{% tab title="Labs 6–10: Layout & Motion" %}
| # | Lab | Key Topics | Time |
|---|-----|------------|------|
| 6 | [Lists, Tables & Navigation](labs/lab-06-forms.md) | ul/ol/dl, table, nav patterns, link states | 25 min |
| 7 | [CSS Flexbox](labs/lab-07-flexbox.md) | flex container, flex items, alignment, holy grail layout | 35 min |
| 8 | [CSS Grid](labs/lab-08-grid.md) | grid-template, named areas, auto-placement, gallery | 35 min |
| 9 | [Responsive Design](labs/lab-09-responsive.md) | viewport, media queries, clamp(), srcset, mobile-first | 35 min |
| 10 | [Animations & Transitions](labs/lab-10-animations.md) | @keyframes, transform, easing, 3D flip, loading spinners | 30 min |
{% endtab %}

{% tab title="Labs 11–15: Advanced & Capstone" %}
| # | Lab | Key Topics | Time |
|---|-----|------------|------|
| 11 | [Forms & Input Styling](labs/lab-11-forms.md) | input types, validation, custom checkboxes, file upload | 35 min |
| 12 | [CSS Variables & Theming](labs/lab-12-variables-themes.md) | custom properties, dark mode, design tokens, JS integration | 30 min |
| 13 | [Accessibility & ARIA](labs/lab-13-accessibility.md) | semantic HTML, WCAG AA, ARIA, keyboard nav, modals | 35 min |
| 14 | [CSS Architecture & BEM](labs/lab-14-sass-preprocessor.md) | BEM, @layer, specificity, logical properties, print styles | 30 min |
| 15 | [Capstone: Portfolio Page](labs/lab-15-capstone.md) | Full responsive portfolio combining all techniques | 60 min |
{% endtab %}
{% endtabs %}

***

## 🧩 Complete Lab Table

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 1 | [HTML Structure & Semantics](labs/lab-01-html-document-structure.md) | DOCTYPE, elements, attributes, semantic HTML5 | 20 min |
| 2 | [CSS Selectors & Specificity](labs/lab-02-text-elements.md) | Selectors, cascade, specificity calculation | 25 min |
| 3 | [Box Model & Layout](labs/lab-03-links-and-images.md) | margin, padding, border, display, box-sizing | 25 min |
| 4 | [Typography & Colors](labs/lab-04-lists.md) | Font properties, text styling, color systems | 25 min |
| 5 | [Positioning & Z-index](labs/lab-05-tables.md) | static, relative, absolute, fixed, sticky | 30 min |
| 6 | [Lists, Tables & Navigation](labs/lab-06-forms.md) | ul/ol, table, nav patterns, link states | 25 min |
| 7 | [CSS Flexbox](labs/lab-07-flexbox.md) | Flex container, items, alignment, wrapping | 35 min |
| 8 | [CSS Grid](labs/lab-08-grid.md) | grid-template, areas, auto-placement | 35 min |
| 9 | [Responsive Design](labs/lab-09-responsive.md) | Media queries, mobile-first, fluid typography | 35 min |
| 10 | [Animations & Transitions](labs/lab-10-animations.md) | Keyframes, transform, easing functions | 30 min |
| 11 | [Forms & Input Styling](labs/lab-11-forms.md) | Input types, validation states, custom UI | 35 min |
| 12 | [CSS Variables & Theming](labs/lab-12-variables-themes.md) | Custom properties, dark mode, design tokens | 30 min |
| 13 | [Accessibility & ARIA](labs/lab-13-accessibility.md) | Semantic HTML, WCAG, keyboard navigation | 35 min |
| 14 | [CSS Architecture & BEM](labs/lab-14-sass-preprocessor.md) | BEM methodology, @layer, organization | 30 min |
| 15 | [Capstone Portfolio Page](labs/lab-15-capstone.md) | Full responsive portfolio — all concepts | 60 min |

**Total estimated time:** ~6 hours

***

## 🎯 What You'll Build

By Lab 15, you'll have built:

- ✅ A **complete developer portfolio** website
- ✅ **Sticky glassmorphism** navigation header
- ✅ **Animated hero** section with gradient text
- ✅ **Responsive skill cards** grid
- ✅ **Project showcase** with hover effects
- ✅ **Accessible contact form** with validation
- ✅ **Dark theme** with CSS custom properties
- ✅ **Print-friendly** stylesheet

***

## 🔍 Lab Verification Pattern

Every lab follows the same verification pattern:

```bash
# 1. Write the HTML file
cat > /tmp/my-file.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
...
EOF

# 2. Verify with Docker + Node.js
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/my-file.html', 'utf8');
console.log(html.includes('display: flex') ? '✓ Flexbox found' : '✗ Missing');
"
```

{% hint style="info" %}
**All files go to `/tmp/`** so Docker can mount them with `-v /tmp:/workspace`. The verification scripts read the file and check for key patterns — no browser needed for verification!
{% endhint %}

{% hint style="success" %}
**Learning tip:** Don't just copy-paste. Type out each code example. The muscle memory of writing CSS properties is part of learning. Then modify it — change colors, sizes, animations — to see what breaks.
{% endhint %}

***

## 📖 Prerequisites

- Basic computer skills (create files, use terminal)
- A text editor (VS Code, Sublime Text, Notepad++ — any works)
- Docker installed (for lab verification)
- A modern browser (Chrome/Firefox/Edge)

**No prior programming experience required for Labs 1-6.**  
Labs 7+ assume you've completed the earlier labs or have equivalent knowledge.
