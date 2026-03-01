# Lab 10: Script Arguments and getopts

## 🎯 Objective
Process command-line arguments in bash scripts using positional parameters (`$1`, `$@`), `shift`, and `getopts` for professional option parsing.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Labs 7–9
- Basic bash scripting knowledge

## 🔬 Lab Instructions

### Step 1: Positional Parameters
```bash
cat > /tmp/args_demo.sh << 'EOF'
#!/bin/bash
echo "Script name: $0"
echo "First arg:   $1"
echo "Second arg:  $2"
echo "Third arg:   $3"
echo "All args:    $@"
echo "Arg count:   $#"
EOF
chmod +x /tmp/args_demo.sh

bash /tmp/args_demo.sh hello world linux
```

### Step 2: $@ vs $*
```bash
cat > /tmp/at_vs_star.sh << 'EOF'
#!/bin/bash
echo "Using \$@:"
for arg in "$@"; do
  echo "  [$arg]"
done

echo "Using \$*:"
for arg in "$*"; do
  echo "  [$arg]"
done
EOF

bash /tmp/at_vs_star.sh "arg one" "arg two" "arg three"
# $@: each arg is separate even with spaces
# $*: all args joined into one string
```

### Step 3: Validate Argument Count
```bash
cat > /tmp/require_args.sh << 'EOF'
#!/bin/bash
if [ $# -ne 2 ]; then
  echo "Usage: $0 <source> <destination>"
  echo "Example: $0 /home/user /backup"
  exit 1
fi
echo "Copying from $1 to $2"
EOF

bash /tmp/require_args.sh
# Output: Usage error

bash /tmp/require_args.sh /home /backup
# Output: Copying...
```

### Step 4: The shift Command
```bash
cat > /tmp/shift_demo.sh << 'EOF'
#!/bin/bash
echo "Before shift: $@"
shift
echo "After shift 1: $@"
shift 2
echo "After shift 3: $@"
EOF

bash /tmp/shift_demo.sh a b c d e
```

### Step 5: Parse Flags with shift
```bash
cat > /tmp/parse_flags.sh << 'EOF'
#!/bin/bash
verbose=false
output=""

while [ $# -gt 0 ]; do
  case "$1" in
    -v|--verbose)
      verbose=true
      shift
      ;;
    -o|--output)
      output="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [-v] [-o output_file] [args...]"
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

echo "Verbose: $verbose"
echo "Output: ${output:-stdout}"
echo "Remaining args: $@"
EOF
chmod +x /tmp/parse_flags.sh

bash /tmp/parse_flags.sh -v -o result.txt file1 file2
```

### Step 6: getopts for Standard Option Parsing
```bash
cat > /tmp/getopts_demo.sh << 'EOF'
#!/bin/bash
# getopts handles short options (-x, -v, -o value)
usage() {
  echo "Usage: $0 [-h] [-v] [-n name] [-c count]"
  exit 0
}

name="World"
count=1
verbose=false

while getopts "hvn:c:" opt; do
  case $opt in
    h) usage ;;
    v) verbose=true ;;
    n) name="$OPTARG" ;;
    c) count="$OPTARG" ;;
    ?) echo "Invalid option: -$OPTARG"; exit 1 ;;
  esac
done

# Shift past the options
shift $((OPTIND - 1))

$verbose && echo "Verbose mode enabled"
for ((i=1; i<=count; i++)); do
  echo "Hello, $name! (iteration $i)"
done
echo "Remaining positional args: $@"
EOF
chmod +x /tmp/getopts_demo.sh

bash /tmp/getopts_demo.sh -v -n Alice -c 3 extra_arg
```

### Step 7: getopts Syntax Explained
```bash
# getopts "hvn:c:" opt
# h, v = flags (no argument)
# n:   = option requires an argument (the colon)
# c:   = option requires an argument
# $OPTARG = the argument to the current option
# $OPTIND = index of next argument to process
```

