"""
roughly checks an .ir file for errors.
no warranty.
"""

import re
import sys

from io import TextIOWrapper
from typing import List
from difflib import get_close_matches

EXIT_NONE = 0
EXIT_CURRENT_LINE = 1
EXIT_ALL_LINES = 2
EXIT_CURRENT_CHECK_FOR_ALL_LINES = 3

###

class Mark:
    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end
    
    def fix(self, line: str) -> None:
        if self.start == -1:
            self.start = len(line)
        if self.end == -1:
            self.end = len(line)

def create_mark_underline_array(length: int, marks: List[Mark], symbol='^') -> List[str]:
    res = [' '] * length
    for m in marks:
        if len(res) <= m.end:
            res.extend([' '] * (m.end - len(res)))
        for i in range(m.end - m.start):
            res[m.end - i - 1] = symbol
    return res

def create_mark_underline(length: int, marks: List[Mark]) -> str:
    return ''.join(create_mark_underline_array(length, marks))

###

class Result:
    def __init__(self, exit_rule: int, marks: List[Mark], error: str, suggestion: str) -> None:
        self.exit_rule = exit_rule
        self.marks = marks
        self.error = error
        self.suggestion = suggestion

    def update(self, line: str):
        for mark in self.marks:
            mark.fix(line)

    def with_exit_rule(self, exit_rule: int) -> 'Result':
        self.exit_rule = exit_rule
        return self

def multi_mark_result(marks: List[Mark], error: str, suggestion: str = None) -> Result:
    return Result(-1, marks, error, suggestion)

def single_mark_result(mark_from: int, mark_to: int, error: str, suggestion: str = None) -> Result:
    return multi_mark_result([Mark(mark_from, mark_to)], error, suggestion)

def single_mark_result_from(mark_from: int, error: str, suggestion: str = None) -> Result:
    return single_mark_result(mark_from, -1, error, suggestion)

def single_mark_result_to(mark_to: int, error: str, suggestion: str = None) -> Result:
    return single_mark_result(0, mark_to, error, suggestion)

###

class Context:
    def __init__(self) -> None:
        self.result = {}
        self.last_key = None
    
    def update_result(self, check: type, result: Result) -> None:
        self.result[check] = result

    def did_check_fail(self, check: type) -> bool:
        return check in self.result
    
    def set_last_key(self, key: str) -> None:
        self.last_key = key

###

class Check:
    def __init__(self) -> None:
        self.active = True

    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        """
        check {line} against current check
        """
        pass

    def ignore_if_failed() -> list:
        """
        do not run this check if one of the returned checks failed
        """
        pass
    
    def set_active(self, active: bool):
        self.active = active
    
    def is_active(self) -> bool:
        return self.active

class EmptyLineCheck(Check):
    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        if len(line.strip()) == 0:
            return single_mark_result(0, 1, "empty lines are not allowed. use comments for separation", suggestion="#") \
                .with_exit_rule(EXIT_CURRENT_LINE)
        return None
    
class WhiteSpaceCommentCheck(Check):
    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        if line.strip().startswith("#") and not line.startswith("#"):
            return single_mark_result_to(line.index("#"), "white space before comment not allowed", suggestion=line.strip()) \
                .with_exit_rule(EXIT_CURRENT_LINE)
        return None
    
class WhiteSpaceCheck(Check):
    """
    checks for whitespace at the end of a line
    'name: test '
               ^
    """
    def __init__(self) -> None:
        super().__init__()
        self.start_pattern = re.compile(r"^([\s]+)")
        self.end_pattern = re.compile(r"([\s]+)$")
        self.multi_space_pattern = re.compile("\s{2,}")
    
    def ignore_if_failed() -> list:
        return [WhiteSpaceCommentCheck]

    def check(self, ctx: Context, _: int, line: str) -> Result:
        # start of line
        res = self.start_pattern.findall(line)
        if len(res) > 0:
            return single_mark_result_to(len(res[0]), "lines cannot start with spaces", suggestion=line.lstrip(' '))
        # end of line
        res = self.end_pattern.findall(line)
        if len(res) > 0:
            return single_mark_result_from(len(line) - len(res[0]), "lines cannot end with spaces", suggestion=line.rstrip(' '))
        # check using 'strip'
        if line.strip() != line:
            return single_mark_result_from(0, "lines cannot start or end with whitespace", suggestion=line.strip())
        # multi space check
        res = []
        for search in self.multi_space_pattern.finditer(line):
            span = search.span()
            res.append(Mark(span[0], span[1]))
        if len(res) > 0:
            suggestion = line
            while '  ' in suggestion:
                suggestion = suggestion.replace('  ', ' ')
            return multi_mark_result(res, "lines cannot contain double spaces", suggestion=suggestion)
        # all fine :)
        return None

