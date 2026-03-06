# Lab 01: Design System Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Build a production design system using a multi-tier token architecture (primitive → semantic → component), automated Style Dictionary pipelines, and versioning strategies for cross-platform delivery.

---

## Step 1: Token Architecture — Three-Tier Model

Design tokens follow a strict hierarchy: **Primitive → Semantic → Component**.

```
tokens/
├── primitive/
│   ├── colors.json       # Raw values: blue-500: #3b82f6
│   ├── spacing.json      # Raw values: 4: 0.25rem
│   └── typography.json   # Raw values: font-size-base: 1rem
├── semantic/
│   ├── colors.json       # Aliases: brand-primary → {color.primitive.blue.500}
│   └── spacing.json      # Aliases: component-padding → {spacing.4}
└── component/
    └── button.json       # btn-bg → {color.semantic.brand.primary}
```

**Primitive tokens** — raw values with no semantic meaning:
```json
{
  "color": {
    "primitive": {
      "blue": {
        "100": { "value": "#dbeafe", "type": "color" },
        "500": { "value": "#3b82f6", "type": "color" },
        "900": { "value": "#1e3a5f", "type": "color" }
      },
      "neutral": {
        "0":   { "value": "#ffffff", "type": "color" },
        "100": { "value": "#f8fafc", "type": "color" },
        "900": { "value": "#0f172a", "type": "color" }
      }
    }
  }
}
```

> 💡 Never reference primitive tokens directly in components. Always go through semantic tokens — this is what enables theming.

---

## Step 2: Semantic Token Layer

```json
{
  "color": {
    "semantic": {
      "brand": {
        "primary":   { "value": "{color.primitive.blue.500}", "type": "color" },
        "primary-subtle": { "value": "{color.primitive.blue.100}", "type": "color" }
      },
      "background": {
        "default":   { "value": "{color.primitive.neutral.0}", "type": "color" },
        "subtle":    { "value": "{color.primitive.neutral.100}", "type": "color" },
        "inverse":   { "value": "{color.primitive.neutral.900}", "type": "color" }
      },
      "text": {
        "primary":   { "value": "{color.primitive.neutral.900}", "type": "color" },
        "inverse":   { "value": "{color.primitive.neutral.0}", "type": "color" }
      }
    }
  }
}
```

---

## Step 3: Component Token Layer

```json
{
  "component": {
    "button": {
      "primary": {
        "background":    { "value": "{color.semantic.brand.primary}", "type": "color" },
        "color":         { "value": "{color.semantic.text.inverse}", "type": "color" },
        "border-radius": { "value": "0.375rem", "type": "dimension" },
        "padding":       { "value": "0.5rem 1rem", "type": "spacing" }
      }
    },
    "card": {
      "background":  { "value": "{color.semantic.background.default}", "type": "color" },
      "border":      { "value": "1px solid {color.primitive.neutral.100}", "type": "border" },
      "shadow":      { "value": "0 1px 3px rgba(0,0,0,0.12)", "type": "shadow" }
    }
  }
}
```

---

## Step 4: Style Dictionary Pipeline Configuration

```javascript
// style-dictionary.config.js
const StyleDictionary = require('style-dictionary');

// Custom transform: px to rem
StyleDictionary.registerTransform({
  name: 'size/pxToRem',
  type: 'value',
  matcher: token => token.attributes.category === 'size',
  transformer: token => `${parseFloat(token.value) / 16}rem`,
});

// Custom format: typed TypeScript constants
StyleDictionary.registerFormat({
  name: 'typescript/constants',
  formatter: ({ dictionary }) => {
    const entries = dictionary.allTokens
      .map(t => `export const ${t.name.toUpperCase().replace(/-/g,'_')} = '${t.value}';`)
      .join('\n');
    return `// Auto-generated design tokens\n${entries}\n`;
  },
});

module.exports = {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      prefix: 'ds',
      buildPath: 'dist/css/',
      files: [{
        destination: 'tokens.css',
        format: 'css/variables',
        options: { outputReferences: true },
      }],
    },
    ios: {
      transformGroup: 'ios-swift',
      buildPath: 'dist/ios/',
      files: [{
        destination: 'StyleDictionary.swift',
        format: 'ios-swift/class.swift',
      }],
    },
    android: {
      transformGroup: 'android',
      buildPath: 'dist/android/',
      files: [{
        destination: 'tokens.xml',
        format: 'android/resources',
      }],
    },
    typescript: {
      transformGroup: 'js',
      buildPath: 'dist/ts/',
      files: [{
        destination: 'tokens.ts',
        format: 'typescript/constants',
      }],
    },
  },
};
```

> 💡 `outputReferences: true` preserves CSS custom property references (`var(--ds-color-primitive-blue-500)`) instead of resolved values — crucial for runtime theming.

---

## Step 5: Run the Pipeline

```bash
# Install and run
npm install style-dictionary
npx style-dictionary build

