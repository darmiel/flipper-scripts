""" Script to generate a blank signal for a specific amount of time
"""

# duration in µs
DURATION = 30_000_000

OUTPUT = [
    "Filetype: Flipper SubGhz RAW File",
    "Version: 1",
    "Frequency: 433920000",
    "Preset: FuriHalSubGhzPresetOok650Async",
    "Protocol: RAW",
]

# WeLl aCtUaLlY iT'S 2,147,483,647
MAX_VALUE = 2_000_000_000
# that's 2_000_000_000 µs
# that's 2_000_000 ms
# that's 2_000 s
# you get the idea

# max 512 values per line
CHUNK_SIZE = 512

# what duration we've already added
current_duration = 0
values = []

while current_duration < DURATION:
    current_duration += 1000
    values.append(1000)

    # remaining time we need to add
    remaining = min(MAX_VALUE, DURATION - current_duration)
    current_duration += remaining
    values.append(-remaining)

for i in range(0, len(values), CHUNK_SIZE):
    vals = values[i:i + CHUNK_SIZE]
    OUTPUT.append(f'RAW_Data: {" ".join([str(z) for z in vals])}')

print('\n'.join(OUTPUT))