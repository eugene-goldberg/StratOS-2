#!/usr/bin/env python3
"""
Script to update .dict() to .model_dump() in all affected files
"""
import os
import re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace .dict() with .model_dump() keeping any parameters
    updated_content = re.sub(r'\.dict\(([^)]*)\)', r'.model_dump(\1)', content)
    
    if updated_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

# Files to update
service_files = [
    'backend/services/auth_service.py',
    'backend/services/strategic_foundation_service.py',
    'backend/services/analysis_service.py',
    'backend/services/subjective_input_service.py',
]

updated_files = []
for filepath in service_files:
    abs_filepath = os.path.join('/home/runner/work/StratOS-2/StratOS-2', filepath)
    if os.path.exists(abs_filepath):
        if update_file(abs_filepath):
            updated_files.append(filepath)
            print(f"Updated {filepath}")
    else:
        print(f"File not found: {filepath}")

print(f"\nUpdated {len(updated_files)} files.")