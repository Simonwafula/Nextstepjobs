#!/usr/bin/env python3
"""
Script to automatically resolve merge conflicts by choosing the update version
"""
import re
import os

def resolve_conflicts_in_file(filepath, prefer_update=True):
    """
    Resolve merge conflicts in a file by choosing one side
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Check if file has conflicts
    if '<<<<<<< HEAD' not in content:
        return False
    
    print(f"Resolving conflicts in {filepath}")
    
    # Pattern to match conflict blocks
    # This handles both update/main and conflict_030725_1936 patterns
    conflict_pattern = r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> (?:update/main|conflict_030725_1936)'
    
    def replace_conflict(match):
        head_content = match.group(1)
        update_content = match.group(2)
        
        if prefer_update:
            return update_content
        else:
            return head_content
    
    # Resolve conflicts
    resolved_content = re.sub(conflict_pattern, replace_conflict, content, flags=re.DOTALL)
    
    # Write back the resolved content
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(resolved_content)
        print(f"Resolved conflicts in {filepath}")
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False

def main():
    files_with_conflicts = [
        'processors/pipeline2.py',
        'backend/server.py',
        'frontend/src/App.js'
    ]
    
    for filepath in files_with_conflicts:
        if os.path.exists(filepath):
            resolve_conflicts_in_file(filepath, prefer_update=True)
        else:
            print(f"File not found: {filepath}")

if __name__ == "__main__":
    main()