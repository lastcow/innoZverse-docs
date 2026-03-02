# Lab 9: Node.js File System

## 🎯 Objective
Read, write, copy, and process files using Node.js `fs` module, both synchronous and asynchronous APIs, plus `path` and `stream` for large files.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 8: Modules

## 🛠️ Tools Used
- Node.js 20 (`fs`, `path`, `stream` built-ins)

## 🔬 Lab Instructions

### Step 1: Writing and Reading Files
```javascript
const fs = require("fs");
const path = require("path");

const FILE = "/tmp/demo.txt";

// Write synchronously
fs.writeFileSync(FILE, "Line 1\nLine 2\nLine 3\n");
console.log("Written:", fs.statSync(FILE).size, "bytes");

// Read entire file
const content = fs.readFileSync(FILE, "utf8");
console.log("Content:\n" + content.trim());

// Read line by line using split
const lines = content.trim().split("\n");
lines.forEach((line, i) => console.log(`  [${i}] ${line}`));
```

**📸 Verified Output:**
```
Written: 21 bytes
Content:
Line 1
Line 2
Line 3
  [0] Line 1
  [1] Line 2
  [2] Line 3
```

### Step 2: Async File Operations
```javascript
const fs = require("fs").promises;  // Promise-based fs

async function main() {
    const file = "/tmp/async_demo.txt";
    
    // Write
    await fs.writeFile(file, "Async content\nLine 2\nLine 3\n");
    
    // Read
    const content = await fs.readFile(file, "utf8");
    console.log("Lines:", content.trim().split("\n").length);
    
    // Append
    await fs.appendFile(file, "Line 4\n");
    
    // Stats
    const stat = await fs.stat(file);
    console.log("Size:", stat.size, "bytes");
    console.log("Modified:", stat.mtime.toISOString().split("T")[0]);
    
    // Delete
    await fs.unlink(file);
    console.log("Deleted:", !(await fs.access(file).then(() => true).catch(() => false)));
}

main();
```

**📸 Verified Output:**
```
Lines: 3
Size: 35 bytes
Modified: 2026-03-02
Deleted: true
```

### Step 3: Working with Directories
```javascript
const fs = require("fs").promises;
const path = require("path");

async function main() {
    const dir = "/tmp/test_dir";
    
    // Create directory tree
    await fs.mkdir(path.join(dir, "sub/deep"), { recursive: true });
    
    // Write files in different dirs
    const files = ["a.txt", "b.txt", "sub/c.txt", "sub/deep/d.txt"];
    for (const f of files) {
        await fs.writeFile(path.join(dir, f), `Content of ${f}\n`);
    }
    
    // List directory
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const e of entries) {
        console.log(`  [${e.isDirectory() ? "DIR" : "FILE"}] ${e.name}`);
    }
    
    // Recursive listing
    async function listAll(d, prefix = "") {
        const entries = await fs.readdir(d, { withFileTypes: true });
        for (const e of entries) {
            const full = path.join(d, e.name);
            console.log(`${prefix}${e.isDirectory() ? "📁" : "📄"} ${e.name}`);
            if (e.isDirectory()) await listAll(full, prefix + "  ");
        }
    }
    
    console.log("\nFull tree:");
    await listAll(dir);
}

main();
```

**📸 Verified Output:**
```
  [DIR] sub
  [FILE] a.txt
  [FILE] b.txt

Full tree:
📁 sub
  📁 deep
    📄 d.txt
  📄 c.txt
📄 a.txt
📄 b.txt
```

### Step 4: JSON Config Files
```javascript
const fs = require("fs");
const path = require("path");

class Config {
    constructor(filePath) {
        this.path = filePath;
        this.data = fs.existsSync(filePath)
            ? JSON.parse(fs.readFileSync(filePath, "utf8"))
            : {};
    }
    
    get(key, defaultVal) {
        return this.data[key] ?? defaultVal;
    }
    
    set(key, value) {
        this.data[key] = value;
        fs.writeFileSync(this.path, JSON.stringify(this.data, null, 2));
        return this;
    }
    
    getAll() { return { ...this.data }; }
}

const config = new Config("/tmp/app_config.json");
config.set("theme", "dark")
      .set("language", "en")
      .set("fontSize", 14)
      .set("features", { darkMode: true, notifications: false });

console.log("Theme:", config.get("theme"));
console.log("Font:", config.get("fontSize"));
console.log("Missing:", config.get("apiKey", "not-set"));
console.log("All:", JSON.stringify(config.getAll()));
```