class DescriptorCheck(Check):
    """
    checks first two lines for expected .ir header
    """
    def __init__(self) -> None:
        super().__init__()
        self.version_pattern = re.compile(r"^Version:\s\d+$")
    
    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        if lnr == 1 and line != "Filetype: IR signals file":
            return single_mark_result_from(0, "first line must contain 'Filetype: IR signals file'", suggestion='Filetype: IR signals file')
        elif lnr == 2 and not self.version_pattern.match(line):
            return single_mark_result_from(0, "second line must contain 'Version: \d'", suggestion='Version: 1')
        return None

class NonASCIICheck(Check):
    """
    checks a line for non-ASCII characters
    """
    def __init__(self) -> None:
        super().__init__()
        self.pattern = re.compile(r"[^\x20-\x7E]")
    
    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        resp = []
        for search in self.pattern.finditer(line):
            span = search.span()
            resp.append(Mark(span[0], span[1]))
        if len(resp) > 0:
            suggestion = ''.join(self.pattern.split(line))
            # if we remove non-ASCII chars there's probably some double spaces ['  ']
            while '  ' in suggestion:
                suggestion = suggestion.replace('  ', ' ')
            return multi_mark_result(resp, "non-ASCII character/s found", suggestion=suggestion)
        return None

class KeyValueValidityCheck(Check):
    """
    checks if an .ir file only contains valid key-value pairs
    'test: abc'
     ^^^^

    'test:abc'
     ^^^^^^^^
    """
    def __init__(self) -> None:
        super().__init__()
        self.pattern_str = r"^([A-Za-z-_]+):\s.+$"
        self.pattern = re.compile(self.pattern_str)
        self.valid_keys = [
            "Filetype", "Version", # header
            "name", "type", "protocol", "address", "command", # parsed signal
            "frequency", "duty_cycle", "data" # raw signal
        ]

    def ignore_if_failed() -> list:
        """
        do not check if line 1 or 2 are not vaild
        """
        return [DescriptorCheck]

    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        # parse key
        if not ':' in line:
            return single_mark_result_from(0, "line is no key-value pair. 'key: value' expected") \
                .with_exit_rule(EXIT_CURRENT_LINE)
        
        # check that value starts witih ' '
        # 'name:value' should be 'name: value'
        value_start_index = line.index(":") + 1
        if not line[value_start_index:].startswith(' '):
            # error but don't stop processing current line
            return single_mark_result(
                value_start_index - 1, value_start_index, "space missing after ':'", 
                suggestion=line[:value_start_index] +" " + line[value_start_index:]
            )

        # check generic pattern
        if not self.pattern.match(line):
            return single_mark_result_from(0, f"key-value pattern does not match expression '{self.pattern_str}'")

        # check if key is valid
        key = line[:line.index(":")]
        if not key in self.valid_keys:
            # find best similar key
            similar = get_close_matches(key, self.valid_keys)
            suggestion = None
            if len(similar) > 0:
                suggestion = f"{similar[0]}:{line[value_start_index:]}"
            return single_mark_result_to(len(key), f"key '{key}' unknown", suggestion=suggestion).with_exit_rule(EXIT_NONE)
        
        ctx.set_last_key(key)
        return None
        
