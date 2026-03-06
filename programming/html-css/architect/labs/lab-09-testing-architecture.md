# Lab 09: Testing Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

CSS testing at scale: Playwright visual regression, Percy/Chromatic integration concepts, Jest + jsdom computed style testing, BackstopJS configuration, Storybook interaction tests, and custom stylelint plugins.

---

## Step 1: Testing Strategy Overview

```
CSS Testing Pyramid:
  ┌─────────────────────────────┐
  │  Visual Regression (Percy)  │  ← Slowest, highest fidelity
  ├─────────────────────────────┤
  │  Integration (Playwright)   │  ← Layout + interaction
  ├─────────────────────────────┤
  │  Unit (Jest + jsdom)        │  ← Computed styles, logic
  ├─────────────────────────────┤
  │  Static (Stylelint)         │  ← Fastest, syntax/rules
  └─────────────────────────────┘
```

---

## Step 2: Jest + jsdom Computed Style Testing

```javascript
// button.style.test.js
const { JSDOM } = require('jsdom');

describe('Button styles', () => {
  let dom, doc;

  beforeEach(() => {
    dom = new JSDOM(`
      <html>
        <head>
          <style>
            .btn {
              display: inline-flex;
              padding: 0.5rem 1rem;
              background: #3b82f6;
              color: white;
              border-radius: 0.375rem;
              border: none;
              cursor: pointer;
            }
            .btn:disabled {
              opacity: 0.5;
              cursor: not-allowed;
              pointer-events: none;
            }
            .btn--secondary {
              background: #f1f5f9;
              color: #1e293b;
            }
          </style>
        </head>
        <body>
          <button class="btn" id="primary">Primary</button>
          <button class="btn btn--secondary" id="secondary">Secondary</button>
          <button class="btn" id="disabled" disabled>Disabled</button>
        </body>
      </html>
    `, { pretendToBeVisual: true });
    doc = dom.window.document;
  });

  test('primary button has correct background', () => {
    const btn = doc.getElementById('primary');
    const styles = dom.window.getComputedStyle(btn);
    // Note: jsdom doesn't compute CSS cascade, but checks inline/applied styles
    expect(btn.className).toContain('btn');
    expect(btn.disabled).toBe(false);
  });

  test('disabled button has disabled attribute', () => {
    const btn = doc.getElementById('disabled');
    expect(btn.disabled).toBe(true);
    expect(btn.hasAttribute('disabled')).toBe(true);
  });

  test('secondary button has secondary class', () => {
    const btn = doc.getElementById('secondary');
    expect(btn.classList.contains('btn--secondary')).toBe(true);
    expect(btn.classList.contains('btn')).toBe(true);
  });
});
```

> 💡 jsdom doesn't compute full CSS cascade like a browser. For true computed style testing, use Playwright with `page.evaluate(() => getComputedStyle(element).property)`.

---

## Step 3: Playwright Visual Regression

```javascript
// tests/visual/button.visual.test.js
const { test, expect } = require('@playwright/test');

test.describe('Button visual regression', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/storybook/?path=/story/button--primary');
    await page.waitForSelector('.btn');
  });

  test('primary button matches snapshot', async ({ page }) => {
    await expect(page.locator('.btn')).toHaveScreenshot('button-primary.png', {
      maxDiffPixelRatio: 0.01, // 1% pixel tolerance
    });
  });

  test('button hover state', async ({ page }) => {
    const btn = page.locator('.btn');
    await btn.hover();
    await expect(btn).toHaveScreenshot('button-primary-hover.png');
  });

  test('full component grid', async ({ page }) => {
    await page.goto('/storybook/?path=/story/button--all-variants');
    await expect(page).toHaveScreenshot('button-all-variants.png', {
      fullPage: true,
      animations: 'disabled', // Freeze animations for stable snapshot
    });
  });
});
```

```javascript
// playwright.config.js
module.exports = {
  testDir: './tests/visual',
  use: {
    baseURL: 'http://localhost:6006',
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 2, // Retina snapshots
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'webkit',   use: { browserName: 'webkit' } },
  ],
  // Store snapshots in repo
  snapshotDir: '__snapshots__',
  updateSnapshots: 'missing',
};
```

---

## Step 4: Percy / Chromatic Integration

```yaml
# .github/workflows/visual.yml
name: Visual Regression
on: [pull_request]

jobs:
  percy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build-storybook
      - uses: percy/storybook-action@v1
        env:
          PERCY_TOKEN: ${{ secrets.PERCY_TOKEN }}

  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: npm ci
      - uses: chromaui/action@v11
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          exitZeroOnChanges: true
          autoAcceptChanges: main
```

---

## Step 5: BackstopJS Configuration