# Expected output:
# css
# ✔︎ dist/css/tokens.css
# ios
# ✔︎ dist/ios/StyleDictionary.swift
# android
# ✔︎ dist/android/tokens.xml
# typescript
# ✔︎ dist/ts/tokens.ts
```

---

## Step 6: Versioning Strategy

```json
// package.json for your design token package
{
  "name": "@company/design-tokens",
  "version": "2.1.0",
  "description": "Design tokens for all platforms",
  "main": "dist/ts/tokens.js",
  "exports": {
    ".": "./dist/ts/tokens.js",
    "./css": "./dist/css/tokens.css",
    "./ios": "./dist/ios/StyleDictionary.swift"
  },
  "files": ["dist/"],
  "scripts": {
    "build": "style-dictionary build",
    "prepublishOnly": "npm run build"
  }
}
```

**Semantic versioning rules for design tokens:**
- **PATCH** (2.1.0 → 2.1.1): New tokens, description updates
- **MINOR** (2.1.x → 2.2.0): Renamed tokens (keep old as deprecated aliases)
- **MAJOR** (2.x.x → 3.0.0): Removed tokens, breaking value changes

---

## Step 7: Storybook Integration Concept

```javascript
// .storybook/preview.js
import '@company/design-tokens/css';

// Token documentation addon
export const parameters = {
  designToken: {
    files: ['dist/css/tokens.css'],
    defaultTab: 'Color',
  },
};
```

```javascript
// Button.stories.js
export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    design: {
      type: 'figma',
      url: 'https://www.figma.com/file/...',
    },
  },
};

export const TokenShowcase = () => `
  <ds-button variant="primary">Primary</ds-button>
  <ds-button variant="secondary">Secondary</ds-button>
`;
TokenShowcase.storyName = 'Token Showcase';
```

---

## Step 8: Capstone — Full Pipeline Demo

```bash
docker run --rm node:20-alpine sh -c "
npm install -g style-dictionary --quiet 2>/dev/null
mkdir -p /tmp/tokens
cat > /tmp/tokens/colors.json << 'EOF'
{
  \"color\": {
    \"primitive\": {
      \"blue\": { \"100\": { \"value\": \"#dbeafe\", \"type\": \"color\" }, \"500\": { \"value\": \"#3b82f6\", \"type\": \"color\" }, \"900\": { \"value\": \"#1e3a5f\", \"type\": \"color\" } }
    },
    \"semantic\": {
      \"brand\": { \"primary\": { \"value\": \"{color.primitive.blue.500}\", \"type\": \"color\" } },
      \"background\": { \"default\": { \"value\": \"{color.primitive.blue.100}\", \"type\": \"color\" } }
    }
  }
}
EOF
cat > /tmp/config.json << 'EOF'
{
  \"source\": [\"/tmp/tokens/**/*.json\"],
  \"platforms\": {
    \"css\": {
      \"transformGroup\": \"css\",
      \"prefix\": \"ds\",
      \"buildPath\": \"/tmp/build/\",
      \"files\": [{ \"destination\": \"tokens.css\", \"format\": \"css/variables\" }]
    }
  }
}
EOF
cd /tmp && style-dictionary build --config /tmp/config.json && cat /tmp/build/tokens.css
"
```

📸 **Verified Output:**
```
css
✔︎ /tmp/build/tokens.css
/**
 * Do not edit directly, this file was auto-generated.
 */

:root {
  --ds-color-primitive-blue-100: #dbeafe;
  --ds-color-primitive-blue-500: #3b82f6;
  --ds-color-primitive-blue-900: #1e3a5f;
  --ds-color-semantic-brand-primary: #3b82f6;
  --ds-color-semantic-background-default: #dbeafe;
}
```

---

## Summary

| Concept | Tool/Pattern | Output |
|---------|-------------|--------|
| Primitive tokens | JSON source files | Raw design decisions |
| Semantic tokens | Alias references | Themeable meanings |
| Component tokens | Semantic aliases | Component-specific CSS vars |
| CSS output | Style Dictionary | `--ds-*` custom properties |
| iOS output | Style Dictionary | Swift constants |
| Android output | Style Dictionary | XML resources |
| TypeScript output | Custom formatter | Typed constants |
| Versioning | Semantic versioning | Breaking change tracking |
| Documentation | Storybook + designToken addon | Living style guide |
