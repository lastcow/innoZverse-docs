# Lab 09: Print & Email CSS

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master print CSS (`@media print`, `@page`, orphans/widows), HTML email fundamentals (table-based layouts, inline styles, client quirks), and the MJML framework.

---

## Step 1: Print Media Query

```css
/* Separate print stylesheet */
<link rel="stylesheet" href="print.css" media="print">

/* Or inline in main stylesheet */
@media print {
  /* ALL print styles here */
}

/* Avoid: avoid loading print stylesheet for screen */
/* Use: @media print {} for co-location */
```

```css
/* Essential print resets */
@media print {
  /* Remove backgrounds (save ink) */
  *, *::before, *::after {
    background: transparent !important;
    color: #000 !important;
    box-shadow: none !important;
    text-shadow: none !important;
  }
  
  /* Remove interactive elements */
  nav, aside, .sidebar, .no-print,
  header .nav, footer .social-links,
  .cookie-banner, .chat-widget,
  video, audio, iframe {
    display: none !important;
  }
  
  /* Ensure links are readable */
  a, a:visited { text-decoration: underline; }
  a[href]::after { content: " (" attr(href) ")"; }
  abbr[title]::after { content: " (" attr(title) ")"; }
  
  /* Don't show hash/javascript links */
  a[href^="#"]::after,
  a[href^="javascript:"]::after { content: ""; }
  
  /* Show images */
  img { max-width: 100% !important; }
  
  /* Page break rules */
  thead { display: table-header-group; } /* repeat table header on each page */
  tr, img { page-break-inside: avoid; }
  
  /* Typography */
  body {
    font-size: 12pt;
    line-height: 1.5;
    font-family: Georgia, serif;
  }
}
```

---

## Step 2: @page Rule

```css
/* Define page box */
@page {
  size: A4 portrait;     /* A4, letter, legal, A3, landscape */
  margin: 2cm 1.5cm;     /* top/bottom left/right */
}

/* Named pages */
@page :first {
  margin-top: 3cm; /* extra space on first page */
}

@page :left {
  margin-right: 2.5cm; /* binding margin */
}

@page :right {
  margin-left: 2.5cm;
}

@page landscape {
  size: A4 landscape;
  margin: 1cm;
}

/* Apply named page to element */
.landscape-section {
  page: landscape;
}

/* Running headers/footers (limited support) */
@page {
  @top-center { content: "My Document"; }
  @bottom-right { content: counter(page) " of " counter(pages); }
}
```

---

## Step 3: Page Breaks, Orphans, Widows

```css
@media print {
  /* page-break-before/after/inside */
  h1 { page-break-before: always; } /* new page before each h1 */
  h2, h3 { page-break-after: avoid; } /* don't break after headings */
  
  /* Modern equivalents (also work in screen) */
  .chapter { break-before: page; }
  h2 { break-after: avoid; }
  
  .no-break {
    break-inside: avoid;      /* don't break this element across pages */
    page-break-inside: avoid; /* legacy */
  }
  
  /* Orphans: min lines at bottom of page before break */
  /* Widows: min lines at top of new page after break */
  p, blockquote {
    orphans: 3; /* at least 3 lines at bottom */
    widows: 3;  /* at least 3 lines at top of new page */
  }
  
  /* Keep elements together */
  .figure, .table-wrapper, .code-block {
    break-inside: avoid;
  }
  
  /* Page numbering with CSS counters */
  body { counter-reset: page 1; }
  .page { counter-increment: page; }
  .page::after { content: "Page " counter(page); }
}
```

---

## Step 4: HTML Email Fundamentals

Email clients ignore most modern CSS. The rules:

```html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Email</title>
  <style>
    /* Limited stylesheet — most will be inlined anyway */
    body { margin: 0; padding: 0; background: #f4f4f4; }
    table { border-collapse: collapse; }
  </style>
</head>
<body>
  <!-- Email wrapper table -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f4f4f4">
    <tr>
      <td align="center" valign="top" style="padding: 20px 0;">

        <!-- Email container -->
        <table width="600" cellpadding="0" cellspacing="0" border="0"
               bgcolor="#ffffff"
               style="max-width: 600px; background: #ffffff;">
          
          <!-- Header -->
          <tr>
            <td bgcolor="#3b82f6"
                style="background-color: #3b82f6; padding: 30px 40px; text-align: center;">
              <img src="https://example.com/logo.png" width="150" height="50"
                   alt="Logo" border="0"
                   style="display: block; margin: 0 auto;">
            </td>
          </tr>
          
          <!-- Body -->
          <tr>
            <td style="padding: 40px;">
              <h1 style="font-family: Arial, sans-serif; font-size: 24px;
                          color: #111827; margin: 0 0 16px; line-height: 1.3;">
                Welcome aboard!
              </h1>
              <p style="font-family: Arial, sans-serif; font-size: 16px;
                         line-height: 1.6; color: #6b7280; margin: 0 0 24px;">
                Thank you for signing up. Click the button below to confirm your email.
              </p>
              <!-- CTA Button — must be table-based for Outlook -->
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td bgcolor="#3b82f6" style="border-radius: 6px;"
                      align="center">
                    <a href="https://example.com/confirm"
                       style="display: inline-block; padding: 14px 32px;
                               font-family: Arial, sans-serif; font-size: 16px;
                               font-weight: bold; color: #ffffff; text-decoration: none;">
                      Confirm Email
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 20px 40px; border-top: 1px solid #e5e7eb;">
              <p style="font-family: Arial, sans-serif; font-size: 12px;
                         color: #9ca3af; margin: 0; text-align: center;">
                © 2024 Example Inc. • 
                <a href="https://example.com/unsubscribe"
                   style="color: #6b7280;">Unsubscribe</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

---

## Step 5: Email Client Quirks

```css
/* Email CSS support guide */

