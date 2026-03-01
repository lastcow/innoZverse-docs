# Lab 13: String Manipulation

## 🎯 Objective
Master bash string manipulation: case conversion, substring extraction, prefix/suffix removal, and string replacement.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Lab 6: Shell Variables

## 🔬 Lab Instructions

### Step 1: String Length

```bash
GREETING="Hello, Linux World!"
echo "String: $GREETING"
echo "Length: ${#GREETING}"
```

**Expected output:**
```
String: Hello, Linux World!
Length: 19
```

```bash
EMPTY=""
echo "Empty string length: ${#EMPTY}"
```

### Step 2: Case Conversion

```bash
TEXT="Hello World"

echo "${TEXT^^}"   # ALL UPPERCASE
echo "${TEXT,,}"   # all lowercase
echo "${TEXT^}"    # Capitalize first character
echo "${TEXT,}"    # Lowercase first character
```

**Expected output:**
```
HELLO WORLD
hello world
Hello World
hello World
```

```bash
# Practical: normalize input
INPUT="  ALICE  "
NORMALIZED="${INPUT,,}"
echo "Normalized: $NORMALIZED"

# Convert filename to lowercase
FILENAME="Report_2026_Q1.CSV"
echo "${FILENAME,,}"
```

### Step 3: Substring Extraction

```bash
PATH_STR="/home/zchen/documents/report-2026.pdf"

# ${var:start:length} — start is 0-indexed
echo "${PATH_STR:0:5}"      # First 5 chars
echo "${PATH_STR:6:5}"      # 5 chars from position 6
echo "${PATH_STR:6}"        # From position 6 to end
echo "${PATH_STR: -3}"      # Last 3 chars (space before -)
```

**Expected output:**
```
/home
zchen
zchen/documents/report-2026.pdf
pdf
```

### Step 4: Prefix Removal (# and ##)

```bash
PATH_STR="/home/zchen/documents/report.pdf"

# Remove shortest matching prefix (#)
echo "${PATH_STR#/}"         # Remove leading /
echo "${PATH_STR#*/}"        # Remove up to first /

# Remove longest matching prefix (##)
echo "${PATH_STR##*/}"       # Remove up to last / (basename!)
```

**Expected output:**
```
home/zchen/documents/report.pdf
home/zchen/documents/report.pdf
report.pdf
```

```bash
# Practical basename equivalent
FILE="/var/log/syslog.1"
echo "Basename: ${FILE##*/}"
```

### Step 5: Suffix Removal (% and %%)

```bash
PATH_STR="/home/zchen/documents/report.pdf"

# Remove shortest matching suffix (%)
echo "${PATH_STR%.*}"        # Remove extension
echo "${PATH_STR%/*}"        # Remove last path component (dirname!)

# Remove longest matching suffix (%%)
echo "${PATH_STR%%.*}"       # Remove everything after first dot
```

**Expected output:**
```
/home/zchen/documents/report
/home/zchen/documents
/home/zchen/documents/report
```

```bash
# Practical examples
VERSIONED="myapp-v1.2.3.tar.gz"
echo "Without .gz:    ${VERSIONED%.gz}"
echo "Without .tar.gz: ${VERSIONED%.tar.gz}"
echo "Without version: ${VERSIONED%-v*}"
```

### Step 6: String Replacement

```bash
SENTENCE="the quick brown fox jumps over the lazy dog"

# Replace first occurrence
echo "${SENTENCE/the/a}"

# Replace ALL occurrences (//)
echo "${SENTENCE//the/a}"

# Replace only at start (match anchored to beginning)
URL="http://example.com/api"
echo "${URL/#http/https}"

# Replace only at end (match anchored to end)
FILE="config.txt"
echo "${FILE/%txt/yaml}"
```

### Step 7: Practical String Processing

```bash
# Extract date components from a filename
REPORT="sales-report-2026-03-01.csv"
DATE_PART="${REPORT%.csv}"
DATE_PART="${DATE_PART##*-report-}"
echo "Date: $DATE_PART"
YEAR="${DATE_PART%%-*}"
echo "Year: $YEAR"
```

```bash
# Process a list of paths
PATHS="/etc/nginx/nginx.conf:/etc/apache2/apache2.conf:/etc/ssh/sshd_config"

# Extract config filenames only
IFS=: read -ra PATH_ARRAY <<< "$PATHS"
for p in "${PATH_ARRAY[@]}"; do
    echo "Config file: ${p##*/}"
done
```

**Expected output:**
```
Config file: nginx.conf
Config file: apache2.conf
Config file: sshd_config
```

### Step 8: String Testing

```bash
EMAIL="user@example.com"

# Check if string contains @
if [[ "$EMAIL" == *@* ]]; then
    echo "Valid email format (contains @)"
fi

# Check prefix
URL="https://secure.site.com"
if [[ "$URL" == https://* ]]; then
    echo "Secure URL"
fi

# Check suffix
SCRIPT="deploy.sh"
if [[ "$SCRIPT" == *.sh ]]; then
    echo "Is a shell script"
fi
```

## ✅ Verification

```bash
TEXT="Hello World 2026"

echo "Length: ${#TEXT}"
echo "Upper: ${TEXT^^}"
echo "Lower: ${TEXT,,}"
echo "Substr: ${TEXT:6:5}"
echo "Replace: ${TEXT/World/Linux}"
echo "Suffix rm: ${TEXT% *}"

FILE="backup-2026-03-01.tar.gz"
echo "Basename would be: ${FILE##*/}"
echo "No extension: ${FILE%.gz}"
echo "No .tar.gz: ${FILE%.tar.gz}"
echo "Practitioner Lab 13 complete"
```

## 📝 Summary
- `${#var}` returns string length
- `${var^^}` uppercases; `${var,,}` lowercases
- `${var:start:len}` extracts substring (0-indexed)
- `${var#pattern}` removes shortest prefix; `##` removes longest
- `${var%pattern}` removes shortest suffix; `%%` removes longest
- `${var/old/new}` replaces first match; `//` replaces all
- `${var/#old/new}` replaces at start; `/%old/new` replaces at end
