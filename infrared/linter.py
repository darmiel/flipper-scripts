"""
roughly checks an .ir file for errors.
no warranty.
"""

from io import TextIOWrapper
import re

EXIT_NONE = 0
EXIT_CURRENT_LINE = 1
EXIT_ALL_LINES = 2
EXIT_CURRENT_CHECK_FOR_ALL_LINES = 3

class Check:
    def __init__(self) -> None:
        self.active = True

    def check(self, lnr: int, line: str) -> list:
        pass
    
    def set_active(self, active: bool):
        self.active = active
    
    def is_active(self) -> bool:
        return self.active

    def exit_rule(self) -> int:
        return EXIT_NONE

class WhiteSpaceCheck(Check):
    """
    checks for whitespace at the end of a line
    """
    def __init__(self) -> None:
        super().__init__()
        self.pattern = re.compile("^[^\s].*[^\s]$")
    
    def check(self, _: int, line: str) -> list:
        if not self.pattern.match(line):
            return [len(line) - 1, "lines cannot start or end with whitespace"]
        return []

class DescriptorCheck(Check):
    """
    checks first two lines for expected .ir header
    """
    def __init__(self) -> None:
        super().__init__()
        self.version_pattern = re.compile(r"^Version:\s\d+$")
    
    def check(self, lnr: int, line: str) -> list:
        if lnr == 1 and line != "Filetype: IR signals file":
            return [0, len(line), "expected 'Filetype: IR signals file' in first line"]
        elif lnr == 2 and not self.version_pattern.match(line):
            return [0, len(line), "expected 'Version: \d' in second line"]
        return []

class NonASCIICheck(Check):
    def __init__(self) -> None:
        super().__init__()
        self.pattern = re.compile(r"[^\x20-\x7E]")
    
    def check(self, lnr: int, line: str) -> list:
        resp = self.pattern.search(line)
        if resp is None:
            return []
        span = resp.span()
        return [span[0], span[1], "non-ASCII character found"]

class KeyValueValidityCheck(Check):
    def __init__(self) -> None:
        super().__init__()
        self.pattern_str = r"^([A-Za-z-_]+):\s.+$"
        self.pattern = re.compile(self.pattern_str)
        self.valid_keys = [
            "Filetype", "Version", # header
            "name", "type", "protocol", "address", "command", # parsed signal
            "frequency", "duty_cycle", "data" # raw signal
        ]

    def check(self, lnr: int, line: str) -> list:
        # parse key
        if not ':' in line:
            return [0, len(line), "line is no key-value pair"]
        if not self.pattern.match(line):
            return [0, len(line), f"key-value pattern does not match '{self.pattern_str}'"]
        key = line[:line.index(":")]
        if not key in self.valid_keys:
            return [0, len(key), "key unknown"]
        return []
        
    def force_exit(self) -> int:
        return EXIT_CURRENT_LINE

class SignalKeyOrderCheck(Check):
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

    def exit_rule(self) -> int:
        return EXIT_CURRENT_CHECK_FOR_ALL_LINES

    def check(self, _: int, line: str) -> list:
        key, value = line.split(": ", 2)

        if key in self.ignored_order_keys:
            return []
        
        key_end = line.index(": ")
        value_start = key_end + 2

        if not key in self.order:
            return [0, key_end, "key not in order"]

        if self.expected_key is None:
            self.expected_key = "name"
        
        if type(self.expected_key) is list:
            if not key in self.expected_key:
                return [0, key_end, f"one of keys '{', '.join(self.expected_key)}' expected"]
        else:
            if key != self.expected_key:
                return [0, key_end, f"key '{self.expected_key}' expected"]
        
        next_expected = self.order[key]
        if type(next_expected) is str or type(next_expected) is list:
            self.expected_key = next_expected
        elif type(next_expected) is dict:
            if not value in next_expected:
                return [value_start, len(line), f"if-order value didn't match any of [{', '.join(next_expected.keys())}]"]
            self.expected_key = next_expected[value]
        else:
            return [0, key_end, "something weird happened. Please create an issue on GitHub"]

###

def check_file(fd: TextIOWrapper) -> str:
    """
    checks a file for errors
    """
    normal_checks = [
        WhiteSpaceCheck(), 
        DescriptorCheck(), 
        NonASCIICheck(), 
        KeyValueValidityCheck(), 
        SignalKeyOrderCheck()
    ]
    comment_checks = []

    for _lnr, line in enumerate([z.strip("\n") for z in fd.readlines()]):
        lnr = _lnr + 1 # human readable line numbers

        # print(lnr, line)
        # comments
        if line.startswith("#"):
            checks = comment_checks
        else:
            checks = normal_checks
        
        for check in [z for z in checks if z.is_active()]:
            resp = check.check(lnr, line)
            if resp is None or len(resp) == 0:
                continue # check did pass
            
            if type(resp) is list:
                if len(resp) == 3:
                    mark_from, mark_to, message = resp
                elif len(resp) == 2:
                    mark_from, message = resp
                    mark_to = mark_from + 1
                else:
                    return f"INVALID CHECK @ {check}"
            else:
                message = resp
                mark_from, mark_to = None, None

            print()
            print(f"error at line {lnr}: {message}")
            print(line)
            if mark_from is not None:
                print(f"{' ' * (mark_from)}{'^'*(mark_to - mark_from)}")
            
            exit_rule = check.exit_rule()
            if exit_rule == EXIT_ALL_LINES:
                return message
            elif exit_rule == EXIT_CURRENT_LINE:
                break
            elif exit_rule == EXIT_CURRENT_CHECK_FOR_ALL_LINES:
                check.set_active(False)
                break

    return ""



if __name__ == "__main__":
    with open("test.ir", "r") as fd:
        check_file(fd)