# Lab 18: Environment Variables

## 🎯 Objective
Understand and manipulate environment variables: view them with `env` and `echo`, set them with `export`, modify `$PATH`, and make changes permanent via `.bashrc`.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Basic bash shell usage

## 🔬 Lab Instructions

### Step 1: View Environment Variables
```bash
# Print all environment variables
env
# Output: large list of name=value pairs

# Or use printenv
printenv | sort | head -20

# Count how many variables are set
env | wc -l
```

### Step 2: View Important Built-in Variables
```bash
echo $HOME
# Output: /home/student

echo $USER
# Output: student

echo $SHELL
# Output: /bin/bash

echo $PATH
# Output: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/home/student/.local/bin

echo $PWD
# Output: current directory

echo $LANG
# Output: en_US.UTF-8

echo $HOSTNAME
# Output: ubuntu
```

### Step 3: Set a Variable (Shell Variable)
```bash
# Without export: only visible in current shell
MYVAR="hello"
echo $MYVAR
# Output: hello

# NOT visible to child processes
bash -c 'echo $MYVAR'
# Output: (empty)
```

### Step 4: Export a Variable (Environment Variable)
```bash
# With export: visible to current shell AND child processes
export MYVAR="hello world"
echo $MYVAR
# Output: hello world

# Now visible in child shells
bash -c 'echo $MYVAR'
# Output: hello world

# Or: export and assign in one line
export GREETING="Good morning"
```

### Step 5: Unset a Variable
```bash
echo $MYVAR
# Output: hello world

unset MYVAR
echo $MYVAR
# Output: (empty)
```

### Step 6: Understand and Modify `$PATH`
`$PATH` tells the shell where to look for commands when you type them.

```bash
echo $PATH
# Output: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Directories are separated by colons :

# Show PATH one entry per line
echo $PATH | tr ':' '\n'

# Which command does "ls" resolve to?
which ls
# Output: /usr/bin/ls
type ls
```

### Step 7: Add a Directory to PATH
```bash
# Create a personal bin directory
mkdir -p ~/bin

# Create a script there
echo '#!/bin/bash\necho "My custom command!"' > ~/bin/mycommand
chmod +x ~/bin/mycommand

# Try running it (might fail if ~/bin not in PATH)
mycommand
# Output: bash: mycommand: command not found

# Add ~/bin to PATH temporarily
export PATH="$HOME/bin:$PATH"
echo $PATH
# Output: /home/student/bin:/usr/local/sbin:...

# Now it works
mycommand
# Output: My custom command!
```

### Step 8: Make Variables Permanent with `.bashrc`
Changes to environment variables are lost when you close the terminal. To persist them:

```bash
# View current .bashrc
cat ~/.bashrc | tail -20

# Add PATH modification to .bashrc
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
echo 'export EDITOR="nano"' >> ~/.bashrc
echo 'export MY_PROJECT="/home/student/projects"' >> ~/.bashrc

# Apply changes to current session
source ~/.bashrc
# or
. ~/.bashrc

# Verify
echo $EDITOR
# Output: nano
```

### Step 9: Difference Between `.bashrc` and `.bash_profile`
```bash
# .bashrc:      loaded for interactive non-login shells (new terminal tabs)
# .bash_profile: loaded for login shells (SSH, console login)

# Best practice: put exports in .bash_profile and source .bashrc from it
cat ~/.bash_profile 2>/dev/null || echo "No .bash_profile yet"

# Ubuntu often uses .profile instead of .bash_profile
cat ~/.profile | tail -10
```

### Step 10: Use Variables in Commands
```bash
# Variables work in any bash context
BACKUP_DIR="/tmp/backups"
mkdir -p $BACKUP_DIR
cp /etc/hosts $BACKUP_DIR/

ls $BACKUP_DIR
# Output: hosts

# Use curly braces for clarity
FILENAME="myapp"
cp $BACKUP_DIR/$FILENAME.conf /tmp/
# Without braces: $FILENAME.conf works here
# With braces: ${FILENAME}.conf  (needed if concatenating with letters)
```

### Step 11: Read-Only Variables
```bash
readonly CONSTANT="never changes"
echo $CONSTANT

# Try to change it
CONSTANT="new value"
# Output: bash: CONSTANT: readonly variable
```

### Step 12: Pass Variables to a Single Command
```bash
# Set a variable just for one command (without exporting)
MYVAR="temporary" env | grep MYVAR
# Output: MYVAR=temporary

echo $MYVAR
# Output: (empty) — not set in current shell

# Common use: override language for a command
LANG=C date
# Output: date in C locale format

# Clean up
rm -rf ~/bin
unset GREETING MY_PROJECT BACKUP_DIR FILENAME
rm -rf /tmp/backups
```

## ✅ Verification
```bash
# Check key variables are set
echo "HOME: $HOME"
echo "USER: $USER"
echo "SHELL: $SHELL"
echo "PATH entries: $(echo $PATH | tr ':' '\n' | wc -l)"

# Export a test variable and verify child process inherits it
export TESTVAR="inherited"
bash -c 'echo "Child sees: $TESTVAR"'
# Output: Child sees: inherited

unset TESTVAR
```

## 📝 Summary
- Environment variables are key=value pairs that configure the shell and programs
- Shell variables (`VAR=val`) are local; `export VAR=val` makes them available to child processes
- `$PATH` controls where the shell looks for commands — prepend your directories at the front
- `env` or `printenv` lists all current environment variables
- Add `export` lines to `~/.bashrc` to make variable changes permanent across sessions
- `source ~/.bashrc` (or `. ~/.bashrc`) reloads the file without starting a new shell
