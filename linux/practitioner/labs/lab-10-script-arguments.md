# Lab 10: Script Arguments

## 🎯 Objective
Handle command-line arguments in scripts using $0, $1, $@, $#, shift, and getopts for option parsing.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Lab 9: Functions

## 🔬 Lab Instructions

### Step 1: Special Variables for Arguments

```bash
cat > /tmp/show-args.sh << 'EOF'
#!/bin/bash
echo "Script name: $0"
echo "First arg:   $1"
echo "Second arg:  $2"
echo "All args:    $@"
echo "Arg count:   $#"
echo "Last exit:   $?"
echo "Script PID:  $$"
EOF

bash /tmp/show-args.sh alpha beta gamma
```

**Expected output:**
```
Script name: /tmp/show-args.sh
First arg:   alpha
Second arg:  beta
All args:    alpha beta gamma
Arg count:   3
Last exit:   0
Script PID:  12345
```

### Step 2: Difference Between $@ and $*

```bash
cat > /tmp/at-vs-star.sh << 'EOF'
#!/bin/bash
echo "=== Using \$@ (preserves args) ==="
for arg in "$@"; do
    echo "  arg: [$arg]"
done

echo "=== Using \$* (merges args) ==="
for arg in "$*"; do
    echo "  arg: [$arg]"
done
EOF

bash /tmp/at-vs-star.sh "hello world" "foo" "bar baz"
```

**Expected output:**
```
=== Using $@ (preserves args) ===
  arg: [hello world]
  arg: [foo]
  arg: [bar baz]
=== Using $* (merges args) ===
  arg: [hello world foo bar baz]
```

### Step 3: Using shift to Process Arguments

```bash
cat > /tmp/shift-demo.sh << 'EOF'
#!/bin/bash
echo "Original args: $@"
echo "Count: $#"

shift       # Remove first argument
echo "After first shift: $@"

shift 2     # Remove next 2 arguments
echo "After shift 2: $@"
EOF

bash /tmp/shift-demo.sh one two three four five
```

**Expected output:**
```
Original args: one two three four five
Count: 5
After first shift: two three four five
After shift 2: four five
```

```bash
# Practical: process all args with shift
cat > /tmp/process-all.sh << 'EOF'
#!/bin/bash
while [[ $# -gt 0 ]]; do
    echo "Processing: $1"
    shift
done
EOF

bash /tmp/process-all.sh apple banana cherry
```

### Step 4: Validate Arguments

```bash
cat > /tmp/validate-args.sh << 'EOF'
#!/bin/bash
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <name> <age>"
    echo "Error: Need at least 2 arguments, got $#"
    exit 1
fi

NAME="$1"
AGE="$2"

if [[ ! "$AGE" =~ ^[0-9]+$ ]]; then
    echo "Error: Age must be a number, got: $AGE"
    exit 2
fi

echo "Name: $NAME, Age: $AGE"
EOF

bash /tmp/validate-args.sh Alice 30
bash /tmp/validate-args.sh Alice 2>/dev/null || echo "Exit code: $?"
```

### Step 5: getopts for Flag Parsing

```bash
cat > /tmp/getopts-demo.sh << 'EOF'
#!/bin/bash
VERBOSE=false
OUTPUT_FILE=""
NAME="default"

while getopts "vf:n:" opt; do
    case $opt in
        v)
            VERBOSE=true
            ;;
        f)
            OUTPUT_FILE="$OPTARG"
            ;;
        n)
            NAME="$OPTARG"
            ;;
        ?)
            echo "Usage: $0 [-v] [-f file] [-n name]"
            exit 1
            ;;
    esac
done

echo "Verbose: $VERBOSE"
echo "Output:  ${OUTPUT_FILE:-none}"
echo "Name:    $NAME"
EOF

bash /tmp/getopts-demo.sh -v -n "Alice" -f /tmp/output.txt
```

**Expected output:**
```
Verbose: true
Output:  /tmp/output.txt
Name:    Alice
```

```bash
# Test with just -v
bash /tmp/getopts-demo.sh -v
```

### Step 6: Handle Remaining Args After getopts

```bash
cat > /tmp/getopts-remaining.sh << 'EOF'
#!/bin/bash
VERBOSE=false

while getopts "v" opt; do
    case $opt in
        v) VERBOSE=true ;;
    esac
done

# Shift past the processed options
shift $((OPTIND-1))

echo "Verbose: $VERBOSE"
echo "Remaining args: $@"
for item in "$@"; do
    echo "  Processing: $item"
done
EOF

bash /tmp/getopts-remaining.sh -v file1.txt file2.txt file3.txt
```

## ✅ Verification

```bash
cat > /tmp/lab10-verify.sh << 'EOF'
#!/bin/bash
[[ $# -eq 3 ]] && echo "PASS: 3 args received" || echo "FAIL: expected 3 args"
[[ "$1" == "hello" ]] && echo "PASS: first arg correct" || echo "FAIL: first arg wrong"
[[ "$2" == "world" ]] && echo "PASS: second arg correct" || echo "FAIL"
echo "All args: $@"
EOF

bash /tmp/lab10-verify.sh hello world 42
rm /tmp/show-args.sh /tmp/at-vs-star.sh /tmp/shift-demo.sh /tmp/process-all.sh /tmp/validate-args.sh /tmp/getopts-demo.sh /tmp/getopts-remaining.sh /tmp/lab10-verify.sh 2>/dev/null
echo "Practitioner Lab 10 complete"
```

## 📝 Summary
- `$0` = script name, `$1`/`$2` = positional params, `$@` = all args, `$#` = count
- `"$@"` preserves each argument as separate word; `"$*"` merges into one string
- `shift N` removes N arguments from the front of the list
- `getopts "vf:n:" opt` parses flags; `:` after letter means it takes an argument
- `$OPTARG` holds the value for options that take arguments
- After getopts, `shift $((OPTIND-1))` removes processed flags leaving remaining args
