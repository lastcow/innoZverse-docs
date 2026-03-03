# Lab 11: HTML Forms & CSS Styling

## Objective
Build beautiful, accessible, and user-friendly forms — from basic inputs to custom checkboxes, styled selects, and complete registration forms with validation states.

## Background
Forms are how users interact with your application. A poorly designed form loses customers; a well-designed one converts them. This lab covers all HTML form elements, CSS styling techniques, and validation states.

## Time
35 minutes

## Prerequisites
- Lab 08: CSS Grid
- Lab 09: Responsive Design

## Tools
```bash
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```

---

## Lab Instructions

### Step 1: Form Elements Reference

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Form Elements</title>
  <style>
    body { font-family: sans-serif; padding: 30px; max-width: 600px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; color: #2d3436; }
    input, textarea, select {
      width: 100%;
      padding: 10px 14px;
      border: 2px solid #dfe6e9;
      border-radius: 6px;
      font-size: 1rem;
      box-sizing: border-box;
      transition: border-color 0.2s ease;
    }
    input:focus, textarea:focus, select:focus {
      outline: none;
      border-color: #667eea;
    }
    .radio-group, .checkbox-group { display: flex; gap: 16px; flex-wrap: wrap; }
    .radio-label, .checkbox-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-weight: normal; }
  </style>