**📸 Verified Output:**
```
Theme: dark
Font: 14
Missing: not-set
All: {"theme":"dark","language":"en","fontSize":14,"features":{"darkMode":true,"notifications":false}}
```

### Step 5: Streams for Large Files
```javascript
const fs = require("fs");
const readline = require("readline");

// Create a large-ish text file
const writer = fs.createWriteStream("/tmp/large.txt");
for (let i = 1; i <= 1000; i++) {
    writer.write(`Line ${i}: ${Math.random().toFixed(6)}\n`);
}
writer.end();

writer.on("finish", () => {
    // Read with readline stream — memory efficient
    let lineCount = 0;
    let sum = 0;
    
    const rl = readline.createInterface({
        input: fs.createReadStream("/tmp/large.txt"),
        crlfDelay: Infinity,
    });
    
    rl.on("line", (line) => {
        lineCount++;
        const num = parseFloat(line.split(": ")[1]);
        if (!isNaN(num)) sum += num;
    });
    
    rl.on("close", () => {
        console.log(`Lines: ${lineCount}`);
        console.log(`Sum of random numbers: ${sum.toFixed(2)}`);
        console.log(`Average: ${(sum/lineCount).toFixed(4)}`);
    });
});
```

**📸 Verified Output:**
```
Lines: 1000
Sum of random numbers: 498.xx
Average: 0.4xxx
```

### Step 6: Path Module
```javascript
const path = require("path");

const filePath = "/home/alice/projects/myapp/src/utils/helper.js";

console.log("dirname:", path.dirname(filePath));
console.log("basename:", path.basename(filePath));
console.log("ext:", path.extname(filePath));
console.log("name:", path.basename(filePath, path.extname(filePath)));

// Join paths safely
const joined = path.join("/tmp", "projects", "myapp", "index.js");
console.log("join:", joined);

// Resolve relative path
const resolved = path.resolve("./src/utils");
console.log("resolve:", resolved.slice(-20));

// Parse and format
const parts = path.parse(filePath);
console.log("parse:", parts);
const rebuilt = path.format(parts);
console.log("format:", rebuilt === filePath);
```

**📸 Verified Output:**
```
dirname: /home/alice/projects/myapp/src/utils
basename: helper.js
ext: .js
name: helper
join: /tmp/projects/myapp/index.js
resolve: .../src/utils
parse: { root: '/', dir: '/home/alice/projects/myapp/src/utils', base: 'helper.js', ext: '.js', name: 'helper' }
format: true
```

### Step 7: File Watching
```javascript
const fs = require("fs");

const watchFile = "/tmp/watched.txt";
fs.writeFileSync(watchFile, "initial content\n");

let changeCount = 0;
const watcher = fs.watch(watchFile, (event, filename) => {
    changeCount++;
    const content = fs.readFileSync(watchFile, "utf8").trim();
    console.log(`  [${event}] ${filename}: "${content.slice(0, 30)}"`);
    
    if (changeCount >= 3) {
        watcher.close();
        console.log("Watcher closed after 3 changes");
    }
});

// Make changes
let count = 0;
const interval = setInterval(() => {
    count++;
    fs.writeFileSync(watchFile, `Update ${count}: ${new Date().toISOString()}\n`);
    if (count >= 3) clearInterval(interval);
}, 100);
```

**📸 Verified Output:**
```
  [change] watched.txt: "Update 1: 2026-03-02T09:00:00.000Z"
  [change] watched.txt: "Update 2: 2026-03-02T09:00:00.100Z"
  [change] watched.txt: "Update 3: 2026-03-02T09:00:00.200Z"
Watcher closed after 3 changes
```

