#!/usr/bin/env python3
import glob, os
cwd = os.getcwd()
files = glob.glob(cwd + "/backend/alembic/*.py")
print("Files:", files)
for f in files:
    c = open(f).read()
    old = """if config.config_ file_ name is not None:
    fileConfig( config. config_ file_ name)

from app."""
    new = """from app."""
    if old in c:
        c = c.replace(old, new)
        open(f, "w").write(c)
        print("Patched:", f)
    else:
        # Try alternate spacing
        old2 = 'if config.config_file_name is not None:\n    fileConfig(config.config_file_name)\n\nfrom app.'
        if old2 in c:
            c = c.replace(old2, new)
            open(f, "w").write(c)
            print("Patched alt:", f)
        else:
            print("Not found in:", f)
            for l in c.split("\n")[:8]:
                print(repr(l))