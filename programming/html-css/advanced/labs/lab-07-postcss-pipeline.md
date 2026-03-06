# Lab 07: PostCSS Pipeline

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build a complete PostCSS pipeline: configuration, autoprefixer, postcss-preset-env for modern CSS polyfills, cssnano for minification, and writing a custom PostCSS plugin.

---

## Step 1: PostCSS Fundamentals

PostCSS is a tool for transforming CSS with JavaScript plugins. It parses CSS into an AST, applies transforms, and outputs CSS.

```javascript
// postcss.config.js (CJS)
module.exports = {
  plugins: [
    require('postcss-import'),           // inline @import statements
    require('postcss-preset-env')({      // modern CSS → compatible CSS
      stage: 3,
      features: {
        'nesting-rules': true,
        'custom-media-queries': true,
        'media-query-ranges': true,
      }
    }),
    require('autoprefixer'),             // add vendor prefixes
    require('cssnano')({ preset: 'default' }), // minify
  ]
};

// postcss.config.mjs (ESM)
import postcssImport from 'postcss-import';
import postcssPresetEnv from 'postcss-preset-env';
import autoprefixer from 'autoprefixer';
import cssnano from 'cssnano';

export default {
  plugins: [
    postcssImport(),
    postcssPresetEnv({ stage: 3 }),
    autoprefixer(),
    cssnano({ preset: 'default' }),
  ]
};
```

---

## Step 2: postcss-preset-env

Transforms modern CSS to be compatible with older browsers, similar to Babel for JS:

```css
/* Input: modern CSS */

/* Nesting (native) */
.card {
  color: red;
  & .card__title {
    font-weight: bold;
  }
}

/* Custom media queries (draft) */
@custom-media --viewport-sm (width >= 640px);
@custom-media --viewport-md (width >= 768px);

@media (--viewport-md) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* Media query ranges */
@media (width >= 768px) and (width <= 1024px) {
  .container { max-width: 900px; }
}

/* :is() selector */
:is(h1, h2, h3) { font-family: serif; }

/* oklch() colors */
.button { background: oklch(57% 0.20 250); }

/* Color-mix */
.faded { color: color-mix(in oklch, blue 50%, white); }
```

```css
/* Output: compatible CSS */
.card { color: red; }
.card .card__title { font-weight: bold; }

@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 768px) and (max-width: 1024px) {
  .container { max-width: 900px; }
}

h1, h2, h3 { font-family: serif; }

.button { background: #3b82f6; } /* converted to hex */
```

---

## Step 3: Autoprefixer

```css
/* Input */
.flex-container {
  display: flex;
  user-select: none;
  backdrop-filter: blur(10px);
  appearance: none;
}

/* Output with autoprefixer */
.flex-container {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-user-select: none;
  -moz-user-select: none;
  user-select: none;
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
}
```

```json
// .browserslistrc — control which browsers to target
last 2 versions
> 1%
not dead
not ie 11
```

```json
// Or in package.json
{
  "browserslist": [
    "last 2 Chrome versions",
    "last 2 Firefox versions",
    "last 2 Safari versions",
    "last 2 Edge versions"
  ]
}
```

---

## Step 4: cssnano Optimization

```css
/* Input */
:root {
  --color-primary: #3b82f6;
}

.container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.button {
  background: var(--color-primary);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background 0.2s ease;
  
  &:hover {
    background: oklch(55% 0.2 250);
  }
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #60a5fa;
  }
}
```

```css
/* Output after cssnano */
:root{--color-primary:#3b82f6}.container{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}.button{background:var(--color-primary);border-radius:4px;padding:.5rem 1rem;transition:background .2s ease;&:hover{background:oklch(55% .2 250)}}@media (prefers-color-scheme:dark){:root{--color-primary:#60a5fa}}
```

---

## Step 5: Custom PostCSS Plugin

```javascript
// plugins/postcss-spacing-scale.js
// Transforms custom spacing notation: space(4) → calc(4 * 0.25rem)

const postcss = require('postcss');

module.exports = postcss.plugin('postcss-spacing-scale', (opts = {}) => {
  const base = opts.base || 0.25; // rem per unit
  const pattern = /space\((\d+(?:\.\d+)?)\)/g;

  return (root) => {
    root.walkDecls((decl) => {
      if (pattern.test(decl.value)) {
        decl.value = decl.value.replace(pattern, (match, n) => {
          const rem = parseFloat(n) * base;
          return `${rem}rem`;
        });
      }
    });
  };
});

// Input CSS:
// .card { padding: space(4) space(6); margin-top: space(8); }

// Output:
// .card { padding: 1rem 1.5rem; margin-top: 2rem; }
```

