"""
Produces GitHub-Markdown friendly output for GitHub Actions
$ python3 github_format.py file_1.ir file_2.ir file_3.ir ... file_n.ir
"""

import sys

from lint import check_file, create_mark_underline
from lint import Result

def callback():
    headers = [] # used to check if the file already has a header
    def inner(file_path: str, lnr: int, line: str, result: Result):
        if not file_path in headers:
            headers.append(file_path)
            print(f"## `🐛 {file_path}`")
        else:
            print("\n---\n") # separator
        
        print("```diff")

        # print line number
        print(f"# Line {lnr}:")
        print(f"- {line}")
        print(" ", create_mark_underline(len(line), result.marks))
        print(f"@@ {result.error} @@")

        print("```")
        if result.suggestion is not None:
            print(f"> **Note**(**suggested**): `{result.suggestion}`")
    return inner

if __name__ == "__main__":
    gh_callback = callback()

    # proxy callback so we can intercept when an error/warning occurrs
    any_error = False
    def proxy_callback(file_path: str, lnr: int, line: str, result: Result):
        global any_error
        any_error = True
        gh_callback(file_path, lnr, line, result)

    for file in sys.argv[1:]:
        with open(file, "r", encoding='UTF-8') as fd:
            check_file(file, fd, proxy_callback)
    
    if any_error:
        sys.exit("\nlinter found errors")
