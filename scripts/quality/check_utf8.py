# -*- coding: utf-8 -*-
"""
Verifica headers UTF-8 em arquivos Python.

Usado pelo pre-commit hook.
"""

import sys
from pathlib import Path


def main() -> int:
    """Verifica todos os arquivos Python em src/."""
    errors = []

    for py_file in Path('src').rglob('*.py'):
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')[:3]

        if not any('# -*- coding: utf-8 -*-' in line for line in lines):
            if py_file.name != '__init__.py' or len(content) > 500:
                errors.append(str(py_file))

    if errors:
        print(f'\n🚨 Missing UTF-8 header in {len(errors)} files:')
        for error in errors[:10]:
            print(f'  - {error}')
        if len(errors) > 10:
            print(f'  ... and {len(errors) - 10} more')
        print('\nAdd at the top of each file:')
        print('# -*- coding: utf-8 -*-')
        return 1

    print('✅ UTF-8 headers OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
