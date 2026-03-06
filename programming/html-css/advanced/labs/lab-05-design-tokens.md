# Lab 05: Design Tokens

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Implement a complete Design Token pipeline: W3C Design Token format, three-tier token architecture (primitive → semantic → component), Style Dictionary transformation, and multi-platform output (CSS custom properties, iOS Swift, Android XML).

---

## Step 1: W3C Design Token Format

```json
// tokens.json — W3C Community Group format
{
  "color": {
    "blue": {
      "50":  { "$value": "#eff6ff", "$type": "color", "$description": "Lightest blue" },
      "100": { "$value": "#dbeafe", "$type": "color" },
      "200": { "$value": "#bfdbfe", "$type": "color" },
      "300": { "$value": "#93c5fd", "$type": "color" },
      "400": { "$value": "#60a5fa", "$type": "color" },
      "500": { "$value": "#3b82f6", "$type": "color", "$description": "Brand primary" },
      "600": { "$value": "#2563eb", "$type": "color" },
      "700": { "$value": "#1d4ed8", "$type": "color" },
      "800": { "$value": "#1e40af", "$type": "color" },
      "900": { "$value": "#1e3a8a", "$type": "color", "$description": "Darkest blue" }
    },
    "gray": {
      "50":  { "$value": "#f9fafb", "$type": "color" },
      "100": { "$value": "#f3f4f6", "$type": "color" },
      "500": { "$value": "#6b7280", "$type": "color" },
      "900": { "$value": "#111827", "$type": "color" }
    }
  },
  "spacing": {
    "1": { "$value": "4px",  "$type": "dimension" },
    "2": { "$value": "8px",  "$type": "dimension" },
    "3": { "$value": "12px", "$type": "dimension" },
    "4": { "$value": "16px", "$type": "dimension" },
    "6": { "$value": "24px", "$type": "dimension" },
    "8": { "$value": "32px", "$type": "dimension" }
  },
  "border-radius": {
    "none": { "$value": "0px",     "$type": "dimension" },
    "sm":   { "$value": "4px",     "$type": "dimension" },
    "md":   { "$value": "8px",     "$type": "dimension" },
    "lg":   { "$value": "12px",    "$type": "dimension" },
    "xl":   { "$value": "16px",    "$type": "dimension" },
    "full": { "$value": "9999px",  "$type": "dimension" }
  },
  "font-size": {
    "xs":  { "$value": "12px", "$type": "dimension" },
    "sm":  { "$value": "14px", "$type": "dimension" },
    "md":  { "$value": "16px", "$type": "dimension" },
    "lg":  { "$value": "18px", "$type": "dimension" },
    "xl":  { "$value": "20px", "$type": "dimension" },
    "2xl": { "$value": "24px", "$type": "dimension" },
    "3xl": { "$value": "30px", "$type": "dimension" },
    "4xl": { "$value": "36px", "$type": "dimension" }
  }
}
```

---

## Step 2: Three-Tier Token Architecture

```
Tier 1: Primitive (Global) Tokens
  — Raw design decisions, no context
  — e.g., --blue-500: #3b82f6
  — Never used directly in components

Tier 2: Semantic Tokens
  — Purpose-based, reference primitives
  — e.g., --color-brand: {color.blue.500}
  — Used in component tokens and CSS

Tier 3: Component Tokens
  — Component-specific, reference semantics
  — e.g., --button-bg: {color.brand}
  — Used directly in component CSS
```

```json
// semantic-tokens.json
{
  "semantic": {
    "color": {
      "brand": {
        "$value": "{color.blue.500}",
        "$type": "color",
        "$description": "Primary brand color"
      },
      "brand-hover": {
        "$value": "{color.blue.600}",
        "$type": "color"
      },
      "text": {
        "default": { "$value": "{color.gray.900}", "$type": "color" },
        "muted":   { "$value": "{color.gray.500}", "$type": "color" },
        "inverse": { "$value": "#ffffff", "$type": "color" }
      },
      "bg": {
        "page":    { "$value": "#ffffff", "$type": "color" },
        "surface": { "$value": "{color.gray.50}", "$type": "color" }
      },
      "border": {
        "default": { "$value": "{color.gray.100}", "$type": "color" }
      }
    }
  }
}
```

