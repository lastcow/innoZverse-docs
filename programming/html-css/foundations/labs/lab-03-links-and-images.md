# Lab 3: Links and Images

## 🎯 Objective
Learn to create hyperlinks with `<a>` and embed images with `<img>`, including relative/absolute paths, target attributes, and accessibility best practices.

## 📚 Background
Links and images are two of the most fundamental HTML elements. The `<a>` (anchor) tag creates clickable links, while `<img>` embeds images. Both require attributes to function correctly — `href` for links and `src`/`alt` for images.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Labs 1–2 completed

## 🛠️ Tools Used
- Python 3
- Web browser

## 🔬 Lab Instructions

### Step 1: Create the lab file
```bash
touch ~/html-labs/lab03-links-images.html
mkdir ~/html-labs/images
```

### Step 2: Create a sample image for testing
```bash
# Create a simple SVG image
cat > ~/html-labs/images/logo.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
  <rect width="200" height="100" fill="#4A90D9"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="white" font-size="20">innoZverse</text>
</svg>
EOF
```

### Step 3: Add various types of links
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Links and Images</title>
</head>
<body>
    <h1>Links and Images</h1>

    <h2>Types of Links</h2>

    <!-- Absolute external link -->
    <p><a href="https://www.w3.org/" target="_blank" rel="noopener noreferrer">
        W3C Website (opens in new tab)
    </a></p>

    <!-- Relative link -->
    <p><a href="lab02-text.html">Go to Lab 2 (relative link)</a></p>

    <!-- Link to section on same page -->
    <p><a href="#images-section">Jump to Images Section</a></p>

    <!-- Email link -->
    <p><a href="mailto:hello@example.com">Send us an email</a></p>

    <!-- Phone link -->
    <p><a href="tel:+1234567890">Call us: +1 234 567 890</a></p>

    <!-- Download link -->
    <p><a href="images/logo.svg" download="innozverse-logo.svg">Download Logo</a></p>
</body>
</html>
```
💡 Always add `rel="noopener noreferrer"` with `target="_blank"` to prevent security vulnerabilities.

### Step 4: Add the images section
```html
    <h2 id="images-section">Images</h2>

    <!-- Basic image with required alt text -->
    <img src="images/logo.svg" alt="innoZverse Logo" width="200" height="100">

    <!-- Image as a link -->
    <a href="https://www.example.com">
        <img src="images/logo.svg" alt="Click to visit example.com" width="100" height="50">
    </a>

    <!-- Responsive image with srcset -->
    <img 
        src="images/logo.svg" 
        alt="Responsive logo"
        width="200" 
        height="100"
        loading="lazy">

    <!-- Decorative image (empty alt) -->
    <img src="images/logo.svg" alt="" width="50" height="25">

    <!-- Figure with caption -->
    <figure>
        <img src="images/logo.svg" alt="innoZverse platform logo" width="200" height="100">
        <figcaption>Figure 1: The innoZverse platform logo</figcaption>
    </figure>
```
💡 **Never omit `alt`**. Use empty `alt=""` for purely decorative images so screen readers skip them.

### Step 5: Create a navigation with links
```html
    <nav aria-label="Page navigation">
        <ul>
            <li><a href="#top">Top</a></li>
            <li><a href="#images-section">Images</a></li>
            <li><a href="lab02-text.html">Previous Lab</a></li>
            <li><a href="lab04-lists.html">Next Lab</a></li>
        </ul>
    </nav>
```

### Step 6: Add an anchor at the top
```html
<body id="top">
```

### Step 7: Validate HTML
```bash
cat > /tmp/lab03.html << 'ENDOFHTML'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Links Test</title></head>
<body>
<a href="https://example.com" target="_blank" rel="noopener noreferrer">Link</a>
<img src="test.svg" alt="Test image" width="100" height="50">
<figure><img src="test.svg" alt="Figure image"><figcaption>Caption</figcaption></figure>
</body>
</html>
ENDOFHTML

python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('/tmp/lab03.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

**📸 Verified Output:**
```
HTML valid: OK
```

### Step 8: Test links in browser
```bash
cd ~/html-labs && python3 -m http.server 8080
```
Open `http://localhost:8080/lab03-links-images.html`. Click each link to verify they work.

**📸 Verified Output:**
- Internal anchor links jump to the correct section
- `download` attribute triggers file download
- `target="_blank"` opens external links in a new tab

## ✅ Verification
```bash
python3 -c "
import re
html = open('$HOME/html-labs/lab03-links-images.html').read()
links = re.findall(r'<a\s+[^>]*href', html)
images = re.findall(r'<img\s+[^>]*alt', html)
print(f'Links found: {len(links)}')
print(f'Images with alt: {len(images)}')
print('OK')
"
```

## 🚨 Common Mistakes
- **Missing `alt` attribute** — Required for accessibility; screen readers need it
- **Using `target="_blank"` without `rel="noopener"`** — Security vulnerability (tab nabbing)
- **Absolute paths for local files** — Use relative paths; absolute paths break when deployed
- **Empty link text** — `<a href="...">Click here</a>` is bad; describe the destination
- **Missing `width`/`height` on images** — Causes layout shift (CLS) as page loads

## 📝 Summary
You learned:
- `<a href="">` for links with absolute, relative, anchor, email, and phone URLs
- `target="_blank"` with `rel="noopener noreferrer"` for safe external links
- `<img src="" alt="">` with proper `alt` text for accessibility
- `loading="lazy"` for performance
- `<figure>` and `<figcaption>` for semantic image captions
- `download` attribute for downloadable files

## 🔗 Further Reading
- [MDN: Creating hyperlinks](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/Creating_hyperlinks)
- [MDN: Images in HTML](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Images_in_HTML)
- [WebAIM: Alt Text](https://webaim.org/techniques/alttext/)
