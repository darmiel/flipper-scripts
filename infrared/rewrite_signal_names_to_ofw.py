from glob import glob
from re import compile, Pattern

# glob pattern - rewrite which files
INPUT_FILES: str = "Flipper-IRDB/Audio_Receivers/**/*.ir"

# manually overwrite some names
rewrite_internal = {v: k for k, u in {
    "Power": [
        "power",
        "pwr",
        compile("^((power|pwr)[_\\s]*)?(toggle|on|off)$"),
        compile("^(turn[_\\s]*)?(on|off)$")
    ],
    "Vol_dn": [
         compile("^vol(ume)?[_\\s]*(d(o?w)?n|[v\\-])$")
    ],
    "Vol_up": [
        compile("^vol(ume)?[_\\s]*(up|[\\^+])$")
    ],
    "Ch_next": [
        compile("^ch(an(nel)?)?[_\\s]*(up|[\\^+])$")
    ],
    "Ch_prev": [
        compile("^ch(an(nel)?)?[_\\s]*(d(o?w)?n|[\\v-])$")
    ],
    "Mute": [
        "mte",
        compile("^mute.*$")
    ]
}.items() for v in u}

for file_name in glob(INPUT_FILES, recursive=True):
    output = ""
    count = 0
    with open(file_name, "r") as fd:
        for line in fd.readlines():
            # only target {name: value} key pairs
            if not line.startswith("name:"):
                output += line
                continue

            # extract key and value from line
            col = line.index(":")
            key = line[:col+1]
            value = line[col+1:].strip()

            new_value = None
            for k in rewrite_internal:
                if type(k) == str:
                    if value.lower() == k.lower():
                        new_value = rewrite_internal[k]
                        break
                if type(k) == Pattern:
                    if k.match(value.lower()):
                        new_value = rewrite_internal[k]
                        break

            if new_value is None:
                new_value = value
                # transform value
                # new_value = value[:1].upper() + value[1:].lower()
                # new_value = new_value.replace(' ', "_")

            output += f"name: {new_value}\n"
            if new_value != value:
                count += 1

    # write output
    with open(file_name, "w") as fd:
        fd.write(output)

    # print("Wrote", file_name, "with", count, "transformed values")