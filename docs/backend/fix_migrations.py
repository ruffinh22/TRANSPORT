#!/usr/bin/env python3
import os
import re
from pathlib import Path

def fix_check_constraints(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    count = content.count('condition=models.Q(')
    
    if count > 0:
        new_content = content.replace('condition=models.Q(', 'check=models.Q(')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return count
    return 0

backend_path = Path('.')
total = 0
for migration_file in backend_path.glob('apps/*/migrations/*.py'):
    if migration_file.name != '__init__.py':
        count = fix_check_constraints(migration_file)
        if count > 0:
            total += count
            print(f"✓ {migration_file}: {count} correction(s)")

print(f"\n✅ Total: {total} CheckConstraint(s) corrigé(s)")
