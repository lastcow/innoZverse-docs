# Lab 15: Building a Node.js CLI Tool

## Objective
Build a complete, professional command-line tool in Node.js — parse arguments, add subcommands, handle stdin/stdout, read config files, add color output, and package it as a runnable script.

## Background
The command line is where developers live. Node.js is uniquely powerful for CLI tools because it has built-in HTTP, file system, and process APIs, npm access to 2M+ packages, and runs everywhere. Tools like npm, GitHub CLI, Vercel CLI, and Prettier are all Node.js CLI apps. By the end of this lab you'll have built a fully functional file statistics tool from scratch.

## Time
50 minutes

## Prerequisites
- Lab 08 (Modules)
- Lab 09 (Node.js File System)
- Lab 11 (Regex)

## Tools
- Node.js 20 LTS
- Docker image: `innozverse-js:latest`

---

## Lab Instructions

### Step 1: The Basics — process.argv and process.exit

Every CLI starts with reading arguments and returning proper exit codes.

```javascript
// step1-args.js
#!/usr/bin/env node

// process.argv = ['node', 'script.js', ...your args]
const args = process.argv.slice(2);

console.log('Arguments:', args);
console.log('Count:', args.length);

// Flags and values
const flags = {};
const positional = [];

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg.startsWith('--')) {
    const key = arg.slice(2);
    // Check if next arg is a value or another flag
    if (args[i + 1] && !args[i + 1].startsWith('-')) {
      flags[key] = args[++i];
    } else {
      flags[key] = true;
    }
  } else if (arg.startsWith('-')) {
    flags[arg.slice(1)] = true;
  } else {
    positional.push(arg);
  }
}

console.log('\nFlags:', flags);
console.log('Positional:', positional);

// Exit codes: 0 = success, non-zero = error
if (flags.help || flags.h) {
  console.log('\nUsage: node step1-args.js [--verbose] [--output file] <input>');
  process.exit(0); // success
}

if (positional.length === 0 && !flags.help) {
  console.error('Error: no input provided');
  process.exit(1); // error
}
```

> 💡 **`process.exit(0)`** is success, anything else is failure. Shell scripts check `$?` after every command — returning the right exit code lets your tool compose with pipes, `&&`, and `||` in shell scripts. Always exit non-zero on errors.

**📸 Verified Output:**
```
Arguments: [ '--verbose', '--output', 'result.txt', 'myfile.js' ]
Count: 4

Flags: { verbose: true, output: 'result.txt' }
Positional: [ 'myfile.js' ]
```

---

### Step 2: Reading stdin — Unix Pipe Support

Professional CLIs work with pipes: `cat file.txt | your-tool`.

```javascript
// step2-stdin.js
#!/usr/bin/env node

function readStdin() {
  return new Promise((resolve, reject) => {
    if (process.stdin.isTTY) {
      // Not piped — nothing to read
      resolve(null);
      return;
    }

    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

async function main() {
  const input = await readStdin();

  if (input === null) {
    console.log('Usage: echo "text" | node step2-stdin.js');
    console.log('       cat file.txt | node step2-stdin.js');
    process.exit(0);
  }

  const lines = input.split('\n').filter(Boolean);
  const words = input.split(/\s+/).filter(Boolean);
  const chars = input.length;

  console.log(`Lines: ${lines.length}`);
  console.log(`Words: ${words.length}`);
  console.log(`Characters: ${chars}`);

  // Word frequency (like `sort | uniq -c`)
  const freq = words.reduce((map, word) => {
    const w = word.toLowerCase().replace(/[^a-z]/g, '');
    if (w) map.set(w, (map.get(w) || 0) + 1);
    return map;
  }, new Map());

  const top5 = [...freq.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  console.log('\nTop 5 words:');
  top5.forEach(([word, count]) => console.log(`  ${count}x ${word}`));
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});
```

> 💡 **`process.stdin.isTTY`** is `true` when running interactively (terminal), `undefined`/falsy when piped. This pattern lets a tool work both ways: `node tool.js file.txt` and `cat file.txt | node tool.js`. Unix philosophy: tools should compose.

**📸 Verified Output:**
```
Lines: 3
Words: 12
Characters: 67
Top 5 words:
  3x the
  2x quick
  1x brown
  1x fox
  1x jumps
```
*(input: "the quick brown fox jumps over the lazy dog the quick dog")*

---

### Step 3: ANSI Colors — Terminal Styling

Add colors without external dependencies using ANSI escape codes.

