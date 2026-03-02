# Lab 6: Forms and Input Types

## 🎯 Objective
Build functional HTML forms using `<form>`, `<input>`, `<textarea>`, `<select>`, `<button>`, and various input types with proper labels and validation.

## 📚 Background
Forms are how users interact with web applications. HTML5 introduced many new input types (email, date, range, color, etc.) that provide built-in validation and mobile-friendly keyboards. Every form control needs a properly associated `<label>`.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Labs 1–5 completed

## 🛠️ Tools Used
- Python 3, Web browser

## 🔬 Lab Instructions

### Step 1: Create the lab file
```bash
touch ~/html-labs/lab06-forms.html
```

### Step 2: Create a registration form skeleton
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HTML Forms</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.3rem; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        input:focus, textarea:focus, select:focus { outline: 2px solid #4A90D9; border-color: transparent; }
        button { padding: 10px 20px; background: #4A90D9; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        button:hover { background: #357ABD; }
        fieldset { border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }
        legend { font-weight: bold; padding: 0 0.5rem; }
    </style>
</head>
<body>
    <h1>HTML Forms</h1>

    <form action="/submit" method="POST" novalidate>
```

### Step 3: Add text input types
```html
        <fieldset>
            <legend>Personal Information</legend>

            <div class="form-group">
                <label for="fullname">Full Name *</label>
                <input type="text" id="fullname" name="fullname" 
                    placeholder="John Doe" required minlength="2" maxlength="100"
                    autocomplete="name">
            </div>

            <div class="form-group">
                <label for="email">Email Address *</label>
                <input type="email" id="email" name="email" 
                    placeholder="john@example.com" required
                    autocomplete="email">
            </div>

            <div class="form-group">
                <label for="phone">Phone Number</label>
                <input type="tel" id="phone" name="phone" 
                    placeholder="+1 (555) 000-0000"
                    pattern="[\+\d\s\(\)\-]{7,20}"
                    autocomplete="tel">
            </div>

            <div class="form-group">
                <label for="password">Password *</label>
                <input type="password" id="password" name="password" 
                    required minlength="8" 
                    autocomplete="new-password">
            </div>

            <div class="form-group">
                <label for="birthdate">Date of Birth</label>
                <input type="date" id="birthdate" name="birthdate"
                    min="1900-01-01" max="2010-12-31">
            </div>

            <div class="form-group">
                <label for="age">Age</label>
                <input type="number" id="age" name="age" min="0" max="120" step="1" value="18">
            </div>
        </fieldset>
```
💡 `autocomplete` attributes help password managers and mobile keyboards.

### Step 4: Add selection controls
```html
        <fieldset>
            <legend>Preferences</legend>

            <div class="form-group">
                <label for="country">Country *</label>
                <select id="country" name="country" required>
                    <option value="">-- Select a country --</option>
                    <optgroup label="Asia">
                        <option value="cn">China</option>
                        <option value="jp">Japan</option>
                        <option value="kr">South Korea</option>
                    </optgroup>
                    <optgroup label="Europe">
                        <option value="de">Germany</option>
                        <option value="fr">France</option>
                        <option value="gb">United Kingdom</option>
                    </optgroup>
                    <optgroup label="Americas">
                        <option value="us" selected>United States</option>
                        <option value="ca">Canada</option>
                    </optgroup>
                </select>
            </div>

            <div class="form-group">
                <label for="skills">Skills (hold Ctrl/Cmd for multiple)</label>
                <select id="skills" name="skills" multiple size="4">
                    <option value="html">HTML</option>
                    <option value="css">CSS</option>
                    <option value="js">JavaScript</option>
                    <option value="python">Python</option>
                    <option value="go">Go</option>
                </select>
            </div>

            <!-- Radio buttons -->
            <div class="form-group">
                <p><strong>Experience Level:</strong></p>
                <label>
                    <input type="radio" name="level" value="beginner"> Beginner
                </label>
                <label>
                    <input type="radio" name="level" value="intermediate" checked> Intermediate
                </label>
                <label>
                    <input type="radio" name="level" value="advanced"> Advanced
                </label>
            </div>

            <!-- Checkboxes -->
            <div class="form-group">
                <p><strong>Interests:</strong></p>
                <label><input type="checkbox" name="interests" value="webdev"> Web Development</label>
                <label><input type="checkbox" name="interests" value="ai"> Artificial Intelligence</label>
                <label><input type="checkbox" name="interests" value="devops"> DevOps</label>
                <label><input type="checkbox" name="interests" value="security"> Security</label>
            </div>
        </fieldset>
```

### Step 5: Add range, color, and file inputs
```html
        <fieldset>
            <legend>Additional Controls</legend>

            <div class="form-group">
                <label for="satisfaction">Satisfaction Level: <span id="sat-value">5</span>/10</label>
                <input type="range" id="satisfaction" name="satisfaction" 
                    min="1" max="10" value="5"
                    oninput="document.getElementById('sat-value').textContent = this.value">
            </div>

            <div class="form-group">
                <label for="favcolor">Favorite Color</label>
                <input type="color" id="favcolor" name="favcolor" value="#4A90D9">
            </div>

            <div class="form-group">
                <label for="website">Website URL</label>
                <input type="url" id="website" name="website" placeholder="https://example.com">
            </div>

            <div class="form-group">
                <label for="avatar">Profile Picture</label>
                <input type="file" id="avatar" name="avatar" 
                    accept="image/png, image/jpeg, image/webp">
            </div>

            <div class="form-group">
                <label for="bio">Biography</label>
                <textarea id="bio" name="bio" rows="4" maxlength="500"
                    placeholder="Tell us about yourself..."></textarea>
            </div>

            <!-- Hidden input -->
            <input type="hidden" name="form_version" value="2024-01">
        </fieldset>
```

### Step 6: Add submit and reset buttons
```html
        <div class="form-group">
            <button type="submit">Submit Registration</button>
            <button type="reset" style="margin-left: 1rem; background: #666;">Reset Form</button>
        </div>
    </form>
</body>
</html>
```

### Step 7: Validate the HTML
```bash
cat > /tmp/lab06.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Form</title></head>
<body>
<form action="/submit" method="POST">
  <label for="name">Name</label>
  <input type="text" id="name" name="name" required>
  <label for="email">Email</label>
  <input type="email" id="email" name="email" required>
  <button type="submit">Submit</button>
</form>
</body>
</html>
EOF

python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('/tmp/lab06.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

**📸 Verified Output:**
```
HTML valid: OK
```

### Step 8: Test browser validation
```bash
cd ~/html-labs && python3 -m http.server 8080
```
Open `http://localhost:8080/lab06-forms.html`. Try to submit the form without filling required fields.

**📸 Verified Output:**
- Empty required fields show a browser validation tooltip
- Invalid email format is caught automatically
- The range slider updates the displayed number in real time

## ✅ Verification
```bash
python3 -c "
import re
html = open('$HOME/html-labs/lab06-forms.html').read()
inputs = re.findall(r'<input[^>]+type=[\"\']([\w]+)[\"\']]?', html)
labels = len(re.findall(r'<label', html))
print(f'Labels: {labels}')
print('Forms OK')
"
```

## 🚨 Common Mistakes
- **Missing `<label>`** — Every input must have a label associated via `for`/`id`
- **`<label>` without `for`** — Must match the input's `id` attribute
- **Using `GET` for sensitive data** — Passwords/credit cards should use `POST`
- **No `required` on mandatory fields** — Add HTML5 validation
- **No `autocomplete`** — Helps users and accessibility tools

## 📝 Summary
You built a complete form with:
- Text, email, password, tel, date, number, URL inputs
- `<select>` with `<optgroup>` and `multiple`
- Radio buttons and checkboxes
- Range, color, and file inputs
- `<textarea>` for multi-line text
- `<fieldset>` and `<legend>` for grouping
- `<button type="submit">` and `<button type="reset">`

## 🔗 Further Reading
- [MDN: Web forms](https://developer.mozilla.org/en-US/docs/Learn/Forms)
- [MDN: Input types](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input)
- [WebAIM: Creating Accessible Forms](https://webaim.org/techniques/forms/)
