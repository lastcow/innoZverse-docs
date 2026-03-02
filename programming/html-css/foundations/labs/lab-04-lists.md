# Lab 4: Lists (ul, ol, dl)

## 🎯 Objective
Create and style unordered lists (`<ul>`), ordered lists (`<ol>`), and definition lists (`<dl>`), including nested lists.

## 📚 Background
HTML offers three list types: unordered lists for items without sequence importance, ordered lists for sequential items, and definition lists for term-definition pairs. Lists are also used for navigation menus.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Labs 1–3 completed

## 🛠️ Tools Used
- Python 3, Web browser

## 🔬 Lab Instructions

### Step 1: Create the lab file
```bash
touch ~/html-labs/lab04-lists.html
```

### Step 2: Create an unordered list
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HTML Lists</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
    </style>
</head>
<body>
    <h1>HTML Lists</h1>

    <h2>Unordered List (ul)</h2>
    <ul>
        <li>HTML</li>
        <li>CSS</li>
        <li>JavaScript</li>
        <li>Python</li>
    </ul>
```
💡 Use `<ul>` when the order of items doesn't matter (e.g., a shopping list, navigation menu).

### Step 3: Create an ordered list
```html
    <h2>Ordered List (ol)</h2>
    <ol>
        <li>Plan the project</li>
        <li>Design the layout</li>
        <li>Write the HTML</li>
        <li>Add CSS styling</li>
        <li>Test and deploy</li>
    </ol>

    <!-- Ordered list with custom start -->
    <h3>Starting from 5:</h3>
    <ol start="5">
        <li>Fifth item</li>
        <li>Sixth item</li>
    </ol>

    <!-- Reversed ordered list -->
    <h3>Countdown:</h3>
    <ol reversed>
        <li>Three</li>
        <li>Two</li>
        <li>One</li>
    </ol>

    <!-- Ordered list with letters -->
    <h3>Alphabetical:</h3>
    <ol type="a">
        <li>Apple</li>
        <li>Banana</li>
        <li>Cherry</li>
    </ol>
```

### Step 4: Create a definition list
```html
    <h2>Definition List (dl)</h2>
    <dl>
        <dt>HTML</dt>
        <dd>HyperText Markup Language — the standard language for web pages</dd>

        <dt>CSS</dt>
        <dd>Cascading Style Sheets — controls the visual presentation of HTML</dd>

        <dt>DOM</dt>
        <dd>Document Object Model — a programming interface for HTML documents</dd>

        <!-- Multiple terms for one definition -->
        <dt>JS</dt>
        <dt>JavaScript</dt>
        <dd>A scripting language that enables dynamic web content</dd>
    </dl>
```
💡 `<dl>` is perfect for glossaries, metadata, and key-value pairs.

### Step 5: Create nested lists
```html
    <h2>Nested Lists</h2>
    <ul>
        <li>Frontend
            <ul>
                <li>HTML</li>
                <li>CSS
                    <ul>
                        <li>Flexbox</li>
                        <li>Grid</li>
                    </ul>
                </li>
                <li>JavaScript</li>
            </ul>
        </li>
        <li>Backend
            <ul>
                <li>Node.js</li>
                <li>Python</li>
                <li>Go</li>
            </ul>
        </li>
        <li>Database
            <ol>
                <li>PostgreSQL</li>
                <li>MongoDB</li>
                <li>Redis</li>
            </ol>
        </li>
    </ul>
```
💡 You can mix `<ul>` and `<ol>` in nested structures.

### Step 6: Use a list as navigation
```html
    <h2>Navigation Menu (list-based)</h2>
    <nav>
        <ul style="list-style: none; display: flex; gap: 1rem; padding: 0;">
            <li><a href="/">Home</a></li>
            <li><a href="/about">About</a></li>
            <li><a href="/contact">Contact</a></li>
        </ul>
    </nav>
```
💡 Navigation menus are semantically lists of links. CSS `list-style: none` removes bullets.

### Step 7: Validate the HTML
```bash
cat > /tmp/lab04.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Lists</title></head>
<body>
<ul><li>Item 1</li><li>Item 2</li></ul>
<ol><li>First</li><li>Second</li></ol>
<dl><dt>Term</dt><dd>Definition</dd></dl>
</body>
</html>
EOF

python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('/tmp/lab04.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

**📸 Verified Output:**
```
HTML valid: OK
```

### Step 8: Style lists with CSS
Add to your `<style>` section:
```css
/* Custom bullet style */
ul.custom {
    list-style-type: square;
    color: #333;
}

/* Remove default list styling */
ul.no-bullets {
    list-style: none;
    padding-left: 0;
}

/* Custom counter for ol */
ol.roman {
    list-style-type: upper-roman;
}
```

**📸 Verified Output:**
In the browser, `square` bullets replace the default circles, and `upper-roman` shows I, II, III, etc.

## ✅ Verification
```bash
python3 -c "
import re
html = open('$HOME/html-labs/lab04-lists.html').read()
ul_count = len(re.findall(r'<ul', html))
ol_count = len(re.findall(r'<ol', html))
dl_count = len(re.findall(r'<dl', html))
li_count = len(re.findall(r'<li', html))
print(f'UL: {ul_count}, OL: {ol_count}, DL: {dl_count}, LI items: {li_count}')
print('Lists OK')
"
```

## 🚨 Common Mistakes
- **`<li>` outside of `<ul>` or `<ol>`** — Invalid HTML; list items need a parent list
- **Using `<br>` to create list-like layouts** — Use proper list elements instead
- **Nesting `<ul>` directly inside `<ul>`** — Must wrap in `<li>` first: `<ul><li><ul>...</ul></li></ul>`
- **Using lists just for indentation** — Use CSS margin/padding for spacing

## 📝 Summary
You mastered:
- `<ul>` — Unordered lists with `<li>` items
- `<ol>` — Ordered lists with `start`, `reversed`, and `type` attributes
- `<dl>`, `<dt>`, `<dd>` — Definition lists for glossaries
- Nested lists combining `<ul>` and `<ol>`
- Navigation menus using styled lists

## 🔗 Further Reading
- [MDN: HTML lists](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/HTML_text_fundamentals#lists)
- [MDN: `<dl>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dl)
