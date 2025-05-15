#!/usr/bin/env python3
"""
This program creates a tags file for help text.

Usage: doctags *.txt ... >tags

In this context, a tag is an identifier between stars, e.g. *c_files*
"""

import sys
from pathlib import Path
from typing import TextIO

def process_file(file_handle: TextIO, filename: str) -> None:
    """
    Process a single file and generate tags.
    Skip sections that are examples (marked by lines ending with '>' or ' >').
    """
    in_example = False
    
    for line in file_handle:
        # Handle example sections
        if in_example:
            if not (line[0].isspace() or line[0] == '\n'):
                in_example = False
            else:
                continue
                
        # Check for start of example section
        stripped = line.rstrip()
        if stripped.endswith('>') and (stripped == '>' or stripped.endswith(' >')):
            in_example = True
            continue

        # Find tags using the same logic as the C program
        pos = 0
        while True:
            # Find first '*'
            start = line.find('*', pos)
            if start == -1:
                break

            # Find second '*'
            end = line.find('*', start + 1)
            if end == -1 or end <= start + 1:
                pos = start + 1
                continue

            tag = line[start+1:end]
            
            # Validate tag - no spaces, tabs, or vertical bars
            if ' ' in tag or '\t' in tag or '|' in tag:
                pos = start + 1
                continue

            # Check whitespace before and after tag
            valid_start = start == 0 or line[start-1].isspace()
            valid_end = end + 1 >= len(line) or line[end+1].isspace()
            
            if valid_start and valid_end:
                # Escape backslashes and forward slashes
                escaped_tag = tag.replace('\\', '\\\\').replace('/', '\\/')
                print(f"{tag}\t{filename}\t/*{escaped_tag}*")

            pos = end + 1

def main() -> None:
    """Process command line arguments and handle file operations."""
    if len(sys.argv) <= 1:
        print("Usage: doctags docfile ... >tags", file=sys.stderr)
        sys.exit(1)

    print("help-tags\ttags\t1")
    
    for filepath in map(Path, sys.argv[1:]):
        try:
            with filepath.open('r', encoding='utf-8') as f:
                process_file(f, str(filepath))
        except IOError as e:
            print(f"Unable to open {filepath} for reading", file=sys.stderr)

if __name__ == "__main__":
    main() 