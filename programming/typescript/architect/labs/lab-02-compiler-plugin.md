# Lab 02: Compiler Plugin Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

TypeScript transformer API: `ts.TransformerFactory`, `ts.visitNode/visitEachChild`, custom transform for auto-injecting logging into function calls, ts-patch for compiler plugins, and ts-morph for large-scale code refactoring pipelines.

---

## Step 1: TypeScript Compiler API Overview

```typescript
// The TypeScript compiler exposes a full AST manipulation API
// Pipeline: Source → Scanner → Parser → AST → Binder → Checker → Emitter

// Key types:
// ts.Node          — base type for all AST nodes
// ts.SourceFile    — root of the AST
// ts.TransformerFactory<T>  — factory returning a transformer
// ts.Transformer<T>         — function: Node → Node
// ts.Visitor               — function: Node → VisitResult

import * as ts from 'typescript';

// Create a minimal transformer factory
const myTransformer: ts.TransformerFactory<ts.SourceFile> = (context) => {
  return (sourceFile) => {
    function visit(node: ts.Node): ts.Node {
      // Transform nodes here
      return ts.visitEachChild(node, visit, context);
    }
    return ts.visitNode(sourceFile, visit) as ts.SourceFile;
  };
};
```

---

## Step 2: Auto-Inject Logging Transformer

```typescript
// transform-logging.ts
import * as ts from 'typescript';

/**
 * Transformer: auto-inject console.log at start of every function body
 * Input:  function add(a: number, b: number) { return a + b; }
 * Output: function add(a: number, b: number) { console.log('[TRACE] Entering add'); return a + b; }
 */
export const loggingTransformer: ts.TransformerFactory<ts.SourceFile> = (context) => {
  return (sourceFile) => {
    function visit(node: ts.Node): ts.Node {
      // Match function declarations
      if (ts.isFunctionDeclaration(node) && node.body && node.name) {
        const functionName = node.name.getText(sourceFile);

        // Create: console.log('[TRACE] Entering functionName');
        const logStatement = ts.factory.createExpressionStatement(
          ts.factory.createCallExpression(
            ts.factory.createPropertyAccessExpression(
              ts.factory.createIdentifier('console'),
              'log'
            ),
            undefined,
            [ts.factory.createStringLiteral(`[TRACE] Entering ${functionName}`)]
          )
        );

        // Prepend to function body
        const newBody = ts.factory.updateBlock(node.body, [
          logStatement,
          ...node.body.statements,
        ]);

        return ts.factory.updateFunctionDeclaration(
          node,
          node.modifiers,
          node.asteriskToken,
          node.name,
          node.typeParameters,
          node.parameters,
          node.type,
          newBody,
        );
      }

      return ts.visitEachChild(node, visit, context);
    }

    return ts.visitNode(sourceFile, visit) as ts.SourceFile;
  };
};
```

---

## Step 3: Run the Transformer

```typescript
// run-transform.ts
import * as ts from 'typescript';
import { loggingTransformer } from './transform-logging';

const sourceCode = `
function add(a: number, b: number): number {
  return a + b;
}

function greet(name: string): string {
  return 'Hello, ' + name;
}
`;

// Parse source
const sourceFile = ts.createSourceFile(
  'input.ts',
  sourceCode,
  ts.ScriptTarget.ES2022,
  true
);

// Apply transformer
const result = ts.transform(sourceFile, [loggingTransformer]);
const transformed = result.transformed[0];

// Emit
const printer = ts.createPrinter({ newLine: ts.NewLineKind.LineFeed });
const output = printer.printFile(transformed);

console.log('=== Transformed Output ===');
console.log(output);
```

---

## Step 4: ts-morph — High-Level AST Manipulation

```typescript
// ts-morph provides a more ergonomic API over the raw compiler API
import { Project, SyntaxKind, FunctionDeclaration } from 'ts-morph';

const project = new Project({ useInMemoryFileSystem: true });
const sourceFile = project.createSourceFile('input.ts', `
function add(a: number, b: number): number { return a + b; }
function greet(name: string): string { return 'Hello, ' + name; }
`);

// Auto-inject logging via ts-morph
sourceFile.getFunctions().forEach((fn: FunctionDeclaration) => {
  const body = fn.getBody();
  if (!body) return;
  const name = fn.getName();
  body.insertStatements(0, `console.log('[TRACE] Entering ${name}');`);
});

console.log('=== ts-morph Transform Output ===');
console.log(sourceFile.getText());
```