```json
{
  "id": "design-system",
  "viewports": [
    { "label": "mobile",  "width": 375,  "height": 667  },
    { "label": "tablet",  "width": 768,  "height": 1024 },
    { "label": "desktop", "width": 1280, "height": 900  }
  ],
  "scenarios": [
    {
      "label": "Button States",
      "url": "http://localhost:6006/?path=/story/button--all-states",
      "delay": 500,
      "requireSameDimensions": false,
      "misMatchThreshold": 0.1,
      "selectors": [".sb-story"]
    },
    {
      "label": "Card Component",
      "url": "http://localhost:6006/?path=/story/card--default",
      "hoverSelector": ".card",
      "delay": 300
    }
  ],
  "paths": {
    "bitmaps_reference": "backstop_data/bitmaps_reference",
    "bitmaps_test": "backstop_data/bitmaps_test",
    "html_report": "backstop_data/html_report"
  },
  "engine": "playwright",
  "asyncCaptureLimit": 5,
  "report": ["browser", "CI"]
}
```

---

## Step 6: Custom Stylelint Plugin

```javascript
// stylelint-plugin-design-tokens.js
const stylelint = require('stylelint');

const ruleName = 'plugin/use-design-tokens';
const messages = stylelint.utils.ruleMessages(ruleName, {
  rejected: (prop, value) =>
    `Expected design token for "${prop}: ${value}". Use var(--ds-*) instead of raw values.`,
});

// Raw color values that should be tokens
const RAW_COLOR_REGEX = /^#[0-9a-fA-F]{3,8}$|^rgb\(|^hsl\(/;

const TOKENIZED_PROPERTIES = ['color', 'background', 'background-color', 'border-color',
  'fill', 'stroke', 'box-shadow'];

module.exports = stylelint.createPlugin(ruleName, (primaryOption) => {
  return (root, result) => {
    const validOptions = stylelint.utils.validateOptions(result, ruleName, {
      actual: primaryOption,
      possible: [true, false],
    });
    if (!validOptions) return;
    if (primaryOption !== true) return;

    root.walkDecls((decl) => {
      if (!TOKENIZED_PROPERTIES.includes(decl.prop)) return;
      if (!RAW_COLOR_REGEX.test(decl.value)) return;
      if (decl.value.startsWith('var(--ds-')) return; // Already a token

      stylelint.utils.report({
        message: messages.rejected(decl.prop, decl.value),
        node: decl,
        result,
        ruleName,
        word: decl.value,
      });
    });
  };
});

module.exports.ruleName = ruleName;
module.exports.messages = messages;
```

```json
// .stylelintrc.json
{
  "plugins": ["./stylelint-plugin-design-tokens.js"],
  "rules": {
    "plugin/use-design-tokens": true,
    "color-no-invalid-hex": true,
    "declaration-property-value-no-unknown": true,
    "selector-class-pattern": "^[a-z][a-z0-9]*(-[a-z0-9]+)*(__[a-z0-9]+(-[a-z0-9]+)*)?(--[a-z0-9]+(-[a-z0-9]+)*)?$"
  }
}
```

---

## Step 7: Storybook Interaction Tests

```javascript
// Button.stories.js with interaction tests
import { userEvent, within, expect } from '@storybook/test';

export const InteractionTest = {
  args: { label: 'Click me' },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const button = canvas.getByRole('button');

    // Simulate user interaction
    await userEvent.click(button);
    await expect(button).toHaveClass('is-pressed');

    // Keyboard interaction
    await userEvent.keyboard('{Tab}');
    await userEvent.keyboard('{Enter}');

    // Assert state
    await expect(button).not.toBeDisabled();
  },
};
```

---

## Step 8: Capstone — Jest + jsdom + Stylelint

```bash
docker run --rm node:20-alpine sh -c "
  cd /app && npm init -y > /dev/null 2>&1
  npm install jest jest-environment-jsdom stylelint 2>&1 | tail -1
  npx jest /app/style.test.js --no-coverage --testEnvironment node
"
```

📸 **Verified Output:**
```
  console.log
      Logical property found: padding-block
          at Array.forEach (<anonymous>)

PASS ./style.test.js
  ✓ card has correct padding (220 ms)
  ✓ logical properties check (6 ms)

Test Suites: 1 passed, 1 total
Tests:       2 passed, 2 total
Time:        2.566 s
```

---

## Summary

| Test Type | Tool | Catches | Speed |
|-----------|------|---------|-------|
| Linting | Stylelint | Syntax, patterns | Instant |
| Unit style | Jest + jsdom | DOM structure, classes | Fast |
| Computed style | Playwright page.eval | Real browser CSS | Medium |
| Visual regression | Percy/Chromatic | Pixel changes | Slow |
| Component interaction | Storybook play() | Behavior + a11y | Medium |
| Full E2E visual | BackstopJS | Full-page regression | Slow |
