# Lab 06: CSS-in-JS

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Compare and implement CSS-in-JS approaches: CSS Modules (compile-time scoping), Vanilla Extract (type-safe zero-runtime), styled-components (runtime), Tailwind CSS (utility-first JIT), and bundle size analysis.

---

## Step 1: CSS Modules — Compile-Time Scoping

CSS Modules transform class names at build time, guaranteeing uniqueness:

```css
/* Button.module.css */
.button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s ease;
}

.button:hover { filter: brightness(1.1); }
.button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.primary   { background: var(--color-primary); color: white; }
.secondary { background: var(--color-surface-2); color: var(--color-text); }
.danger    { background: var(--color-danger); color: white; }

.small  { padding: 0.25rem 0.75rem; font-size: 0.75rem; }
.large  { padding: 0.75rem 1.5rem; font-size: 1rem; }

/* Composes: inherit styles from another class */
.icon-button {
  composes: button;  /* inherit base button */
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  border-radius: 50%;
}
```

```javascript
// Button.jsx
import styles from './Button.module.css';

export function Button({
  variant = 'primary',
  size,
  children,
  className = '',
  ...props
}) {
  const classes = [
    styles.button,
    styles[variant],
    size && styles[size],
    className
  ].filter(Boolean).join(' ');

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}

// Generated HTML:
// <button class="button_ab12cd primary_ef34gh">Click me</button>
// No name collisions — even if another component has .primary!
```

---

## Step 2: Vanilla Extract — Zero-Runtime Type-Safe CSS

```typescript
// button.css.ts
import { style, styleVariants, globalStyle } from '@vanilla-extract/css';
import { tokens } from './tokens.css';

// Base styles
export const button = style({
  display: 'inline-flex',
  alignItems: 'center',
  gap: tokens.space[2],
  padding: `${tokens.space[2]} ${tokens.space[4]}`,
  borderRadius: tokens.borderRadius.md,
  fontSize: tokens.fontSize.sm,
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'filter 0.15s ease',
  ':hover': {
    filter: 'brightness(1.1)',
  },
  ':focus-visible': {
    outline: `2px solid ${tokens.color.brand}`,
    outlineOffset: '2px',
  },
});

// Variant map (generates class for each variant)
export const buttonVariant = styleVariants({
  primary:   { background: tokens.color.brand, color: 'white' },
  secondary: { background: tokens.color.surface2, color: tokens.color.text },
  danger:    { background: tokens.color.danger, color: 'white' },
});

export const buttonSize = styleVariants({
  sm: { padding: `${tokens.space[1]} ${tokens.space[3]}`, fontSize: tokens.fontSize.xs },
  md: {}, // default
  lg: { padding: `${tokens.space[3]} ${tokens.space[6]}`, fontSize: tokens.fontSize.md },
});
```

```typescript
// Button.tsx
import { button, buttonVariant, buttonSize } from './button.css';

type ButtonProps = {
  variant?: keyof typeof buttonVariant;
  size?: keyof typeof buttonSize;
  children: React.ReactNode;
};

export function Button({ variant = 'primary', size = 'md', children }: ButtonProps) {
  return (
    <button className={`${button} ${buttonVariant[variant]} ${buttonSize[size]}`}>
      {children}
    </button>
  );
}
// TypeScript error if you use a non-existent variant!
```

---

## Step 3: styled-components — Runtime CSS-in-JS

```javascript
// Button.styled.js
import styled, { css } from 'styled-components';

// Base button styles
const ButtonBase = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: filter 0.15s ease;

  &:hover { filter: brightness(1.1); }
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.colors.brand};
    outline-offset: 2px;
  }
`;

// Variant styles via css helper
const variants = {
  primary: css`
    background: ${({ theme }) => theme.colors.brand};
    color: white;
  `,
  secondary: css`
    background: ${({ theme }) => theme.colors.surface2};
    color: ${({ theme }) => theme.colors.text};
  `,
  danger: css`
    background: ${({ theme }) => theme.colors.danger};
    color: white;
  `,
};

export const Button = styled(ButtonBase)`
  ${({ variant = 'primary' }) => variants[variant]}
`;

// Usage:
// <ThemeProvider theme={theme}>
//   <Button variant="primary">Click</Button>
// </ThemeProvider>
```

---

## Step 4: Tailwind CSS — Utility-First

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          900: '#1e3a8a',
        }
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
      fontFamily: {
        sans: ['Inter var', ...require('tailwindcss/defaultTheme').fontFamily.sans],
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ]
};
```

