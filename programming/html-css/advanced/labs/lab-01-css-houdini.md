# Lab 01: CSS Houdini

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Explore CSS Houdini APIs: `@property` with typed syntax, animatable custom properties, CSS Typed OM simulation, the Paint API concept, and browser support status.

---

## Step 1: @property — Registered Custom Properties

```css
/* Unregistered: browser treats as opaque string, can't animate */
:root { --angle: 0deg; }
/* transition: --angle 1s; */  /* WON'T WORK — browser doesn't know it's an angle */

/* @property: tell the browser the TYPE */
@property --angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

@property --brand-color {
  syntax: '<color>';
  inherits: true;
  initial-value: #3b82f6;
}

@property --progress {
  syntax: '<number>';
  inherits: false;
  initial-value: 0;
}

@property --gradient-stop {
  syntax: '<percentage>';
  inherits: false;
  initial-value: 0%;
}

/* Now these ARE animatable! */
.animated-gradient {
  background: conic-gradient(from var(--angle), blue, purple, blue);
  transition: --angle 1s ease;
}

.animated-gradient:hover {
  --angle: 180deg; /* smoothly interpolates! */
}
```

---

## Step 2: Syntax Types Reference

```css
/* All valid @property syntax values */

/* Primitives */
@property --my-color      { syntax: '<color>'; }
@property --my-length     { syntax: '<length>'; }
@property --my-number     { syntax: '<number>'; }
@property --my-percent    { syntax: '<percentage>'; }
@property --my-angle      { syntax: '<angle>'; }
@property --my-time       { syntax: '<time>'; }
@property --my-resolution { syntax: '<resolution>'; }
@property --my-transform  { syntax: '<transform-function>'; }
@property --my-transforms { syntax: '<transform-list>'; }
@property --my-image      { syntax: '<image>'; }

/* Length or percentage */
@property --my-len-pct { syntax: '<length-percentage>'; }

/* Space-separated list */
@property --my-colors {
  syntax: '<color>+';   /* one or more */
  inherits: true;
  initial-value: black;
}

/* Or-separated */
@property --my-mixed {
  syntax: '<color> | <length>';
  inherits: false;
  initial-value: 0px;
}

/* Any value (no type checking, like unregistered) */
@property --my-any {
  syntax: '*';
  inherits: false;
  initial-value: ;
}
```

> 💡 `inherits: true` means child elements inherit the value. `inherits: false` means each element gets its own copy — important for per-element animations.

---

## Step 3: Animated Conic Gradient

```css
@property --gradient-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

@keyframes rotate-gradient {
  0%   { --gradient-angle: 0deg; }
  100% { --gradient-angle: 360deg; }
}

.spinning-border {
  position: relative;
  border-radius: 12px;
  padding: 2px; /* border width */
  background: conic-gradient(
    from var(--gradient-angle),
    #3b82f6,
    #8b5cf6,
    #ec4899,
    #3b82f6
  );
  animation: rotate-gradient 3s linear infinite;
}

.spinning-border__inner {
  background: white;
  border-radius: 10px;
  padding: 1rem;
}
```

---

## Step 4: Per-Element Animation with inherits: false

```css
@property --progress {
  syntax: '<number>';
  inherits: false;  /* CRITICAL: each element gets own copy */
  initial-value: 0;
}

@keyframes fill-progress {
  to { --progress: 1; }
}

/* Each bar animates independently with different durations */
.progress-bar {
  width: calc(var(--progress) * var(--target-width, 100%));
  background: var(--color-primary);
  height: 8px;
  border-radius: 4px;
  animation: fill-progress 1s ease-out forwards;
}

.progress-bar:nth-child(1) { --target-width: 85%; animation-delay: 0s; }
.progress-bar:nth-child(2) { --target-width: 65%; animation-delay: 0.2s; }
.progress-bar:nth-child(3) { --target-width: 42%; animation-delay: 0.4s; }
```

---

## Step 5: CSS Typed OM Concept

CSS Typed OM (`computedStyleMap()`) provides typed access to CSS values:

```javascript
// Traditional (string-based):
const color = getComputedStyle(el).getPropertyValue('color');
// => "rgb(59, 130, 246)" — a string you have to parse

// CSS Typed OM (type-safe):
const styleMap = el.computedStyleMap();

// Length value
const width = styleMap.get('width');
// => CSSUnitValue { value: 200, unit: "px" }
width.value; // 200
width.unit;  // "px"

// Convert units
const inRem = width.to('rem');
// => CSSUnitValue { value: 12.5, unit: "rem" }

// Color (not yet standardized across browsers)
const bg = styleMap.get('background-color');

// Transform
const transform = styleMap.get('transform');
// => CSSTransformValue [CSSTranslate, CSSRotate, ...]

// Computed style for custom property
const progress = styleMap.get('--progress');
// => CSSUnparsedValue (unregistered) OR typed value (if @property used)

// CSS.px(), CSS.percent(), CSS.number()
el.attributeStyleMap.set('width', CSS.px(200));
el.attributeStyleMap.set('opacity', CSS.number(0.5));
el.attributeStyleMap.set('--progress', CSS.number(0.75));
```

