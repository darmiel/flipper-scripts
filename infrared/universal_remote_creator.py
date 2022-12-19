import sys
sys.path.insert(0, '..') # ugly ass hack :/

from glob import glob
from collections import Counter

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir

####################################################################################################

ACCEPTED_SIGNAL_NAMES = {
    "POWER": ["power", "pwr", "sleep", "off", "turn_off", "power_toggle"]
}

INPUT_FILES = "_Converted_/**/*.ir"
OUTPUT_FILE = "outpu4t.ir"
WRITE_SOURCE = True

####################################################################################################

accepted = {iv.strip().lower(): ok for ok, ov in ACCEPTED_SIGNAL_NAMES.items() for iv in ov}
count = 0
hashes = Counter()

for file_name in glob(INPUT_FILES, recursive=True):
    with open(OUTPUT_FILE, "w+") as f:
        if file_name == OUTPUT_FILE:
            print("oh oh!")
            break
        with FlipperFormat(file_name) as fff:
            file_count = 0
            for signal in read_ir(fff):
                if signal.name.strip().lower() not in accepted:
                    continue

                # skip duplicates | WIP
                h = hash(signal)
                hashes[h] += 1
                if hashes[h] > 1:
                    continue
                
                # write source header above signal (if WRITE_SOURCE was enabled)
                if WRITE_SOURCE:
                    f.write(f"# from: {file_name}\n#\n")
                
                # write signal to file
                print(signal)
                f.write(str(signal))
                f.write("\n#\n")
                count += 1; file_count += 1
            print(f"[local] Wrote {file_count} signals from {file_name} to {OUTPUT_FILE}")

print(f"[global] Wrote {count} signals to {OUTPUT_FILE}")
print(f"[global] Skipped a total of {sum([z for z in hashes.values() if z > 1])} duplicates")