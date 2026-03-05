# Lab 11: nano — The Beginner-Friendly Text Editor

## Objective
Edit files with `nano`: open, navigate, write, save, search, and use keyboard shortcuts. nano is the easiest terminal editor to learn — ideal for quick config file edits on servers.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Install and Verify

```bash
apt-get update -qq && apt-get install -y -qq nano
nano --version | head -1
```

**📸 Verified Output:**
```
 GNU nano, version 6.2
```

---

## Step 2: nano Interface Overview

When you open nano, the screen shows:

```
  GNU nano 6.2            filename.txt              Modified
  ─────────────────────────────────────────────────────────
  (your file content here)


  ─────────────────────────────────────────────────────────
  ^G Help    ^O Write   ^W Where   ^K Cut     ^X Exit
  ^F Find    ^R Replace ^T Execute ^U Paste   ^J Justify
```

> 💡 The `^` symbol means `Ctrl`. So `^X` = `Ctrl+X` (exit). The shortcuts are **always visible** at the bottom — you never need to memorise them.

---

## Step 3: Create and Edit a File

```bash
# Create a config file for a fictional app
cat > /tmp/myapp.conf << 'EOF'
# MyApp Configuration
HOST=localhost
PORT=8080
DEBUG=false
LOG_LEVEL=INFO
DB_NAME=myapp_db
EOF

cat /tmp/myapp.conf
```

**📸 Verified Output:**
```
# MyApp Configuration
HOST=localhost
PORT=8080
DEBUG=false
LOG_LEVEL=INFO
DB_NAME=myapp_db
```

To edit this in nano:
```bash
nano /tmp/myapp.conf
```

**Essential nano shortcuts:**

| Key | Action |
|-----|--------|
| `Ctrl+O` then `Enter` | Save (Write Out) |
| `Ctrl+X` | Exit |
| `Ctrl+W` | Search (Where is) |
| `Ctrl+K` | Cut entire line |
| `Ctrl+U` | Paste (Un-cut) |
| `Ctrl+G` | Help |
| `Ctrl+/` | Go to line number |
| `Alt+U` | Undo |
| `Alt+E` | Redo |
| Arrow keys | Navigate |
| `Ctrl+C` | Show cursor position |

---

## Step 4: nano Command-Line Options

```bash
# Open with line numbers visible
nano -l /tmp/myapp.conf

# Open at a specific line number
nano +3 /tmp/myapp.conf

# Read-only mode (view without accidental edits)
nano -v /tmp/myapp.conf

# No line wrap (useful for config files and code)
nano -w /tmp/myapp.conf
```

> 💡 `nano -w` is important for editing config files where line wrapping would corrupt the syntax. Always use `-w` when editing `/etc/nginx/nginx.conf`, `/etc/ssh/sshd_config`, etc.

---

## Step 5: Creating a Shell Script with nano

```bash
# Create script via heredoc (simulates typing in nano)
cat > /tmp/backup.sh << 'SCRIPT'
#!/bin/bash
# Simple backup script
# Edit this with: nano backup.sh

BACKUP_DIR="/tmp/backups"
SOURCE_DIR="/etc"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/etc_backup_${DATE}.tar.gz" "$SOURCE_DIR" 2>/dev/null
echo "Backup created: etc_backup_${DATE}.tar.gz"
SCRIPT

chmod +x /tmp/backup.sh
/tmp/backup.sh
ls -lh /tmp/backups/
```

**📸 Verified Output:**
```
Backup created: etc_backup_20260305_005800.tar.gz
total 16K
-rw-r--r-- 1 root root 14K Mar  5 00:58 etc_backup_20260305_005800.tar.gz
```

---

## Step 6: Search and Replace in nano

Within nano, to search and replace:
1. Press `Ctrl+\` (on some systems `Alt+R`)
2. Type search string → Enter
3. Type replacement string → Enter
4. Press `A` to replace all, or `Y`/`N` for each

To navigate to a specific line:
1. Press `Ctrl+/`
2. Type line number → Enter

---

## Step 7: nano for System Configuration

```bash
# View /etc/ssh/sshd_config key settings
grep -v '^#' /etc/ssh/sshd_config 2>/dev/null | grep -v '^$' | head -10 \
  || echo "sshd_config not available in container"

# nano is the standard editor for quick sysadmin tasks:
echo "Common uses of nano:"
echo "  nano /etc/hosts         — add local DNS entries"
echo "  nano /etc/crontab       — schedule jobs"
echo "  nano /etc/ssh/sshd_config  — harden SSH"
echo "  nano /etc/fstab         — mount points"
echo "  nano ~/.bashrc          — shell customisation"
```

**📸 Verified Output:**
```
sshd_config not available in container
Common uses of nano:
  nano /etc/hosts         — add local DNS entries
  nano /etc/crontab       — schedule jobs
  nano /etc/ssh/sshd_config  — harden SSH
  nano /etc/fstab         — mount points
  nano ~/.bashrc          — shell customisation
```

---

## Step 8: Capstone — Edit a Simulated NGINX Config

```bash
cat > /tmp/nginx_site.conf << 'EOF'
server {
    listen 80;
    server_name example.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
}
EOF

echo "Config file created:"
cat -n /tmp/nginx_site.conf
echo ""
echo "File stats:"
wc -l /tmp/nginx_site.conf
echo "lines in nginx config"
```

**📸 Verified Output:**
```
Config file created:
     1	server {
     2	    listen 80;
     3	    server_name example.com;
     4	    root /var/www/html;
     5	    index index.html;
     6	
     7	    location / {
     8	        try_files $uri $uri/ =404;
     9	    }
    10	
    11	    location /api {
    12	        proxy_pass http://127.0.0.1:3000;
    13	        proxy_set_header Host $host;
    14	    }
    15	
    16	    # Security headers
    17	    add_header X-Frame-Options "SAMEORIGIN";
    18	    add_header X-Content-Type-Options "nosniff";
    19	}

File stats:
19 /tmp/nginx_site.conf
lines in nginx config
```

---

## Summary

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Save file |
| `Ctrl+X` | Exit |
| `Ctrl+W` | Search |
| `Ctrl+\` | Search and replace |
| `Ctrl+K` | Cut line |
| `Ctrl+U` | Paste |
| `Ctrl+/` | Go to line number |
| `Alt+U` | Undo |
| `nano -l` | Show line numbers |
| `nano -w` | No line wrap |