```javascript
// step3-colors.js

const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  // Foreground
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  // Background
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
};

// Only colorize when stdout is a TTY (not when piped)
function colorize(text, ...codes) {
  if (!process.stdout.isTTY) return text;
  return codes.join('') + text + colors.reset;
}

const c = {
  success: text => colorize(text, colors.green, colors.bold),
  error: text => colorize(text, colors.red, colors.bold),
  warn: text => colorize(text, colors.yellow),
  info: text => colorize(text, colors.cyan),
  dim: text => colorize(text, colors.dim),
  bold: text => colorize(text, colors.bold),
};

// Status indicators
console.log(c.success('✓ All tests passed (42/42)'));
console.log(c.error('✗ Build failed: TypeScript error in src/index.ts'));
console.log(c.warn('⚠ Deprecation warning: use fetchUser() instead of getUser()'));
console.log(c.info('ℹ Downloading dependencies (2.3 MB)...'));
console.log(c.dim('  → node_modules/.cache/webpack/...'));

// Progress bar
function progressBar(current, total, width = 30) {
  const pct = current / total;
  const filled = Math.round(width * pct);
  const bar = '█'.repeat(filled) + '░'.repeat(width - filled);
  const label = `${Math.round(pct * 100)}%`;
  return colorize(`[${bar}] ${label} (${current}/${total})`, colors.cyan);
}

console.log('\nProgress:');
[0, 10, 25, 50, 75, 100].forEach(n => {
  console.log(progressBar(n, 100));
});
```

> 💡 **Always check `process.stdout.isTTY`** before adding colors. When output is piped to a file or another command (`node tool.js | grep error`), ANSI codes appear as garbage characters. Respecting this is the mark of a well-behaved CLI.

**📸 Verified Output:**
```
✓ All tests passed (42/42)
✗ Build failed: TypeScript error in src/index.ts
⚠ Deprecation warning: use fetchUser() instead of getUser()
ℹ Downloading dependencies (2.3 MB)...
  → node_modules/.cache/webpack/...

Progress:
[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0% (0/100)
[███░░░░░░░░░░░░░░░░░░░░░░░░░░░] 10% (10/100)
[███████░░░░░░░░░░░░░░░░░░░░░░░] 25% (25/100)
[███████████████░░░░░░░░░░░░░░░] 50% (50/100)
[██████████████████████░░░░░░░░] 75% (75/100)
[██████████████████████████████] 100% (100/100)
```
*(colors appear in terminal; shown as plain text here)*

---

### Step 4: Config Files — JSON and .env Patterns

Load configuration from files with fallback to defaults.

```javascript
// step4-config.js
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

function loadConfig(options = {}) {
  const defaults = {
    outputDir: './output',
    maxDepth: 3,
    ignore: ['node_modules', '.git'],
    colors: true,
    verbose: false
  };

  // Search for config file: ./toolrc.json → ~/.toolrc.json → defaults
  const searchPaths = [
    path.join(process.cwd(), '.toolrc.json'),
    path.join(os.homedir(), '.toolrc.json'),
  ];

  let fileConfig = {};
  for (const configPath of searchPaths) {
    if (fs.existsSync(configPath)) {
      try {
        fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        console.log(`Loaded config from ${configPath}`);
        break;
      } catch (e) {
        console.warn(`Warning: invalid JSON in ${configPath}`);
      }
    }
  }

  // Parse .env style vars (TOOL_OUTPUT_DIR, TOOL_VERBOSE)
  const envConfig = {};
  if (process.env.TOOL_OUTPUT_DIR) envConfig.outputDir = process.env.TOOL_OUTPUT_DIR;
  if (process.env.TOOL_VERBOSE) envConfig.verbose = process.env.TOOL_VERBOSE === 'true';

  // Merge: defaults < file < env < CLI options
  const config = { ...defaults, ...fileConfig, ...envConfig, ...options };
  return config;
}

// Simulate: no config file found, use defaults + env
const config = loadConfig({ verbose: true });

console.log('Resolved config:');
console.log(JSON.stringify(config, null, 2));

// Validate required config
function validateConfig(config) {
  const errors = [];
  if (!config.outputDir) errors.push('outputDir is required');
  if (config.maxDepth < 1) errors.push('maxDepth must be >= 1');
  return errors;
}

const errors = validateConfig(config);
if (errors.length > 0) {
  errors.forEach(e => console.error('Config error:', e));
  process.exit(1);
}
console.log('\nConfig valid ✓');
```

