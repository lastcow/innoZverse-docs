# Lab 14: Arrays in bash

## 🎯 Objective
Create and manipulate indexed and associative arrays: add elements, iterate, slice, and use array operations.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Lab 6: Shell Variables

## 🔬 Lab Instructions

### Step 1: Create Indexed Arrays

```bash
# Method 1: Declare with ()
FRUITS=("apple" "banana" "cherry" "date" "elderberry")

# Method 2: Assign element by index
COLORS[0]="red"
COLORS[1]="green"
COLORS[2]="blue"

# Method 3: declare -a
declare -a NUMBERS=(10 20 30 40 50)

echo "First fruit: ${FRUITS[0]}"
echo "Second color: ${COLORS[1]}"
echo "Third number: ${NUMBERS[2]}"
```

**Expected output:**
```
First fruit: apple
Second color: green
Third number: 30
```

### Step 2: Array Length and All Elements

```bash
FRUITS=("apple" "banana" "cherry" "date" "elderberry")

# Number of elements
echo "Count: ${#FRUITS[@]}"

# All elements
echo "All: ${FRUITS[@]}"

# All as quoted list
for f in "${FRUITS[@]}"; do
    echo "  - $f"
done
```

**Expected output:**
```
Count: 5
All: apple banana cherry date elderberry
  - apple
  - banana
  - cherry
  - date
  - elderberry
```

### Step 3: Array Indices

```bash
FRUITS=("apple" "banana" "cherry" "date" "elderberry")

# Get all indices
echo "Indices: ${!FRUITS[@]}"

# Iterate with index
for i in "${!FRUITS[@]}"; do
    echo "  $i: ${FRUITS[$i]}"
done
```

**Expected output:**
```
Indices: 0 1 2 3 4
  0: apple
  1: banana
  2: cherry
  3: date
  4: elderberry
```

### Step 4: Modify Arrays

```bash
FRUITS=("apple" "banana" "cherry")

# Append with +=
FRUITS+=("date")
FRUITS+=("elderberry" "fig")
echo "After append: ${FRUITS[@]}"

# Modify element
FRUITS[1]="blueberry"
echo "After modify: ${FRUITS[@]}"

# Delete element
unset FRUITS[0]
echo "After delete: ${FRUITS[@]}"
echo "Indices now: ${!FRUITS[@]}"
```

### Step 5: Array Slicing

```bash
NUMS=(10 20 30 40 50 60 70 80 90 100)

# Slice: ${array[@]:start:length}
echo "First 3:  ${NUMS[@]:0:3}"
echo "Middle 3: ${NUMS[@]:3:3}"
echo "Last 3:   ${NUMS[@]: -3}"
```

**Expected output:**
```
First 3:  10 20 30
Middle 3: 40 50 60
Last 3:   80 90 100
```

### Step 6: Associative Arrays (Key-Value)

```bash
# declare -A is required for associative arrays
declare -A USER_INFO
USER_INFO["name"]="Alice"
USER_INFO["age"]="30"
USER_INFO["role"]="engineer"
USER_INFO["city"]="London"

# Access by key
echo "Name: ${USER_INFO[name]}"
echo "Role: ${USER_INFO[role]}"

# All keys
echo "Keys: ${!USER_INFO[@]}"

# All values
echo "Values: ${USER_INFO[@]}"
```

```bash
# Iterate over associative array
for key in "${!USER_INFO[@]}"; do
    echo "  $key = ${USER_INFO[$key]}"
done
```

### Step 7: Practical Array Use Cases

```bash
# Collect command results into array
readarray -t USERS < <(cut -d: -f1 /etc/passwd | head -5)
echo "First 5 users: ${USERS[@]}"
echo "Count: ${#USERS[@]}"
for u in "${USERS[@]}"; do
    echo "  User: $u"
done
```

```bash
# Word frequency counter
declare -A FREQ
WORDS="apple banana apple cherry banana apple"
for word in $WORDS; do
    FREQ[$word]=$(( ${FREQ[$word]:-0} + 1 ))
done
for word in "${!FREQ[@]}"; do
    echo "$word: ${FREQ[$word]}"
done | sort
```

**Expected output:**
```
apple: 3
banana: 2
cherry: 1
```

### Step 8: Array Operations Summary

```bash
# Build, populate, and report
declare -a SERVERS=("web01" "web02" "db01" "cache01")

echo "Total servers: ${#SERVERS[@]}"
echo "Web servers: $(for s in "${SERVERS[@]}"; do [[ "$s" == web* ]] && echo $s; done | tr '\n' ' ')"
echo "Last server: ${SERVERS[-1]}"
echo "Servers 1-2: ${SERVERS[@]:0:2}"
```

## ✅ Verification

```bash
# Test indexed array
ARR=(a b c d e)
echo "Length: ${#ARR[@]} (expect 5)"
echo "Index 2: ${ARR[2]} (expect c)"
echo "Slice: ${ARR[@]:1:3} (expect b c d)"

# Test associative array
declare -A MAP=([key1]="val1" [key2]="val2")
echo "key1: ${MAP[key1]} (expect val1)"
echo "Keys: ${!MAP[@]}"

echo "Practitioner Lab 14 complete"
```

## 📝 Summary
- `ARR=("a" "b" "c")` creates an indexed array; `ARR+=("d")` appends
- `${ARR[@]}` expands all elements; `${#ARR[@]}` gives count
- `${!ARR[@]}` returns all indices; `ARR[-1]` accesses the last element
- `${ARR[@]:start:len}` slices an array
- `declare -A HASH` creates an associative array (key-value pairs)
- `${!HASH[@]}` returns all keys; `${HASH[@]}` returns all values
- `readarray -t ARR < <(command)` fills array from command output
