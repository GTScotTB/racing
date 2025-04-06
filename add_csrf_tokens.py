#!/usr/bin/env python
"""
Script to add CSRF tokens to all POST forms in HTML templates.
This helps ensure CSRF protection is properly applied across the application.
"""

import os
import re
from pathlib import Path

def add_csrf_token_to_file(file_path):
    """
    Add CSRF token to all POST forms in a file.
    
    Args:
        file_path: Path to the HTML template file
        
    Returns:
        True if changes were made, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find forms with method="POST" or method="post"
    form_pattern = re.compile(r'<form\s+[^>]*method\s*=\s*["\'](?:POST|post)["\'][^>]*>', re.IGNORECASE)
    form_matches = form_pattern.finditer(content)
    
    # For each form, check if it already has a CSRF token
    original_content = content
    offset = 0
    
    for match in form_matches:
        form_start = match.end() + offset
        
        # Look for CSRF token in the form
        # We'll search from form start to either the </form> tag or 300 characters later
        form_end_match = re.search(r'</form>', content[form_start:form_start+1000])
        if not form_end_match:
            continue  # Skip if we can't find the end of the form
        
        form_content = content[form_start:form_start+form_end_match.start()]
        
        # Check if CSRF token already exists
        if 'csrf_token' in form_content:
            continue  # Skip if CSRF token already exists
        
        # Add CSRF token after form opening tag
        csrf_token_line = '\n    <!-- CSRF token for security -->\n    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
        content = content[:form_start] + csrf_token_line + content[form_start:]
        offset += len(csrf_token_line)
    
    # Write changes back to file if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def scan_directory(base_dir):
    """
    Recursively scan a directory for HTML templates and add CSRF tokens.
    
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
                    if add_csrf_token_to_file(file_path):
                        print(f"Added CSRF token to: {file_path}")
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
    print(f"\nSummary: Added CSRF tokens to {modified} forms")
    
    print("\nNOTE: This script is a helper tool. You should still manually review")
    print("all forms to ensure CSRF protection is properly implemented.")
    print("Forms with non-standard structure may have been missed.") 