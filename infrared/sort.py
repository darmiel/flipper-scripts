import sys
sys.path.insert(0, '..') # ugly ass hack :/

from fsc.flipper_format.bulk import parse_all_ir_unique, write_all_ir_ir, write_all_ir_json

####################################################################################################

INPUT_FILES = "_Converted_/**/*.ir"
OUTPUT_FILE = "sorted_ir"
ORDER = "ASC" # or DESC

####################################################################################################

if __name__ == "__main__":
    # parse .ir files, convert to list and order by name
    all = [v for _, v in parse_all_ir_unique(INPUT_FILES).items()]
    all.sort(key=lambda x: x.get_name(), reverse=ORDER == "DESC")

    # write to file
    write_all_ir_ir(OUTPUT_FILE + ".ir", all)
    write_all_ir_json(OUTPUT_FILE + ".json", all)
