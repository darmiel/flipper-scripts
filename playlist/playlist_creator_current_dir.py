# adds all .sub files from the current directory to a playlist file

import os.path
from glob import glob

RECURSIVE = True
IN_FILES = "**/*.sub"
OUT_FILE = "doorbells.txt"

PREFIX = "/ext/subghz/Misc/"

REPLACE = {
    '\\\\': '/',
    '\\': '/',
    # 'sub_files/': ''
}

if __name__ == "__main__":
    with open(OUT_FILE, "w") as f:
        for sub in glob(IN_FILES, recursive=RECURSIVE):
                p = '/'.join(os.path.split(sub))
                for k, v in REPLACE.items():
                    p = p.replace(k, v)
                f.write(f"sub: {PREFIX}{p}\n")
