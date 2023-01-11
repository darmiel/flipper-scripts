import sys
sys.path.insert(0, '..') # ugly ass hack :/

import json
import os

from glob import glob

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir

####################################################################################################

if os.path.exists("signal_name_rewrites.json"):
    # load accepted signal names from json file
    with open("signal_name_rewrites.json", "r") as fd:
        ACCEPTED_SIGNAL_NAMES = json.load(fd)
else:
    # write default json file
    # !!!
    # DON'T CHANGE THIS
    # MAKE CHANGES IN signal_name_rewrites.json
    # !!!
    ACCEPTED_SIGNAL_NAMES = {
        "POWER": ["power", "power on", "power off"],
    }
    with open("signal_name_rewrites.json", "w") as fd:
        json.dump(fd, ACCEPTED_SIGNAL_NAMES, indent=4)

INPUT_FILES = "Flipper-IRDB/TVs/**/*.ir"
OUTPUT_FILE = "output_universal_tv.ir"
WRITE_SOURCE = True

####################################################################################################

# transform accepted signal names to a dict
# with the original name as key and the accepted name as value
accepted = {iv.strip().lower(): ok for ok, ov in ACCEPTED_SIGNAL_NAMES.items() for iv in ov}

# keep track of how many signals were written
count = 0

# keep track of how many duplicates were skipped
added = {}

with open(OUTPUT_FILE, "w") as fd:
    for file_name in glob(INPUT_FILES, recursive=True):
        file_count = 0
        file_skip_count = 0

        # skip output file
        if file_name == OUTPUT_FILE:
            print("oh oh!")
            continue
        
        # read signals from file
        with FlipperFormat(file_name) as fff:
            for signal in read_ir(fff):
                # check if signal name is accepted
                original_name = signal.name.strip().lower()
                if original_name not in accepted:
                    continue
                
                # rewrite signal name to accepted name
                signal.name = accepted[original_name]

                h = hash(signal)
                if h in added:
                    added[h] += 1
                    file_skip_count += 1
                    continue
                added[h] = 0
                
                # write source header above signal (if WRITE_SOURCE was enabled)
                if WRITE_SOURCE:
                    fd.write(f"# from: {file_name}\n#\n")
                
                # write signal to file
                fd.write(str(signal))
                fd.write("\n#\n")

                # update counters
                count += 1; file_count += 1

            # print summary for current file
            print(f"[local] Wrote {file_count} [skipped: {file_skip_count}] signals from {file_name} to {OUTPUT_FILE}")

print(f"[global] Wrote a total of {count} signals to {OUTPUT_FILE}")
print(f"[global] Skipped a total of {sum([z for z in added.values() if z > 1])} duplicates")
