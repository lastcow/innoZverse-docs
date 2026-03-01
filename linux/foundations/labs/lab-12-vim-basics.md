# Lab 12: vim Basics

## 🎯 Objective
Learn the fundamental concepts of the `vim` editor: understanding modes, navigating without arrow keys, inserting and editing text, and saving/quitting files.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Completed Lab 11 (nano) or basic text editor experience
- Patience — vim has a learning curve but is extremely powerful

## 🔬 Lab Instructions

### Step 1: Install vim
```bash
sudo apt install vim -y
vim --version | head -1
# Output: VIM - Vi IMproved 8.2 ...
```

### Step 2: Open a File in vim
```bash
vim ~/vimtest.txt
# The screen clears and vim opens
# You are in NORMAL mode (default)
```

### Step 3: Understand vim's Three Core Modes
```
NORMAL mode:   Default. Navigation and commands. (press Esc to return here)
INSERT mode:   Typing text. (press i, a, o to enter)
COMMAND mode:  Saving, quitting, searching. (press : to enter from normal)
```

The mode is shown at the bottom:
- Nothing shown = NORMAL
- `-- INSERT --` = INSERT
- `:` = COMMAND

### Step 4: Enter Insert Mode and Type Text
```bash
# In NORMAL mode, press: i
# You'll see -- INSERT -- at the bottom

# Now type:
# This is line one.
# This is line two.
# This is line three.
# vim is a powerful editor.
# Learning it is worth the effort.

# Press Esc to return to NORMAL mode
```

### Step 5: Navigate in NORMAL Mode
```
h:  move left
l:  move right
j:  move down
k:  move up

w:  jump forward one word
b:  jump backward one word
e:  jump to end of current word

0:  go to beginning of line
$:  go to end of line
gg: go to first line of file
G:  go to last line of file
5G: go to line 5
```

```bash
# Practice: press Esc (ensure NORMAL mode)
# Use hjkl to navigate
# Press G to go to last line
# Press gg to go to first line
```

### Step 6: Different Ways to Enter Insert Mode
```
i:  insert before cursor
a:  append after cursor
I:  insert at beginning of line
A:  append at end of line
o:  open new line below and insert
O:  open new line above and insert
```

```bash
# Go to end of line 1 with $
# Press a to append after the last character
# Type: (edited)
# Press Esc
```

### Step 7: Delete Text in NORMAL Mode
```
x:   delete character under cursor
dd:  delete (cut) entire line
dw:  delete word
d$:  delete from cursor to end of line
d0:  delete from cursor to beginning of line
3dd: delete 3 lines
```

```bash
# Place cursor on a line you want to delete
# Press dd to cut it
```

### Step 8: Undo and Redo
```
u:        undo last change
Ctrl+r:   redo (undo the undo)
```

```bash
# Delete a line with dd
# Press u to undo it — the line comes back!
# Press Ctrl+r to redo
```

### Step 9: Copy (Yank) and Paste
```
yy:   yank (copy) current line
yw:   yank word
y$:   yank to end of line
p:    paste below current line
P:    paste above current line
3yy:  yank 3 lines
```

```bash
# Go to line 1 (gg)
# Press yy to copy line 1
# Press G to go to last line
# Press p to paste it below
```

### Step 10: Search in vim
```bash
# In NORMAL mode:
# Press / to search forward
/vim
# Press Enter to search
# Press n for next match
# Press N for previous match

# Press ? to search backward
?line
# Press Enter
```

### Step 11: Save and Quit (Command Mode)
```bash
# Press Esc first (ensure NORMAL mode)
# Then press : to enter COMMAND mode

:w          # Save (write)
:q          # Quit (only works if no unsaved changes)
:wq         # Save and quit
:q!         # Quit WITHOUT saving (force)
:wq!        # Force save and quit
:x          # Save and quit (like :wq)

# Save to a different file:
:w ~/vimtest_copy.txt
```

### Step 12: Useful Quick Commands
```
:set number       # Show line numbers
:set nonumber     # Hide line numbers
:syntax on        # Enable syntax highlighting
:%s/old/new/g     # Replace all 'old' with 'new' in file
:10               # Go to line 10
```

```bash
# In vim, try:
:set number
# Line numbers appear on the left

# Replace all instances of "line" with "LINE"
:%s/line/LINE/g
# Press Enter — all occurrences are replaced

# Save and quit
:wq
```

## ✅ Verification
```bash
# Create a file with vim, verify contents
vim /tmp/vimcheck.txt
# Press i
# Type: vim is working correctly
# Press Esc
# Type: :wq
# Press Enter

cat /tmp/vimcheck.txt
# Output: vim is working correctly

rm /tmp/vimcheck.txt ~/vimtest.txt ~/vimtest_copy.txt 2>/dev/null
```

## 📝 Summary
- vim has three modes: NORMAL (navigate), INSERT (type), COMMAND (`:` prefix for save/quit)
- Always press `Esc` to return to NORMAL mode
- `i/a/o` enter INSERT mode; `Esc` exits it
- Navigate with `hjkl`; jump with `gg/G/w/b/$`
- Save with `:w`; quit with `:q`; save-and-quit with `:wq`; force quit with `:q!`
- `dd` cuts a line, `yy` copies, `p` pastes, `u` undoes — these are incredibly fast once learned
