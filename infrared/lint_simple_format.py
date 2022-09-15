from lint import create_mark_underline_array
from lint import Result

def result_simple_output():
    def callback(_: str, lnr: int, line: str, result: Result):
        # print line number
        print("Error in line", lnr)
        print(f"'{line}'")

        mark = create_mark_underline_array(len(line), result.marks, symbol='↑')
        print("", ''.join(mark))
        print((' '*(mark.index("↑") + 1)) + "[error]:", result.error)

        # print suggestion
        if result.suggestion is not None:
            print(f"[suggested] '{result.suggestion}'")
        print("---")
    return callback