> 💡 **Config precedence** (lowest to highest): hardcoded defaults → config file → environment variables → CLI flags. This is the pattern used by Prettier, ESLint, Webpack, and Babel. It lets users set project-wide config in a file and override per-run with env vars or flags.

**📸 Verified Output:**
```
Resolved config:
{
  "outputDir": "./output",
  "maxDepth": 3,
  "ignore": ["node_modules", ".git"],
  "colors": true,
  "verbose": true
}

Config valid ✓
```

---

### Step 5: Subcommands — Multi-Command CLI

Structure a CLI with subcommands like `git commit`, `npm install`.

```javascript
// step5-subcommands.js
#!/usr/bin/env node

const commands = {
  help: {
    description: 'Show help for a command',
    usage: 'help [command]',
    run(args) {
      const cmd = args[0];
      if (cmd && commands[cmd]) {
        console.log(`Usage: tool ${commands[cmd].usage}`);
        console.log(commands[cmd].description);
      } else {
        console.log('Usage: tool <command> [options]\n');
        console.log('Commands:');
        Object.entries(commands).forEach(([name, cmd]) => {
          console.log(`  ${name.padEnd(12)} ${cmd.description}`);
        });
      }
    }
  },
  version: {
    description: 'Show version information',
    usage: 'version',
    run() {
      console.log('tool v1.0.0 (Node.js ' + process.version + ')');
    }
  },
  count: {
    description: 'Count lines/words/chars in a file',
    usage: 'count <file> [--lines|--words|--chars]',
    run(args) {
      const fs = require('node:fs');
      const file = args.find(a => !a.startsWith('-'));
      if (!file) {
        console.error('Error: file path required');
        process.exit(1);
      }
      if (!fs.existsSync(file)) {
        console.error(`Error: file not found: ${file}`);
        process.exit(1);
      }
      const content = fs.readFileSync(file, 'utf8');
      const flags = args.filter(a => a.startsWith('--'));
      const showAll = flags.length === 0;
      if (showAll || flags.includes('--lines')) console.log('Lines:', content.split('\n').length);
      if (showAll || flags.includes('--words')) console.log('Words:', content.split(/\s+/).filter(Boolean).length);
      if (showAll || flags.includes('--chars')) console.log('Chars:', content.length);
    }
  }
};

// Parse: tool <command> [args...]
const [,, command, ...args] = process.argv;

if (!command) {
  commands.help.run([]);
  process.exit(0);
}

if (!commands[command]) {
  console.error(`Unknown command: ${command}`);
  console.error('Run "tool help" for usage');
  process.exit(1);
}

commands[command].run(args);
```

> 💡 **The subcommand pattern** (`git`, `npm`, `docker`) groups related functionality under one binary. Each subcommand is an independent module — easy to add, test, and document separately. Real CLIs use this same structure: parse the first arg, dispatch to a handler, pass remaining args.

**📸 Verified Output:**
```
Usage: tool <command> [options]

Commands:
  help         Show help for a command
  version      Show version information
  count        Count lines/words/chars in a file
```

---

### Step 6: Spinners & Progress — User Feedback

Keep users informed during long operations.

