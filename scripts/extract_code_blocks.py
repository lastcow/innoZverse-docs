#!/usr/bin/env python3
"""
Extract runnable bash code blocks from markdown lab files.
Skips blocks containing dangerous commands.
"""
import sys
import re

SKIP_PATTERNS = [
    r'\bsudo reboot\b', r'\bshutdown\b', r'\brm -rf /\b',
    r'\bdd if=.*of=/dev/sd\b', r'\bmkfs\b', r'\bfdisk\b',
    r'\bparted\b', r'\b# SKIP\b', r'\biptables -F\b',
    r'\bsystemctl reboot\b', r'\bpoweroff\b',
    r'keepalived', r'pacemaker', r'drbd', r'targetcli',
    r'haproxy.*backend', r'numactl', r'perf record',
    r'vagrant', r'virsh',
]

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
            
        # Remove comment-only lines and expected output markers
        lines = []
        for line in block.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            # Skip lines that look like expected output (no command chars)
            if stripped.startswith('#') and not stripped.startswith('#!/'):
                continue
            lines.append(line)
        
        if lines:
            runnable.append('\n'.join(lines))
    
    if not runnable:
        sys.exit(1)
    
    print('#!/bin/bash')
    print('set -euo pipefail')
    print()
    for block in runnable:
        print(block)
        print()

if __name__ == '__main__':
    extract_bash_blocks(sys.argv[1])