### Step 8: Handling Missing Required Arguments
```bash
cat > /tmp/validated.sh << 'EOF'
#!/bin/bash
source_dir=""
dest_dir=""

while getopts "s:d:h" opt; do
  case $opt in
    s) source_dir="$OPTARG" ;;
    d) dest_dir="$OPTARG" ;;
    h) echo "Usage: $0 -s <source> -d <dest>"; exit 0 ;;
  esac
done

# Validate required arguments
[ -z "$source_dir" ] && { echo "ERROR: -s source required"; exit 1; }
[ -z "$dest_dir" ]   && { echo "ERROR: -d destination required"; exit 1; }
[ ! -d "$source_dir" ] && { echo "ERROR: $source_dir not a directory"; exit 1; }

echo "Syncing $source_dir to $dest_dir"
EOF

bash /tmp/validated.sh
# Output: ERROR: -s source required

bash /tmp/validated.sh -s /etc -d /tmp/backup_test
# Output: Syncing /etc to /tmp/backup_test
```

### Step 9: Read from Pipe or File Argument
```bash
cat > /tmp/flexible_input.sh << 'EOF'
#!/bin/bash
# Accept input from file argument or stdin
if [ $# -gt 0 ]; then
  input_source="$1"
  [ -f "$input_source" ] || { echo "File not found: $input_source"; exit 1; }
else
  input_source="/dev/stdin"
fi

while IFS= read -r line; do
  echo "Processing: $line"
done < "$input_source"
EOF

echo -e "line1\nline2\nline3" | bash /tmp/flexible_input.sh
# Reads from stdin

echo -e "a\nb\nc" > /tmp/test_input.txt
bash /tmp/flexible_input.sh /tmp/test_input.txt
# Reads from file
```

### Step 10: Environment Variable Defaults
```bash
cat > /tmp/env_defaults.sh << 'EOF'
#!/bin/bash
# Allow env vars to set defaults, overridden by CLI args
LOG_LEVEL=${LOG_LEVEL:-INFO}
CONFIG_FILE=${CONFIG_FILE:-/etc/myapp.conf}

while getopts "l:c:" opt; do
  case $opt in
    l) LOG_LEVEL="$OPTARG" ;;
    c) CONFIG_FILE="$OPTARG" ;;
  esac
done

echo "Log level: $LOG_LEVEL"
echo "Config: $CONFIG_FILE"
EOF

LOG_LEVEL=DEBUG bash /tmp/env_defaults.sh
bash /tmp/env_defaults.sh -l WARN -c /tmp/myconf
```

### Step 11: Argument Validation Patterns
```bash
cat > /tmp/arg_validate.sh << 'EOF'
#!/bin/bash
validate_port() {
  local port=$1
  if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
    echo "Invalid port: $port" >&2
    return 1
  fi
}

PORT=${1:-8080}
validate_port "$PORT" || exit 1
echo "Using port: $PORT"
EOF

bash /tmp/arg_validate.sh 8080  # Valid
bash /tmp/arg_validate.sh 99999 # Invalid
bash /tmp/arg_validate.sh abc   # Invalid
```

### Step 12: Clean Up
```bash
rm -f /tmp/args_demo.sh /tmp/at_vs_star.sh /tmp/require_args.sh
rm -f /tmp/shift_demo.sh /tmp/parse_flags.sh /tmp/getopts_demo.sh
rm -f /tmp/validated.sh /tmp/flexible_input.sh /tmp/env_defaults.sh
rm -f /tmp/arg_validate.sh /tmp/test_input.txt
```

## ✅ Verification
```bash
cat > /tmp/final_test.sh << 'EOF'
#!/bin/bash
while getopts "n:v" opt; do
  case $opt in
    n) NAME="$OPTARG" ;;
    v) VERBOSE=true ;;
  esac
done
echo "Name: ${NAME:-unknown}"
${VERBOSE:-false} && echo "Verbose is ON"
EOF

bash /tmp/final_test.sh -n Alice -v
# Output: Name: Alice
# Output: Verbose is ON
rm /tmp/final_test.sh
```

## 📝 Summary
- `$1`, `$2`... are positional parameters; `$@` is all args; `$#` is the count
- `"$@"` preserves spacing in each argument; `"$*"` joins all args into one string
- `shift N` discards the first N positional parameters
- `getopts "n:v"` parses short options; `:` after letter means it takes an argument
- `$OPTARG` holds the option's argument; `$OPTIND` tracks parsing position
- Always validate required arguments and provide a `usage()` function with `-h`