---

## Step 3: Style Dictionary Configuration

```javascript
// style-dictionary.config.js
const StyleDictionary = require('style-dictionary');

// Register custom transform: px to rem
StyleDictionary.registerTransform({
  name: 'size/pxToRem',
  type: 'value',
  matcher: (token) => token.$type === 'dimension',
  transformer: (token) => {
    const value = parseFloat(token.$value);
    if (token.$value.endsWith('px') && token.attributes.category !== 'border-radius') {
      return `${value / 16}rem`;
    }
    return token.$value;
  }
});

// Register custom format: CSS variables
StyleDictionary.registerFormat({
  name: 'css/custom-properties',
  formatter: ({ dictionary }) => {
    const vars = dictionary.allTokens
      .map(token => `  --${token.path.join('-')}: ${token.value};`)
      .join('\n');
    return `:root {\n${vars}\n}\n`;
  }
});

module.exports = {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      prefix: '',
      buildPath: 'dist/css/',
      files: [{
        destination: 'tokens.css',
        format: 'css/variables',
        options: { outputReferences: true }
      }]
    },
    ios: {
      transformGroup: 'ios-swift',
      buildPath: 'dist/ios/',
      files: [{
        destination: 'StyleTokens.swift',
        format: 'ios-swift/class.swift'
      }]
    },
    android: {
      transformGroup: 'android',
      buildPath: 'dist/android/',
      files: [{
        destination: 'tokens.xml',
        format: 'android/colors'
      }]
    }
  }
};
```

---

## Step 4: Platform Output Examples

**CSS Custom Properties output:**
```css
/* dist/css/tokens.css */
:root {
  --color-blue-50: #eff6ff;
  --color-blue-500: #3b82f6;
  --color-blue-900: #1e3a8a;
  --color-gray-50: #f9fafb;
  --color-gray-900: #111827;

  --semantic-color-brand: var(--color-blue-500);
  --semantic-color-brand-hover: var(--color-blue-600);
  --semantic-color-text-default: var(--color-gray-900);
  --semantic-color-bg-page: #ffffff;

  --spacing-1: 0.25rem;
  --spacing-4: 1rem;
  --spacing-8: 2rem;

  --border-radius-sm: 4px;
  --border-radius-md: 8px;
}
```

**iOS Swift output:**
```swift
// dist/ios/StyleTokens.swift
import UIKit

public class StyleTokens {
    public static let colorBlue50  = UIColor(hex: "#eff6ff")
    public static let colorBlue500 = UIColor(hex: "#3b82f6")
    public static let colorBlue900 = UIColor(hex: "#1e3a8a")

    public static let semanticColorBrand = colorBlue500
    public static let spacingBase = CGFloat(16)
}
```

**Android XML output:**
```xml
<!-- dist/android/tokens.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<resources>
    <color name="color_blue_50">#eff6ff</color>
    <color name="color_blue_500">#3b82f6</color>
    <color name="color_blue_900">#1e3a8a</color>
    <color name="semantic_color_brand">@color/color_blue_500</color>
    <dimen name="spacing_1">4dp</dimen>
    <dimen name="spacing_4">16dp</dimen>
    <dimen name="border_radius_md">8dp</dimen>
</resources>
```

---

## Step 5: Dark Mode Token Overrides

```json
// tokens/themes/dark.json
{
  "semantic": {
    "color": {
      "text": {
        "default": { "$value": "{color.gray.50}",  "$type": "color" },
        "muted":   { "$value": "{color.gray.400}", "$type": "color" }
      },
      "bg": {
        "page":    { "$value": "#0f172a", "$type": "color" },
        "surface": { "$value": "#1e293b", "$type": "color" }
      },
      "brand": {
        "$value": "{color.blue.400}", "$type": "color"
      }
    }
  }
}
```

```css
/* Generated dark mode override */
[data-theme="dark"] {
  --semantic-color-text-default: var(--color-gray-50);
  --semantic-color-bg-page: #0f172a;
  --semantic-color-brand: var(--color-blue-400);
}
```

---

## Step 6: Component Token Usage

