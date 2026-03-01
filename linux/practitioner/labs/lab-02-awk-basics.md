# Lab 2: awk Basics

## 🎯 Objective
Use `awk` to extract and process structured text: print specific fields, use NR/NF built-in variables, filter with patterns, and use BEGIN/END blocks.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Completed Foundations Labs 14 and 19
- Basic understanding of fields and columns in text

## 🔬 Lab Instructions

### Step 1: Understanding awk's Structure
awk processes text line by line. Each line is split into fields by a delimiter (default: whitespace).

```bash
# Basic syntax: awk 'pattern { action }' file
echo "hello world" | awk '{ print $1 }'
# Output: hello  ($1 = first field)

echo "hello world" | awk '{ print $2 }'
# Output: world  ($2 = second field)

echo "hello world" | awk '{ print $0 }'
# Output: hello world  ($0 = entire line)
```

### Step 2: Create a Test Dataset
```bash
cat > /tmp/employees.txt << 'EOF'
Alice Engineering 95000 Senior
Bob Marketing 72000 Junior
Carol Engineering 88000 Mid
Dave Sales 65000 Junior
Eve Engineering 110000 Senior
Frank Marketing 80000 Mid
Grace Sales 70000 Senior
EOF
```

### Step 3: Print Specific Fields
```bash
# Print name and salary (fields 1 and 3)
awk '{ print $1, $3 }' /tmp/employees.txt
# Output:
# Alice 95000
# Bob 72000
# ...

# Custom separator between fields
awk '{ print $1 ":" $3 }' /tmp/employees.txt
# Output: Alice:95000

# Print with formatting
awk '{ printf "%-10s %s\n", $1, $3 }' /tmp/employees.txt
```

### Step 4: Use Built-in Variables NR and NF
```bash
# NR = Number of Records (current line number)
awk '{ print NR, $1 }' /tmp/employees.txt
# Output:
# 1 Alice
# 2 Bob
# ...

# NF = Number of Fields (fields in current line)
awk '{ print NF, $0 }' /tmp/employees.txt
# Output: 4 Alice Engineering 95000 Senior

# Print only the last field using NF
awk '{ print $NF }' /tmp/employees.txt
# Output: Senior, Junior, Mid, ...
```

### Step 5: Filter Lines with Patterns
```bash
# Print lines matching a pattern
awk '/Engineering/ { print $1 }' /tmp/employees.txt
# Output: Alice, Carol, Eve

# Numeric comparison
awk '$3 > 85000 { print $1, $3 }' /tmp/employees.txt
# Output: Alice 95000, Carol 88000, Eve 110000

# Multiple conditions
awk '$3 > 80000 && /Senior/ { print $1, $4, $3 }' /tmp/employees.txt
```

### Step 6: Use a Custom Field Separator with `-F`
```bash
# Parse /etc/passwd with : as separator
awk -F: '{ print $1, $7 }' /etc/passwd | head -10
# Prints username and login shell

# Show only users with /bin/bash
awk -F: '$7 == "/bin/bash" { print $1 }' /etc/passwd

# Parse CSV
echo "name,dept,salary" > /tmp/data.csv
echo "Alice,Eng,95000" >> /tmp/data.csv
echo "Bob,Mkt,72000" >> /tmp/data.csv
awk -F, '{ print $1, $3 }' /tmp/data.csv
```

### Step 7: BEGIN and END Blocks
```bash
# BEGIN runs before any lines are processed
# END runs after all lines are processed
awk 'BEGIN { print "--- Employee Report ---" }
     { print $1, $3 }
     END { print "--- End of Report ---" }' /tmp/employees.txt
```

### Step 8: Calculate Totals and Averages
```bash
# Sum salaries
awk '{ total += $3 }
     END { print "Total payroll: $" total }' /tmp/employees.txt

# Average salary
awk '{ total += $3; count++ }
     END { printf "Average salary: $%.0f\n", total/count }' /tmp/employees.txt

# Min and max
awk 'BEGIN { min=999999; max=0 }
     { if($3 > max) max=$3; if($3 < min) min=$3 }
     END { print "Min:", min, "Max:", max }' /tmp/employees.txt
```

### Step 9: Use Variables and Conditionals
```bash
awk '{
  if ($4 == "Senior") level="S"
  else if ($4 == "Mid") level="M"
  else level="J"
  print level, $1, $3
}' /tmp/employees.txt
```

### Step 10: Count Records by Category
```bash
awk '{ dept[$2]++ }
     END {
       for (d in dept)
         print d ":", dept[d], "employees"
     }' /tmp/employees.txt
```

### Step 11: Process System Files
```bash
# Disk usage summary
df -h | awk 'NR > 1 && $5+0 > 50 { print "WARNING:", $6, "is", $5, "full" }'

# Top memory-using processes
ps aux | sort -k4 -rn | awk 'NR <= 5 { printf "%-20s %s%%\n", $11, $4 }'
```

### Step 12: Multi-line awk Script
```bash
awk '
BEGIN {
  FS = " "
  print "Department Summary"
  print "=================="
}
{
  dept[$2] += $3
  count[$2]++
}
END {
  for (d in dept)
    printf "%-15s Total: $%d  Avg: $%d\n", d, dept[d], dept[d]/count[d]
}
' /tmp/employees.txt

# Clean up
rm /tmp/employees.txt /tmp/data.csv
```

## ✅ Verification
```bash
echo -e "a 1\nb 2\nc 3\nd 4\ne 5" > /tmp/awktest.txt

awk '{ sum += $2 } END { print "Sum:", sum }' /tmp/awktest.txt
# Output: Sum: 15

awk '$2 > 3 { print $1 }' /tmp/awktest.txt
# Output: d, e

awk 'BEGIN{print "Start"} {print NR,$0} END{print "End"}' /tmp/awktest.txt

rm /tmp/awktest.txt
```

## 📝 Summary
- awk processes text line by line; `$1`, `$2`... are fields; `$0` is the whole line
- `NR` = current line number; `NF` = number of fields in the line
- `-F` sets field separator; default is whitespace
- `BEGIN { }` runs before input; `END { }` runs after all input is processed
- Arrays (`dept[$2]++`) enable counting and aggregation by category
- awk combines pattern matching with calculation — ideal for structured text processing