---

## Step 6: Paint API Concept

The CSS Paint API (Houdini) lets JavaScript define custom CSS images:

```javascript
// paint-worklet.js — registered as a worklet
registerPaint('checkerboard', class {
  static get inputProperties() {
    return ['--checker-size', '--checker-color-1', '--checker-color-2'];
  }
  
  paint(ctx, size, properties) {
    const checkerSize = parseInt(properties.get('--checker-size')) || 20;
    const color1 = properties.get('--checker-color-1').toString() || 'white';
    const color2 = properties.get('--checker-color-2').toString() || '#eee';
    
    for (let x = 0; x < size.width / checkerSize; x++) {
      for (let y = 0; y < size.height / checkerSize; y++) {
        ctx.fillStyle = (x + y) % 2 === 0 ? color1 : color2;
        ctx.fillRect(x * checkerSize, y * checkerSize, checkerSize, checkerSize);
      }
    }
  }
});
```

```javascript
// Register the worklet
CSS.paintWorklet.addModule('paint-worklet.js');
```

```css
/* Use in CSS */
.checker-bg {
  --checker-size: 20;
  --checker-color-1: white;
  --checker-color-2: #e5e7eb;
  background: paint(checkerboard);
}
```

---

## Step 7: Houdini Browser Support (2024)

```
API                          Chrome  Firefox  Safari  Node
───────────────────────────────────────────────────────────
@property                      ✓       ✓       ✓      N/A
CSS.registerProperty()         ✓       ✓       ✓      N/A
CSS Typed OM (attributeStyleMap) ✓     ~       ~      N/A
CSS Paint API (Houdini)        ✓       ✗       ✗      N/A
Layout API                     🧪      ✗       ✗      N/A
Animation Worklet              🧪      ✗       ✗      N/A

✓ = Supported  ~ = Partial  ✗ = Not supported  🧪 = Behind flag
```

```css
/* Progressive enhancement with @supports */
@supports (background: paint(anything)) {
  .paint-api-enhanced {
    background: paint(my-pattern);
  }
}

/* Fallback for non-Paint API browsers */
.paint-api-element {
  background: #e5e7eb; /* fallback */
}
@supports (background: paint(anything)) {
  .paint-api-element {
    background: paint(checkerboard);
  }
}
```

---

## Step 8: Capstone — @property Syntax Generator

```bash
docker run --rm -v /tmp/houdini_test.js:/test.js node:20-alpine node /test.js
```

*(First create the file:)*
```bash
cat > /tmp/houdini_test.js << 'EOF'
var properties = [
  {name:"--brand-color",syntax:"<color>",inherits:"true",initial:"#3b82f6"},
  {name:"--spacing-base",syntax:"<length>",inherits:"true",initial:"16px"},
  {name:"--animation-progress",syntax:"<number>",inherits:"false",initial:"0"},
  {name:"--gradient-angle",syntax:"<angle>",inherits:"false",initial:"0deg"},
];
properties.forEach(function(p){
  console.log("@property " + p.name + " {");
  console.log("  syntax: '" + p.syntax + "';");
  console.log("  inherits: " + p.inherits + ";");
  console.log("  initial-value: " + p.initial + ";");
  console.log("}");
});
EOF
docker run --rm -v /tmp/houdini_test.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
@property --brand-color {
  syntax: '<color>';
  inherits: true;
  initial-value: #3b82f6;
}
@property --spacing-base {
  syntax: '<length>';
  inherits: true;
  initial-value: 16px;
}
@property --animation-progress {
  syntax: '<number>';
  inherits: false;
  initial-value: 0;
}
@property --gradient-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}
```

---

## Summary

| Feature | Syntax | Support |
|---------|--------|---------|
| `@property` declaration | `syntax`, `inherits`, `initial-value` | Chrome/FF/Safari ✓ |
| Animatable color | `syntax: '<color>'` | All modern ✓ |
| Animatable angle | `syntax: '<angle>'` | All modern ✓ |
| Per-element animation | `inherits: false` | All modern ✓ |
| Typed OM | `el.computedStyleMap()` | Chrome ~, limited |
| Paint API | `CSS.paintWorklet.addModule()` | Chrome only ✗ |
| `CSS.px()` factory | `CSS.px(200)` | Chrome ✓ |
| `@supports` guard | `@supports (background: paint(x))` | Feature-detect |
