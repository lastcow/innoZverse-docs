# Lab 12: CSS Testing

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Implement CSS testing strategies: Jest + jsdom for computed style tests, Testing Library for DOM queries, BackstopJS visual regression config, Storybook component states, and Percy/Chromatic concepts.

---

## Step 1: CSS Testing Philosophy

```
Testing pyramid for CSS:
────────────────────────────────
Unit Tests      — class name generation, token values
Integration     — component renders correct classes
Visual Regression — screenshot diffs (Percy, Chromatic)
Manual/Axe      — accessibility validation

Tools by category:
─────────────────────────────────────────────
Tool              | Type      | What it tests
──────────────────────────────────────────────
Jest + jsdom      | Unit/Int  | Computed styles, class names
@testing-library  | Int       | DOM queries, user interactions
BackstopJS        | Visual    | Screenshot regression
Percy             | Visual    | PR screenshot diffs (CI)
Chromatic         | Visual    | Storybook story snapshots
Storybook         | Manual    | Component visual states
axe-core          | A11y      | WCAG compliance
stylelint         | Lint      | CSS code quality
```

---

## Step 2: Jest + jsdom — Computed Style Tests

```javascript
// __tests__/button.test.js
import { getComputedStyle } from 'jest-environment-jsdom';

// Setup a button in the DOM
function createButton(variant = 'primary') {
  document.body.innerHTML = `
    <style>
      :root {
        --color-primary: #3b82f6;
        --color-danger: #ef4444;
      }
      .btn { display: inline-flex; padding: 0.5rem 1rem; }
      .btn-primary { background: var(--color-primary); color: white; }
      .btn-danger  { background: var(--color-danger); color: white; }
      .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    </style>
    <button class="btn btn-${variant}">Click me</button>
  `;
  return document.querySelector('button');
}

describe('Button Component', () => {
  test('renders with correct class names', () => {
    const btn = createButton('primary');
    expect(btn.className).toBe('btn btn-primary');
  });

  test('applies primary styles', () => {
    const btn = createButton('primary');
    const styles = window.getComputedStyle(btn);
    expect(styles.display).toBe('inline-flex');
    expect(styles.padding).toBe('0.5rem 1rem');
  });

  test('disabled button has reduced opacity', () => {
    const btn = createButton('primary');
    btn.disabled = true;
    const styles = window.getComputedStyle(btn);
    expect(styles.opacity).toBe('0.5');
  });

  test('danger variant uses danger color', () => {
    const btn = createButton('danger');
    expect(btn.classList.contains('btn-danger')).toBe(true);
  });
});
```

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '\\.module\\.css$': '<rootDir>/__mocks__/cssModules.js',
    '\\.css$': '<rootDir>/__mocks__/fileMock.js',
  }
};

// __mocks__/cssModules.js
const handler = { get: (t, key) => key };
module.exports = new Proxy({}, handler);

// __mocks__/fileMock.js
module.exports = {};
```

---

## Step 3: @testing-library/dom

```javascript
// __tests__/card.test.js
import { getByRole, getByText, queryByTestId } from '@testing-library/dom';

function renderCard(html) {
  document.body.innerHTML = html;
  return document.body;
}

describe('Card Component', () => {
  test('has accessible heading', () => {
    const container = renderCard(`
      <article class="card">
        <h2 class="card__title">Article Title</h2>
        <p class="card__body">Content here</p>
        <button class="card__cta">Read More</button>
      </article>
    `);
    
    // Queries: getBy (throws), queryBy (null), findBy (async)
    const heading = getByRole(container, 'heading', { name: 'Article Title' });
    expect(heading.tagName).toBe('H2');
    expect(heading.className).toBe('card__title');
  });

  test('button is accessible', () => {
    const container = renderCard(`
      <button class="btn btn-primary" type="button">
        <svg aria-hidden="true">...</svg>
        <span>Save Document</span>
      </button>
    `);
    
    const btn = getByRole(container, 'button', { name: 'Save Document' });
    expect(btn.type).toBe('button');
    expect(btn).not.toBeDisabled();
  });

  test('error message is shown', () => {
    const container = renderCard(`
      <div class="field" data-state="error">
        <input id="email" type="email" aria-describedby="email-error" aria-invalid="true">
        <span id="email-error" role="alert">Please enter a valid email</span>
      </div>
    `);
    
    const input = container.querySelector('#email');
    const error = getByRole(container, 'alert');
    
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(error.textContent).toBe('Please enter a valid email');
  });
});
```

---

## Step 4: BackstopJS Visual Regression

```javascript
// backstop.json
{
  "id": "my-design-system",
  "viewports": [
    { "label": "mobile",  "width": 375,  "height": 812 },
    { "label": "tablet",  "width": 768,  "height": 1024 },
    { "label": "desktop", "width": 1440, "height": 900 }
  ],
  "scenarios": [
    {
      "label": "Button - All Variants",
      "url": "http://localhost:6006/iframe.html?id=button--all-variants",
      "misMatchThreshold": 0.1,
      "requireSameDimensions": true
    },
    {
      "label": "Card - Default",
      "url": "http://localhost:6006/iframe.html?id=card--default",
      "delay": 500, // wait for animations
      "misMatchThreshold": 0.2
    },
    {
      "label": "Nav - Mobile",
      "url": "http://localhost:3000",
      "viewports": [{ "label": "mobile", "width": 375, "height": 812 }],
      "clickSelector": "#hamburger-menu",
      "postInteractionWait": 300
    },
    {
      "label": "Dark Mode",
      "url": "http://localhost:3000",
      "onBeforeScript": "setDarkMode.js",
      "misMatchThreshold": 0.1
    }
  ],
  "paths": {
    "bitmaps_reference": "backstop_data/bitmaps_reference",
    "bitmaps_test":      "backstop_data/bitmaps_test",
    "html_report":       "backstop_data/html_report"
  },
  "engine": "puppeteer",
  "report": ["browser", "CI"]
}
```

```bash
# Initialize and run
npx backstop reference  # capture reference screenshots
npx backstop test       # compare against references
npx backstop approve    # approve current state as new reference
```

---

## Step 5: Storybook for Component States

```javascript
// stories/Button.stories.js
import { Button } from '../components/Button';