---

## Step 5: ts-morph Code Refactoring Pipeline

```typescript
// Large-scale refactoring: migrate all callbacks to async/await
import { Project, CallExpression, Node } from 'ts-morph';

const project = new Project({ tsConfigFilePath: './tsconfig.json' });

// Find all .then() chains
project.getSourceFiles().forEach(file => {
  file.getDescendantsOfKind(SyntaxKind.CallExpression).forEach(call => {
    const expr = call.getExpression();
    if (!Node.isPropertyAccessExpression(expr)) return;
    if (expr.getName() !== 'then') return;

    // Log for manual review (full auto-migration is complex)
    console.log(`Promise.then() at ${file.getFilePath()}:${call.getStartLineNumber()}`);
  });
});

// Find all console.log calls for removal (example)
project.getSourceFiles().forEach(file => {
  const consoleLogs = file
    .getDescendantsOfKind(SyntaxKind.CallExpression)
    .filter(call => {
      const expr = call.getExpression();
      return Node.isPropertyAccessExpression(expr) &&
        expr.getExpression().getText() === 'console' &&
        expr.getName() === 'log';
    });

  if (consoleLogs.length > 0) {
    consoleLogs.forEach(c => c.getParent()?.remove());
    file.save();
    console.log(`Removed ${consoleLogs.length} console.log from ${file.getBaseName()}`);
  }
});
```

---

## Step 6: ts-patch Compiler Plugin

```json
// tsconfig.json with ts-patch plugin
{
  "compilerOptions": {
    "plugins": [
      {
        "transform": "./dist/transform-logging.js",
        "type": "program"
      },
      {
        "transform": "ts-transform-paths",
        "type": "raw"
      }
    ]
  }
}
```

```bash
# Install ts-patch to enable compiler plugins in tsconfig
npm install ts-patch
npx ts-patch install  # Patches TypeScript compiler

# Now 'tsc' runs your plugins automatically
tsc --noEmit  # Type check with plugin
tsc           # Compile with plugin transformations applied
```

---

## Step 7: Custom Lint-Style Transform

```typescript
// Transform as a linter: detect + report issues
const securityAuditTransformer: ts.TransformerFactory<ts.SourceFile> = (context) => {
  return (sourceFile) => {
    const issues: string[] = [];

    function visit(node: ts.Node): ts.Node {
      // Detect: eval() calls
      if (ts.isCallExpression(node)) {
        const expr = node.expression;
        if (ts.isIdentifier(expr) && expr.text === 'eval') {
          const { line } = sourceFile.getLineAndCharacterOfPosition(node.pos);
          issues.push(`eval() at line ${line + 1} — potential XSS`);
        }
      }

      // Detect: document.write()
      if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
        const { expression, name } = node.expression;
        if (ts.isIdentifier(expression) && expression.text === 'document' &&
            ts.isIdentifier(name) && name.text === 'write') {
          const { line } = sourceFile.getLineAndCharacterOfPosition(node.pos);
          issues.push(`document.write() at line ${line + 1} — deprecated + XSS risk`);
        }
      }

      return ts.visitEachChild(node, visit, context);
    }

    const result = ts.visitNode(sourceFile, visit) as ts.SourceFile;
    if (issues.length > 0) {
      console.warn('Security issues found:', issues);
    }
    return result;
  };
};
```

---

## Step 8: Capstone — ts-morph Transformer

```bash
docker run --rm node:20-alpine sh -c "
  cd /work && npm init -y > /dev/null 2>&1
  npm install ts-morph 2>&1 | tail -1
  node transform.js
"
```

*(where transform.js mounts the ts-morph script)*

📸 **Verified Output:**
```
=== ts-morph AST Transform: Auto-inject logging ===
function add(a: number, b: number): number {
    console.log("[TRACE] Entering add"); return a + b; }
function greet(name: string): string {
    console.log("[TRACE] Entering greet"); return "Hello, " + name; }
```

---

## Summary

| Tool | API Level | Use Case |
|------|----------|----------|
| `ts.TransformerFactory` | Raw compiler API | Production transforms |
| `ts.visitNode/visitEachChild` | Raw AST traversal | Fine-grained control |
| ts-morph | High-level wrapper | Codemod scripts |
| ts-patch | Compiler plugin hook | tsconfig.json integration |
| AST Explorer | Debugging | Understand node types |
| tsc --diagnostics | Performance | Find slow type checks |