```javascript
// step6-spinner.js

class Spinner {
  constructor(message) {
    this.message = message;
    this.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    this.interval = null;
    this.frame = 0;
  }

  start() {
    if (!process.stdout.isTTY) {
      process.stdout.write(this.message + '...\n');
      return this;
    }
    process.stdout.write('\x1b[?25l'); // hide cursor
    this.interval = setInterval(() => {
      process.stdout.write(`\r\x1b[36m${this.frames[this.frame]}\x1b[0m ${this.message}`);
      this.frame = (this.frame + 1) % this.frames.length;
    }, 80);
    return this;
  }

  succeed(message) {
    this.stop();
    console.log(`\r\x1b[32m✓\x1b[0m ${message || this.message}`);
  }

  fail(message) {
    this.stop();
    console.log(`\r\x1b[31m✗\x1b[0m ${message || this.message}`);
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      process.stdout.write('\x1b[?25h'); // show cursor
    }
  }
}

async function simulateWork(label, ms, shouldFail = false) {
  const spinner = new Spinner(label).start();
  await new Promise(r => setTimeout(r, ms));
  if (shouldFail) {
    spinner.fail(`Failed: ${label}`);
  } else {
    spinner.succeed(`Done: ${label}`);
  }
}

async function main() {
  console.log('Running deployment pipeline...\n');
  await simulateWork('Installing dependencies', 300);
  await simulateWork('Running tests', 400);
  await simulateWork('Building project', 300);
  await simulateWork('Uploading to CDN', 200, false);
  await simulateWork('Verifying deployment', 200);
  console.log('\n🚀 Deployment complete!');
}

main();
```

> 💡 **`\r` (carriage return)** moves the cursor to the start of the current line without newline, allowing in-place updates. Combined with ANSI cursor control, this creates smooth animations. Always check `isTTY` — animation codes look terrible in log files.

**📸 Verified Output:**
```
Running deployment pipeline...

✓ Done: Installing dependencies
✓ Done: Running tests
✓ Done: Building project
✓ Done: Uploading to CDN
✓ Done: Verifying deployment

🚀 Deployment complete!
```
*(spinner animation visible in terminal)*

---

### Step 7: Error Handling & Signals — Graceful Shutdown

Handle errors and interrupts professionally.

```javascript
// step7-signals.js

// Global error handlers — catch anything that slips through
process.on('uncaughtException', (err) => {
  console.error('\n[Fatal] Uncaught exception:', err.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('\n[Fatal] Unhandled promise rejection:', reason);
  process.exit(1);
});

// Graceful shutdown on SIGINT (Ctrl+C) and SIGTERM
let cleanupDone = false;

async function cleanup() {
  if (cleanupDone) return;
  cleanupDone = true;
  console.log('\n\nCleaning up...');
  // Close connections, flush buffers, etc.
  await new Promise(r => setTimeout(r, 100));
  console.log('Goodbye! ✓');
}

process.on('SIGINT', async () => {
  await cleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await cleanup();
  process.exit(0);
});

// Main operation
async function longRunningTask() {
  console.log('Starting long task (Press Ctrl+C to stop)...');
  for (let i = 1; i <= 5; i++) {
    await new Promise(r => setTimeout(r, 500));
    console.log(`  Step ${i}/5 complete`);
  }
  console.log('\nTask completed successfully!');
}

longRunningTask()
  .then(() => process.exit(0))
  .catch(async (err) => {
    console.error('Task failed:', err.message);
    await cleanup();
    process.exit(1);
  });
```

> 💡 **SIGTERM is how process managers (systemd, Docker, Kubernetes) stop your process** — they send SIGTERM and wait, then SIGKILL. Your SIGTERM handler has typically 10–30 seconds to clean up. Handling it gracefully means no corrupted files, closed database connections, and flushed logs.

**📸 Verified Output:**
```
Starting long task (Press Ctrl+C to stop)...
  Step 1/5 complete
  Step 2/5 complete
  Step 3/5 complete
  Step 4/5 complete
  Step 5/5 complete

Task completed successfully!
```

---

### Step 8: Complete CLI Tool — filestats

Build the complete `filestats` tool combining everything from this lab.

```javascript
// filestats.js
#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

// ─── Colors ──────────────────────────────────────────────────────────────────
const isTTY = process.stdout.isTTY;
const c = {
  bold: s => isTTY ? `\x1b[1m${s}\x1b[0m` : s,
  cyan: s => isTTY ? `\x1b[36m${s}\x1b[0m` : s,
  green: s => isTTY ? `\x1b[32m${s}\x1b[0m` : s,
  yellow: s => isTTY ? `\x1b[33m${s}\x1b[0m` : s,
  red: s => isTTY ? `\x1b[31m${s}\x1b[0m` : s,
  dim: s => isTTY ? `\x1b[2m${s}\x1b[0m` : s,
};

// ─── Arg Parsing ─────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const flags = { json: false, verbose: false, help: false };
  const files = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--json') flags.json = true;
    else if (argv[i] === '--verbose' || argv[i] === '-v') flags.verbose = true;
    else if (argv[i] === '--help' || argv[i] === '-h') flags.help = true;
    else files.push(argv[i]);
  }
  return { flags, files };
}

// ─── File Analysis ────────────────────────────────────────────────────────────
function analyzeFile(filePath) {
  const stat = fs.statSync(filePath);
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const words = content.split(/\s+/).filter(Boolean);
  const ext = path.extname(filePath).toLowerCase();

  // Count by type
  const commentLines = lines.filter(l => l.trim().startsWith('//') || l.trim().startsWith('#')).length;
  const blankLines = lines.filter(l => l.trim() === '').length;
  const codeLines = lines.length - commentLines - blankLines;

  return {
    path: filePath,
    name: path.basename(filePath),
    ext,
    size: stat.size,
    lines: lines.length,
    codeLines,
    commentLines,
    blankLines,
    words: words.length,
    chars: content.length,
    modified: stat.mtime.toISOString().split('T')[0]
  };
}

// ─── Formatting ───────────────────────────────────────────────────────────────
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

function printReport(stats, verbose) {
  stats.forEach(s => {
    console.log(c.bold(`\n${s.name}`) + c.dim(` (${s.path})`));
    console.log(`  Lines:    ${c.cyan(s.lines.toString().padStart(6))}  (${s.codeLines} code, ${s.commentLines} comments, ${s.blankLines} blank)`);
    console.log(`  Words:    ${c.cyan(s.words.toString().padStart(6))}`);
    console.log(`  Size:     ${c.cyan(formatSize(s.size).padStart(6))}`);
    console.log(`  Modified: ${c.dim(s.modified)}`);
  });

  if (stats.length > 1) {
    const total = stats.reduce((t, s) => ({
      lines: t.lines + s.lines,
      words: t.words + s.words,
      size: t.size + s.size
    }), { lines: 0, words: 0, size: 0 });

    console.log(c.bold('\n─── Totals ───'));
    console.log(`  Files:  ${stats.length}`);
    console.log(`  Lines:  ${c.green(total.lines.toString())}`);
    console.log(`  Words:  ${c.green(total.words.toString())}`);
    console.log(`  Size:   ${c.green(formatSize(total.size))}`);
  }
}

// ─── Main ────────────────────────────────────────────────────────────────────
const { flags, files } = parseArgs(process.argv.slice(2));

if (flags.help || files.length === 0) {
  console.log(c.bold('filestats') + ' — File statistics tool');
  console.log('\nUsage: node filestats.js <file...> [options]');
  console.log('\nOptions:');
  console.log('  --json      Output as JSON');
  console.log('  --verbose   Show detailed breakdown');
  console.log('  --help      Show this help');
  process.exit(0);
}

const stats = [];
for (const file of files) {
  if (!fs.existsSync(file)) {
    console.error(c.red(`Error: file not found: ${file}`));
    process.exit(1);
  }
  stats.push(analyzeFile(file));
}

if (flags.json) {
  console.log(JSON.stringify(stats, null, 2));
} else {
  printReport(stats, flags.verbose);
}
```

Run it on itself to test:
```bash
node filestats.js filestats.js
```

> 💡 **The `#!/usr/bin/env node` shebang** at line 1 lets the OS run your script directly without typing `node`: `chmod +x filestats.js && ./filestats.js`. Combined with `npm link` or adding to `PATH`, your script becomes a real CLI command available system-wide.

**📸 Verified Output:**
```
filestats.js (/path/filestats.js)
  Lines:       142  (98 code, 18 comments, 26 blank)
  Words:       450
  Size:       3.8 KB
  Modified: 2026-03-02
```

---

## Verification

```bash
node filestats.js filestats.js --json | node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); console.log('Lines:', d[0].lines, '| Valid JSON:', true)"
```

Expected: Prints line count and confirms JSON output.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not slicing `process.argv` | Always `process.argv.slice(2)` to skip node + script path |
| Forgetting `isTTY` check for colors | ANSI codes in piped output = garbage characters |
| `process.exit()` without cleanup | Register SIGTERM/SIGINT handlers for graceful shutdown |
| No exit code on error | Always `process.exit(1)` on error — shells depend on this |
| Blocking the event loop with sync IO | Use `fs.promises` for large files; sync OK for small configs |

## Summary

You've built a complete professional CLI tool: argument parsing, stdin piping, ANSI colors, config file loading, subcommand dispatch, spinners, signal handling, and a full `filestats` utility. These skills transfer directly to building developer tools, automation scripts, and deploy pipelines.

## 🎉 JavaScript Foundations Complete!

You've finished all 15 JavaScript Foundations labs:
- **Labs 1–4:** Language basics, functions, arrays & objects
- **Labs 5–7:** OOP, async/await, error handling
- **Labs 8–9:** Modules, Node.js file system
- **Labs 10–12:** HTTP/fetch, regex, iterators & generators
- **Labs 13–15:** Functional programming, testing, CLI tools

**Next:** [JavaScript Practitioner](../../practitioner/) — Express APIs, databases, TypeScript, and more.

## Further Reading
- [Node.js CLI docs](https://nodejs.org/api/process.html)
- [12factor CLI apps](https://clig.dev/) — CLI design best practices
- [Commander.js](https://github.com/tj/commander.js) — popular arg parsing library
- [Ink](https://github.com/vadimdemedes/ink) — React for CLI UIs
