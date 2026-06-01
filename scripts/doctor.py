from __future__ import annotations
import importlib.util
import platform
import sys
from pathlib import Path

print('Roomies Doctor')
print('Python:', sys.version)
print('Platform:', platform.platform())
print('Project:', Path.cwd())

packages = ['flask', 'sqlalchemy', 'psycopg', 'pymysql', 'boto3', 'PIL']
missing = []
for name in packages:
    if importlib.util.find_spec(name) is None:
        missing.append(name)
    print(f'{name}:', 'OK' if name not in missing else 'MISSING')

if missing:
    print('\nMissing packages found. Run:')
    print('python -m pip install --upgrade pip setuptools wheel')
    print('python -m pip install -r requirements.txt')
else:
    print('\nAll important packages are installed.')
