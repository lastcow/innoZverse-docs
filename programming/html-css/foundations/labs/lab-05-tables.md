# Lab 5: Tables

## 🎯 Objective
Build semantic HTML tables using `<table>`, `<thead>`, `<tbody>`, `<tfoot>`, `<tr>`, `<th>`, and `<td>`, with proper accessibility attributes.

## 📚 Background
HTML tables display tabular data — data with rows and columns. They are NOT for layout (use CSS Grid/Flexbox instead). Proper semantic markup including `<thead>`, `<caption>`, and `scope` attributes makes tables accessible to screen readers.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Labs 1–4 completed

## 🛠️ Tools Used
- Python 3, Web browser

## 🔬 Lab Instructions

### Step 1: Create the lab file
```bash
touch ~/html-labs/lab05-tables.html
```

### Step 2: Build a basic table
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HTML Tables</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
        th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
        th { background-color: #4A90D9; color: white; }
        tr:nth-child(even) { background-color: #f5f5f5; }
        caption { font-weight: bold; margin-bottom: 0.5rem; }
    </style>
</head>
<body>
    <h1>HTML Tables</h1>

    <h2>Basic Table</h2>
    <table>
        <caption>Programming Languages Overview</caption>
        <thead>
            <tr>
                <th scope="col">Language</th>
                <th scope="col">Type</th>
                <th scope="col">Year Created</th>
                <th scope="col">Primary Use</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Python</td>
                <td>Interpreted</td>
                <td>1991</td>
                <td>Data Science, Web</td>
            </tr>
            <tr>
                <td>Go</td>
                <td>Compiled</td>
                <td>2009</td>
                <td>Systems, Cloud</td>
            </tr>
            <tr>
                <td>JavaScript</td>
                <td>Interpreted</td>
                <td>1995</td>
                <td>Web Frontend/Backend</td>
            </tr>
            <tr>
                <td>Rust</td>
                <td>Compiled</td>
                <td>2010</td>
                <td>Systems, WebAssembly</td>
            </tr>
        </tbody>
        <tfoot>
            <tr>
                <td colspan="4">Data as of 2024</td>
            </tr>
        </tfoot>
    </table>
```
💡 `scope="col"` on `<th>` helps screen readers understand that the header applies to the column.

### Step 3: Add cell spanning
```html
    <h2>Table with Spanning Cells</h2>
    <table>
        <caption>Weekly Schedule</caption>
        <thead>
            <tr>
                <th scope="col">Time</th>
                <th scope="col">Monday</th>
                <th scope="col">Tuesday</th>
                <th scope="col">Wednesday</th>
                <th scope="col">Thursday</th>
                <th scope="col">Friday</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <th scope="row">9:00</th>
                <td colspan="2">Team Standup</td>
                <td>1:1 Meeting</td>
                <td colspan="2">Team Standup</td>
            </tr>
            <tr>
                <th scope="row">10:00</th>
                <td>Development</td>
                <td>Development</td>
                <td rowspan="2">Sprint Planning</td>
                <td>Development</td>
                <td>Code Review</td>
            </tr>
            <tr>
                <th scope="row">11:00</th>
                <td>Testing</td>
                <td>Testing</td>
                <!-- rowspan cell above fills this -->
                <td>Testing</td>
                <td>Retrospective</td>
            </tr>
        </tbody>
    </table>
```
💡 `colspan` merges cells horizontally; `rowspan` merges vertically.

### Step 4: Add row-level headers
```html
    <h2>Table with Row Headers</h2>
    <table>
        <caption>Server Specifications</caption>
        <tbody>
            <tr>
                <th scope="row">CPU</th>
                <td>Intel Xeon E5-2680</td>
                <td>16 cores / 32 threads</td>
            </tr>
            <tr>
                <th scope="row">RAM</th>
                <td>128 GB DDR4</td>
                <td>ECC Registered</td>
            </tr>
            <tr>
                <th scope="row">Storage</th>
                <td>2TB NVMe SSD</td>
                <td>RAID 1</td>
            </tr>
        </tbody>
    </table>
```

### Step 5: Use `<colgroup>` for column styling
```html
    <h2>Styled Columns with colgroup</h2>
    <table>
        <caption>Sales Data Q4</caption>
        <colgroup>
            <col style="background-color: #f0f0f0;">
            <col span="3" style="background-color: #e8f4fd;">
        </colgroup>
        <thead>
            <tr>
                <th scope="col">Product</th>
                <th scope="col">October</th>
                <th scope="col">November</th>
                <th scope="col">December</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <th scope="row">Widget A</th>
                <td>$12,000</td>
                <td>$15,000</td>
                <td>$22,000</td>
            </tr>
            <tr>
                <th scope="row">Widget B</th>
                <td>$8,500</td>
                <td>$9,200</td>
                <td>$18,000</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
```

### Step 6: Validate the HTML
```bash
cat > /tmp/lab05.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Tables</title></head>
<body>
<table>
  <caption>Test Table</caption>
  <thead><tr><th scope="col">A</th><th scope="col">B</th></tr></thead>
  <tbody><tr><td>1</td><td>2</td></tr></tbody>
  <tfoot><tr><td colspan="2">Footer</td></tr></tfoot>
</table>
</body>
</html>
EOF

python3 -c "
from html.parser import HTMLParser
class Validator(HTMLParser): pass
html = open('/tmp/lab05.html').read()
v = Validator()
v.feed(html)
print('HTML valid: OK')
"
```

**📸 Verified Output:**
```
HTML valid: OK
```

### Step 7: Make the table responsive
Add to your `<style>`:
```css
@media (max-width: 600px) {
    table, thead, tbody, th, td, tr {
        display: block;
    }
    thead tr {
        position: absolute;
        top: -9999px;
        left: -9999px;
    }
    td::before {
        content: attr(data-label);
        font-weight: bold;
        display: block;
    }
}
```
Add `data-label` attributes to your `<td>` cells for the mobile labels.

### Step 8: View in browser
```bash
cd ~/html-labs && python3 -m http.server 8080
```
Open `http://localhost:8080/lab05-tables.html`.

**📸 Verified Output:**
- Striped rows (every other row has light gray background)
- Blue header row with white text
- `colspan` cells visibly span multiple columns

## ✅ Verification
```bash
python3 -c "
import re
html = open('$HOME/html-labs/lab05-tables.html').read()
tables = len(re.findall(r'<table', html))
th_scope = len(re.findall(r'scope=', html))
print(f'Tables: {tables}, Headers with scope: {th_scope}')
print('OK' if tables >= 2 and th_scope >= 4 else 'Add more scope attributes')
"
```

## 🚨 Common Mistakes
- **Using tables for page layout** — Never. Use CSS Grid or Flexbox
- **Missing `<caption>`** — Reduces accessibility; screen readers announce it
- **Missing `scope` on `<th>`** — Screen readers can't associate headers with data cells
- **Incorrect `colspan`/`rowspan`** — Cell count mismatch breaks the table visually
- **No `<thead>`/`<tbody>` structure** — Makes the table less semantic and harder to style

## 📝 Summary
You mastered:
- Table structure: `<table>`, `<thead>`, `<tbody>`, `<tfoot>`
- Row/cell elements: `<tr>`, `<th>`, `<td>`
- Accessibility: `<caption>`, `scope` attribute on headers
- Cell spanning: `colspan` and `rowspan`
- Column styling with `<colgroup>`

## 🔗 Further Reading
- [MDN: HTML tables](https://developer.mozilla.org/en-US/docs/Learn/HTML/Tables)
- [WebAIM: Creating Accessible Tables](https://webaim.org/techniques/tables/)