/* ✓ Works everywhere: */
/* - Table layouts */
/* - Inline styles */
/* - Basic font-size, color, background-color */
/* - border-collapse */
/* - padding (but not margin on most) */
/* - width/height on tables and cells */

/* ⚠ Works in some clients: */
/* - @media queries (Gmail app: NO; Outlook: NO) */
/* - Flexbox (most modern clients: yes; Outlook: NO) */
/* - border-radius (Outlook: NO) */
/* - box-shadow (Outlook: NO) */
/* - CSS animations (Apple Mail: yes; others: NO) */

/* ❌ Never works: */
/* - CSS Grid (all email clients) */
/* - position: absolute/fixed */
/* - z-index */
/* - JavaScript */
/* - External stylesheets (mostly) */

/* Outlook-specific hacks */
<!--[if mso]>
<style>
  .button-link { display: none !important; }
  v\:* { behavior: url(#default#VML); display: inline-block; }
</style>
<![endif]-->

/* Outlook VML button (since CSS border-radius doesn't work) */
<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
             href="https://example.com" style="height:46px;v-text-anchor:middle;width:200px;"
             arcsize="13%" fillcolor="#3b82f6" stroke="f">
  <w:anchorlock/>
  <center style="color:#ffffff;font-family:sans-serif;font-size:16px;font-weight:bold;">
    Click Here
  </center>
</v:roundrect>
<![endif]-->
```

---

## Step 6: Responsive Email

```css
/* Mobile-first email with @media */
<style>
  /* Default: mobile */
  .container { width: 100% !important; max-width: 600px; }
  .column { display: block; width: 100% !important; }
  .hide-mobile { display: none !important; }
  .show-mobile { display: block !important; }

  /* Desktop */
  @media (min-width: 600px) {
    .column { display: table-cell !important; width: 50% !important; }
    .hide-mobile { display: table-cell !important; }
    .show-mobile { display: none !important; }
  }
</style>
```

---

## Step 7: MJML Framework

```html
<!-- MJML: write components, get HTML email output -->
<!-- Install: npm install mjml -->

<mjml>
  <mj-head>
    <mj-title>Welcome Email</mj-title>
    <mj-font name="Inter" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600"/>
    <mj-attributes>
      <mj-all font-family="Inter, Arial, sans-serif"/>
      <mj-text font-size="16px" line-height="1.6" color="#111827"/>
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f4f4f4">
    <mj-section background-color="#3b82f6" padding="30px 40px">
      <mj-column>
        <mj-image width="150px" src="logo.png" alt="Logo"/>
      </mj-column>
    </mj-section>
    <mj-section background-color="#ffffff" padding="40px">
      <mj-column>
        <mj-text font-size="24px" font-weight="600">Welcome aboard!</mj-text>
        <mj-text>Thank you for signing up. Click below to confirm.</mj-text>
        <mj-button background-color="#3b82f6" href="https://example.com/confirm">
          Confirm Email
        </mj-button>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

```bash
# Compile MJML to HTML email
npx mjml welcome.mjml -o welcome.html

# Watch mode
npx mjml welcome.mjml -o welcome.html --watch
```

---

## Step 8: Capstone — Print CSS Generator

```bash
docker run --rm -v /tmp/print_css.js:/test.js node:20-alpine node /test.js
```

*(Create the file:)*
```bash
cat > /tmp/print_css.js << 'EOF'
var printStyles = "\n/* Print CSS Generator Output */\n\n@media print {\n  *, *::before, *::after {\n    background: transparent !important;\n    color: #000 !important;\n    box-shadow: none !important;\n  }\n\n  @page {\n    size: A4 portrait;\n    margin: 2cm 1.5cm;\n  }\n\n  body {\n    font-size: 12pt;\n    line-height: 1.5;\n    font-family: Georgia, serif;\n  }\n\n  h1 { font-size: 22pt; page-break-after: avoid; }\n  h2 { font-size: 18pt; page-break-after: avoid; }\n\n  p, blockquote {\n    orphans: 3;\n    widows: 3;\n  }\n\n  .page-break-before { page-break-before: always; }\n  .no-break { page-break-inside: avoid; }\n  \n  nav, aside, .no-print, footer { display: none !important; }\n\n  a[href]::after { content: \" (\" attr(href) \")\"; }\n}";
console.log(printStyles);
console.log("\n--- Validation ---");
var rules = ["@media print","@page","orphans","widows","page-break-before","page-break-inside"];
rules.forEach(function(r){
  console.log("[OK] " + r + " present: " + printStyles.includes(r));
});
EOF
docker run --rm -v /tmp/print_css.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
/* Print CSS Generator Output */

@media print {
  *, *::before, *::after {
    background: transparent !important;
    color: #000 !important;
    box-shadow: none !important;
  }

  @page {
    size: A4 portrait;
    margin: 2cm 1.5cm;
  }
  ...
}

--- Validation ---
[OK] @media print present: true
[OK] @page present: true
[OK] orphans present: true
[OK] widows present: true
[OK] page-break-before present: true
[OK] page-break-inside present: true
```

---

## Summary

| Feature | CSS | Support |
|---------|-----|---------|
| Print media | `@media print {}` | Universal |
| Page size | `@page { size: A4 }` | Modern browsers |
| Page margins | `@page { margin: 2cm }` | Universal |
| Page break | `break-before: page` | Modern (+ legacy) |
| Orphans/widows | `orphans: 3` | Most browsers |
| Email layout | Table-based HTML | All clients |
| Inline styles | Required for email | All clients |
| Responsive email | `@media` in `<style>` | Most clients |
| MJML | Component-based | Compiles to HTML |
| Outlook VML | `<!--[if mso]>` | Outlook only |
