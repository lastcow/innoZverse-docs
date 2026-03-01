# Lab 11: nano — Terminal Text Editor

## 🎯 Objective
Get comfortable using the `nano` text editor: opening files, navigating, editing, searching, saving, and exiting — without needing to memorize complex commands.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Basic terminal navigation

## 🔬 Lab Instructions

### Step 1: Install nano (if not present)
```bash
which nano || sudo apt install nano -y
nano --version
# Output: GNU nano, version 6.2
```

### Step 2: Open nano with a New File
```bash
nano ~/myfile.txt
# Opens nano editor
# The bottom shows key shortcuts (^ = Ctrl)
```

### Step 3: Understand the nano Interface
When nano opens, you'll see:
```
  GNU nano 6.2           myfile.txt

  (cursor is here — start typing)




^G Help     ^O Write Out  ^W Where Is  ^K Cut Line   ^T Execute
^X Exit     ^R Read File  ^\ Replace   ^U Paste       ^J Justify
```
- `^` means Ctrl key
- The status bar shows the filename and modification status

### Step 4: Type Some Content
```bash
# In nano, just start typing:
# Line 1: This is my first file.
# Line 2: Nano is easy to use.
# Line 3: Press Enter for new lines.
# Line 4: Let's learn nano!
```

### Step 5: Navigate with Arrow Keys and Shortcuts
```
Arrow keys: move cursor
Ctrl+A:     go to beginning of line
Ctrl+E:     go to end of line
Ctrl+Y:     scroll up one page
Ctrl+V:     scroll down one page
Ctrl+W:     search (Where Is)
Ctrl+_:     go to specific line number
```

### Step 6: Search for Text
```bash
# While in nano, press Ctrl+W
# Type: nano
# Press Enter to find it
# Press Ctrl+W again and Enter to find next occurrence
```

### Step 7: Search and Replace
```bash
# Press Ctrl+\  (that's backslash)
# Enter: easy
# Press Enter
# Enter replacement: simple
# Press Enter
# Press Y to replace this instance, or A to replace all
```

### Step 8: Cut and Paste Lines
```bash
# Move cursor to a line you want to cut
# Press Ctrl+K to cut the entire line
# Move to where you want to paste
# Press Ctrl+U to paste (uncut)
```

### Step 9: Copy Lines (Mark + Cut + Paste)
```bash
# Move cursor to start of text to copy
# Press Ctrl+^ (Ctrl+Shift+6) to set mark
# Move cursor to end of selection (text highlights)
# Press Ctrl+K to cut (but we'll paste it back)
# Move to destination
# Press Ctrl+U to paste
```

### Step 10: Save the File
```bash
# Press Ctrl+O (Write Out)
# nano shows: File Name to Write: myfile.txt
# Press Enter to confirm

# The status bar briefly shows:
# [ Wrote X lines ]
```

### Step 11: Open and Edit an Existing File
```bash
# Exit nano first: Ctrl+X
# Then reopen:
nano ~/myfile.txt

# Navigate to line 2 and add text
# Ctrl+_ → enter line number 2 → Enter
# Home key to go to start of line, or End to go to end
# Add some text and save again with Ctrl+O
```

### Step 12: Exit nano
```bash
# Press Ctrl+X
# If there are unsaved changes:
# nano asks: Save modified buffer?
# Y = yes (save and exit)
# N = no (discard changes and exit)
# Ctrl+C = cancel (go back to editing)
```

## ✅ Verification
```bash
# Create a file with nano, verify content
nano /tmp/nanotest.txt
# Type: "Nano works!"
# Save with Ctrl+O, exit with Ctrl+X

cat /tmp/nanotest.txt
# Output: Nano works!

# Edit a system-like config (in /tmp for safety)
cp /etc/hosts /tmp/hosts_test.txt
nano /tmp/hosts_test.txt
# Add a comment line: # test comment
# Save and exit

grep "test comment" /tmp/hosts_test.txt
# Output: # test comment

rm /tmp/nanotest.txt /tmp/hosts_test.txt
```

## 📝 Summary
- nano is a beginner-friendly terminal editor — key shortcuts are shown at the bottom
- `Ctrl+O` saves; `Ctrl+X` exits; `Ctrl+W` searches; `Ctrl+\` replaces
- `Ctrl+K` cuts a line; `Ctrl+U` pastes it
- When exiting with unsaved changes, nano asks whether to save — press Y, N, or Ctrl+C
- nano is ideal for quick edits; for complex work, consider learning vim (Lab 12)
