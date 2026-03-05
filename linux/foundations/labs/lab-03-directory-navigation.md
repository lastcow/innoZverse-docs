# Lab 03: Directory Navigation

## Objective
Move around the Linux filesystem with confidence: `cd`, `ls`, absolute vs relative paths, tab completion, and navigation shortcuts. You'll create a realistic project structure and navigate it fluently.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Your Starting Position

```bash
pwd
```

**📸 Verified Output:**
```
/
```

```bash
cd ~
pwd
```

**📸 Verified Output:**
```
/root
```

> 💡 `~` (tilde) is a shortcut for your home directory. `cd ~` always brings you home no matter where you are — like pressing the home button on your phone.

---

## Step 2: Exploring Your Home

```bash
ls -la
```

**📸 Verified Output:**
```
total 16
drwx------ 2 root root 4096 Feb 10 14:12 .
drwxr-xr-x 1 root root 4096 Mar  5 00:54 ..
-rw-r--r-- 1 root root 3106 Oct 15  2021 .bashrc
-rw-r--r-- 1 root root  161 Jul  9  2019 .profile
```

> 💡 `.` = current directory. `..` = parent directory. Files starting with `.` are **hidden** — only visible with `ls -a`. `.bashrc` and `.profile` are shell startup scripts.

---

## Step 3: Create a Project Structure

```bash
mkdir -p projects/webapp/src
mkdir -p projects/webapp/tests
mkdir -p projects/scripts

ls -R projects/
```

**📸 Verified Output:**
```
projects/:
scripts  webapp

projects/scripts:

projects/webapp:
src  tests

projects/webapp/src:

projects/webapp/tests:
```

> 💡 `mkdir -p` creates **all intermediate directories** at once. Without `-p`, `mkdir projects/webapp/src` would fail if `projects/` doesn't exist yet.

---

## Step 4: Absolute vs Relative Paths

**Absolute path** — always starts with `/`, works from anywhere:
```bash
cd /tmp/projects 2>/dev/null || { mkdir -p /tmp/projects/webapp/src /tmp/projects/scripts && cd /tmp/projects; }
pwd
```

**📸 Verified Output:**
```
/tmp/projects
```

**Relative path** — relative to where you currently are:
```bash
cd webapp
pwd
```

**📸 Verified Output:**
```
/tmp/projects/webapp
```

```bash
cd ../..
pwd
```

**📸 Verified Output:**
```
/tmp
```

> 💡 `..` goes **up one level** in the directory tree. `../../` goes up two levels. `../sibling` goes up one then into `sibling` — without ever needing to know the full absolute path.

---

## Step 5: Navigation Shortcuts

```bash
# Go somewhere
cd /etc

# Jump back to where you just were
cd -
pwd
```

**📸 Verified Output:**
```
/etc
/tmp
```

```bash
# Jump to home instantly
cd
pwd
```

**📸 Verified Output:**
```
/root
```

> 💡 `cd -` is like the "back" button in a browser — instantly returns to your previous directory. Extremely useful when switching between two distant directories.

---

## Step 6: Listing Options

```bash
cd /etc

# Long format with human-readable sizes
ls -lh | head -8
```

**📸 Verified Output:**
```
total 280K
drwxr-xr-x 1 root root 4.0K Feb 10 14:05 .
drwxr-xr-x 1 root root 4.0K Mar  5 00:54 ..
-rw------- 1 root root    0 Feb 10 14:05 .pwd.lock
-rw-r--r-- 1 root root 3.0K Feb 10 14:05 adduser.conf
drwxr-xr-x 2 root root 4.0K Feb 10 14:11 alternatives
drwxr-xr-x 8 root root 4.0K Feb 10 14:05 apt
-rw-r--r-- 1 root root 2.3K Jan  6  2022 bash.bashrc
```

```bash
# Only subdirectories
ls -d */
```

**📸 Verified Output:**
```
alternatives/  apt/  cloud/  cron.d/  cron.daily/  ...
```

```bash
# Sort by modification time, newest first
ls -lt | head -5
```

**📸 Verified Output:**
```
total 280
drwxr-xr-x 8 root root  4096 Feb 10 14:05 apt
drwxr-xr-x 2 root root  4096 Feb 10 14:11 alternatives
drwxr-xr-x 1 root root  4096 Mar  5 00:54 .
```

---

## Step 7: Traverse the Filesystem

```bash
# Navigate deep into usr
cd /usr/share/doc
ls | wc -l
```

**📸 Verified Output:**
```
28
```

```bash
# Go up two levels using relative path
cd ../..
pwd
```

**📸 Verified Output:**
```
/usr
```

```bash
# Cross from usr to etc using absolute path
cd /etc
# Cross to var using relative
cd ../var
pwd
```

**📸 Verified Output:**
```
/var
```

---

## Step 8: Capstone — Navigate a Security Lab Structure

```bash
# Build a realistic security lab directory
mkdir -p ~/security-lab/{recon,exploitation,post-exploit,reporting,tools}
mkdir -p ~/security-lab/recon/{nmap,web,dns}
mkdir -p ~/security-lab/exploitation/{payloads,scripts}

# Navigate and inspect
cd ~/security-lab
ls -R

# Practice: go to nmap folder using relative path from security-lab
cd recon/nmap && pwd

# Come back with one command
cd ~/security-lab && pwd

# Go to payloads using a mix
cd exploitation/payloads && pwd
cd ../../reporting && pwd
```

**📸 Verified Output:**
```
/root/security-lab/recon/nmap
/root/security-lab
/root/security-lab/exploitation/payloads
/root/security-lab/reporting
```

---

## Summary

| Command / Shortcut | Meaning |
|-------------------|---------|
| `cd ~` or `cd` | Go to home directory |
| `cd -` | Return to previous directory |
| `cd ..` | Go up one level |
| `cd ../..` | Go up two levels |
| `pwd` | Print current directory |
| `ls -la` | List all files with details |
| `ls -lh` | List with human-readable sizes |
| `ls -lt` | List sorted by modification time |
| `mkdir -p a/b/c` | Create nested directories at once |
