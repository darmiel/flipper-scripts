import os
import os.path

from glob import glob

IN_DIR = "sub_files/*"
OUT_DIR = "playlists"
CHUNK_SIZE = "128"
PREFIX = "/ext/subghz/flipperzero-bruteforce/"

REPLACE = {
    '\\\\': '/',
    '\\': '/',
    # 'sub_files/': ''
}

# create output directry if it doens't exist
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

def generate_playlist(dir, name):
    print("generating playlist for", dir, "...", end='')
    with open(os.path.join("playlists", name), "w") as f:
        for sub in glob(os.path.join(dir, "*.sub")):
            p = '/'.join(os.path.split(sub))
            for k, v in REPLACE.items():
                p = p.replace(k, v)
            f.write(f"sub: {PREFIX}{p}\n")
    print(" done!")

if __name__ == "__main__":
    # create single playlist
    # generate_playlist(f"sub_files/CAME-12bit-433/{CHUNK_SIZE}", f"CAME-12bit-433-{CHUNK_SIZE}.txt")

    # create multiple playlists
    for dir in glob(IN_DIR):
        generate_playlist(os.path.join(dir, CHUNK_SIZE), os.path.basename(dir) + f"-{CHUNK_SIZE}.txt")