# Lab 14: Modern HTML Semantics

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Use HTML5 semantic elements correctly, implement JSON-LD structured data, add Open Graph/Twitter Card meta tags, and write accessible HTML that communicates meaning to browsers, search engines, and assistive technologies.

---

## Step 1: HTML5 Semantic Elements

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Article Page</title>
</head>
<body>

  <!-- <header>: introductory content, navigation -->
  <header>
    <nav aria-label="Main navigation">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  </header>

  <!-- <main>: primary content (one per page) -->
  <main id="main-content">

    <!-- <article>: self-contained, redistributable content -->
    <article>
      <header>
        <h1>Article Title</h1>
        <p>By <address><a href="/author">Jane Doe</a></address></p>
        <!-- <time>: machine-readable datetime -->
        <time datetime="2024-03-15T14:30:00Z">March 15, 2024</time>
      </header>

      <!-- <section>: thematic grouping with heading -->
      <section aria-labelledby="intro-heading">
        <h2 id="intro-heading">Introduction</h2>
        <p>Content with <mark>highlighted term</mark> for context.</p>
      </section>

      <section>
        <h2>Details</h2>
        <!-- <details>/<summary>: disclosure widget -->
        <details>
          <summary>Show technical details</summary>
          <p>Hidden content revealed on click.</p>
        </details>

        <!-- <figure>/<figcaption> -->
        <figure>
          <img src="diagram.png" alt="System architecture diagram">
          <figcaption>Figure 1: System architecture overview</figcaption>
        </figure>
      </section>

      <!-- <aside>: tangential content -->
      <aside aria-label="Related links">
        <h3>See Also</h3>
        <ul>
          <li><a href="/related">Related Article</a></li>
        </ul>
      </aside>

    </article>
  </main>

  <!-- <footer>: authorship, copyright, links -->
  <footer>
    <p><small>&copy; 2024 My Site. All rights reserved.</small></p>
  </footer>

</body>
</html>
```

---

## Step 2: Semantic Interactive Elements

```html
<!-- <dialog>: native modal dialog -->
<dialog id="confirm-dialog" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm Action</h2>
  <p>Are you sure you want to delete this item?</p>
  <footer>
    <button type="button" onclick="dialog.close('cancel')">Cancel</button>
    <button type="button" onclick="dialog.close('confirm')">Delete</button>
  </footer>
</dialog>

<button onclick="document.getElementById('confirm-dialog').showModal()">
  Delete Item
</button>

<script>
  const dialog = document.getElementById('confirm-dialog');
  dialog.addEventListener('close', () => {
    if (dialog.returnValue === 'confirm') deleteItem();
  });
</script>
```

```html
<!-- <details>/<summary>: no JS accordion -->
<details>
  <summary>How does billing work?</summary>
  <div>
    <p>You're billed monthly based on usage...</p>
  </div>
</details>

<!-- Open by default -->
<details open>
  <summary>Default expanded section</summary>
  <p>This starts expanded.</p>
</details>
```

---

## Step 3: Semantic Text Elements

```html
<!-- <mark>: highlighted/relevant text -->
Search results for "CSS Grid": 
<p>The <mark>CSS Grid</mark> layout module is powerful.</p>

<!-- <time>: machine-readable dates/times -->
<time datetime="2024-12-25">Christmas Day</time>
<time datetime="14:30">2:30 PM</time>
<time datetime="PT2H30M">2 hours 30 minutes</time>
<time datetime="2024-03-15T09:00:00-05:00">March 15, 9 AM EST</time>

<!-- <output>: result of calculation/user action -->
<form oninput="result.value = parseInt(qty.value) * parseInt(price.value)">
  <input type="number" id="qty" value="1"> ×
  <input type="number" id="price" value="10"> =
  <output name="result" for="qty price">10</output>
</form>

<!-- <abbr>: abbreviation with expansion -->
<abbr title="World Wide Web Consortium">W3C</abbr>
<abbr title="Cascading Style Sheets">CSS</abbr>

<!-- <cite>: creative work title -->
<cite>The Design of Everyday Things</cite> by Don Norman.

<!-- <kbd>: keyboard input -->
Press <kbd>Ctrl</kbd> + <kbd>C</kbd> to copy.

<!-- <code>, <pre>, <samp> -->
Use <code>git commit -m "message"</code> to commit.

<pre><code class="language-js">
const greeting = 'Hello, World!';
console.log(greeting);
</code></pre>

<!-- <data>: machine-readable value -->
<data value="12345">Widget A</data>
```

---

## Step 4: Microdata

```html
<!-- Inline microdata (alternative to JSON-LD) -->
<article itemscope itemtype="https://schema.org/Article">
  <h1 itemprop="headline">CSS Grid: Complete Guide</h1>
  
  <div itemprop="author" itemscope itemtype="https://schema.org/Person">
    <span itemprop="name">Jane Doe</span>
  </div>
  
  <time itemprop="datePublished" datetime="2024-01-15">
    January 15, 2024
  </time>
  
  <meta itemprop="description" content="Comprehensive CSS Grid tutorial">
  
  <div itemprop="image" itemscope itemtype="https://schema.org/ImageObject">
    <img itemprop="url" src="/images/css-grid.jpg" alt="CSS Grid diagram">
    <meta itemprop="width" content="1200">
    <meta itemprop="height" content="630">
  </div>
