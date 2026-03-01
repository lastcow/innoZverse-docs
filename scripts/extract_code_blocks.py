#!/usr/bin/env python3
"""
Extract runnable bash code blocks from markdown lab files.
Skips dangerous commands, prompt examples, and non-executable lines.
"""
import sys
import re

SKIP_PATTERNS = [
    r'\bsudo reboot\b', r'\bshutdown\b', r'\brm -rf /\b',
    r'\bdd if=.*of=/dev/sd\b', r'\bmkfs\b', r'\bfdisk\b',
    r'\bparted\b', r'\b# SKIP\b', r'\biptables -F\b',
    r'\bsystemctl reboot\b', r'\bpoweroff\b',
    r'keepalived', r'pacemaker', r'drbd', r'targetcli',
    r'\bnumactl\b', r'\bperf record\b',
    r'vagrant', r'virsh',
]

# Lines that look like shell prompts or non-commands
SKIP_LINE_PATTERNS = [
    r'^[a-z_]+@[a-z_\-]+:',   # user@host: prompt
    r'<TAB>',                   # tab completion examples
    r'^#.*[Ee]xpected',        # expected output comments
    r'^\s*#\s*Output:',        # output examples
    r'^\s*#\s*Shows ',         # description comments
    r'^\s*#\s*Should ',
    r'^\s*#\s*Prints ',
    r'^\s*#\s*Lists ',
    r'^\s*#\s*Clears ',
    r'^\s*#\s*Shortcut',
    r'^\s*#\s*Or press',
    r'^\s*#\s*Press ',
    r'^\s*#\s*Type ',
    r'^\s*#\s*Auto-complete',
]

def should_skip_line(line):
    stripped = line.strip()
    for pattern in SKIP_LINE_PATTERNS:
        if re.search(pattern, stripped):
            return True
    # Skip bare 'exit' which would kill the script
    if stripped == 'exit':
        return True
    # Skip lines with <TAB> literal
    if '<TAB>' in line:
        return True
    return False

def extract_bash_blocks(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all ```bash ... ``` blocks
    pattern = r'```bash\n(.*?)```'
    blocks = re.findall(pattern, content, re.DOTALL)

    runnable = []
    for block in blocks:
        # Skip if contains dangerous patterns
        skip = False
        for pattern in SKIP_PATTERNS:
            if re.search(pattern, block, re.IGNORECASE):
                skip = True
                break
        if skip:
            continue

        # Filter lines
        lines = []
        for line in block.split('\n'):
            if should_skip_line(line):
                continue
            stripped = line.strip()
            if not stripped:
                continue
            lines.append(line)

        if lines:
            runnable.append('\n'.join(lines))

    if not runnable:
        sys.exit(1)

    print('#!/bin/bash')
    print('set -uo pipefail')
    print()
    for block in runnable:
        print(block)
        print()

if __name__ == '__main__':
    extract_bash_blocks(sys.argv[1])
