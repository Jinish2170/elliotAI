import ast
import glob
import sys

for f in glob.glob('veritas/**/*.py', recursive=True):
    try:
        content = open(f, 'r', encoding='utf-8').read()
        tree = ast.parse(content)
        uses_os = any(isinstance(n, ast.Name) and n.id == 'os' for n in ast.walk(tree))
        imports_os = any(
            isinstance(n, ast.Import) and any(alias.name == 'os' for alias in n.names)
            for n in ast.walk(tree)
        )
        if uses_os and not imports_os:
            print(f'File missing import os: {f}')
    except Exception as e:
        pass
