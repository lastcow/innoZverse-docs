# Navigating the File System

## The Linux Directory Structure

```
/                   ← Root (everything starts here)
├── home/           ← User home directories
│   └── alice/      ← Your home (~)
├── etc/            ← System configuration files
├── var/            ← Variable data (logs, databases)
├── usr/            ← Installed programs
├── bin/            ← Essential binaries
├── tmp/            ← Temporary files (cleared on reboot)
├── dev/            ← Device files
└── proc/           ← Virtual filesystem (running processes)
```

## Essential Navigation Commands

```bash
pwd                 # Print Working Directory — where am I?
ls                  # List files
ls -l               # Long format (permissions, size, date)
ls -la              # Include hidden files (starting with .)
ls -lh              # Human-readable file sizes

cd /etc             # Go to /etc
cd ~                # Go to home directory
cd ..               # Go up one level
cd -                # Go to previous directory
cd /var/log/nginx   # Absolute path
```

## Useful Shortcuts

| Shortcut | Meaning |
|----------|---------|
| `~` | Your home directory (`/home/username`) |
| `.` | Current directory |
| `..` | Parent directory |
| `-` | Previous directory |
| `/` | Root directory |

## Finding Things

```bash
find / -name "config.txt"           # Find by name
find /home -type f -size +10M       # Files larger than 10MB
find /etc -name "*.conf" -mtime -7  # .conf files modified in last 7 days
locate filename                     # Fast search (uses database)
which python3                       # Where is this command?
```

---

*Next: [File & Directory Management →](file-directory-management.md)*
