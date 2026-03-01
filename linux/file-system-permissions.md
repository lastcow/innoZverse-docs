# File System & Permissions

Understanding Linux file permissions is essential for security and system administration.

## The Linux File System Hierarchy

```
/               Root directory
├── bin/        Essential user binaries
├── etc/        System configuration files
├── home/       User home directories
├── var/        Variable data (logs, databases)
├── tmp/        Temporary files
├── usr/        User programs and data
└── proc/       Virtual filesystem (process info)
```

## Understanding Permissions

Every file has three permission sets: **owner**, **group**, **others**

```bash
ls -l file.txt
# -rwxr-xr-- 1 alice developers 1234 Mar 1 2026 file.txt
#  ^^^rwxr-xr--
#  |  |||
#  |  ||+-- Others: r-- (read only)
#  |  |+--- Group: r-x (read + execute)
#  |  +---- Owner: rwx (read + write + execute)
#  +------- File type (- = file, d = directory)
```

## Changing Permissions

```bash
# Symbolic mode
chmod u+x file.sh       # Add execute for owner
chmod g-w file.txt      # Remove write from group
chmod o=r file.txt      # Set others to read-only
chmod a+x script.sh     # Add execute for all

# Numeric mode
chmod 755 script.sh     # rwxr-xr-x
chmod 644 file.txt      # rw-r--r--
chmod 600 private.key   # rw------- (private key best practice)
```

## Changing Ownership

```bash
chown alice file.txt            # Change owner
chown alice:developers file.txt # Change owner and group
chown -R alice /home/alice/     # Recursive ownership change
```

## Special Permissions

```bash
chmod +s script.sh    # Setuid — run as file owner
chmod +t /tmp/        # Sticky bit — only owner can delete
```

---

*Next: [Shell Scripting →](shell-scripting.md)*
