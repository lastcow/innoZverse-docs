# Lab 6: Deleting Files Safely

## 🎯 Objective
Learn to remove files and directories with `rm`, understand the dangers of `rm -rf`, and explore safer alternatives using the trash concept.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Labs 1–5
- Understanding of files and directories

## 🔬 Lab Instructions

### Step 1: Create Test Files and Directories
```bash
mkdir -p ~/lab06/keep ~/lab06/delete
echo "Keep this" > ~/lab06/keep/important.txt
echo "Delete me" > ~/lab06/delete/junk.txt
echo "Also delete" > ~/lab06/delete/trash.txt
touch ~/lab06/delete/empty.txt
ls -R ~/lab06
```

### Step 2: Delete a Single File with `rm`
```bash
rm ~/lab06/delete/empty.txt
ls ~/lab06/delete/
# Output: junk.txt  trash.txt
# empty.txt is gone — permanently, no trash!
```

### Step 3: Prompt Before Deleting with `-i`
```bash
rm -i ~/lab06/delete/junk.txt
# Output: rm: remove regular file '/home/student/lab06/delete/junk.txt'? 
# Type 'y' then Enter to confirm
```

### Step 4: Delete Multiple Files
```bash
# Create more test files
touch ~/lab06/delete/file{1..5}.txt
ls ~/lab06/delete/

# Remove them all using a glob pattern
rm ~/lab06/delete/file*.txt
ls ~/lab06/delete/
# Output: trash.txt
```

### Step 5: Try to Remove a Directory with `rm` (Without Flags)
```bash
rm ~/lab06/delete
# Output: rm: cannot remove '/home/student/lab06/delete': Is a directory
# rm alone doesn't delete directories
```

### Step 6: Remove an Empty Directory
```bash
mkdir ~/lab06/emptydir
rmdir ~/lab06/emptydir
# Success — rmdir works only on empty directories
```

### Step 7: Remove a Directory with Contents Using `rm -r`
```bash
rm -r ~/lab06/delete
ls ~/lab06/
# Output: keep
# The entire delete/ directory and its contents are gone
```

### Step 8: Understand the Danger of `rm -rf`
```bash
# WARNING: rm -rf is IRREVERSIBLE
# Always double-check what you're removing

# Bad practice (never run without confirmation):
# rm -rf /important/directory

# Safe approach: preview first with ls
ls ~/lab06/keep
# Output: important.txt

# Only then remove
rm -rf ~/lab06/keep
ls ~/lab06/
# Output: (empty)
```

### Step 9: Install and Use `trash-cli` (Safer Alternative)
```bash
sudo apt install trash-cli -y

# Create test files
echo "Trashable" > ~/testfile.txt

# Move to trash instead of permanent delete
trash-put ~/testfile.txt

# View trash contents
trash-list
# Output: 2026-03-01 ... /home/student/testfile.txt

# Restore from trash
trash-restore
# Follow the prompts to select which file to restore

# Empty the trash
trash-empty
```

### Step 10: Create a Safe `rm` Alias
```bash
# Add this to ~/.bashrc for safer deletion
echo "alias rm='rm -i'" >> ~/.bashrc
source ~/.bashrc

# Now rm will always prompt before deleting
rm /tmp/somefile.txt
# Will ask for confirmation
```

### Step 11: Force Remove Without Prompts with `-f`
```bash
# -f suppresses errors and prompts (use with extreme caution)
touch ~/tempfile.txt
rm -f ~/tempfile.txt
# No confirmation, no error if file doesn't exist
```

### Step 12: Best Practices for Safe Deletion
```bash
# 1. Always use absolute paths when deleting as root
# 2. Run ls first to preview what you'll delete
ls ~/lab06/

# 3. Use rm -ri for interactive recursive delete
mkdir -p ~/lab06/test/subdir
touch ~/lab06/test/subdir/file.txt
rm -ri ~/lab06/test
# Will ask before each file/dir

# 4. Clean up
rm -rf ~/lab06
```

## ✅ Verification
```bash
# Create, verify, and safely delete
mkdir /tmp/rmtest
touch /tmp/rmtest/file1.txt /tmp/rmtest/file2.txt

ls /tmp/rmtest
# Output: file1.txt  file2.txt

rm /tmp/rmtest/file1.txt
ls /tmp/rmtest
# Output: file2.txt

rm -r /tmp/rmtest
ls /tmp/rmtest 2>&1
# Output: ls: cannot access '/tmp/rmtest': No such file or directory
```

## 📝 Summary
- `rm file` permanently deletes a file — there is no undo without backups
- `rm -i` prompts before each deletion — use this when unsure
- `rm -r dir` deletes a directory and all its contents recursively
- `rm -rf` is the most powerful and most dangerous: forces recursive delete with no prompts
- `trash-put` (from `trash-cli`) sends files to a recoverable trash — use it for important data
- Never run `rm -rf /` or `rm -rf *` as root — this can destroy the entire system
