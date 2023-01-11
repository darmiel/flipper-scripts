"""
# ---
# found in Flipper-IRDB-official\Digital_Signs\Panasonic\Panasonic_DPVF1615ZA.ir: Vol_Up
# found in Flipper-IRDB-official\TVs\Panasonic\Panasonic_TX_42AS650E.ir: Vol+
# found in Flipper-IRDB-official\TVs\Panasonic\Panasonic_Unknown_Full.ir: VOL_UP
# found in Flipper-IRDB-official\VCR\Panasonic\Panasonic_VSQS1331_VCR.ir: Vol_Up
name: VOL+
type: parsed
protocol: Kaseikyo
address: 80 02 20 00
command: 00 02 00 00
# ---
"""

import sys
sys.path.insert(0, '..') # ugly ass hack :/

import math

from glob import glob
from typing import List, Union

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import RawSignal, ParsedSignal

from fsc.flipper_format.infrared import read_ir

####################################################################################################

DB_FILES = "Flipper-IRDB*/**/*.ir"
SILENT_MODE = False

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
                self.hashes[h].append(signal)

class SignalMatch:
    def __init__(self, file: IRDBFile, h: int) -> None:
        self.file = file
        self.hash = h

    def get_signals(self) -> List[Union[RawSignal, ParsedSignal]]:
        return self.file.hashes[self.hash]

    def __str__(self) -> str:
        return f"# Found in {self.file.path}: {', '.join([s.name for s in self.get_signals()])}"
        

def create_database() -> List[IRDBFile]:
    res = []
    for ir in glob(DB_FILES, recursive=True):
        if not SILENT_MODE: print("[DB] Loading", ir)
        irdb = IRDBFile(ir)
        irdb.load()
        res.append(irdb)
    return res

####################################################################################################

def check_signal_hash(db: List[IRDBFile], h) -> List[SignalMatch]:
    return [SignalMatch(d, h) for d in db if h in d.hashes]


def check(db: List[IRDBFile], path: str) -> None:
    source = IRDBFile(path)
    source.load()

    for h, sig in source.hashes.items():
        if len(sig) <= 0:
            continue
        matches = check_signal_hash(db, h)
        
        print("\n# ---")

        # print matches
        if len(matches) == 0:
            print("# [x] Not in IRDB")
        else:
            for match in matches:
                print(str(match))

        # print signal
        print(str(sig[0]))
        print('# ---\n')

if __name__ == "__main__":
    if not SILENT_MODE: print("[db] Reading database ...")
    db = create_database()
    if not SILENT_MODE: print("  [db] done!\n")

    input_files = []
    for arg in sys.argv[1:]:
        if arg.startswith("glob:"):
            input_files.extend(glob(arg[5:], recursive=True))
        elif arg.startswith("file:"):
            with open(arg[5:], "r") as fd:
                input_files.extend([z.strip() for z in fd.readlines()])
        else:
            input_files.append(arg)

    for file in input_files:
        check(db, file)
