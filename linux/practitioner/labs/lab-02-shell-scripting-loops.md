# Lab 02: Shell Scripting — Loops

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Loops are the engine of automation. In this lab you'll master every major loop type in Bash: `for` loops over lists, ranges, globs, and arrays; `while` and `until` loops; flow control with `break` and `continue`; reading files line-by-line; and nesting loops for matrix operations.

---

## Step 1: for Loop — Iterating a List

The simplest loop: iterate over a space-separated list of values.

```bash
for fruit in apple banana cherry; do
  echo "Fruit: $fruit"
done
```

📸 **Verified Output:**
```
Fruit: apple
Fruit: banana
Fruit: cherry
```

> 💡 **Tip:** The list items can be any whitespace-separated values. If items contain spaces, quote them individually: `for item in "two words" "another item"`.

---

## Step 2: for Loop — Numeric Range with Brace Expansion

Use `{start..end}` to generate a numeric sequence without external tools:

```bash
for i in {1..5}; do
  echo "Count: $i"
done
```

📸 **Verified Output:**
```
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
```

> 💡 **Tip:** You can also use a step: `{1..10..2}` produces `1 3 5 7 9`. For dynamic ranges (variables), use `seq`: `for i in $(seq 1 $max)`.

---

## Step 3: for Loop — Glob Pattern (Files)

Loops over matching filenames — essential for batch file processing:

```bash
mkdir -p /tmp/testdir
touch /tmp/testdir/file1.txt /tmp/testdir/file2.txt /tmp/testdir/notes.txt

for f in /tmp/testdir/*.txt; do
  echo "File: $(basename $f)"
done
```

📸 **Verified Output:**
```
File: file1.txt
File: file2.txt
File: notes.txt
```

> 💡 **Tip:** Always check that the glob matched something. If no files match, `$f` will literally be `/tmp/testdir/*.txt`. Guard with: `shopt -s nullglob` so the loop body is skipped when there are no matches.

---

## Step 4: for Loop — Array Iteration

Arrays let you store structured lists and iterate cleanly:

```bash
colors=("red" "green" "blue")
for color in "${colors[@]}"; do
  echo "Color: $color"
done
```

📸 **Verified Output:**
```
Color: red
Color: green
Color: blue
```

> 💡 **Tip:** Always use `"${array[@]}"` (double-quoted, `@` not `*`) to iterate arrays safely. Using `*` joins all elements into one string; `@` preserves element boundaries even when elements contain spaces.

---

## Step 5: while Loop

Runs while a condition is true — ideal when the iteration count isn't known in advance:

```bash
count=1
while [ $count -le 5 ]; do
  echo "While: $count"
  ((count++))
done
```

📸 **Verified Output:**
```
While: 1
While: 2
While: 3
While: 4
While: 5
```

> 💡 **Tip:** `((count++))` is shorthand for `count=$((count + 1))`. The `(( ))` form also returns exit status 1 when the result is 0 — be careful with `set -e` (covered in Lab 04).

---

## Step 6: until Loop

Runs until a condition becomes true — the logical inverse of `while`:

```bash
n=1
until [ $n -gt 3 ]; do
  echo "Until: $n"
  ((n++))
done
```

📸 **Verified Output:**
```
Until: 1
Until: 2
Until: 3
```

> 💡 **Tip:** `until [ cond ]` is equivalent to `while [ ! cond ]`. Use whichever reads more naturally. `until` is less common but can make polling logic read cleanly: `until server_is_ready; do sleep 1; done`.

---

## Step 7: break and continue

`break` exits the loop immediately; `continue` skips to the next iteration:

```bash
for i in {1..10}; do
  [ $i -eq 4 ] && { echo "Skipping 4"; continue; }
  [ $i -eq 7 ] && { echo "Breaking at 7"; break; }
  echo "i=$i"
done
```

📸 **Verified Output:**
```
i=1
i=2
i=3
Skipping 4
i=5
i=6
Breaking at 7
```

> 💡 **Tip:** In nested loops, `break 2` exits two levels at once and `continue 2` continues the outer loop. This is cleaner than setting a flag variable.

---

## Step 8: Capstone — Nested Loops and Reading Files

Combine reading a file line-by-line, nested loops, and break/continue in a realistic report generator:

```bash
# Setup: create sample data
printf "alice:admin\nbob:user\ncharlie:user\n" > /tmp/users.txt

declare -A PERMS
PERMS[admin]="read write execute"
PERMS[user]="read write"

echo "=== Permission Report ==="
while IFS=: read -r user role; do
  echo ""
  echo "User: $user  Role: $role"
  perms=${PERMS[$role]:-none}
  for perm in $perms; do
    echo "  - $perm"
  done
done < /tmp/users.txt
echo ""
echo "=== End Report ==="
```

📸 **Verified Output:**
```
=== Permission Report ===

User: alice  Role: admin
  - read
  - write
  - execute

User: bob  Role: user
  - read
  - write

User: charlie  Role: user
  - read
  - write

=== End Report ===
```

> 💡 **Tip:** `IFS=:` before `read -r user role` splits each line on `:` — a powerful pattern for parsing colon-separated files like `/etc/passwd`. Always use `-r` with `read` to prevent backslash interpretation.

---

## Summary

| Loop Type | Syntax | Best Used For |
|---|---|---|
| `for` over list | `for x in a b c; do ... done` | Known set of values |
| `for` over range | `for i in {1..10}; do ... done` | Numeric sequences |
| `for` over glob | `for f in *.txt; do ... done` | Batch file processing |
| `for` over array | `for x in "${arr[@]}"; do ... done` | Structured data sets |
| `while` | `while [ cond ]; do ... done` | Unknown iteration count |
| `until` | `until [ cond ]; do ... done` | Poll until success |
| `break` | `break` / `break N` | Exit 1 or N loop levels |
| `continue` | `continue` / `continue N` | Skip to next iteration |
| Read file lines | `while IFS= read -r line; do ... done < file` | Line-by-line file parsing |
| Nested loops | `for i in ...; do for j in ...; done; done` | Matrix / cross-product ops |
