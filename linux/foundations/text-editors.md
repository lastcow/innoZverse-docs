# Text Editors (nano, vim)

## nano — Beginner Friendly

```bash
nano file.txt
```

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Save file |
| `Ctrl+X` | Exit |
| `Ctrl+K` | Cut line |
| `Ctrl+U` | Paste |
| `Ctrl+W` | Search |
| `Ctrl+\` | Search & replace |

## vim — Powerful, Modal Editor

```bash
vim file.txt
```

Vim has **modes**:
- **Normal mode** — Navigate and issue commands (default)
- **Insert mode** — Type text (press `i`)
- **Visual mode** — Select text (press `v`)
- **Command mode** — Run commands (press `:`)

### Essential vim Commands

```
i           Enter insert mode
Esc         Return to normal mode
:w          Save
:q          Quit
:wq         Save and quit
:q!         Quit without saving

# Navigation (normal mode)
h j k l     Left, down, up, right
gg          Go to first line
G           Go to last line
/pattern    Search forward
n           Next search result

# Editing
dd          Delete line
yy          Copy line
p           Paste
u           Undo
Ctrl+r      Redo
```

### Quick vim Cheatsheet

```bash
vim +42 file.txt        # Open at line 42
vim +/pattern file.txt  # Open at first match
```

---

*Next: [Text Processing (grep, awk, sed) →](../tier-2-data-automation/text-processing.md)*
