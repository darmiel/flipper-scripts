import sys
sys.path.insert(0, '..') # ugly ass hack :/

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir
from fsc.flipper_format.bulk import write_all_ir_ir

from fff_ir_lint.lint import Result, check_file

from glob import glob

if __name__ == "__main__":
    for file in glob("input_files/**/*.ir", recursive=True):
        hashes = []
        uniq = []
        with FlipperFormat(file) as fff:
            for signal in read_ir(fff):
                h = hash(signal)
                if h in hashes:
                    continue
                hashes.append(h)
                uniq.append(signal)
        write_all_ir_ir(file, uniq)
        print("wrote", file)
