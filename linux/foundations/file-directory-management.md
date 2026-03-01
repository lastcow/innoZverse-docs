# File & Directory Management

## Creating Files & Directories

```bash
touch file.txt              # Create empty file (or update timestamp)
mkdir my-folder             # Create directory
mkdir -p a/b/c              # Create nested directories
```

## Copying & Moving

```bash
cp file.txt backup.txt              # Copy file
cp -r folder/ folder-backup/        # Copy directory recursively
mv file.txt /tmp/file.txt           # Move file
mv old-name.txt new-name.txt        # Rename file
```

## Deleting

```bash
rm file.txt                 # Delete file
rm -i file.txt              # Ask for confirmation
rm -rf directory/           # Delete directory + contents (⚠️ irreversible!)
rmdir empty-folder/         # Delete empty directory only
```

## Viewing File Contents

```bash
cat file.txt                # Print entire file
less file.txt               # Scroll through (q to quit)
head -20 file.txt           # First 20 lines
tail -20 file.txt           # Last 20 lines
tail -f /var/log/syslog     # Follow log in real-time
```

## Compression & Archives

```bash
tar -czf archive.tar.gz folder/     # Create .tar.gz
tar -xzf archive.tar.gz             # Extract .tar.gz
zip -r archive.zip folder/          # Create .zip
unzip archive.zip                   # Extract .zip
```

---

*Next: [Permissions & Ownership →](permissions-ownership.md)*
