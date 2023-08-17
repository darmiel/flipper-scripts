from glob import glob
import re

space = re.compile("\\s+")
freq_min = 10_000
freq_max = 56_000

for file_name in glob("Flipper-IRDB/**/*.ir", recursive=True):
    output = []
    with open(file_name, "r") as fd:
        for line in fd.readlines():
            line = line.rstrip('\r\n')

            # some weird ass line or comment
            if line.startswith("#") or ':' not in line:
                output.append(line)
                continue

            # extract key and value from line
            col = line.index(":")
            key = line[:col]
            value = line[col+1:].strip()

            if line.startswith("frequency:"):
                freq = int(value)
                output.append(f"{key}: {min(freq_max, max(freq_min, freq))}")
            elif line.startswith("data:"):
                packs = []
                for pack in space.split(value):
                    packs.append(abs(int(pack)))
                value = ' '.join(str(z) for z in packs)
                output.append(f"{key}: {value}")
            else:
                output.append(line)

    # write output
    with open(file_name, "w") as fd:
        fd.write('\n'.join(output) + '\n')