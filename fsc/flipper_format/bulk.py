import json

from glob import glob

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir

def parse_all_ir_unique(pattern):
    all = {}
    for file_name in glob(pattern, recursive=True):
        with FlipperFormat(file_name) as fff:
            signals = read_ir(fff)
            for signal in signals:
                h = hash(signal)
                if h in all:
                    continue
                all[h] = signal
    return all

def write_all_ir_json(file_name, signals):
    with open(file_name, "w") as f:
        json.dump([z.to_obj() for z in signals], f)

def write_all_ir_ir(file_name, signals):
    with open(file_name, "w", encoding="UTF-8") as f:
        f.write("\n#\n".join([str(signal) for signal in signals]))

def write_all_ir(file_name, signals):
    if file_name.endswith(".json"):
        return write_all_ir_json(file_name, signals)
    elif file_name.endswith(".ir"):
        return write_all_ir_ir(file_name, signals)
    else:
        raise Exception("invalid extension")
