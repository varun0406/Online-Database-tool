import os
import re

project_dir = '.'  # Set to your project root
imports = set()

for root, dirs, files in os.walk(project_dir):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file), encoding='utf-8') as f:
                for line in f:
                    # Match both 'import x' and 'from x import y'
                    match = re.match(r'\s*(import|from)\s+([a-zA-Z0-9_\.]+)', line)
                    if match:
                        lib = match.group(2).split('.')[0]
                        # Exclude your own package and standard library (optional)
                        if lib not in ('Codes', '__future__', 'os', 'sys', 're', 'csv', 'time', 'threading', 'datetime', 'tkinter', 'importlib', 'concurrent', 'builtins'):
                            imports.add(lib)
                        # Always include these if you want to be sure
                        if lib in ('selenium', 'tkinter'):
                            imports.add(lib)

print('Required libraries:')
for lib in sorted(imports):
    print(lib)