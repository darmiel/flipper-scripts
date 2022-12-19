import sys
sys.path.insert(0, '..') # ugly ass hack :/

import math

from glob import glob
from typing import List

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir
from fsc.flipper_format.bulk import parse_all_ir_unique, write_all_ir_ir, write_all_ir_json

####################################################################################################

INPUT_FILES = "input_files/AC.ir"
DB_FILES = "Flipper-IRDB-official/**/*.ir"

####################################################################################################

class IRDBFile:
    def __init__(self, path) -> None:
        self.path = path
        # load signal hashes
        self.hashes = {}
        self.count = 0
        with FlipperFormat(path) as fff:
            signals = read_ir(fff)
            for signal in signals:
                self.count += 1
                h = hash(signal)
                if h not in self.hashes:
                    self.hashes[h] = []
                self.hashes[h].append(signal.name)

    def get_matching_signal_names(self, hashed_signal) -> List[str]:
        if hashed_signal in self.hashes:
            return self.hashes[hashed_signal]
        return []
    
    def get_all_matched_signal_names(self, hashed_signals) -> dict:
        res = {}
        for hs in hashed_signals:
            res = self.get_matching_signal_names(hs)
            if len(res) > 0:
                res[hs] = res
        return res

def create_database() -> List[IRDBFile]:
    res = []
    for ir in glob(DB_FILES, recursive=True):
        print("[DB] Loading", ir)
        irdb = IRDBFile(ir)
        res.append(irdb)
    return res

def create_progress_bar(percentage: float, width: int = 30) -> str:
    count = math.ceil(percentage * width)
    return f"[{'#'*count}{' '*(width-count)}] {round(percentage*100)}%"


def check(db: List[IRDBFile], path: str) -> None:
    # parse signals in current file
    with FlipperFormat(path) as fff:
        signals = [z for z in read_ir(fff)]
    
    for d in db:
        total_signal_count = d.count
        # find similar signals in file
        
        # iterate over signals in current file
        # {current} -> {checking file}
        similars = {}
        for signal in signals:
            similar = d.get_matching_signal_names(hash(signal))
            if len(similar) == 0:
                continue
            similars[signal.name] = similar
        
        # if more than 50% similar, output
        similarity = len(similars) / total_signal_count
        if similarity >= .5:
            header = f"{d.path} | {create_progress_bar(similarity)} confidence ┐"
            print(header)
            print(f"┌{'─'*(len(header)-2)}┘")

            max_print_count = 5
            print_count = 0
            for sn, sv in similars.items():
                print_count += 1
                if print_count > max_print_count:
                    print("└ ... and", len(similars) - max_print_count, "more")
                    break
                print(f"├ [checking] {sn} ◄► [checked] {', '.join(sv)}")
            print()

if __name__ == "__main__":
    print("[db] Reading database ...")
    db = create_database()
    print("  [db] done!")
    print()
    for file in glob(INPUT_FILES, recursive=True):
        check(db, file)
