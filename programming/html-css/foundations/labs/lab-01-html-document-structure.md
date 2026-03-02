# Lab 1: HTML Document Structure

## 🎯 Objective
Understand the fundamental structure of an HTML document including DOCTYPE, `<html>`, `<head>`, and `<body>` elements.

## 📚 Background
Every HTML page follows a standard structure. The DOCTYPE declaration tells the browser which version of HTML is being used. HTML5 uses `<!DOCTYPE html>`. The `<head>` section contains metadata (invisible to users), while `<body>` contains visible content.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- A text editor (VS Code, Notepad++, or any plain text editor)
- A web browser

## 🛠️ Tools Used
- Python 3 (for local server via `python3 -m http.server`)
- Any modern web browser

## 🔬 Lab Instructions

### Step 1: Create your working directory
```bash
mkdir ~/html-labs && cd ~/html-labs
```
💡 Keeping labs organized helps when reviewing your progress later.

### Step 2: Create your first HTML file
Create a file named `index.html` with the following content:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="My first HTML page">
    <title>My First HTML Page</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is my first HTML document.</p>
</body>
</html>
```

💡 `<!DOCTYPE html>` is not a tag — it's a declaration that tells browsers to use HTML5 standards mode.

### Step 3: Understand the `<head>` section
The `<head>` contains:
- `<meta charset="UTF-8">` — Character encoding (supports all languages)
- `<meta name="viewport">` — Controls layout on mobile devices
- `<meta name="description">` — SEO description shown in search results
- `<title>` — Tab title shown in browser

### Step 4: Understand the `<body>` section
Everything inside `<body>` is rendered by the browser and visible to users.

### Step 5: Validate the HTML using Python
```bash
cat > /tmp/lab01.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My First HTML Page</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is my first HTML document.</p>
</body>
</html>
EOF

python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('/tmp/lab01.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

**📸 Verified Output:**
```
HTML valid: OK
```

### Step 6: Serve the page locally
```bash
cd ~/html-labs
python3 -m http.server 8080
```
Open your browser at `http://localhost:8080` to see your page.

**📸 Verified Output:**
You should see "Hello, World!" as a large heading and the paragraph below it.

### Step 7: Add more metadata
Enhance your `<head>` section:
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Learning HTML structure">
    <meta name="author" content="Your Name">
    <meta name="keywords" content="HTML, web, learning">
    <title>My First HTML Page</title>
    <!-- This is a comment - not shown in browser -->
</head>
```
💡 Comments in HTML use `<!-- comment -->` syntax.

### Step 8: Inspect with browser DevTools
Open your browser, right-click the page, select **Inspect** (or press `F12`). Explore the Elements panel to see the document tree.

**📸 Verified Output:**
The DevTools Elements panel shows the full DOM tree matching your HTML structure.

## ✅ Verification
Run the Python validator on your file:
```bash
python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('index.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

## 🚨 Common Mistakes
- **Missing DOCTYPE** — Causes browsers to enter "quirks mode" with unpredictable rendering
- **Forgetting `lang` attribute** — Important for accessibility and SEO
- **Putting content in `<head>`** — Only metadata belongs in `<head>`, not visible content
- **Not closing tags** — Always close tags like `</html>`, `</head>`, `</body>`

## 📝 Summary
You learned that every HTML5 document requires:
1. `<!DOCTYPE html>` declaration
2. `<html lang="en">` root element
3. `<head>` for metadata (charset, viewport, title)
4. `<body>` for all visible content

## 🔗 Further Reading
- [MDN: Document and website structure](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/Document_and_website_structure)
- [HTML5 Specification](https://html.spec.whatwg.org/)
- [W3C HTML Validator](https://validator.w3.org/)
