#!/usr/bin/env python
"""
Script to fix CSRF token syntax in HTML templates.
Changes {{ csrf_token() }} to {{ csrf_token }} since it's a string, not a callable.
"""

import os
import re
from pathlib import Path

def fix_csrf_syntax_in_file(file_path):
    """
    Fix CSRF token syntax in a file, changing {{ csrf_token() }} to {{ csrf_token }}.
    
    Args:
        file_path: Path to the HTML template file
        
    Returns:
        True if changes were made, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find instances of {{ csrf_token() }}
    pattern = re.compile(r'value\s*=\s*"\{\{\s*csrf_token\(\)\s*\}\}"')
    
    # Replace with {{ csrf_token }}
    new_content = pattern.sub(r'value="{{ csrf_token }}"', content)
    
    # Check if changes were made
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    
    return False

def scan_directory(base_dir):
    """
    Recursively scan a directory for HTML templates and fix CSRF syntax.
    
    Args:
        base_dir: Base directory to scan
        
    Returns:
        Counter of files modified
    """
    files_modified = 0
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                try:
                    if fix_csrf_syntax_in_file(file_path):
                        print(f"Fixed CSRF syntax in: {file_path}")
                        files_modified += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return files_modified

if __name__ == "__main__":
    templates_dir = Path('templates')
    
    if not templates_dir.exists():
        print(f"Error: Templates directory '{templates_dir}' not found.")
        exit(1)
    
    print(f"Scanning templates in: {templates_dir}")
    modified = scan_directory(templates_dir)
    print(f"\nSummary: Fixed CSRF syntax in {modified} templates") 