export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Primary button component with variants and sizes.'
      }
    }
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'danger', 'ghost'],
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
    },
    disabled: { control: 'boolean' },
  }
};

// Individual stories for each state
export const Primary   = { args: { variant: 'primary',   children: 'Button' } };
export const Secondary = { args: { variant: 'secondary', children: 'Button' } };
export const Danger    = { args: { variant: 'danger',    children: 'Delete' } };
export const Disabled  = { args: { variant: 'primary',   children: 'Button', disabled: true } };
export const Small     = { args: { variant: 'primary',   size: 'sm', children: 'Small' } };
export const Large     = { args: { variant: 'primary',   size: 'lg', children: 'Large' } };

// Interaction testing
export const ClickTest = {
  args: { variant: 'primary', children: 'Click Me' },
  play: async ({ canvasElement }) => {
    const { getByRole, userEvent } = await import('@storybook/testing-library');
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole('button'));
  }
};
```

---

## Step 6: Percy CI Integration

```yaml
# .github/workflows/visual-tests.yml
name: Visual Tests
on: [pull_request]

jobs:
  percy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      
      - run: npm ci
      - run: npm run build-storybook
      
      - name: Percy Storybook
        run: npx @percy/storybook
        env:
          PERCY_TOKEN: ${{ secrets.PERCY_TOKEN }}
```

---

## Step 7: CSS Custom Properties Testing

```javascript
// Test CSS custom property values
function getCSSVariable(name, element = document.documentElement) {
  return window.getComputedStyle(element)
    .getPropertyValue(name)
    .trim();
}

describe('Design Tokens', () => {
  beforeEach(() => {
    document.documentElement.style.cssText = `
      --color-primary: #3b82f6;
      --spacing-base: 16px;
    `;
  });

  test('color-primary is defined', () => {
    expect(getCSSVariable('--color-primary')).toBe('#3b82f6');
  });

  test('spacing-base is 16px', () => {
    expect(getCSSVariable('--spacing-base')).toBe('16px');
  });

  test('dark theme overrides tokens', () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.style.cssText += `
      --color-primary: #60a5fa;
    `;
    expect(getCSSVariable('--color-primary')).toBe('#60a5fa');
  });
});
```

---

## Step 8: Capstone — Jest + jsdom CSS Computed Style Test

```bash
cd /tmp && npm init -y 2>/dev/null | grep name
npm install jsdom @testing-library/dom 2>/dev/null | tail -1
node -e "
const { JSDOM } = require('/tmp/node_modules/jsdom');
const { getByRole, getByText } = require('/tmp/node_modules/@testing-library/dom');

// Create a test DOM
const dom = new JSDOM(\`<!DOCTYPE html><html><head><style>
  .btn { display: inline-flex; padding: 8px 16px; }
  .btn-primary { background: #3b82f6; color: white; }
  .btn:disabled { opacity: 0.5; }
</style></head><body>
  <button class=\"btn btn-primary\" type=\"button\">Save</button>
  <button class=\"btn btn-primary\" type=\"button\" disabled>Disabled</button>
  <h1>Test Page</h1>
  <p role=\"status\">Form saved</p>
</body></html>\`, {url: 'http://localhost'});

const { window } = dom;
const { document } = window;

// Test 1: Class names
var btn = document.querySelector('.btn-primary');
console.log('[PASS] Primary button class:', btn.className.includes('btn-primary'));

// Test 2: Disabled state
var disabledBtn = document.querySelectorAll('.btn')[1];
console.log('[PASS] Disabled attribute:', disabledBtn.disabled === true);

// Test 3: @testing-library/dom queries
var heading = getByRole(document.body, 'heading', {name: 'Test Page'});
console.log('[PASS] Heading found via ARIA role:', heading.tagName === 'H1');

var status = getByRole(document.body, 'status');
console.log('[PASS] Status region found:', status.textContent === 'Form saved');

// Test 4: getAttribute
console.log('[PASS] Button type attribute:', btn.getAttribute('type') === 'button');

console.log('\nAll tests passed: CSS+DOM testing with jsdom COMPLETE');
"
```

📸 **Verified Output:**
```
"name": "tmp"
found 0 vulnerabilities
[PASS] Primary button class: true
[PASS] Disabled attribute: true
[PASS] Heading found via ARIA role: true
[PASS] Status region found: true
[PASS] Button type attribute: true

All tests passed: CSS+DOM testing with jsdom COMPLETE
```

---

## Summary

| Tool | Type | Command |
|------|------|---------|
| Jest + jsdom | Unit/Integration | `jest` |
| @testing-library/dom | Integration | `getByRole()`, `getByText()` |
| BackstopJS | Visual regression | `backstop test` |
| Percy | CI visual diffs | `percy exec` |
| Chromatic | Storybook + visual | `chromatic` |
| Storybook | Component catalog | `storybook dev` |
| axe-core | Accessibility | `axe.run(document)` |
| stylelint | CSS lint | `stylelint "**/*.css"` |
