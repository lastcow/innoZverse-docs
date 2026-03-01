# Command Line Basics

The terminal is your most powerful tool as a Linux user. This guide covers the essential commands you'll use every day.

## Navigating the File System

```bash
pwd          # Print working directory
ls           # List files and directories
ls -la       # List with details and hidden files
cd /path     # Change directory
cd ..        # Go up one level
cd ~         # Go to home directory
```

## Working with Files

```bash
touch file.txt          # Create empty file
cat file.txt            # Display file contents
less file.txt           # Scroll through file
cp file.txt backup.txt  # Copy file
mv file.txt new.txt     # Move/rename file
rm file.txt             # Delete file
rm -rf directory/       # Delete directory recursively (use with caution!)
```

## Searching & Finding

```bash
find / -name "file.txt"         # Find file by name
grep "pattern" file.txt         # Search text in file
grep -r "pattern" /directory    # Recursive search
which python3                   # Find location of command
```

## Getting Help

```bash
man ls          # Manual page for 'ls'
ls --help       # Quick help
tldr ls         # Simplified examples (install tldr first)
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current command |
| `Ctrl+Z` | Suspend process |
| `Ctrl+L` | Clear terminal |
| `Tab` | Auto-complete |
| `↑ / ↓` | Navigate command history |
| `Ctrl+R` | Search command history |

## Practice Exercises

1. Navigate to `/etc` and list all files sorted by modification time
2. Find all `.log` files in `/var/log`
3. Search for the word "error" in `/var/log/syslog`

---

*Next: [File System & Permissions →](file-system-permissions.md)*
