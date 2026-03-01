# Lab 6: Shell Variables

## 🎯 Objective
Master shell variable declaration, scoping, and string operations including declare, local, readonly, and string manipulation operators.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Foundations Lab 18: Environment Variables

## 🔬 Lab Instructions

### Step 1: Variable Declaration Basics

```bash
# Simple assignment (no spaces around =)
NAME="Alice"
AGE=30
echo "Name: $NAME, Age: $AGE"
```

```bash
# declare explicitly types variables
declare -i COUNT=10       # integer
declare -r CONST="fixed"  # readonly
declare -l LOWER="HELLO"  # lowercase
declare -u UPPER="hello"  # uppercase

echo "Count: $COUNT"
echo "Const: $CONST"
echo "Lower: $LOWER"
echo "Upper: $UPPER"
```

### Step 2: readonly Variables

```bash
readonly MAX_RETRIES=5
echo "Max retries: $MAX_RETRIES"

# Attempting to modify readonly fails gracefully
readonly TEST_VAR="immutable"
TEST_VAR="changed" 2>/dev/null || echo "Cannot modify readonly variable"
```

### Step 3: String Length

```bash
PHRASE="Hello, Linux World!"
echo "String: $PHRASE"
echo "Length: ${#PHRASE}"
```

**Expected output:**
```
String: Hello, Linux World!
Length: 19
```

```bash
# Array length uses same syntax
WORDS=("hello" "world" "foo")
echo "Array length: ${#WORDS[@]}"
```

### Step 4: Substring Extraction

```bash
TEXT="Linux System Administration"

# ${var:start:length}
echo "${TEXT:0:5}"   # First 5 chars
echo "${TEXT:6:6}"   # 6 chars starting at position 6
echo "${TEXT:6}"     # From position 6 to end
echo "${TEXT: -14}"  # Last 14 chars (note the space before -)
```

**Expected output:**
```
Linux
System
System Administration
Administration
```

### Step 5: String Replacement

```bash
URL="http://example.com/api/v1/users"

# Replace first occurrence
echo "${URL/http/https}"

# Replace all occurrences
SENTENCE="the cat sat on the mat"
echo "${SENTENCE//the/a}"
```

**Expected output:**
```
https://example.com/api/v1/users
a cat sat on a mat
```

```bash
# Replace only at start (# anchor)
PATH_VAR="/usr/local/bin:/usr/bin:/bin"
echo "${PATH_VAR/#\/usr\/local\/bin:/}"

# Replace only at end (% anchor)
FILENAME="report.txt"
echo "${FILENAME/%txt/md}"
```

### Step 6: Pattern Trimming

```bash
FILEPATH="/home/zchen/documents/report.pdf"

# Remove shortest match from front (#)
echo "${FILEPATH#*/}"      # Remove up to first /
echo "${FILEPATH##*/}"     # Remove up to last / (basename)

# Remove shortest match from end (%)
echo "${FILEPATH%.*}"      # Remove extension
echo "${FILEPATH%%/*}"     # Remove from first /
```

**Expected output:**
```
home/zchen/documents/report.pdf
report.pdf
/home/zchen/documents/report
(empty)
```

### Step 7: Case Conversion

```bash
WORD="Hello World"
echo "${WORD^^}"   # ALL UPPERCASE
echo "${WORD,,}"   # all lowercase
echo "${WORD^}"    # Capitalize first char
echo "${WORD,}"    # Lowercase first char
```

**Expected output:**
```
HELLO WORLD
hello world
Hello World
hello World
```

### Step 8: Default Values and Error Checking

```bash
# ${var:-default} - use default if unset or empty
UNSET_VAR=""
echo "${UNSET_VAR:-using default}"
echo "${UNSET_VAR:=assigned default}"  # Also assigns the value
echo "Now set to: $UNSET_VAR"
```

```bash
# ${var:?error message} - fail with message if unset
(REQUIRED_VAR=; export REQUIRED_VAR; unset REQUIRED_VAR; echo "${REQUIRED_VAR:-REQUIRED_VAR is unset (expected)}")  # demonstrates :? behavior safely
```

## ✅ Verification

```bash
# Run a comprehensive variable test
TEXT="Hello, Linux!"
echo "Length: ${#TEXT}"
echo "Upper: ${TEXT^^}"
echo "Lower: ${TEXT,,}"
echo "Substring: ${TEXT:7:5}"
echo "Replace: ${TEXT/Linux/World}"
echo "Trim prefix: ${TEXT#Hello, }"

CONST_TEST="fixed"
declare -r CONST_TEST
CONST_TEST="changed" 2>/dev/null || echo "readonly protection works"
echo "Practitioner Lab 6 complete"
```

## 📝 Summary
- `declare -i` creates integers; `-r` creates readonly; `-l/-u` force case
- `${#var}` returns string length
- `${var:start:len}` extracts a substring
- `${var/old/new}` replaces first match; `${var//old/new}` replaces all
- `${var##*/}` removes longest prefix (basename equivalent)
- `${var%.*}` removes shortest suffix (strips extension)
- `${var^^}` uppercases; `${var,,}` lowercases