```javascript
// Advanced plugin: add CSS custom property fallbacks
const postcss = require('postcss');

module.exports = postcss.plugin('postcss-var-fallback', () => {
  return (root) => {
    // Walk all declarations
    root.walkDecls((decl) => {
      // Find declarations using CSS custom properties without fallback
      const varPattern = /var\((--[\w-]+)(?!\s*,)/g;
      
      if (varPattern.test(decl.value)) {
        // Add a warning comment before the declaration
        decl.before(postcss.comment({
          text: ` ⚠ var() missing fallback: ${decl.prop} `
        }));
      }
    });
  };
});
```

---

## Step 6: PostCSS CLI Usage

```bash
# Install
npm install -D postcss postcss-cli autoprefixer cssnano postcss-preset-env

# Process single file
npx postcss src/styles.css -o dist/styles.css

# Watch mode
npx postcss src/styles.css -o dist/styles.css --watch

# With config file
npx postcss src/*.css --dir dist/

# Without config file (inline plugins)
npx postcss input.css \
  --use autoprefixer \
  --use cssnano \
  -o output.css

# Map source maps
npx postcss src/styles.css -o dist/styles.css --map
```

---

## Step 7: Integration Examples

```javascript
// vite.config.js
import autoprefixer from 'autoprefixer';
import postcssPresetEnv from 'postcss-preset-env';

export default {
  css: {
    postcss: {
      plugins: [
        postcssPresetEnv({ stage: 3 }),
        autoprefixer()
      ]
    }
  }
};

// webpack.config.js (with css-loader)
module.exports = {
  module: {
    rules: [{
      test: /\.css$/,
      use: [
        'style-loader',
        'css-loader',
        {
          loader: 'postcss-loader',
          options: {
            postcssOptions: {
              plugins: [
                'postcss-preset-env',
                'autoprefixer',
                'cssnano'
              ]
            }
          }
        }
      ]
    }]
  }
};
```

---

## Step 8: Capstone — PostCSS Pipeline Verification

```bash
docker run --rm -v /tmp/postcss_test.css:/test.css node:20-alpine sh -c '
cd /tmp
npm init -y 2>/dev/null | grep name
npm install postcss autoprefixer cssnano postcss-preset-env 2>/dev/null | tail -1
node -e "
var postcss = require(\"/tmp/node_modules/postcss\");
var autoprefixer = require(\"/tmp/node_modules/autoprefixer\");
var cssnano = require(\"/tmp/node_modules/cssnano\");
var fs = require(\"fs\");
var css = fs.readFileSync(\"/test.css\", \"utf8\");
postcss([autoprefixer, cssnano({preset:\"default\"})]).process(css, {from:\"/test.css\"}).then(function(result){
  console.log(\"Original size: \" + css.length + \" bytes\");
  console.log(\"Minified size: \" + result.css.length + \" bytes\");
  console.log(\"Savings: \" + ((1-result.css.length/css.length)*100).toFixed(1) + \"%\");
  console.log(\"\");
  console.log(result.css);
}).catch(function(e){ console.error(e.message); });
"
'
```

📸 **Verified Output:**
```
"name": "tmp"
found 0 vulnerabilities
Original size: 419 bytes
Minified size: 333 bytes
Savings: 20.5%

:root{--color-primary:#3b82f6}.container{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}.button{background:var(--color-primary);border-radius:4px;padding:.5rem 1rem;transition:background .2s ease;&:hover{background:oklch(55% .2 250)}}@media (prefers-color-scheme:dark){:root{--color-primary:#60a5fa}}
```

---

## Summary

| Plugin | Purpose | Impact |
|--------|---------|--------|
| `postcss-import` | Inline `@import` | Bundle CSS |
| `postcss-preset-env` | Modern CSS polyfills | Cross-browser |
| `autoprefixer` | Vendor prefixes | Cross-browser |
| `cssnano` | Minification | Bundle size |
| `postcss-nested` | Sass-style nesting | DX |
| Custom plugin | Any transform | Extensibility |
| `.browserslistrc` | Target browsers | Controls prefixes |
| `--map` flag | Source maps | Debugging |