</article>
```

---

## Step 5: JSON-LD Structured Data

JSON-LD is preferred — it doesn't require HTML modification:

```html
<head>
  <!-- Article schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "CSS Grid: Complete Guide",
    "description": "A comprehensive guide to CSS Grid layout",
    "image": "https://example.com/images/css-grid.jpg",
    "author": {
      "@type": "Person",
      "name": "Jane Doe",
      "url": "https://example.com/author/jane"
    },
    "publisher": {
      "@type": "Organization",
      "name": "My Blog",
      "logo": {
        "@type": "ImageObject",
        "url": "https://example.com/logo.png"
      }
    },
    "datePublished": "2024-01-15",
    "dateModified": "2024-03-20"
  }
  </script>

  <!-- Product schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "CSS Grid Mastery Course",
    "description": "Learn CSS Grid from beginner to expert",
    "offers": {
      "@type": "Offer",
      "price": "49.99",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "reviewCount": "127"
    }
  }
  </script>

  <!-- BreadcrumbList schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com" },
      { "@type": "ListItem", "position": 2, "name": "CSS", "item": "https://example.com/css" },
      { "@type": "ListItem", "position": 3, "name": "Grid Guide" }
    ]
  }
  </script>
</head>
```

---

## Step 6: Open Graph & Twitter Cards

```html
<head>
  <!-- Open Graph (Facebook, LinkedIn, WhatsApp, Slack) -->
  <meta property="og:title"       content="CSS Grid: Complete Guide">
  <meta property="og:description" content="Comprehensive CSS Grid tutorial">
  <meta property="og:image"       content="https://example.com/og-css-grid.jpg">
  <meta property="og:image:width"  content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt"    content="CSS Grid diagram">
  <meta property="og:url"         content="https://example.com/css/grid">
  <meta property="og:type"        content="article">
  <meta property="og:site_name"   content="My Dev Blog">
  <meta property="og:locale"      content="en_US">
  
  <!-- Article-specific OG -->
  <meta property="article:author"        content="https://example.com/author/jane">
  <meta property="article:published_time" content="2024-01-15T00:00:00Z">
  <meta property="article:section"       content="CSS">
  <meta property="article:tag"           content="css, grid, layout">

  <!-- Twitter Card -->
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:site"        content="@mydevblog">
  <meta name="twitter:creator"     content="@janedoe">
  <meta name="twitter:title"       content="CSS Grid: Complete Guide">
  <meta name="twitter:description" content="Comprehensive CSS Grid tutorial">
  <meta name="twitter:image"       content="https://example.com/og-css-grid.jpg">
  <meta name="twitter:image:alt"   content="CSS Grid diagram">

  <!-- Canonical URL (avoid duplicate content) -->
  <link rel="canonical" href="https://example.com/css/grid">

  <!-- Alternate language versions -->
  <link rel="alternate" hreflang="es" href="https://example.com/es/css/grid">
  <link rel="alternate" hreflang="zh" href="https://example.com/zh/css/grid">
  <link rel="alternate" hreflang="x-default" href="https://example.com/css/grid">
</head>
```

---

## Step 7: Additional Head Meta

```html
<head>
  <!-- Essential -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CSS Grid: Complete Guide | My Dev Blog</title>
  <meta name="description" content="Learn CSS Grid with 30+ examples...">
  
  <!-- Robots -->
  <meta name="robots" content="index, follow, max-image-preview:large">
  
  <!-- Theme color -->
  <meta name="theme-color" content="#3b82f6">
  <meta name="theme-color" media="(prefers-color-scheme: dark)" content="#1e3a8a">
  
  <!-- Color scheme -->
  <meta name="color-scheme" content="light dark">

  <!-- Manifest (PWA) -->
  <link rel="manifest" href="/manifest.json">
  
  <!-- Favicon -->
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" href="/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
```

---

## Step 8: Capstone — JSON-LD Schema Validator

```bash
docker run --rm node:20-alpine node -e "
var schema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  'headline': 'Introduction to HTML5',
  'author': {'@type': 'Person', 'name': 'Jane Doe'},
  'datePublished': '2024-01-15',
  'description': 'A comprehensive guide to HTML5 features'
};
var required = ['@context','@type','headline','author','datePublished'];
var missing = required.filter(function(f){ return !schema[f]; });
console.log('Schema type:', schema['@type']);
console.log('Required fields present:', (required.length - missing.length) + '/' + required.length);
console.log('Missing fields:', missing.length === 0 ? 'none' : missing.join(','));
console.log('Valid JSON-LD:', missing.length === 0);
console.log('');
console.log('Output:');
console.log(JSON.stringify(schema, null, 2));
"
```

📸 **Verified Output:**
```
Schema type: Article
Required fields present: 5/5
Missing fields: none
Valid JSON-LD: true

Output:
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Introduction to HTML5",
  "author": {
    "@type": "Person",
    "name": "Jane Doe"
  },
  "datePublished": "2024-01-15",
  "description": "A comprehensive guide to HTML5 features"
}
```

---

## Summary

| Element | Purpose | SEO/A11y Impact |
|---------|---------|----------------|
| `<article>` | Self-contained content | Crawler context |
| `<section>` | Thematic grouping | Document outline |
| `<aside>` | Supplementary content | Skip in screen readers |
| `<main>` | Primary content | Landmark navigation |
| `<dialog>` | Native modal | Built-in a11y |
| `<details>/<summary>` | Disclosure widget | No JS needed |
| `<time datetime>` | Machine date | Search rich results |
| `<mark>` | Highlighted text | Emphasis in search |
| JSON-LD | Structured data | Rich results |
| Open Graph | Social preview | Click-through rates |
| canonical | Dedup URLs | SEO ranking |
