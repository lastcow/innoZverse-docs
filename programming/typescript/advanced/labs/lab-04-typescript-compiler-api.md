# Lab 04: TypeScript Compiler API & AST

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Use the TypeScript Compiler API to parse, analyze, and transform TypeScript source code programmatically. Then simplify with ts-morph.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript
mkdir lab04 && cd lab04
npm init -y
npm install typescript ts-morph
```

> 💡 We use `node` (not ts-node) here since the Compiler API is a JS library. ts-morph wraps it for a friendlier API.

---

## Step 2: Creating a TypeScript Program

The `ts.createProgram` function is the entry point to TypeScript's compiler:

```javascript
// explore-ast.js
const ts = require('typescript');
const fs = require('fs');

// Write a sample TS file to analyze
const sampleCode = `
function greet(name: string): string {
  return "Hello, " + name;
}

async function fetchUser(id: number): Promise<string> {
  return "user-" + id;
}

const arrowFn = (x: number, y: number): number => x + y;

class UserService {
  constructor(private name: string) {}
  getUser(): string { return this.name; }
}
`;

fs.writeFileSync('sample.ts', sampleCode);

// Create compiler host and program
const program = ts.createProgram(['sample.ts'], {
  target: ts.ScriptTarget.ES2020,
  module: ts.ModuleKind.CommonJS,
  strict: true,
});

const sourceFile = program.getSourceFile('sample.ts');
console.log('Source file:', sourceFile?.fileName);
console.log('Language version:', sourceFile?.languageVersion);
console.log('Statements count:', sourceFile?.statements.length);
```

Run:
```bash
node explore-ast.js
```

---

## Step 3: Understanding SyntaxKind

`ts.SyntaxKind` is an enum with 350+ values identifying every AST node type:

```javascript
// syntax-kinds.js
const ts = require('typescript');

// Key SyntaxKind values
const kinds = {
  FunctionDeclaration: ts.SyntaxKind.FunctionDeclaration,
  ClassDeclaration: ts.SyntaxKind.ClassDeclaration,
  MethodDeclaration: ts.SyntaxKind.MethodDeclaration,
  ArrowFunction: ts.SyntaxKind.ArrowFunction,
  Parameter: ts.SyntaxKind.Parameter,
  Identifier: ts.SyntaxKind.Identifier,
  StringKeyword: ts.SyntaxKind.StringKeyword,
  NumberKeyword: ts.SyntaxKind.NumberKeyword,
};

console.log('SyntaxKind values:');
Object.entries(kinds).forEach(([name, val]) => {
  console.log(`  ${name}: ${val}`);
});
```

> 💡 You can check a node's kind with `node.kind === ts.SyntaxKind.FunctionDeclaration` or use TypeScript's type guard helpers like `ts.isFunctionDeclaration(node)`.

---

## Step 4: AST Traversal with forEachChild

Traverse every node in the AST:

```javascript
// traverse.js
const ts = require('typescript');
const fs = require('fs');

const code = fs.readFileSync('sample.ts', 'utf-8');
const sourceFile = ts.createSourceFile(
  'sample.ts',
  code,
  ts.ScriptTarget.ES2020,
  true // setParentNodes
);

function printNodeTree(node, indent = 0) {
  const kindName = ts.SyntaxKind[node.kind];
  const text = node.getText(sourceFile).substring(0, 30).replace(/\n/g, '↵');
  console.log(' '.repeat(indent * 2) + `[${kindName}] "${text}"`);
  ts.forEachChild(node, child => printNodeTree(child, indent + 1));
}

// Only print top-level statements to avoid huge output
sourceFile.statements.forEach(stmt => {
  console.log('\n--- Statement ---');
  printNodeTree(stmt, 0);
});
```

---

## Step 5: Finding All Function Declarations

A practical use case — extract all function signatures:

```javascript
// find-functions.js
const ts = require('typescript');
const fs = require('fs');