class SignalKeyOrderCheck(Check):
    """
    since the order of the key-value pairs is important, the order is checked here.
    `name` must always be followed by `type`, `protocol` by `address` and so on.
    otherwise there will be problems
    """
    def __init__(self) -> None:
        super().__init__()
        self.ignored_order_keys = [
            "Filetype", "Version"
        ]
        self.value_space_pattern = re.compile("^[\s]{3,}")
        self.expected_key = None
        self.order = {
            "name": "type",
            "type": {
                "parsed": "protocol",
                "raw": "frequency"
            },
            
            "protocol": "address",
            "address": "command",
            "command": "name",

            "frequency": "duty_cycle",
            "duty_cycle": "data",
            "data": ["data", "name"]
        }

    def check(self, ctx: Context, lnr: int, line: str) -> Result:
        split = line.split(":", 2)
        if len(split) != 2:
            return single_mark_result_from(0, "cannot unpack key-value")
        key, value = split
        key, value = key.strip(), value.strip()

        if key in self.ignored_order_keys:
            return None
        
        key_end = line.index(":")
        
        value_start = key_end + 1
        for c in line[key_end + 1:]:
            if c == ' ':
                value_start += 1
            else:
                break

        if not key in self.order:
            return single_mark_result_to(key_end, "key has no order-rule") \
                .with_exit_rule(EXIT_CURRENT_CHECK_FOR_ALL_LINES)

        # always start order-search with "name"
        if self.expected_key is None:
            self.expected_key = "name"
        
        if type(self.expected_key) is list:
            if not key in self.expected_key:
                return single_mark_result_to(key_end, f"one of keys '{', '.join(self.expected_key)}' expected") \
                    .with_exit_rule(EXIT_CURRENT_CHECK_FOR_ALL_LINES)
        else:
            if key != self.expected_key:
                return single_mark_result_to(
                    key_end, f"key '{self.expected_key}' expected", 
                    suggestion=f"{self.expected_key}: ..."
                ).with_exit_rule(EXIT_CURRENT_CHECK_FOR_ALL_LINES)
        
        next_expected = self.order[key]
        if type(next_expected) is str or type(next_expected) is list:
            self.expected_key = next_expected
        elif type(next_expected) is dict:
            if not value in next_expected:
                return single_mark_result_from( value_start, f"[check-error]: can't find next expected key in [{', '.join(next_expected.keys())}]") \
                    .with_exit_rule(EXIT_CURRENT_CHECK_FOR_ALL_LINES)
            self.expected_key = next_expected[value]
        else:
            return single_mark_result_to(key_end, "[check-error]: something weird happened. Please create an issue on GitHub.") \
                .with_exit_rule(EXIT_CURRENT_CHECK_FOR_ALL_LINES)
        
        return None

###

def check_file(file_path: str, fd: TextIOWrapper, on_found = None) -> bool:
    """
    checks a file for errors
    """

    # these checks are applied to "normal" lines
    normal_checks = [
        EmptyLineCheck(),
        WhiteSpaceCommentCheck(),
        WhiteSpaceCheck(), 
        DescriptorCheck(), 
        NonASCIICheck(), 
        KeyValueValidityCheck(), 
        SignalKeyOrderCheck(),
    ]

    # these checks are applied to commented lines
    comment_checks = [
        NonASCIICheck(),
    ]

    did_pass = True
    context = Context()

    for _lnr, line in enumerate([z.strip("\n") for z in fd.readlines()]):
        lnr = _lnr + 1 # human readable line numbers

        # comments
        if line.startswith("#"):
            checks = comment_checks
        else:
            checks = normal_checks
        
        for check in [z for z in checks if z.is_active()]:
            # check if check is disabled because a previous check failed
            if type(check.ignore_if_failed) is list and type(check) in check.ignore_if_failed:
                continue

            # execute check
            resp: Result = check.check(context, lnr, line)

            # if check passed, do nothing
            if resp is None:
                continue
            elif type(resp) is not Result:
                print("[lint-error] result of response was not Result for check", type(check))
                continue
            else:
                did_pass = False

            # add line number to result and fix markers
            resp.update(line)

            # cache check result
            context.update_result(type(check), resp)

            # pass result to callback
            on_found(file_path, lnr, line, resp)
            
            if resp.exit_rule == EXIT_ALL_LINES:
                # cancel all other checks for all other lines
                return did_pass
            elif resp.exit_rule == EXIT_CURRENT_LINE:
                # cancel all other checks for current line
                break
            elif resp.exit_rule == EXIT_CURRENT_CHECK_FOR_ALL_LINES:
                # cancel current check for all other lines
                check.set_active(False)
                break

    return did_pass


if __name__ == "__main__":
    total_count = 0

    # change the output format here
    from lint_simple_format import result_simple_output
    error_callback = result_simple_output()

    for file in sys.argv[1:]:
        header = f"[lint] checking '{file}'"
        print('*'*len(header))
        print(header)

        count = 0
        with open(file, "r", encoding='UTF-8') as fd:

            # proxy callback to count warnings
            def proxy_callback(file_path: str, lnr: int, line: str, result: Result):
                global count, total_count
                count += 1
                total_count += 1

                # pass callback to second-level callback
                error_callback(file_path, lnr, line, result)

            res = check_file(file, fd, proxy_callback)

        print(f"[lint] found {count} warnings/errors in file.")
        print('*'*len(header))
        print()
    
    print(f"[lint] found a total of {total_count} warnings/errors")

    if total_count != 0:
        sys.exit('[lint] found warnings/errors')
    exit(0 if total_count == 0 else 1)
