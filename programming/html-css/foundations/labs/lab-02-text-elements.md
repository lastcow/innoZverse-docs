# Lab 2: Text Elements

## 🎯 Objective
Master HTML text elements including headings (`h1`–`h6`), paragraphs (`p`), inline elements (`span`, `strong`, `em`), and text formatting tags.

## 📚 Background
Text is the core of web content. HTML provides semantic tags that give meaning to text — not just style it. Using the right tag (e.g., `<strong>` vs `<b>`) matters for accessibility and SEO.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 1 (HTML Document Structure)

## 🛠️ Tools Used
- Python 3 (validation and server)
- Web browser

## 🔬 Lab Instructions

### Step 1: Create the lab file
```bash
touch ~/html-labs/lab02-text.html
```

### Step 2: Add heading hierarchy
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Text Elements Lab</title>
</head>
<body>
    <h1>Main Page Title (H1)</h1>
    <h2>Section Heading (H2)</h2>
    <h3>Subsection (H3)</h3>
    <h4>Sub-subsection (H4)</h4>
    <h5>Minor heading (H5)</h5>
    <h6>Smallest heading (H6)</h6>
</body>
</html>
```
💡 There should only be **one `<h1>`** per page. Use headings in order (don't skip from h1 to h4).

### Step 3: Add paragraphs and whitespace
```html
<p>This is a paragraph. HTML ignores extra   spaces    and
line breaks in source code.</p>

<p>This is a second paragraph. Browsers add spacing between paragraphs automatically.</p>

<p>Use <br> for a line break<br>within a paragraph.</p>

<hr>

<p>The horizontal rule above creates a thematic break.</p>
```
💡 `<br>` and `<hr>` are void elements — they don't need closing tags.

### Step 4: Add inline text formatting
```html
<p>
    This text is <strong>bold/important</strong> (semantic).<br>
    This text is <b>bold</b> (visual only).<br>
    This text is <em>emphasized/italic</em> (semantic).<br>
    This text is <i>italic</i> (visual only).<br>
    This is <mark>highlighted text</mark>.<br>
    This is <del>deleted text</del> and <ins>inserted text</ins>.<br>
    H<sub>2</sub>O uses subscript. E=mc<sup>2</sup> uses superscript.<br>
    <code>console.log('code')</code> is inline code.<br>
    <abbr title="HyperText Markup Language">HTML</abbr> uses abbreviation.
</p>
```

### Step 5: Use `<span>` for inline grouping
```html
<p>
    My favorite colors are 
    <span style="color: red;">red</span>, 
    <span style="color: blue;">blue</span>, and 
    <span style="color: green;">green</span>.
</p>
```
💡 `<span>` is a generic inline container with no semantic meaning. Use it when you need to style or target specific inline text.

### Step 6: Add preformatted text and blockquote
```html
<pre>
    This text preserves
        whitespace    and
    line breaks.
</pre>

<blockquote cite="https://www.w3.org/">
    <p>The World Wide Web Consortium (W3C) develops international standards for the Web.</p>
    <footer>— <cite>W3C</cite></footer>
</blockquote>
```

### Step 7: Validate your HTML
```bash
python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('$HOME/html-labs/lab02-text.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

**📸 Verified Output:**
```
HTML valid: OK
```

### Step 8: View in browser
```bash
cd ~/html-labs && python3 -m http.server 8080
```
Open `http://localhost:8080/lab02-text.html` and observe the visual difference between each text element.

**📸 Verified Output:**
- Headings display in decreasing font sizes
- `<strong>` and `<em>` apply bold/italic with semantic meaning
- `<pre>` preserves whitespace formatting

## ✅ Verification
Count the text elements in your file:
```bash
grep -c "<h[1-6]\|<p\|<strong\|<em\|<span" ~/html-labs/lab02-text.html
```

## 🚨 Common Mistakes
- **Using `<b>` instead of `<strong>`** — Screen readers treat these differently
- **Multiple `<h1>` tags** — Breaks document outline for SEO and accessibility
- **Using `<br>` for spacing** — Use CSS margin/padding instead
- **Skipping heading levels** — Jump from `<h1>` to `<h3>` confuses screen readers

## 📝 Summary
You learned:
- Heading hierarchy `h1`–`h6` for document structure
- `<p>` for paragraphs, `<br>` for line breaks, `<hr>` for thematic breaks
- Semantic tags: `<strong>`, `<em>`, `<mark>`, `<del>`, `<ins>`, `<abbr>`
- Inline grouping with `<span>`
- Block-level elements: `<pre>`, `<blockquote>`

## 🔗 Further Reading
- [MDN: HTML text fundamentals](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/HTML_text_fundamentals)
- [MDN: Advanced text formatting](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/Advanced_text_formatting)
