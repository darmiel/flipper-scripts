from typing import List, Union

from fsc.flipper_format.base import EOFException, FlipperFormat, marshal

MAX_DATA_PER_LINE = 50

def _to_hex_str(nums: list, sep: str = ' ') -> str:
    return sep.join([hex(z)[2:].zfill(2) for z in nums]).upper()

class BaseSignal:
    def __init__(self, src: str, is_raw: bool, name: str) -> None:
        self.src = src
        self.is_raw = is_raw
        self.name = name
        self.last_comment = None
    
    def set_last_comment(self, comment: str) -> None:
        self.last_comment = comment
    
    def get_last_comment(self) -> None:
        return self.last_comment

    def get_name(self):
        return self.name

    def get_source(self):
        return self.src

class RawSignal(BaseSignal):
    """
    name: POWER
    type: raw
    frequency: 38000
    duty_cycle: 0.330000
    data: 8437 4188 538 1565 539 1565 539 513 544 508 538 513 544 1559 545
    """

    def __init__(self, src: str, name: str, frequency: int, duty_circle: float, data: list) -> None:
        super().__init__(src, True, name)
        self.frequency = frequency
        self.duty_circle = duty_circle
        self.data = data
   
    def to_obj(self):
        return {
            "name": self.name,
            "type": "raw",
            "frequency": self.frequency,
            "duty_circle": self.duty_circle,
            "data": self.data,
        }

    def __str__(self) -> str:
        r = marshal(self.to_obj())
        return r

    def __hash__(self) -> int:
        return hash(f"{self.frequency}@{self.duty_circle}::{'-'.join([str(u) for u in self.data])}".replace(" ", "#").lower())
    
class ParsedSignal(BaseSignal):
    """
    name: VOL-
    type: parsed
    protocol: NEC
    address: 00 00 00 00
    command: 15 00 00 00
    """

    def __init__(self, src: str, name: str, protocol: str, address: List[int], command: List[int]) -> None:
        super().__init__(src, False, name)
        self.protocol = protocol
        self.address = address
        self.command = command

    def to_obj(self):
        return {
            "name": self.name,
            "type": "parsed",
            "protocol": self.protocol,
            "address": _to_hex_str(self.address),
            "command": _to_hex_str(self.command)
        }

    def __str__(self) -> str:
        return marshal(self.to_obj())

    def __hash__(self) -> int:
        return hash(f"{_to_hex_str(self.command)}@{_to_hex_str(self.address)}::{self.protocol}".replace(" ", "#").lower())

def _parse_raw(fff: FlipperFormat, name: str) -> RawSignal:
    freq = fff.read_int("frequency")
    dc = fff.read_float("duty_cycle")
    data = []

    while True:
        pos = fff.fd.tell()
        try:
            k, v = fff.read_next_pair()
            if k != "data":
                fff.fd.seek(pos)
                break
            data.extend([int(z) for z in v.split()])
        except EOFException:
            break

    return RawSignal(fff.get_file_name(), name, frequency=freq, duty_circle=dc, data=data)

def _parse_parsed(fff: FlipperFormat, name: str) -> ParsedSignal:
    protocol = fff.read_str("protocol")
    address = fff.read_hex_multi("address")
    command = fff.read_hex_multi("command")
    return ParsedSignal(fff.get_file_name(), name, protocol=protocol, address=address, command=command)

def read_ir(fff: FlipperFormat) -> List[Union[RawSignal, ParsedSignal]]:
    while True:
        try:
            name = fff.read_str("name")
        except EOFException:
            break

        typ = fff.read_str("type")
        if typ == "raw":
            r = _parse_raw(fff, name)
        elif typ == "parsed":
            r = _parse_parsed(fff, name)
        else:
            raise Exception(f"unknown signal type '{typ}'")
        r.set_last_comment(fff.get_last_comment())
        yield r

if __name__ == "__main__":
    print("reading")
    fff = FlipperFormat("audio.ir")

    hashes = {}
    for resp in read_ir(fff):
        print(resp)
        h = hash(resp)
        if not h in hashes: hashes[h] = [resp] 
        else: 
            hashes[h].append(resp)
            if len(hashes[h]) > 1:
                print(">> DUPLICATE")
        print("#")
    fff.close()
