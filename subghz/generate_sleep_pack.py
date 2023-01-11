from generate_sleep import generate_sleep

values_in_s = [
    5, 10, 15, 30, 45, 60, 120, 300, 600, 900, 1800, 3600
]

def format_time(duration_in_s: int) -> str:
    out = ''
    if duration_in_s >= 3600:
        out += f'{duration_in_s // 3600}h'
        duration_in_s %= 3600
    if duration_in_s >= 60:
        out += f'{duration_in_s // 60}m'
        duration_in_s %= 60
    if duration_in_s > 0:
        out += f'{duration_in_s}s'
    return out

for val in values_in_s:
    value_in_µs = val * 1000 * 1000
    name = f'sleep_{format_time(val)}.sub'
    with open(name, "w") as fd:
        fd.write('\n'.join(generate_sleep(value_in_μs)))
    print(f"wrote {name}")