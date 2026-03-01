# Permissions & Ownership

## Reading Permissions

```bash
ls -l
# -rwxr-xr-- 1 alice devs 1234 Mar 1 file.sh
#  ^^^ ^^^ ^^^
#  |   |   └── Others: r-- (read only)
#  |   └─────── Group:  r-x (read + execute)
#  └─────────── Owner:  rwx (read + write + execute)
```

| Symbol | Meaning |
|--------|---------|
| `r` | Read (4) |
| `w` | Write (2) |
| `x` | Execute (1) |
| `-` | No permission (0) |

## chmod — Change Permissions

```bash
# Symbolic
chmod u+x script.sh         # Owner: add execute
chmod g-w file.txt          # Group: remove write
chmod o=r file.txt          # Others: read only
chmod a+x script.sh         # All: add execute

# Numeric (octal)
chmod 755 script.sh         # rwxr-xr-x
chmod 644 file.txt          # rw-r--r--
chmod 600 ~/.ssh/id_rsa     # rw------- (private key)
chmod 777 file              # ⚠️ Everyone can do everything
```

## chown — Change Ownership

```bash
chown alice file.txt                # Change owner
chown alice:developers file.txt     # Change owner and group
chown -R alice /home/alice/         # Recursive
```

## Special Permissions

```bash
chmod u+s /usr/bin/sudo     # Setuid: run as file owner
chmod g+s /shared/          # Setgid: new files inherit group
chmod +t /tmp/              # Sticky bit: only owner can delete
```

---

*Next: [Text Editors →](text-editors.md)*