```javascript
// Button.jsx (Tailwind)
const variantClasses = {
  primary:   'bg-brand-500 text-white hover:bg-brand-600',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
  danger:    'bg-red-500 text-white hover:bg-red-600',
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export function Button({ variant = 'primary', size = 'md', children, className = '' }) {
  return (
    <button className={`
      inline-flex items-center gap-2 rounded-md font-semibold
      transition-colors duration-150 cursor-pointer
      focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500
      ${variantClasses[variant]}
      ${sizeClasses[size]}
      ${className}
    `.trim()}>
      {children}
    </button>
  );
}
```

---

## Step 5: Comparison Table

```
Approach        | Runtime JS | Type Safety | File Size | DX      | Colocation
──────────────────────────────────────────────────────────────────────────────
CSS Modules     | ✗ None     | Partial     | Minimal   | Good    | Separate
Vanilla Extract | ✗ None     | Full TS     | Minimal   | Great   | Same file
styled-components| ✓ Yes     | Good        | +14kb     | Great   | Same file
Emotion         | ✓ Yes      | Good        | +11kb     | Great   | Same file
Tailwind JIT    | ✗ None     | Partial     | ~10kb     | Fast    | HTML/JSX
CSS custom props| ✗ None     | None        | Zero      | Simple  | Separate
```

---

## Step 6: Bundle Size Strategies

```javascript
// Measure CSS bundle impact
// Option 1: PurgeCSS — remove unused CSS
// Option 2: Tailwind JIT — only generates used classes
// Option 3: CSS Modules — each module is tree-shakeable
// Option 4: Vanilla Extract — zero runtime, static extraction

// Tailwind: configure content for tree-shaking
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './public/index.html',
  ],
  // JIT generates only classes found in content files
  // Result: usually 5-20kb of CSS vs 3mb full Tailwind
};

// PurgeCSS config
module.exports = {
  content: ['./src/**/*.html', './src/**/*.js'],
  css: ['./dist/styles.css'],
};
```

---

## Step 7: Choosing the Right Approach

```
Use CSS Modules when:
  ✓ React/Vue/Svelte project
  ✓ Team knows CSS well
  ✓ Want zero runtime overhead
  ✓ Bundle size is critical

Use Vanilla Extract when:
  ✓ TypeScript project
  ✓ Need type-safe theme access
  ✓ Want zero runtime AND type safety
  ✓ Building a design system

Use styled-components/Emotion when:
  ✓ Dynamic styles based on props
  ✓ Theming via ThemeProvider
  ✓ Team prefers JS-first styling
  ✓ SSR not critical for performance

Use Tailwind when:
  ✓ Rapid prototyping
  ✓ Small team / solo developer
  ✓ Design system has constraints
  ✓ Don't want to name things

Use plain CSS/Custom Props when:
  ✓ No build step
  ✓ Progressive enhancement
  ✓ Multi-framework components
  ✓ Maximum performance
```

---

## Step 8: Capstone — CSS Modules Class Name Hashing

```bash
docker run --rm -v /tmp/css_modules.js:/test.js node:20-alpine node /test.js
```

*(Create the test file:)*
```bash
cat > /tmp/css_modules.js << 'EOF'
var crypto = require("crypto");
function hashClassName(filePath, localName) {
  var hash = crypto.createHash("md5")
    .update(filePath + localName)
    .digest("hex")
    .substring(0, 6);
  return localName + "_" + hash;
}
var file = "./components/Button.module.css";
var classes = ["button","button--primary","button--secondary","button__icon","button__label"];
console.log("CSS Modules: Scoped class name generation");
console.log("File: " + file);
console.log("=".repeat(50));
classes.forEach(function(cls){
  var hashed = hashClassName(file, cls);
  console.log("." + cls + " => ." + hashed);
});
console.log("\nBenefit: No global namespace collisions!");
console.log("Import: import styles from './Button.module.css'");
console.log("Usage: <button className={styles.button}>");
EOF
docker run --rm -v /tmp/css_modules.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
CSS Modules: Scoped class name generation
File: ./components/Button.module.css
==================================================
.button => .button_87fef1
.button--primary => .button--primary_a03352
.button--secondary => .button--secondary_1657d8
.button__icon => .button__icon_18fe6e
.button__label => .button__label_38c0aa

Benefit: No global namespace collisions!
Import: import styles from './Button.module.css'
Usage: <button className={styles.button}>
```

---

## Summary

| Approach | Runtime | Type Safety | Best For |
|----------|---------|-------------|----------|
| CSS Modules | None | Partial | Component isolation |
| Vanilla Extract | None | Full TS | Type-safe design systems |
| styled-components | ~14kb | Good | Dynamic themes |
| Tailwind JIT | None | Partial | Rapid development |
| CSS custom props | None | None | Universal theming |
| Emotion | ~11kb | Good | SSR + dynamic |