</head>
<body>
  <h2>HTML Form Elements</h2>
  <form>
    <!-- Text inputs -->
    <div class="form-group">
      <label for="text">Text Input</label>
      <input type="text" id="text" placeholder="Enter text...">
    </div>
    <div class="form-group">
      <label for="email">Email Input</label>
      <input type="email" id="email" placeholder="you@example.com">
    </div>
    <div class="form-group">
      <label for="password">Password Input</label>
      <input type="password" id="password" placeholder="••••••••">
    </div>
    <div class="form-group">
      <label for="number">Number Input</label>
      <input type="number" id="number" min="0" max="100" step="5" value="50">
    </div>
    <div class="form-group">
      <label for="date">Date Input</label>
      <input type="date" id="date">
    </div>
    <div class="form-group">
      <label for="color">Color Picker</label>
      <input type="color" id="color" value="#667eea" style="height:44px;padding:4px">
    </div>
    <div class="form-group">
      <label for="range">Range Slider</label>
      <input type="range" id="range" min="0" max="100" value="40" style="padding:0">
    </div>
    <!-- Textarea -->
    <div class="form-group">
      <label for="bio">Textarea</label>
      <textarea id="bio" rows="4" placeholder="Tell us about yourself..."></textarea>
    </div>
    <!-- Select -->
    <div class="form-group">
      <label for="country">Select Dropdown</label>
      <select id="country">
        <option value="">Choose a country</option>
        <option value="us">United States</option>
        <option value="uk">United Kingdom</option>
        <option value="cn">China</option>
      </select>
    </div>
    <!-- Radio -->
    <div class="form-group">
      <label>Radio Buttons</label>
      <div class="radio-group">
        <label class="radio-label"><input type="radio" name="size" value="sm"> Small</label>
        <label class="radio-label"><input type="radio" name="size" value="md" checked> Medium</label>
        <label class="radio-label"><input type="radio" name="size" value="lg"> Large</label>
      </div>
    </div>
    <!-- Checkbox -->
    <div class="form-group">
      <label>Checkboxes</label>
      <div class="checkbox-group">
        <label class="checkbox-label"><input type="checkbox" checked> HTML</label>
        <label class="checkbox-label"><input type="checkbox" checked> CSS</label>
        <label class="checkbox-label"><input type="checkbox"> JavaScript</label>
      </div>
    </div>
    <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 28px;border-radius:6px;font-size:1rem;cursor:pointer">Submit</button>
  </form>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step1.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Form Elements</title>
  <style>
    body { font-family: sans-serif; padding: 30px; max-width: 600px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; }
    input, textarea, select { width: 100%; padding: 10px 14px; border: 2px solid #dfe6e9; border-radius: 6px; font-size: 1rem; box-sizing: border-box; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; }
  </style>
</head>
<body>
  <form>
    <div class="form-group"><label for="name">Name</label><input type="text" id="name" placeholder="John Doe"></div>
    <div class="form-group"><label for="email">Email</label><input type="email" id="email" placeholder="you@example.com"></div>
    <div class="form-group"><label for="bio">Bio</label><textarea id="bio" rows="3" placeholder="About you..."></textarea></div>
    <div class="form-group"><label for="country">Country</label><select id="country"><option>USA</option><option>UK</option><option>China</option></select></div>
    <div class="form-group"><label><input type="checkbox" checked> I agree to terms</label></div>
    <button type="submit" style="background:#667eea;color:white;border:none;padding:12px 28px;border-radius:6px;cursor:pointer">Submit</button>
  </form>
</body>
</html>
EOF
```

> 💡 **Use semantic input types** (`email`, `tel`, `number`, `date`) — browsers add automatic validation, mobile keyboards show the appropriate layout (number pad for `tel`, email keyboard for `email`), and accessibility tools announce them correctly.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step1.html', 'utf8');
console.log(html.includes('<form>') ? '✓ Form element found' : '✗ Missing');
console.log(html.includes('type=\"email\"') ? '✓ Email input type found' : '✗ Missing email type');
"
✓ Form element found
✓ Email input type found
```

---

### Step 2: Form Validation Attributes

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Form Validation</title>
  <style>
    body { font-family: sans-serif; padding: 30px; max-width: 500px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; }
    input {
      width: 100%;
      padding: 10px 14px;
      border: 2px solid #dfe6e9;
      border-radius: 6px;
      font-size: 1rem;
      box-sizing: border-box;
    }
    input:invalid { border-color: #e74c3c; }
    input:valid { border-color: #2ecc71; }
    .hint { font-size: 0.8rem; color: #636e72; margin-top: 4px; }
    button { background: #667eea; color: white; border: none; padding: 12px 28px; border-radius: 6px; font-size: 1rem; cursor: pointer; }
  </style>
</head>
<body>
  <h2>HTML5 Form Validation</h2>
  <form novalidate>
    <div class="form-group">
      <label for="username">Username <span style="color:red">*</span></label>
      <input type="text" id="username" required minlength="3" maxlength="20" pattern="[a-zA-Z0-9_]+" placeholder="letters, numbers, underscore">
      <div class="hint">3-20 characters, letters/numbers/underscore only</div>
    </div>
    <div class="form-group">
      <label for="email2">Email <span style="color:red">*</span></label>
      <input type="email" id="email2" required placeholder="you@example.com">
    </div>
    <div class="form-group">
      <label for="age">Age (18-120)</label>
      <input type="number" id="age" min="18" max="120" placeholder="Your age">
    </div>
    <div class="form-group">
      <label for="website">Website (optional)</label>
      <input type="url" id="website" placeholder="https://your-site.com">
    </div>
    <div class="form-group">
      <label for="phone">Phone</label>
      <input type="tel" id="phone" pattern="[0-9]{10,15}" placeholder="1234567890">
      <div class="hint">10-15 digits</div>
    </div>
    <button type="submit">Validate & Submit</button>
  </form>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step2.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Form Validation</title>
  <style>
    body { font-family: sans-serif; padding: 30px; max-width: 500px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; }
    input { width: 100%; padding: 10px 14px; border: 2px solid #dfe6e9; border-radius: 6px; font-size: 1rem; box-sizing: border-box; }
    input:invalid { border-color: #e74c3c; }
    input:valid:not(:placeholder-shown) { border-color: #2ecc71; }
    button { background: #667eea; color: white; border: none; padding: 12px 28px; border-radius: 6px; cursor: pointer; }
  </style>
</head>
<body>
  <form>
    <div class="form-group"><label>Username *</label><input type="text" required minlength="3" maxlength="20" pattern="[a-zA-Z0-9_]+" placeholder="letters_numbers"></div>
    <div class="form-group"><label>Email *</label><input type="email" required placeholder="you@example.com"></div>
    <div class="form-group"><label>Age (18-120)</label><input type="number" min="18" max="120" placeholder="Your age"></div>
    <button type="submit">Submit</button>
  </form>
</body>
</html>
EOF
```

> 💡 **HTML5 validation attributes** work without JavaScript: `required` (must be filled), `minlength`/`maxlength` (character limits), `min`/`max` (number/date range), `pattern` (regex match). The `:valid` and `:invalid` pseudo-classes let you style states with CSS.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step2.html', 'utf8');
console.log(html.includes('required') ? '✓ required attribute found' : '✗ Missing required');
console.log(html.includes('pattern') ? '✓ pattern attribute found' : '✗ Missing pattern');
console.log(html.includes(':invalid') ? '✓ :invalid CSS found' : '✗ Missing :invalid');
"
✓ required attribute found
✓ pattern attribute found
✓ :invalid CSS found
```

---

### Step 3: Form Layout with CSS Grid

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Grid Form Layout</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .form-card {
      background: white;
      border-radius: 16px;
      padding: 32px;
      max-width: 700px;
      margin: 0 auto;
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    h2 { margin-bottom: 24px; color: #2d3436; }
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .full-width { grid-column: 1 / -1; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    label { font-weight: 600; font-size: 0.9rem; color: #636e72; }
    input, textarea, select {
      padding: 12px 14px;
      border: 2px solid #dfe6e9;
      border-radius: 8px;
      font-size: 1rem;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    input:focus, textarea:focus, select:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102,126,234,0.15);
    }
    .form-actions {
      display: flex;
      gap: 12px;
      justify-content: flex-end;
      margin-top: 8px;
      grid-column: 1 / -1;
    }
    .btn-cancel { background: transparent; border: 2px solid #dfe6e9; color: #636e72; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 1rem; }
    .btn-submit { background: #667eea; color: white; border: none; padding: 12px 28px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
    @media (max-width: 480px) { .form-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="form-card">
    <h2>Account Settings</h2>
    <form>
      <div class="form-grid">
        <div class="form-group">
          <label for="fname">First Name</label>
          <input type="text" id="fname" placeholder="John">
        </div>
        <div class="form-group">
          <label for="lname">Last Name</label>
          <input type="text" id="lname" placeholder="Doe">
        </div>
        <div class="form-group full-width">
          <label for="email3">Email Address</label>
          <input type="email" id="email3" placeholder="john.doe@example.com">
        </div>
        <div class="form-group">
          <label for="phone2">Phone</label>
          <input type="tel" id="phone2" placeholder="+1 234 567 890">
        </div>
        <div class="form-group">
          <label for="country2">Country</label>
          <select id="country2"><option>United States</option><option>UK</option><option>Canada</option></select>
        </div>
        <div class="form-group full-width">
          <label for="bio2">Bio</label>
          <textarea id="bio2" rows="3" placeholder="Tell us about yourself..."></textarea>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-cancel">Cancel</button>
          <button type="submit" class="btn-submit">Save Changes</button>
        </div>
      </div>
    </form>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step3.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Grid Form Layout</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .form-card { background: white; border-radius: 16px; padding: 32px; max-width: 700px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .full-width { grid-column: 1 / -1; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    label { font-weight: 600; font-size: 0.9rem; color: #636e72; }
    input, textarea, select { padding: 12px 14px; border: 2px solid #dfe6e9; border-radius: 8px; font-size: 1rem; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
    .btn-submit { background: #667eea; color: white; border: none; padding: 12px 28px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
    @media (max-width: 480px) { .form-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="form-card">
    <h2>Account Settings</h2>
    <form>
      <div class="form-grid">
        <div class="form-group"><label>First Name</label><input type="text" placeholder="John"></div>
        <div class="form-group"><label>Last Name</label><input type="text" placeholder="Doe"></div>
        <div class="form-group full-width"><label>Email</label><input type="email" placeholder="john@example.com"></div>
        <div class="form-group full-width"><label>Bio</label><textarea rows="3" placeholder="About you..."></textarea></div>
        <div class="full-width" style="text-align:right"><button type="submit" class="btn-submit">Save Changes</button></div>
      </div>
    </form>
  </div>
</body>
</html>
EOF
```

> 💡 **CSS Grid for forms** is perfect — `grid-template-columns: 1fr 1fr` creates a two-column layout. `grid-column: 1 / -1` makes any field span the full width. The form collapses to single-column on mobile with one `@media` query.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step3.html', 'utf8');
console.log(html.includes('form-grid') ? '✓ Grid form layout found' : '✗ Missing');
console.log(html.includes('full-width') ? '✓ Full-width fields found' : '✗ Missing full-width');
"
✓ Grid form layout found
✓ Full-width fields found
```

---

### Step 4: Custom Checkbox & Radio Styling

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Custom Checkboxes & Radios</title>
  <style>
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .control-group { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    h3 { margin-bottom: 16px; color: #2d3436; }
    /* Hide the real checkbox/radio */
    .custom-check input,
    .custom-radio input { position: absolute; opacity: 0; width: 0; height: 0; }
    /* Custom checkbox */
    .custom-check { display: flex; align-items: center; gap: 12px; cursor: pointer; margin-bottom: 12px; }
    .checkmark {
      width: 22px; height: 22px;
      border: 2px solid #b2bec3;
      border-radius: 5px;
      display: flex; align-items: center; justify-content: center;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }
    .checkmark::after { content: ''; width: 6px; height: 10px; border-right: 2px solid white; border-bottom: 2px solid white; transform: rotate(45deg) scale(0); transition: transform 0.2s ease; }
    .custom-check input:checked + .checkmark { background: #667eea; border-color: #667eea; }
    .custom-check input:checked + .checkmark::after { transform: rotate(45deg) scale(1); }
    .custom-check:hover .checkmark { border-color: #667eea; }
    /* Custom radio */
    .custom-radio { display: flex; align-items: center; gap: 12px; cursor: pointer; margin-bottom: 12px; }
    .radiomark {
      width: 22px; height: 22px;
      border: 2px solid #b2bec3;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }
    .radiomark::after { content: ''; width: 10px; height: 10px; background: white; border-radius: 50%; transform: scale(0); transition: transform 0.2s ease; }
    .custom-radio input:checked + .radiomark { background: #667eea; border-color: #667eea; }
    .custom-radio input:checked + .radiomark::after { transform: scale(1); }
    /* Toggle switch */
    .toggle-wrap { display: flex; align-items: center; gap: 12px; cursor: pointer; }
    .toggle-switch {
      width: 52px; height: 28px;
      background: #b2bec3;
      border-radius: 14px;
      position: relative;
      transition: background 0.3s ease;
    }
    .toggle-switch::after {
      content: '';
      position: absolute;
      top: 3px; left: 3px;
      width: 22px; height: 22px;
      background: white;
      border-radius: 50%;
      transition: transform 0.3s ease;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .toggle-wrap input { position: absolute; opacity: 0; }
    .toggle-wrap input:checked + .toggle-switch { background: #667eea; }
    .toggle-wrap input:checked + .toggle-switch::after { transform: translateX(24px); }
  </style>
</head>
<body>
  <div class="control-group">
    <h3>Custom Checkboxes</h3>
    <label class="custom-check">
      <input type="checkbox" checked>
      <span class="checkmark"></span>
      HTML5 (checked)
    </label>
    <label class="custom-check">
      <input type="checkbox">
      <span class="checkmark"></span>
      CSS3
    </label>
    <label class="custom-check">
      <input type="checkbox" checked>
      <span class="checkmark"></span>
      JavaScript (checked)
    </label>
  </div>
  <div class="control-group">
    <h3>Custom Radio Buttons</h3>
    <label class="custom-radio">
      <input type="radio" name="plan" value="free">
      <span class="radiomark"></span>
      Free Plan
    </label>
    <label class="custom-radio">
      <input type="radio" name="plan" value="pro" checked>
      <span class="radiomark"></span>
      Pro Plan (selected)
    </label>
    <label class="custom-radio">
      <input type="radio" name="plan" value="enterprise">
      <span class="radiomark"></span>
      Enterprise
    </label>
  </div>
  <div class="control-group">
    <h3>Toggle Switches</h3>
    <label class="toggle-wrap">
      <input type="checkbox" checked>
      <span class="toggle-switch"></span>
      Notifications (on)
    </label>
    <br><br>
    <label class="toggle-wrap">
      <input type="checkbox">
      <span class="toggle-switch"></span>
      Dark Mode (off)
    </label>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step4.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Custom Controls</title>
  <style>
    body { font-family: sans-serif; padding: 30px; }
    .custom-check input { position: absolute; opacity: 0; width: 0; height: 0; }
    .custom-check { display: flex; align-items: center; gap: 12px; cursor: pointer; margin-bottom: 12px; }
    .checkmark { width: 22px; height: 22px; border: 2px solid #b2bec3; border-radius: 5px; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease; flex-shrink: 0; }
    .checkmark::after { content: ''; width: 6px; height: 10px; border-right: 2px solid white; border-bottom: 2px solid white; transform: rotate(45deg) scale(0); transition: transform 0.2s ease; }
    .custom-check input:checked + .checkmark { background: #667eea; border-color: #667eea; }
    .custom-check input:checked + .checkmark::after { transform: rotate(45deg) scale(1); }
    .toggle-wrap { display: flex; align-items: center; gap: 12px; cursor: pointer; margin-top: 20px; }
    .toggle-wrap input { position: absolute; opacity: 0; }
    .toggle-switch { width: 52px; height: 28px; background: #b2bec3; border-radius: 14px; position: relative; transition: background 0.3s; }
    .toggle-switch::after { content: ''; position: absolute; top: 3px; left: 3px; width: 22px; height: 22px; background: white; border-radius: 50%; transition: transform 0.3s; }
    .toggle-wrap input:checked + .toggle-switch { background: #667eea; }
    .toggle-wrap input:checked + .toggle-switch::after { transform: translateX(24px); }
  </style>
</head>
<body>
  <h3>Custom Checkboxes</h3>
  <label class="custom-check"><input type="checkbox" checked><span class="checkmark"></span>HTML5 (checked)</label>
  <label class="custom-check"><input type="checkbox"><span class="checkmark"></span>CSS3</label>
  <h3 style="margin-top:20px">Toggle Switch</h3>
  <label class="toggle-wrap"><input type="checkbox" checked><span class="toggle-switch"></span>Notifications (on)</label>
</body>
</html>
EOF
```

> 💡 **The CSS-only custom control pattern:** Hide the native input (`opacity: 0`), place a sibling `<span>` right after it, then use `input:checked + span` to style the checked state. The label wrapping both elements makes the whole area clickable. No JavaScript needed.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step4.html', 'utf8');
console.log(html.includes('checkmark') ? '✓ Custom checkbox found' : '✗ Missing');
console.log(html.includes(':checked') ? '✓ :checked pseudo-class' : '✗ Missing :checked');
"
✓ Custom checkbox found
✓ :checked pseudo-class
```

---

### Step 5: Input Focus & Validation States

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Input States</title>
  <style>
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .field { margin-bottom: 24px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.9rem; color: #636e72; }
    .input-wrapper { position: relative; }
    input {
      width: 100%;
      padding: 12px 14px 12px 40px;
      border: 2px solid #dfe6e9;
      border-radius: 8px;
      font-size: 1rem;
      box-sizing: border-box;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .input-icon {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 1.1rem;
      pointer-events: none;
    }
    /* Focus state */
    input:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
    }
    /* Valid state */
    input:valid:not(:placeholder-shown) {
      border-color: #00b894;
    }
    .field.success input { border-color: #00b894; }
    .field.success .status { color: #00b894; }
    /* Error state */
    .field.error input { border-color: #e74c3c; }
    .field.error .status { color: #e74c3c; }
    /* Warning state */
    .field.warning input { border-color: #f39c12; }
    .field.warning .status { color: #f39c12; }
    /* Disabled */
    input:disabled { background: #f5f6fa; color: #b2bec3; cursor: not-allowed; }
    .status { font-size: 0.8rem; margin-top: 6px; display: flex; align-items: center; gap: 4px; }
  </style>
</head>
<body>
  <h2>Input States</h2>
  <div class="field">
    <label>Default (hover/focus me)</label>
    <div class="input-wrapper">
      <span class="input-icon">👤</span>
      <input type="text" placeholder="Focus to see the glow effect">
    </div>
  </div>
  <div class="field success">
    <label>Success State</label>
    <div class="input-wrapper">
      <span class="input-icon">✉️</span>
      <input type="email" value="user@example.com">
    </div>
    <div class="status">✅ Email is valid</div>
  </div>
  <div class="field error">
    <label>Error State</label>
    <div class="input-wrapper">
      <span class="input-icon">🔑</span>
      <input type="password" value="123">
    </div>
    <div class="status">❌ Password must be at least 8 characters</div>
  </div>
  <div class="field warning">
    <label>Warning State</label>
    <div class="input-wrapper">
      <span class="input-icon">👤</span>
      <input type="text" value="john">
    </div>
    <div class="status">⚠️ Username might already be taken</div>
  </div>
  <div class="field">
    <label>Disabled State</label>
    <div class="input-wrapper">
      <span class="input-icon">🔒</span>
      <input type="text" value="Cannot edit this" disabled>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step5.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Input States</title>
  <style>
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .field { margin-bottom: 24px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.9rem; color: #636e72; }
    input { width: 100%; padding: 12px 14px; border: 2px solid #dfe6e9; border-radius: 8px; font-size: 1rem; box-sizing: border-box; transition: border-color 0.2s, box-shadow 0.2s; }
    input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 4px rgba(102,126,234,0.15); }
    input:valid:not(:placeholder-shown) { border-color: #00b894; }
    input:invalid:not(:placeholder-shown) { border-color: #e74c3c; }
    input:disabled { background: #f5f6fa; color: #b2bec3; cursor: not-allowed; }
    .status { font-size: 0.8rem; margin-top: 6px; }
    .error { color: #e74c3c; }
    .success { color: #00b894; }
  </style>
</head>
<body>
  <div class="field"><label>Email (type to validate)</label><input type="email" placeholder="you@example.com"></div>
  <div class="field"><label>Success</label><input type="email" value="valid@email.com"><div class="status success">✅ Valid email</div></div>
  <div class="field"><label>Error</label><input type="password" value="123"><div class="status error">❌ Too short</div></div>
  <div class="field"><label>Disabled</label><input type="text" value="Read only" disabled></div>
</body>
</html>
EOF
```

> 💡 **CSS pseudo-classes for validation:** `:valid` and `:invalid` check HTML5 validation rules; `:placeholder-shown` detects empty fields (so you don't show red on empty required fields before the user touches them). `:focus` for keyboard/click focus styling. `:disabled` for disabled inputs.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step5.html', 'utf8');
console.log(html.includes(':focus') ? '✓ :focus state' : '✗ Missing :focus');
console.log(html.includes(':valid') ? '✓ :valid state' : '✗ Missing :valid');
console.log(html.includes(':disabled') ? '✓ :disabled state' : '✗ Missing :disabled');
"
✓ :focus state
✓ :valid state
✓ :disabled state
```

---

### Step 6: Custom Select Dropdown

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Custom Select</title>
  <style>
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .select-wrapper {
      position: relative;
      width: 300px;
    }
    /* Hide default arrow and style select */
    select {
      appearance: none;
      -webkit-appearance: none;
      width: 100%;
      padding: 12px 44px 12px 16px;
      border: 2px solid #dfe6e9;
      border-radius: 8px;
      font-size: 1rem;
      background: white;
      cursor: pointer;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    select:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 4px rgba(102,126,234,0.15);
    }
    /* Custom arrow using pseudo-element */
    .select-wrapper::after {
      content: '▼';
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 0.7rem;
      color: #636e72;
      pointer-events: none;
    }
    /* Multi-select */
    select[multiple] {
      padding: 8px;
      height: 120px;
    }
    select[multiple] option { padding: 8px; border-radius: 4px; }
    select[multiple] option:checked { background: #667eea; color: white; }
  </style>
</head>
<body>
  <h2>Custom Styled Selects</h2>
  <div style="margin-bottom:24px">
    <label style="display:block;margin-bottom:8px;font-weight:600">Country</label>
    <div class="select-wrapper">
      <select>
        <option value="">Select a country...</option>
        <option value="us">🇺🇸 United States</option>
        <option value="gb">🇬🇧 United Kingdom</option>
        <option value="cn">🇨🇳 China</option>
        <option value="jp">🇯🇵 Japan</option>
        <option value="de">🇩🇪 Germany</option>
      </select>
    </div>
  </div>
  <div>
    <label style="display:block;margin-bottom:8px;font-weight:600">Skills (hold Ctrl/Cmd to select multiple)</label>
    <div class="select-wrapper" style="width:300px">
      <select multiple>
        <option value="html" selected>HTML</option>
        <option value="css" selected>CSS</option>
        <option value="js">JavaScript</option>
        <option value="react">React</option>
        <option value="node">Node.js</option>
        <option value="python">Python</option>
      </select>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step6.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Custom Select</title>
  <style>
    body { font-family: sans-serif; padding: 30px; }
    .select-wrapper { position: relative; width: 300px; }
    select { appearance: none; -webkit-appearance: none; width: 100%; padding: 12px 44px 12px 16px; border: 2px solid #dfe6e9; border-radius: 8px; font-size: 1rem; background: white; cursor: pointer; }
    select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 4px rgba(102,126,234,0.15); }
    .select-wrapper::after { content: '▼'; position: absolute; right: 14px; top: 50%; transform: translateY(-50%); font-size: 0.7rem; color: #636e72; pointer-events: none; }
  </style>
</head>
<body>
  <label style="display:block;margin-bottom:8px;font-weight:600">Country</label>
  <div class="select-wrapper">
    <select>
      <option value="">Select a country...</option>
      <option>🇺🇸 United States</option>
      <option>🇬🇧 United Kingdom</option>
      <option>🇨🇳 China</option>
    </select>
  </div>
</body>
</html>
EOF
```

> 💡 **`appearance: none`** removes the browser's default select styling, letting you fully customize it. You lose the dropdown arrow, so add it back with a `::after` pseudo-element. `pointer-events: none` on the arrow prevents it from blocking click events on the select.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step6.html', 'utf8');
console.log(html.includes('appearance: none') || html.includes('appearance:none') ? '✓ Custom select styling' : '✗ Missing appearance:none');
"
✓ Custom select styling
```

---

### Step 7: File Upload Styling

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>File Upload</title>
  <style>
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    /* Hide the real file input */
    .file-input-real { position: absolute; opacity: 0; width: 0; height: 0; }
    /* Styled drop zone */
    .dropzone {
      border: 2px dashed #b2bec3;
      border-radius: 12px;
      padding: 40px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.2s, background 0.2s;
      background: white;
      max-width: 400px;
    }
    .dropzone:hover { border-color: #667eea; background: rgba(102,126,234,0.05); }
    .dropzone-icon { font-size: 3rem; margin-bottom: 12px; }
    .dropzone h3 { color: #2d3436; margin-bottom: 8px; }
    .dropzone p { color: #636e72; font-size: 0.9rem; margin-bottom: 16px; }
    .btn-select { background: #667eea; color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; }
    .dropzone small { display: block; margin-top: 12px; color: #b2bec3; font-size: 0.8rem; }
    /* Avatar upload variant */
    .avatar-upload { display: inline-block; position: relative; cursor: pointer; }
    .avatar-preview {
      width: 80px; height: 80px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea, #764ba2);
      display: flex; align-items: center; justify-content: center;
      font-size: 2rem;
      border: 3px solid white;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .avatar-overlay {
      position: absolute;
      bottom: 0; right: 0;
      background: #667eea;
      color: white;
      width: 26px; height: 26px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.8rem;
      border: 2px solid white;
    }
  </style>
</head>
<body>
  <h2>File Upload Styles</h2>
  <label class="dropzone">
    <input type="file" class="file-input-real" multiple accept="image/*,.pdf">
    <div class="dropzone-icon">📁</div>
    <h3>Drop files here</h3>
    <p>or click to browse your computer</p>
    <button class="btn-select" onclick="event.preventDefault()">Browse Files</button>
    <small>PNG, JPG, PDF up to 10MB</small>
  </label>
  <br>
  <h3 style="margin:20px 0 10px">Avatar Upload</h3>
  <label class="avatar-upload">
    <input type="file" class="file-input-real" accept="image/*">
    <div class="avatar-preview">😀</div>
    <div class="avatar-overlay">✏️</div>
  </label>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/form-step7.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>File Upload</title>
  <style>
    body { font-family: sans-serif; padding: 30px; background: #f8f9fa; }
    .file-input-real { position: absolute; opacity: 0; width: 0; height: 0; }
    .dropzone { border: 2px dashed #b2bec3; border-radius: 12px; padding: 40px; text-align: center; cursor: pointer; background: white; max-width: 400px; transition: border-color 0.2s; }
    .dropzone:hover { border-color: #667eea; background: rgba(102,126,234,0.05); }
    .btn-select { background: #667eea; color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; }
  </style>
</head>
<body>
  <h2>File Upload</h2>
  <label class="dropzone">
    <input type="file" class="file-input-real" multiple>
    <div style="font-size:3rem">📁</div>
    <h3>Drop files here or click to browse</h3>
    <button class="btn-select" onclick="event.preventDefault()">Browse Files</button>
    <small style="color:#b2bec3;display:block;margin-top:12px">PNG, JPG, PDF up to 10MB</small>
  </label>
</body>
</html>
EOF
```

> 💡 **Custom file inputs:** Hide the real `<input type="file">` and wrap everything in a `<label>` — clicking anywhere in the label triggers the file picker. The `accept` attribute filters allowed file types. This pattern works without JavaScript for basic uploads.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/form-step7.html', 'utf8');
console.log(html.includes('type=\"file\"') ? '✓ File input found' : '✗ Missing file input');
console.log(html.includes('dropzone') ? '✓ Dropzone style found' : '✗ Missing dropzone');
"
✓ File input found
✓ Dropzone style found
```

---

### Step 8: Capstone — Styled Registration Form

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registration Form</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .card { background: white; border-radius: 20px; padding: 40px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
    .card-header { text-align: center; margin-bottom: 32px; }
    .card-header h1 { font-size: 1.8rem; color: #2d3436; margin-bottom: 8px; }
    .card-header p { color: #636e72; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .field { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.85rem; color: #636e72; text-transform: uppercase; letter-spacing: 0.5px; }
    input, select { width: 100%; padding: 12px 16px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 1rem; background: white; transition: border-color 0.2s, box-shadow 0.2s; }
    input:focus, select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 4px rgba(102,126,234,0.1); }
    input:valid:not(:placeholder-shown) { border-color: #00b894; }
    .select-wrap { position: relative; }
    .select-wrap select { appearance: none; -webkit-appearance: none; padding-right: 44px; }
    .select-wrap::after { content: '▼'; position: absolute; right: 14px; top: 50%; transform: translateY(-50%); font-size: 0.7rem; color: #636e72; pointer-events: none; }
    /* Custom checkbox */
    .terms-check input { position: absolute; opacity: 0; }
    .terms-check { display: flex; align-items: flex-start; gap: 10px; cursor: pointer; margin-bottom: 20px; }
    .checkmark { width: 20px; height: 20px; min-width: 20px; border: 2px solid #b2bec3; border-radius: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; margin-top: 2px; }
    .checkmark::after { content: ''; width: 5px; height: 9px; border-right: 2px solid white; border-bottom: 2px solid white; transform: rotate(45deg) scale(0); transition: transform 0.2s; }
    .terms-check input:checked + .checkmark { background: #667eea; border-color: #667eea; }
    .terms-check input:checked + .checkmark::after { transform: rotate(45deg) scale(1); }
    .terms-text { font-size: 0.9rem; color: #636e72; line-height: 1.4; }
    .terms-text a { color: #667eea; }
    .btn-submit { width: 100%; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 16px; border-radius: 8px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: transform 0.2s, box-shadow 0.3s; }
    .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102,126,234,0.4); }
    .divider { text-align: center; margin: 20px 0; color: #b2bec3; font-size: 0.85rem; }
    .social-btns { display: flex; gap: 12px; }
    .btn-social { flex: 1; padding: 12px; border: 2px solid #e9ecef; border-radius: 8px; background: white; cursor: pointer; font-size: 0.9rem; font-weight: 600; transition: border-color 0.2s; }
    .btn-social:hover { border-color: #667eea; }
    .login-link { text-align: center; margin-top: 20px; font-size: 0.9rem; color: #636e72; }
    .login-link a { color: #667eea; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <h1>Create Account</h1>
      <p>Join thousands of developers building amazing things</p>
    </div>
    <form>
      <div class="form-row">
        <div class="field"><label>First Name</label><input type="text" placeholder="John" required></div>
        <div class="field"><label>Last Name</label><input type="text" placeholder="Doe" required></div>
      </div>
      <div class="field"><label>Email Address</label><input type="email" placeholder="john.doe@example.com" required></div>
      <div class="field"><label>Password</label><input type="password" placeholder="Min. 8 characters" minlength="8" required></div>
      <div class="field">
        <label>Role</label>
        <div class="select-wrap">
          <select required>
            <option value="">Select your role</option>
            <option>Frontend Developer</option>
            <option>Backend Developer</option>
            <option>Full Stack Developer</option>
            <option>Designer</option>
            <option>Product Manager</option>
          </select>
        </div>
      </div>
      <label class="terms-check">
        <input type="checkbox" required>
        <span class="checkmark"></span>
        <span class="terms-text">I agree to the <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a></span>
      </label>
      <button type="submit" class="btn-submit">Create Account →</button>
      <div class="divider">or sign up with</div>
      <div class="social-btns">
        <button type="button" class="btn-social">🔵 Google</button>
        <button type="button" class="btn-social">⬛ GitHub</button>
      </div>
    </form>
    <div class="login-link">Already have an account? <a href="#">Sign in</a></div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/forms.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registration Form</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .card { background: white; border-radius: 20px; padding: 40px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
    .card h1 { font-size: 1.8rem; color: #2d3436; margin-bottom: 24px; text-align: center; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .field { margin-bottom: 20px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.85rem; color: #636e72; }
    input, select { width: 100%; padding: 12px 16px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 1rem; }
    input:focus, select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 4px rgba(102,126,234,0.1); }
    input:valid:not(:placeholder-shown) { border-color: #00b894; }
    .btn-submit { width: 100%; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 16px; border-radius: 8px; font-size: 1rem; font-weight: 700; cursor: pointer; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Create Account</h1>
    <form>
      <div class="form-row">
        <div class="field"><label>First Name</label><input type="text" placeholder="John" required></div>
        <div class="field"><label>Last Name</label><input type="text" placeholder="Doe" required></div>
      </div>
      <div class="field"><label>Email</label><input type="email" placeholder="john@example.com" required></div>
      <div class="field"><label>Password</label><input type="password" placeholder="Min. 8 characters" minlength="8" required></div>
      <button type="submit" class="btn-submit">Create Account →</button>
    </form>
  </div>
</body>
</html>
EOF
```

> 💡 **Registration form best practices:** Two-column name row (feels shorter), clear labels above inputs (not inside as placeholder — accessibility), visible validation states, prominent CTA button with hover feedback, and alternative sign-in methods. The gradient background makes even a simple form feel premium.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/forms.html', 'utf8');
console.log(html.includes('<form>') ? '✓ Form found' : '✗ Missing form');
console.log(html.includes('grid-template-columns') ? '✓ Grid layout' : '✗ Missing grid');
console.log(html.includes('required') ? '✓ Validation attributes' : '✗ Missing required');
"
✓ Form found
✓ Grid layout
✓ Validation attributes
```

---

## Verification

```bash
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const files = ['form-step1.html','form-step2.html','form-step3.html','form-step4.html','form-step5.html','form-step6.html','form-step7.html','forms.html'];
files.forEach(f => {
  try { fs.accessSync('/workspace/' + f); console.log('✓ ' + f); }
  catch(e) { console.log('✗ ' + f); }
});
"
```

## Summary

| Element | HTML | CSS Technique |
|---------|------|---------------|
| Text input | `<input type="text">` | `:focus`, `:valid`, `:invalid` |
| Custom checkbox | `input` + `span.checkmark` | `input:checked + span` |
| Custom radio | Same pattern | Same pattern |
| Toggle switch | Same pattern | `translateX()` |
| Custom select | `appearance: none` | `::after` arrow |
| File upload | Hidden input + label | Drag & drop zone |

## Further Reading
- [MDN Forms Guide](https://developer.mozilla.org/en-US/docs/Learn/Forms)
- [web.dev Form Best Practices](https://web.dev/learn/forms/)
- [CSS Custom Checkboxes](https://moderncss.dev/pure-css-custom-checkbox-style/)