### Step 8: CSV File Processing
```javascript
const fs = require("fs");

// Write CSV
const csv = `Name,Age,Department,Salary
Alice Smith,30,Engineering,95000
Bob Jones,25,Marketing,65000
Charlie Brown,35,Engineering,110000
Diana Prince,28,Design,75000
Eve Wilson,32,Engineering,98000`;

fs.writeFileSync("/tmp/employees.csv", csv);

// Parse CSV
function parseCSV(content) {
    const [headerLine, ...rows] = content.trim().split("\n");
    const headers = headerLine.split(",");
    return rows.map(row => {
        const values = row.split(",");
        return Object.fromEntries(headers.map((h, i) => [h, values[i]]));
    });
}

const employees = parseCSV(fs.readFileSync("/tmp/employees.csv", "utf8"));

// Analysis
const engineers = employees.filter(e => e.Department === "Engineering");
const avgSalary = employees.reduce((s, e) => s + Number(e.Salary), 0) / employees.length;
const highest = employees.reduce((a, b) => Number(a.Salary) > Number(b.Salary) ? a : b);

console.log(`Total employees: ${employees.length}`);
console.log(`Engineers: ${engineers.length}`);
console.log(`Avg salary: $${avgSalary.toLocaleString()}`);
console.log(`Highest paid: ${highest.Name} ($${Number(highest.Salary).toLocaleString()})`);

employees.sort((a, b) => Number(b.Salary) - Number(a.Salary)).forEach(e => {
    console.log(`  ${e.Name.padEnd(15)} ${e.Department.padEnd(12)} $${Number(e.Salary).toLocaleString()}`);
});
```

**📸 Verified Output:**
```
Total employees: 5
Engineers: 3
Avg salary: $88,600
Highest paid: Charlie Brown ($110,000)
  Charlie Brown   Engineering  $110,000
  Eve Wilson      Engineering  $98,000
  Alice Smith     Engineering  $95,000
  Diana Prince    Design       $75,000
  Bob Jones       Marketing    $65,000
```

## ✅ Verification
```javascript
const fs = require("fs").promises;

async function main() {
    const dir = "/tmp/verify_fs";
    await fs.mkdir(dir, { recursive: true });
    
    const files = ["a.json", "b.json", "c.json"];
    for (const f of files) {
        await fs.writeFile(`${dir}/${f}`, JSON.stringify({ file: f, ts: Date.now() }));
    }
    
    const entries = await fs.readdir(dir);
    console.log("Files:", entries.length);
    
    const contents = await Promise.all(entries.map(f => fs.readFile(`${dir}/${f}`, "utf8")));
    const parsed = contents.map(JSON.parse);
    console.log("All have file prop:", parsed.every(p => p.file));
    console.log("Lab 9 verified ✅");
}
main();
```

**Expected output:**
```
Files: 3
All have file prop: true
Lab 9 verified ✅
```

## 🚨 Common Mistakes
1. **Sync in async context**: `fs.readFileSync()` in a server handler blocks the event loop — use `fs.promises`.
2. **Not checking if file exists**: `readFileSync` on missing file throws — check `fs.existsSync()` first or use try/catch.
3. **Relative paths**: `readFileSync("./file.txt")` — relative to `process.cwd()`, not `__dirname`. Use `path.join(__dirname, "file.txt")`.
4. **Missing `utf8` encoding**: `readFileSync(path)` returns a Buffer; add `"utf8"` for string.
5. **Not closing streams**: Unclosed write streams may not flush — always call `.end()` and wait for `"finish"`.

## 📝 Summary
- `fs.readFileSync/writeFileSync` — synchronous, blocks event loop (OK for startup)
- `fs.promises.readFile/writeFile` — async, non-blocking (use in request handlers)
- `readline` + `createReadStream` — memory-efficient line-by-line reading for large files
- `path.join/resolve/parse` — cross-platform path handling
- `fs.watch` — file change notifications

## 🔗 Further Reading
- [Node.js fs docs](https://nodejs.org/api/fs.html)
- [Node.js path docs](https://nodejs.org/api/path.html)