const code = fs.readFileSync('sample.ts', 'utf-8');
const sourceFile = ts.createSourceFile('sample.ts', code, ts.ScriptTarget.ES2020, true);
const checker = ts.createProgram(['sample.ts'], {}).getTypeChecker();

function findFunctions(node) {
  const results = [];

  function visit(node) {
    // Function declarations
    if (ts.isFunctionDeclaration(node) && node.name) {
      const params = node.parameters.map(p => {
        const name = p.name.getText(sourceFile);
        const type = p.type ? p.type.getText(sourceFile) : 'any';
        return `${name}: ${type}`;
      });
      const returnType = node.type ? node.type.getText(sourceFile) : 'void';
      const isAsync = node.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword);

      results.push({
        name: node.name.getText(sourceFile),
        params,
        returnType,
        isAsync: !!isAsync,
        line: sourceFile.getLineAndCharacterOfPosition(node.pos).line + 1,
      });
    }

    // Method declarations
    if (ts.isMethodDeclaration(node) && node.name) {
      results.push({
        name: node.name.getText(sourceFile),
        type: 'method',
        line: sourceFile.getLineAndCharacterOfPosition(node.pos).line + 1,
      });
    }

    ts.forEachChild(node, visit);
  }

  visit(node);
  return results;
}

const functions = findFunctions(sourceFile);
console.log('Found functions:');
functions.forEach(fn => {
  if (fn.params) {
    const asyncStr = fn.isAsync ? 'async ' : '';
    console.log(`  ${asyncStr}${fn.name}(${fn.params.join(', ')}): ${fn.returnType} [line ${fn.line}]`);
  } else {
    console.log(`  method: ${fn.name} [line ${fn.line}]`);
  }
});
```

---

## Step 6: Type Checking with the Type Checker

Access inferred types programmatically:

```javascript
// type-checker.js
const ts = require('typescript');
const fs = require('fs');

const program = ts.createProgram(['sample.ts'], {
  target: ts.ScriptTarget.ES2020,
  strict: true,
});
const checker = program.getTypeChecker();
const sourceFile = program.getSourceFile('sample.ts');

function inspectTypes(node) {
  if (ts.isVariableDeclaration(node) && node.name) {
    try {
      const type = checker.getTypeAtLocation(node.name);
      const typeStr = checker.typeToString(type);
      const name = node.name.getText(sourceFile);
      console.log(`  Variable '${name}': ${typeStr}`);
    } catch {}
  }

  if (ts.isFunctionDeclaration(node) && node.name) {
    const signature = checker.getSignatureFromDeclaration(node);
    if (signature) {
      const returnType = checker.typeToString(
        checker.getReturnTypeOfSignature(signature)
      );
      console.log(`  Function '${node.name.text}' returns: ${returnType}`);
    }
  }

  ts.forEachChild(node, inspectTypes);
}

console.log('Type information:');
inspectTypes(sourceFile);
```

---

## Step 7: Simpler Access with ts-morph

ts-morph wraps the Compiler API with a clean, ergonomic interface:

```javascript
// ts-morph-demo.js
const { Project } = require('ts-morph');
const fs = require('fs');

const project = new Project({
  compilerOptions: { strict: true, target: 99 }, // 99 = ES2022
});

// Add source file in-memory
const sourceFile = project.createSourceFile('analysis.ts', `
function add(x: number, y: number): number { return x + y; }
async function fetchData(url: string): Promise<{ data: string }> {
  return { data: 'result' };
}
class Calculator {
  private history: number[] = [];
  add(a: number, b: number): number {
    const result = a + b;
    this.history.push(result);
    return result;
  }
  getHistory(): number[] { return this.history; }
}
`);

// Get all functions
const functions = sourceFile.getFunctions();
console.log('Functions:');
functions.forEach(fn => {
  const params = fn.getParameters().map(p =>
    `${p.getName()}: ${p.getType().getText()}`
  );
  console.log(`  ${fn.isAsync() ? 'async ' : ''}${fn.getName()}(${params.join(', ')}): ${fn.getReturnType().getText()}`);
});

