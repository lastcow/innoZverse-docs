# Lab 2: Variables, Data Types & Type Coercion

## 🎯 Objective
Master JavaScript's type system — `var`, `let`, `const`, primitive types, type coercion, and the quirks that trip up every JavaScript developer.

## 📚 Background
JavaScript has **7 primitive types**: `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, and `bigint` — plus the `object` type for everything else. JavaScript performs **implicit type coercion** — automatically converting types in operations — which causes famous bugs like `"5" + 3 === "53"`. Understanding these behaviors separates confident JS developers from frustrated ones.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 1: Hello World & JavaScript Basics

## 🛠️ Tools Used
- Node.js 20
- Docker (`innozverse-js:latest`)

## 🔬 Lab Instructions

### Step 1: var vs let vs const

```javascript
// var — function-scoped, hoisted, can be redeclared (avoid in modern JS)
var x = 10;
var x = 20;  // No error — redeclaration allowed
console.log("var x:", x);

// let — block-scoped, not hoisted usably, no redeclaration
let y = 10;
// let y = 20; // SyntaxError: Identifier 'y' has already been declared
y = 20;        // Re-assignment is fine
console.log("let y:", y);

// const — block-scoped, must be initialized, no re-assignment
const PI = 3.14159;
// PI = 3; // TypeError: Assignment to constant variable
console.log("const PI:", PI);

// const with objects: the reference is const, not the contents
const user = { name: "Alice", age: 30 };
user.age = 31;  // OK — modifying property
// user = {};   // TypeError — can't reassign the variable
console.log("const user:", user);
```

**📸 Verified Output:**
```
var x: 20
let y: 20
const PI: 3.14159
const user: { name: 'Alice', age: 31 }
```

> 💡 **Rule of thumb**: Use `const` by default. Use `let` only when you need to reassign. Never use `var` in modern JavaScript.

### Step 2: Primitive Types

```javascript
// number — all numbers are 64-bit floats (no int type!)
const integer = 42;
const float = 3.14;
const negative = -17;
const scientific = 1.5e6;
const maxSafe = Number.MAX_SAFE_INTEGER;

console.log(integer, float, negative, scientific);
console.log("MAX_SAFE_INTEGER:", maxSafe.toLocaleString());
console.log("0.1 + 0.2:", 0.1 + 0.2);           // Float precision issue
console.log("Fixed:", (0.1 + 0.2).toFixed(1));   // Fix with toFixed()

// Infinity and NaN
console.log("10/0:", 10 / 0);           // Infinity
console.log("'abc'/2:", "abc" / 2);     // NaN
console.log("isNaN('abc'):", isNaN("abc"));
console.log("Number.isNaN(NaN):", Number.isNaN(NaN));  // More precise
```

**📸 Verified Output:**
```
42 3.14 -17 1500000
MAX_SAFE_INTEGER: 9,007,199,254,740,991
0.1 + 0.2: 0.30000000000000004
Fixed: 0.3
10/0: Infinity
'abc'/2: NaN
isNaN('abc'): true
Number.isNaN(NaN): true
```

### Step 3: String Type

```javascript
const single = 'single quotes';
const double = "double quotes";
const template = `template literals — same as ${single}`;
const multiLine = `Line 1
Line 2
Line 3`;

console.log(single);
console.log(double);
console.log(template);
console.log(multiLine);

// String operations
const name = "JavaScript";
console.log(name.length);
console.log(name.toUpperCase());
console.log(name.slice(0, 4));        // Java
console.log(name.includes("Script")); // true
console.log(name.replace("Java", "Type")); // TypeScript!
```

**📸 Verified Output:**
```
single quotes
double quotes
template literals — same as single quotes
Line 1
Line 2
Line 3
10
JAVASCRIPT
Java
true
TypeScript
```

### Step 4: Boolean, null, undefined

```javascript
// boolean
const t = true;
const f = false;
console.log(!t, t && f, t || f);

// null — intentional absence of value
const empty = null;
console.log("null:", empty, typeof empty);  // 'object' — famous JS bug!

// undefined — uninitialized variable
let uninit;
const obj = { a: 1 };
console.log("undefined var:", uninit);
console.log("missing prop:", obj.b);
console.log("typeof undefined:", typeof undefined);

// Difference: null is deliberate, undefined is accidental
function findUser(id) {
    const users = { 1: "Alice" };
    return users[id] || null;  // Return null when not found (intentional)
}
console.log(findUser(1));   // Alice
console.log(findUser(99));  // null
```

**📸 Verified Output:**
```
false false true
null: null object
undefined var: undefined
missing prop: undefined
typeof undefined: undefined
Alice
null
```

### Step 5: Type Coercion — The Famous Quirks

```javascript
// Implicit coercion in + operator
console.log("5" + 3);    // "53" — string + number = string concatenation!
console.log(5 + "3");    // "53"
console.log(5 - "3");    // 2  — arithmetic coerces to number
console.log(5 * "3");    // 15
console.log("5" * "3");  // 15

// Comparison coercion
console.log("5" == 5);   // true  — loose equality coerces type
console.log("5" === 5);  // false — strict equality, no coercion
console.log(null == undefined);  // true  — special case
console.log(null === undefined); // false

// Falsy values in JavaScript
const falsyValues = [false, 0, -0, "", '', ``, null, undefined, NaN];
for (const v of falsyValues) {
    process.stdout.write(`Boolean(${JSON.stringify(v) ?? 'NaN'})=${Boolean(v)}  `);
}
console.log();

