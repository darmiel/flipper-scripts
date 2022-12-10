# https://github.com/DarkFlippers/unleashed-firmware/issues/200

import sys
sys.path.insert(0, '..') # ugly ass hack :/

from fsc.flipper_format.base import FlipperFormat
from fsc.flipper_format.infrared import read_ir

if __name__ == "__main__":
    groups = {}
    target_rewrite = {
        "POWER_OFF": "OFF",
        "POWER OFF": "OFF",
        "POWER_ON": "ON",
        "POWER ON": "ON",
    }
    file = "input_files/ac.ir.txt"

    with FlipperFormat(file) as fff:
        signals = read_ir(fff)
        for signal in signals:
            group_name = f"{signal.name}"

            target = signal.get_last_comment()
            if target is not None:
                target = target.strip()
                if target in target_rewrite:
                    target = target_rewrite[target]
                if target != "":
                    group_name += f":{target}"
            
            if not group_name in groups:
                groups[group_name] = []
            groups[group_name].append(signal)

    with open(f"{file}-grouped.ir", "w+") as fd:
        for group in sorted(groups.keys()):
            print("writing group", group)
            fd.write(f"# section {group} start\n")
            for signal in groups[group]:
                fd.write('#\n')
                if signal.get_last_comment() is not None and signal.get_last_comment().strip() != "":
                    fd.write(f'# {signal.get_last_comment()}\n')
                fd.write(str(signal))
                fd.write('\n')
            fd.write(f"#\n# / section {group} end\n#\n")

    print(groups.keys())