// Get all classes
const classes = sourceFile.getClasses();
console.log('\nClasses:');
classes.forEach(cls => {
  console.log(`  class ${cls.getName()}`);
  cls.getMethods().forEach(m => {
    console.log(`    method: ${m.getName()}(): ${m.getReturnType().getText()}`);
  });
});

// Diagnostics
const diagnostics = project.getPreEmitDiagnostics();
console.log(`\nDiagnostics: ${diagnostics.length} errors`);
console.log('ts-morph analysis complete!');
```

📸 **Verified Output:**
```
Functions:
  add(x: number, y: number): number
  async fetchData(url: string): Promise<{ data: string; }>
Classes:
  class Calculator
    method: add(): number
    method: getHistory(): number[]

Diagnostics: 0 errors
ts-morph analysis complete!
```

---

## Step 8: Capstone — Code Analysis Tool

Build a complete TypeScript code analyzer:

```javascript
// analyzer.js
const { Project, SyntaxKind } = require('ts-morph');

function analyzeCode(code) {
  const project = new Project({ compilerOptions: { strict: true } });
  const sf = project.createSourceFile('code.ts', code);

  const report = {
    functions: [],
    classes: [],
    interfaces: [],
    typeAliases: [],
    issues: [],
  };

  // Functions
  sf.getFunctions().forEach(fn => {
    const name = fn.getName() || '(anonymous)';
    const params = fn.getParameters().length;
    const hasReturn = fn.getReturnType().getText() !== 'void';
    report.functions.push({ name, params, hasReturn, async: fn.isAsync() });

    // Check for missing return type annotation
    if (!fn.getReturnTypeNode()) {
      report.issues.push(`Function '${name}' is missing explicit return type`);
    }
  });

  // Classes
  sf.getClasses().forEach(cls => {
    report.classes.push({
      name: cls.getName(),
      methods: cls.getMethods().length,
      properties: cls.getProperties().length,
    });
  });

  // Interfaces
  sf.getInterfaces().forEach(iface => {
    report.interfaces.push({
      name: iface.getName(),
      members: iface.getMembers().length,
    });
  });

  // Type aliases
  sf.getTypeAliases().forEach(alias => {
    report.typeAliases.push(alias.getName());
  });

  return report;
}

const code = `
interface User { id: number; name: string; email: string }
type Status = 'active' | 'inactive' | 'pending';

function createUser(name: string, email: string): User {
  return { id: Math.random(), name, email };
}

// Missing return type - will be flagged
function processUser(user: User) {
  console.log(user.name);
}

class UserRepository {
  private users: User[] = [];
  add(user: User): void { this.users.push(user); }
  findById(id: number): User | undefined {
    return this.users.find(u => u.id === id);
  }
  getAll(): User[] { return [...this.users]; }
}
`;

const report = analyzeCode(code);
console.log('=== Code Analysis Report ===');
console.log(`Functions: ${report.functions.length}`);
report.functions.forEach(f => console.log(`  - ${f.name}(${f.params} params)`));
console.log(`Classes: ${report.classes.length}`);
report.classes.forEach(c => console.log(`  - ${c.name} (${c.methods} methods)`));
console.log(`Interfaces: ${report.interfaces.length}`);
console.log(`Type Aliases: ${report.typeAliases.join(', ')}`);
console.log(`Issues found: ${report.issues.length}`);
report.issues.forEach(i => console.log(`  ⚠ ${i}`));
console.log('✅ Lab 04 complete');
```

Run:
```bash
node analyzer.js
```

---

## Summary

| Concept | API | Use Case |
|---|---|---|
| Parse source | `ts.createProgram` / `ts.createSourceFile` | Load TS files |
| Traverse AST | `ts.forEachChild(node, visitor)` | Walk all nodes |
| Identify nodes | `ts.SyntaxKind` enum / type guards | `isFunctionDeclaration(n)` |
| Type information | `program.getTypeChecker()` | Get inferred types |
| High-level API | `ts-morph` Project/SourceFile | Ergonomic analysis |
| Diagnostics | `project.getPreEmitDiagnostics()` | Find type errors |