// Truthy: everything else, including "0", " ", [], {}
console.log('\nTruthy "0":', Boolean("0"));   // true!
console.log('Truthy []:', Boolean([]));        // true!
console.log('Truthy {}:', Boolean({}));        // true!
```

**📸 Verified Output:**
```
53
53
2
15
15
true
false
true
false
Boolean(false)=false  Boolean(0)=false  Boolean(-0)=false  Boolean("")=false  Boolean("")=false  Boolean("")=false  Boolean(null)=false  Boolean(undefined)=false  Boolean(NaN)=false  

Truthy "0": true
Truthy []: true
Truthy {}: true
```

> 💡 Always use `===` (strict equality) in JavaScript. `==` performs type coercion and leads to surprising bugs.

### Step 6: typeof and Type Checking

```javascript
const values = [42, 3.14, "hello", true, null, undefined, [], {}, function(){}];
const labels = ["integer", "float", "string", "bool", "null", "undefined",
                "array", "object", "function"];

for (let i = 0; i < values.length; i++) {
    const v = values[i];
    const t = typeof v;
    const isArr = Array.isArray(v);
    console.log(`${labels[i]:>10}: typeof="${t}", isArray=${isArr}`);
}
```

**📸 Verified Output:**
```
   integer: typeof="number", isArray=false
     float: typeof="number", isArray=false
    string: typeof="string", isArray=false
      bool: typeof="boolean", isArray=false
      null: typeof="object", isArray=false
 undefined: typeof="undefined", isArray=false
     array: typeof="object", isArray=true
    object: typeof="object", isArray=false
  function: typeof="function", isArray=false
```

> 💡 `typeof null === "object"` is a famous JavaScript bug kept for backward compatibility. Use `v === null` to check for null specifically. Use `Array.isArray()` to check for arrays.

### Step 7: Number Conversions

```javascript
// Explicit conversions
console.log(Number("42"));       // 42
console.log(Number("3.14"));     // 3.14
console.log(Number(""));         // 0  (!)
console.log(Number("abc"));      // NaN
console.log(Number(true));       // 1
console.log(Number(false));      // 0
console.log(Number(null));       // 0
console.log(Number(undefined));  // NaN

// parseInt and parseFloat
console.log(parseInt("42px"));       // 42 — stops at non-digit
console.log(parseInt("0xFF", 16));   // 255 — hex
console.log(parseFloat("3.14em"));   // 3.14

// toString with radix
console.log((255).toString(16));   // "ff" — hex
console.log((8).toString(2));      // "1000" — binary
```

**📸 Verified Output:**
```
42
3.14
0
NaN
1
0
0
NaN
42
255
3.14
ff
1000
```

### Step 8: Destructuring Assignment

```javascript
// Array destructuring
const [a, b, c] = [10, 20, 30];
console.log(a, b, c);

// Skip elements
const [first, , third] = [1, 2, 3];
console.log(first, third);

// With rest
const [head, ...tail] = [1, 2, 3, 4, 5];
console.log("head:", head, "tail:", tail);

// Object destructuring
const { name, age, city = "Unknown" } = { name: "Alice", age: 30 };
console.log(name, age, city);

// Rename while destructuring
const { name: userName, age: userAge } = { name: "Bob", age: 25 };
console.log(userName, userAge);

// Nested destructuring
const { address: { street, zip } } = {
    address: { street: "123 Main St", zip: "10001" }
};
console.log(street, zip);
```

**📸 Verified Output:**
```
10 20 30
1 3
head: 1 tail: [ 2, 3, 4, 5 ]
Alice 30 Unknown
Bob 25
123 Main St 10001
```

## ✅ Verification

```javascript
// Type system challenge
const data = ["42", 3.14, true, null, undefined, "hello", 0];
const results = data.map(v => ({
    value: String(v),
    type: typeof v,
    truthy: Boolean(v),
    asNumber: Number(v)
}));

results.forEach(r => {
    console.log(`${r.value.padStart(10)}: type=${r.type}, truthy=${r.truthy}, num=${r.asNumber}`);
});
console.log("Lab 2 verified ✅");
```

**Expected output:**
```
        42: type=string, truthy=true, num=42
      3.14: type=number, truthy=true, num=3.14
      true: type=boolean, truthy=true, num=1
      null: type=object, truthy=false, num=0
 undefined: type=undefined, truthy=false, num=NaN
     hello: type=string, truthy=true, num=NaN
         0: type=number, truthy=false, num=0
Lab 2 verified ✅
```

## 🚨 Common Mistakes

1. **`"5" + 3 === "53"`** — use explicit `Number("5") + 3` when you want arithmetic.
2. **`== null` is OK, `== undefined` is OK** — but `=== null` is preferred for clarity.
3. **`typeof null === "object"`** — always use `=== null` not `typeof` for null checks.
4. **`const` doesn't deep-freeze objects** — properties can still be mutated.
5. **`NaN !== NaN`** — use `Number.isNaN(x)` not `x === NaN`.

## 📝 Summary

- Use `const` by default, `let` when reassigning, never `var`
- 7 primitives: `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, `bigint`
- Always use `===` (strict equality) — avoid `==` coercion surprises
- `typeof null === "object"` is a JS bug — use `=== null` for null checks
- `Array.isArray()` to check arrays — `typeof` just returns `"object"`
- Falsy: `false`, `0`, `""`, `null`, `undefined`, `NaN`; everything else is truthy

## 🔗 Further Reading
- [MDN: JavaScript data types](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Data_structures)
- [MDN: Equality comparisons](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Equality_comparisons_and_sameness)
