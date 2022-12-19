"""
minimal implementation of FlipperFormat
"""

from typing import Union, List

class EOFException(Exception): pass
class NotAPair(Exception): pass

class FlipperFormat:
    file_name: str
    last_comment: str

    def __init__(self, file_name):
        self.file_name = file_name
        self.last_comment = ""
        self.fd = open(self.file_name, "r", encoding="UTF-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fd.close()

    def close(self):
        self.fd.close()

    # ------------------------------------------------------------

    def get_file_name(self):
        return self.file_name

    def rewind(self) -> None:
        self.fd.seek(0)
    
    def get_last_comment(self) -> str:
        return self.last_comment
    
    def _read_next_line_pair(self) -> List[str]:
        line = self.fd.readline()
        if not line: # EOL
            raise EOFException()
        # store last comment
        # but ignore them for pairs
        if line.startswith("#"):
            self.last_comment = line[1:].strip()
            raise NotAPair()
        # if we want to read a key:value pair, the line should contain a ":"
        if line.startswith("#") or line.strip() == "" or not ":" in line:
            raise NotAPair()
        return [z.strip() for z in line.split(":", 1)]

    def read_next_pair(self) -> List[str]:
        while True:
            try:
                return self._read_next_line_pair()
            except NotAPair:
                continue

    def read_str(self, key: str) -> str:
        while True:
            k, v = self.read_next_pair()
            if k == key: 
                return v

    def read_int(self, key: str) -> int:
        return int(self.read_str(key))

    def read_hex(self, key: str) -> int:
        return int(self.read_str(key), base=16)

    def read_hex_multi(self, key: str) -> List[int]:
        return [int(z, base=16) for z in self.read_str(key).split()]

    def read_float(self, key: str) -> Union[float, None]:
        return float(self.read_str(key))

    def count_subsequent_keys(self, key: str) -> int:
        count = 0
        pos = self.fd.tell()
        while True:
            try:
                k, _ = self._read_next_line_pair()
                if k != key:
                    break
            except EOFException:
                break
            except NotAPair:
                continue
            count += 1
        self.fd.seek(pos)
        return count

def marshal(a: dict) -> str:
    r = ""
    f = True
    for k, v in a.items():
        if f:
            f = False
        else:
            r += "\n"
        if type(v) != str:
            v = str(v)
        r += f"{k}: {v}"
    return r