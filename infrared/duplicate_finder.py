import sys
sys.path.insert(0, '..') # ugly ass hack :/

import math

from glob import glob
from typing import List

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir

####################################################################################################

INPUT_FILES = "input_files/AC.ir"
DB_FILES = "Flipper-IRDB-official/**/*.ir"
SILENT_MODE = True

####################################################################################################

class IRDBFile:
    def __init__(self, path) -> None:
        self.path = path
        self.hashes = {}
        self.count = 0

    def load(self):
        # load signal hashes
        with FlipperFormat(self.path) as fff:
            signals = read_ir(fff)
            for signal in signals:
                self.count += 1
                h = hash(signal)
                if h not in self.hashes:
                    self.hashes[h] = []
                self.hashes[h].append(signal.name)

def create_progress_bar(percentage: float, width: int = 30, symbol: str = "#") -> str:
    count = min(width, math.ceil(percentage * width))
    return f"[{symbol*count}{' '*(width-count)}] ({round(percentage*100)} %)"

def create_distribution(percentage: float, width: int = 30, symbol: str = "#") -> str:
    count = min(width, math.ceil(percentage * width))
    return symbol*count

def check(db: List[IRDBFile], path: str) -> bool:
    # parse signals in current file
    with FlipperFormat(path) as fff:
        signals = [z for z in read_ir(fff)]
    signals_len = len(signals)
    
    found_any = False
    for data in db:
        # ignore self
        if data.path == path:
            continue

        # find similar signals in file
        
        # iterate over signals in current file
        # {current} -> {checking file}

        # common: same signal in both files
        # checked_only: signals only in checking file
        # checking_only: signals only in checked file
        common, input_only, checked_only = {}, {}, {}
        common_count, input_count, checked_count = 0, 0, 0

        """
        common   [both]: { hash -> [POWER OFF, [POWER ON]] }
        left [checking]: { hash -> FANS ON }
        right [checked]: { hash -> FANS OFF }
        """
        for input_signal in signals:
            input_signal_hash = hash(input_signal)
            if input_signal_hash in data.hashes:
                # both files have the same signal
                common[input_signal_hash] = [input_signal.name, data.hashes[input_signal_hash]]
                common_count += 1
            else:
                # the input file has a signal more
                input_only[input_signal_hash] = input_signal.name
                input_count += 1
        for checked_signal_hash, checked_signal_name in data.hashes.items():
            if not checked_signal_hash in common:
                # the checked file has a signal more
                checked_only[checked_signal_hash] = checked_signal_name
                checked_count += 1
        
        # confidence from 0.0 to 1.0 that the checking signals match the file
        # even if the checked file contains less signals, the confidence can be 1.0.
        common_confidence = common_count / data.count

        # percentage how many new signals from input file to checked file
        # if the input file contains 4 signals and the checked file only contains 3,
        # the checking_balance would be 0.25 if the other 3 signals matche
        input_balance = input_count / data.count

        # percentage how many new signals from checked file to checking file
        # see above.
        checked_balance = checked_count / signals_len

        # confidence from 0.0 to 1.0 that both the checking file and checked file 
        # have the same amounts of signals
        balance_confidence = min(data.count, signals_len) / max(data.count, signals_len)

        # example output
        # TODO: yes make this output pretty :)
        """
        Flipper-IRDB-official\AC.ir | [##############################] (100 %) signals match        ┐
          :: BAL: [=============] 96 % | +++ (adds 12 signals, 4 %) - (misses 4 signals, 7 %)       |
        ┌────────────────────────────┬──────────────────────┬──────────────────────┬────────────────┘
        ├ ◙ POWER OFF ◄► ○ POWER OFF | ○ + POWER OFF        | ◙ - POWER OFF        |
        ├ ◙ TEMP+     ◄► ○ TEMP+     | ○ + TEMP+            | ◙ - TEMP+            |
        ├ ◙ TEMP-     ◄► ○ TEMP-     | ○ + TEMP-            | ◙ - TEMP-            |
        └─ ... and 14 more ... ──────┴─ ... and 9 more ... ─┴─ ... and 1 more ... ─┘
        """

        if common_confidence >= .8 and balance_confidence >= .8:
            # print file name
            if not found_any:
                print()
                print(f"## `{path}`")
                print()
                print("```")
            else:
                print()
                print("---")
                print()

            line_header = f"{data.path} | {create_progress_bar(common_confidence)} signals match"
            line_balance = f"  :: BAL: {create_progress_bar(balance_confidence, width=14, symbol='=')} | " + \
                f"[{create_distribution(checked_balance * 3, width=10, symbol='+')}] (adds {checked_count} signals, {round(checked_balance * 100)}%/input) " + \
                f"[{create_distribution(input_balance * 3, width=10, symbol='-')}] (misses {input_count} signals, {round(input_balance * 100)}%/checked)"
            
            max_line = max(len(line_header), len(line_balance)) + 1
            line_header += ' ' * (max_line - len(line_header)) + "┐"
            line_balance += ' ' * (max_line - len(line_balance)) + "|"

            print(line_header)
            print(line_balance)

            # print first separator
            print(f"┌{'─' * (len(line_header) - 2)}┘")
            print(f"├ [+ adds: {', '.join(['/'.join(v) for _, v in checked_only.items()])}] [- misses: {', '.join(input_only.values())}]")

            max_print_count = 3
            print_count = 0

            # print common
            print_count = 0
            for _, cn in common.items():
                print_count += 1
                if print_count > max_print_count:
                    print("└─ ... and", len(common) - max_print_count, "more common signals ...")
                    break
                print(f"├ ◙ {cn[0]} ◄► ○ {', '.join(cn[1])}")

            found_any = True
    if found_any:
        print("```")
    return found_any

def create_database() -> List[IRDBFile]:
    res = []
    for ir in glob(DB_FILES, recursive=True):
        if not SILENT_MODE: print("[DB] Loading", ir)
        irdb = IRDBFile(ir)
        irdb.load()
        res.append(irdb)
    return res

if __name__ == "__main__":
    if not SILENT_MODE: print("[db] Reading database ...")
    db = create_database()
    if not SILENT_MODE: 
        print("  [db] done!")
        print()

    input_files = []
    for arg in sys.argv[1:]:
        if arg.startswith("glob:"):
            input_files.extend(glob(arg[5:], recursive=True))
        elif arg.startswith("file:"):
            with open(arg[5:], "r") as fd:
                input_files.extend([z.strip() for z in fd.readlines()])
        else:
            input_files.append(arg)

    found_any = False
    for file in input_files:
        if check(db, file):
            found_any = True