```css
/* Button component tokens */
.btn {
  --btn-bg:         var(--semantic-color-brand);
  --btn-bg-hover:   var(--semantic-color-brand-hover);
  --btn-color:      var(--semantic-color-text-inverse);
  --btn-radius:     var(--border-radius-md);
  --btn-padding-x:  var(--spacing-4);
  --btn-padding-y:  var(--spacing-2);
  --btn-font-size:  var(--font-size-sm);

  /* Apply component tokens */
  background: var(--btn-bg);
  color: var(--btn-color);
  border-radius: var(--btn-radius);
  padding: var(--btn-padding-y) var(--btn-padding-x);
  font-size: var(--btn-font-size);
}

.btn:hover {
  background: var(--btn-bg-hover);
}

/* Override per instance */
.btn-danger {
  --btn-bg: var(--color-red-500);
  --btn-bg-hover: var(--color-red-600);
}
```

---

## Step 7: Token Naming Conventions

```
Naming pattern: {tier}-{category}-{property}-{variant}-{state}

Primitive:  color-blue-500
            spacing-4
            border-radius-md

Semantic:   color-text-default
            color-bg-surface
            color-brand

Component:  button-bg
            button-bg-hover
            input-border-focus
            card-padding
            nav-height
```

---

## Step 8: Capstone — Style Dictionary Token Transformer

```bash
docker run --rm -v /tmp/style_dict.js:/test.js node:20-alpine node /test.js
```

*(Create the file:)*
```bash
cat > /tmp/style_dict.js << 'EOF'
var tokens = {
  color: {
    primitive: {
      "blue-500": {"$value":"#3b82f6","$type":"color"},
      "blue-600": {"$value":"#2563eb","$type":"color"},
      "gray-100": {"$value":"#f3f4f6","$type":"color"},
      "gray-900": {"$value":"#111827","$type":"color"}
    },
    semantic: {
      "brand-primary": {"$value":"{color.primitive.blue-500}","$type":"color"},
      "text-default":  {"$value":"{color.primitive.gray-900}","$type":"color"},
      "bg-surface":    {"$value":"{color.primitive.gray-100}","$type":"color"}
    }
  },
  spacing: {
    base: {"$value":"4px","$type":"dimension"},
    sm:   {"$value":"8px","$type":"dimension"},
    md:   {"$value":"16px","$type":"dimension"},
    lg:   {"$value":"32px","$type":"dimension"}
  }
};
var primitives = {
  "{color.primitive.blue-500}": "#3b82f6",
  "{color.primitive.gray-900}": "#111827",
  "{color.primitive.gray-100}": "#f3f4f6"
};
console.log("/* Generated CSS Custom Properties */");
console.log(":root {");
Object.entries(tokens.color.primitive).forEach(function(e){
  console.log("  --color-" + e[0] + ": " + e[1]["$value"] + ";");
});
Object.entries(tokens.color.semantic).forEach(function(e){
  var val = primitives[e[1]["$value"]] || e[1]["$value"];
  console.log("  --" + e[0] + ": " + val + ";");
});
Object.entries(tokens.spacing).forEach(function(e){
  if(e[1]["$value"]) console.log("  --spacing-" + e[0] + ": " + e[1]["$value"] + ";");
});
console.log("}");
EOF
docker run --rm -v /tmp/style_dict.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
/* Generated CSS Custom Properties */
:root {
  --color-blue-500: #3b82f6;
  --color-blue-600: #2563eb;
  --color-gray-100: #f3f4f6;
  --color-gray-900: #111827;
  --brand-primary: #3b82f6;
  --text-default: #111827;
  --bg-surface: #f3f4f6;
  --spacing-base: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 32px;
}
```

---

## Summary

| Concept | W3C Token Format | Tool |
|---------|-----------------|------|
| Token file | JSON with `$value`, `$type` | Any editor |
| Transform | Primitive → Semantic → Component | Style Dictionary |
| CSS output | `:root { --token: value; }` | `css/variables` format |
| iOS output | Swift UIColor/CGFloat | `ios-swift` format |
| Android output | `res/values/colors.xml` | `android/colors` format |
| Dark mode | Override semantic tokens | `[data-theme="dark"]` |
| References | `"{other.token.path}"` | Style Dictionary resolves |
| Component tokens | Component-level CSS vars | Manual or generated |
