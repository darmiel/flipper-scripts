from glob import glob

# glob pattern - rewrite which files
INPUT_FILES: str = "Flipper-IRDB/**/*.ir"

# check transformed name against pattern?
VERIFY: bool = False
# pattern to check for correct name transformation
import re
pattern = re.compile("^[A-Z0-9][a-z0-9_\-\+\s]*$")

# manually overwrite some names
rewrites = {
    "Power": [ "PWR" ],
    "Vol_dn": ["VOL-", "Vol_-"],
    "Vol_up": ["VOL+", "Vol_+"],
    "Ch_next": ["CH+", "CH_Up", "CHANNEL_UP", "CHANNEL UP"],
    "Ch-Prev": ["CH-", "CH_Dn", "CHANNEL_DOWN", "CHANNEL_DN", "CHANNEL_DWN", "CHANNEL DOWN"]
}
rewrite_internal = {v: k for k, u in rewrites.items() for v in u}

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

            if value.lower() in rewrites:
                new_value = rewrites[value.lower()]
            else:
                # transform value
                new_value = value[:1].upper() + value[1:].lower()
                new_value = new_value.replace(' ', "_")
            
            if VERIFY:
                if not pattern.match(new_value):
                    print("[verify] failed in", file_name, "for", value, "-> tried", new_value, "reverting to default")
                    output += line
                    continue

            output += f"name: {new_value}\n"
            if new_value != value:
                count += 1

    # write output
    with open(file_name, "w") as fd:
        fd.write(output)

    # print("Wrote", file_name, "with", count, "transformed values")