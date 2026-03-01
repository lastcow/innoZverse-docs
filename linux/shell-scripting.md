# Shell Scripting

Shell scripts let you automate repetitive tasks and build powerful workflows.

## Your First Script

```bash
#!/bin/bash
# my_script.sh

echo "Hello, World!"
echo "Today is: $(date)"
```

```bash
chmod +x my_script.sh
./my_script.sh
```

## Variables

```bash
NAME="Innozverse"
echo "Welcome to $NAME"
echo "Welcome to ${NAME}!"

# Command substitution
CURRENT_DIR=$(pwd)
FILE_COUNT=$(ls | wc -l)
```

## User Input

```bash
echo "Enter your name:"
read USERNAME
echo "Hello, $USERNAME!"
```

## Conditionals

```bash
if [ "$1" == "hello" ]; then
    echo "Hello to you too!"
elif [ "$1" == "bye" ]; then
    echo "Goodbye!"
else
    echo "I don't understand: $1"
fi

# File checks
if [ -f "/etc/passwd" ]; then
    echo "File exists"
fi

if [ -d "/home" ]; then
    echo "Directory exists"
fi
```

## Loops

```bash
# For loop
for i in 1 2 3 4 5; do
    echo "Number: $i"
done

# While loop
COUNT=0
while [ $COUNT -lt 5 ]; do
    echo "Count: $COUNT"
    ((COUNT++))
done

# Loop over files
for FILE in *.txt; do
    echo "Processing: $FILE"
done
```

## Functions

```bash
greet() {
    local NAME=$1
    echo "Hello, $NAME!"
}

greet "Alice"
greet "Bob"
```

## Practical Example: Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y-%m-%d)"
SOURCE="/home/alice/documents"

mkdir -p "$BACKUP_DIR"
cp -r "$SOURCE" "$BACKUP_DIR"
echo "Backup complete: $BACKUP_DIR"
```

---

*Next: [System Administration →](system-administration.md)*
