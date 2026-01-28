#!/usr/bin/env python3
import argparse
import sys
import os
import shutil
import re

CONSTANTS_SRC = r"""
DIRECTIONS = {
    "^": (0, -1),
    ">": (1, 0),
    "<": (-1, 0),
    "V": (0, 1)
}

TURN_RIGHT = {
    (0, -1): (1, 0),
    (1, 0): (0, 1),
    (-1, 0): (0, -1),
    (0, 1): (-1, 0)
}

TURN_LEFT = {
    (0, -1): (-1, 0),
    (1, 0): (0, -1),
    (-1, 0): (0, 1),
    (0, 1): (1, 0)
}
"""

GRIDMAP_SRC = r"""
class GridMap:
    def __init__(self, file=None, content=None):
        if content:
            lines = content.splitlines()
        elif file and os.path.exists(file):
            with open(file, 'r') as map_file:
                lines = map_file.readlines()
        else:
            raise ValueError

        raw_grid = [list(line.rstrip('\n')) for line in lines]
        self.rows = len(raw_grid)
        self.cols = max(len(row) for row in raw_grid) if raw_grid else 0

        self._map = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        for r, row in enumerate(raw_grid):
            for c, char in enumerate(row):
                self._map[r][c] = char

    def get_map(self):
        return [row[:] for row in self._map]

    def get_item(self, x: int, y: int) -> str:
        if 0 <= y < len(self._map) and 0 <= x < len(self._map[y]):
            return self._map[y][x]
        return ""

    def set_item(self, x: int, y: int, char: str):
        if x < 0 or y < 0:
            return

        self._ensure_size(x + 1, y + 1)
        self._map[y][x] = char

    def _ensure_size(self, w, h):
        current_h = len(self._map)
        current_w = len(self._map[0]) if current_h > 0 else 0

        if h > current_h:
            for _ in range(h - current_h):
                self._map.append([''] * current_w)

        if w > current_w:
            for r in range(len(self._map)):
                self._map[r].extend([''] * (w - len(self._map[r])))

        self.rows = len(self._map)
        self.cols = len(self._map[0]) if self.rows > 0 else 0

    def merge_grid(self, other_grid_file: str, x_offset: int, y_offset: int):
        try:
            other = GridMap(file=other_grid_file)
            other_map = other.get_map()
            h = len(other_map)
            w = len(other_map[0]) if h > 0 else 0

            self._ensure_size(x_offset + w, y_offset + h)

            for r in range(h):
                for c in range(w):
                    val = other_map[r][c]
                    if val != '':
                        self._map[r + y_offset][c + x_offset] = val
            return True
        except Exception:
            return False

    def __len__(self):
        return self.rows * self.cols
"""

INTERPRETER_SRC_RAW = r"""
class Interpreter:
    def __init__(self, program_input: str | None = None, build_in_input: Callable = None) -> None:
        self.program = None
        self.stack = []
        self.addition_stack = []
        self.output = []
        self.call_stack = []
        self.heap = {}
        self.x = 0
        self.y = 0
        self.direction = (1, 0)
        self.ignore_mode = False
        self.string_mode = False
        self.input = program_input
        self.input_pointer = 0
        self.built_in_input = build_in_input
        self.ops = {
            "^": self.op_up,
            ">": self.op_right,
            "<": self.op_left,
            "V": self.op_down,
            "?": self.op_random_dir,
            "+": self.op_add,
            "-": self.op_sub,
            "*": self.op_mul,
            ":": self.op_div,
            "%": self.op_mod,
            "&": self.op_and,
            "o": self.op_or,
            "x": self.op_xor,
            "~": self.op_not,
            "=": self.op_eq,
            "(": self.op_less,
            ")": self.op_greater,
            "P": self.op_pop,
            "S": self.op_swap,
            "C": self.op_copy,
            "D": self.op_move_to_aux,
            "U": self.op_move_from_aux,
            "{": self.op_rotate_left,
            "}": self.op_rotate_right,
            "L": self.op_len,
            "Z": self.op_clear,
            "N": self.op_print_num,
            "A": self.op_print_char,
            "I": self.op_input,
            "h": self.op_heap_store,
            "H": self.op_heap_load,
            "g": self.op_grid_get,
            "p": self.op_grid_put,
            "j": self.op_jump,
            "F": self.op_func_call,
            "R": self.op_return,
            "M": self.op_merge,
            "T": self.op_time,
            "W": self.op_wait,
            "|": self.op_vertical_mirror,
            "_": self.op_horizontal_mirror,
            "/": self.op_mirror_slash,
            "\\": self.op_mirror_backslash,
            "@": self.op_exit,
            "\"": self.op_quote
        }

    def load_program(self, file: str) -> None:
        self.program = GridMap(file=file)

    def load_code(self, code: str) -> None:
        self.program = GridMap(content=code)

    def run(self, steps: int = 0) -> bool:
        if steps < 0:
            raise ValueError
        if steps > 0:
            for _ in range(steps):
                char = self.program.get_item(self.x, self.y)
                if self.process_char(char) is False:
                    return False
        else:
            while True:
                char = self.program.get_item(self.x, self.y)
                if self.process_char(char) is False:
                    return False
        return 0 < steps

    def get_current_char(self) -> str:
        if self.program:
            return self.program.get_item(self.x, self.y)
        return ""

    def get_output(self) -> str:
        return "".join(self.output)

    def get_program(self) -> GridMap | None:
        if self.program:
            return self.program.get_map()
        return None

    def get_information(self) -> dict[str, Any]:
        return {
            "output": self.get_output(),
            "stack": self.stack,
            "addition_stack": self.addition_stack,
            "call_stack": self.call_stack,
            "heap": self.heap,
            "position": (self.x, self.y),
            "direction": self.direction,
            "character": self.get_current_char(),
            "ignore_mode": self.ignore_mode,
            "string_mode": self.string_mode,
            "input": self.input,
            "input_pointer": self.input_pointer,
        }

    def reset(self) -> None:
        self.stack = []
        self.addition_stack = []
        self.output = []
        self.call_stack = []
        self.heap = {}
        self.ignore_mode = False
        self.string_mode = False
        self.input_pointer = 0
        self.x = 0
        self.y = 0
        self.direction = (1, 0)

    def set_input(self, input_data: str = "", pointer_position: int = 0) -> None:
        self.input = input_data
        self.input_pointer = pointer_position
        self.built_in_input = False if self.input else True

    def _pop_string(self) -> str:
        chars = []
        while self.stack:
            val = self.stack.pop()
            if val == 0:
                break
            chars.append(chr(val))
        return "".join(chars)

    def process_char(self, char: str) -> bool:
        if self.string_mode:
            if char == '"':
                self.string_mode = False
            else:
                self.stack.append(ord(char))
            self.move()
            return True

        if self.ignore_mode:
            if char in "|_":
                self.ignore_mode = False
            self.move()
            return True

        try:
            if not char:
                pass
            elif char.isdigit():
                self.stack.append(int(char))
            elif char in self.ops:
                res = self.ops[char]()
                if res is False:
                    return False
                if res == "JUMPED":
                    return True

        except Exception:
            return False

        self.move()
        return True

    def move(self):
        self.x += self.direction[0]
        self.y += self.direction[1]

    def op_up(self): self.direction = DIRECTIONS["^"]
    def op_right(self): self.direction = DIRECTIONS[">"]
    def op_left(self): self.direction = DIRECTIONS["<"]
    def op_down(self): self.direction = DIRECTIONS["V"]
    def op_random_dir(self): self.direction = random.choice(list(DIRECTIONS.values()))

    def op_add(self):
        if len(self.stack) < 2: return
        self.stack.append(self.stack.pop() + self.stack.pop())

    def op_sub(self):
        if len(self.stack) < 2: return
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a - b)

    def op_mul(self):
        if len(self.stack) < 2: return
        self.stack.append(self.stack.pop() * self.stack.pop())

    def op_div(self):
        if len(self.stack) < 2: return
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(0 if b == 0 else a // b)

    def op_mod(self):
        if len(self.stack) < 2: return
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(0 if b == 0 else a % b)

    def op_and(self):
        if len(self.stack) < 2: return
        self.stack.append(self.stack.pop() & self.stack.pop())

    def op_or(self):
        if len(self.stack) < 2: return
        self.stack.append(self.stack.pop() | self.stack.pop())

    def op_xor(self):
        if len(self.stack) < 2: return
        self.stack.append(self.stack.pop() ^ self.stack.pop())

    def op_not(self):
        if not self.stack: return
        self.stack.append(~self.stack.pop())

    def op_eq(self):
        if len(self.stack) < 2: return
        self.stack.append(1 if self.stack.pop() == self.stack.pop() else 0)

    def op_less(self):
        if len(self.stack) < 2: return
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(1 if a < b else 0)

    def op_greater(self):
        if len(self.stack) < 2: return
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(1 if a > b else 0)

    def op_pop(self):
        if self.stack: self.stack.pop()

    def op_swap(self):
        if len(self.stack) < 2: return
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.extend([b, a])

    def op_copy(self):
        if self.stack: self.stack.append(self.stack[-1])

    def op_move_to_aux(self):
        if self.stack: self.addition_stack.append(self.stack.pop())

    def op_move_from_aux(self):
        if self.addition_stack: self.stack.append(self.addition_stack.pop())

    def op_rotate_left(self):
        if len(self.stack) > 1: self.stack.insert(0, self.stack.pop())

    def op_rotate_right(self):
        if len(self.stack) > 1: self.stack.append(self.stack.pop(0))

    def op_len(self):
        self.stack.append(len(self.stack))

    def op_clear(self):
        self.stack.clear()

    def op_print_num(self):
        if self.stack:
            s = str(self.stack.pop())
            self.output.append(s)
            sys.stdout.write(s)
            sys.stdout.flush()

    def op_print_char(self):
        if self.stack:
            c = chr(self.stack.pop())
            self.output.append(c)
            sys.stdout.write(c)
            sys.stdout.flush()

    def op_input(self):
        if not self.input:
            if self.built_in_input:
                val = self.built_in_input()
                if isinstance(val, str) and val: self.stack.append(ord(val[0]))
                elif isinstance(val, int): self.stack.append(val)
        else:
            if self.input_pointer < len(self.input):
                self.stack.append(ord(self.input[self.input_pointer]))
                self.input_pointer += 1
            else:
                self.stack.append(-1)

    def op_heap_store(self):
        if len(self.stack) < 2: return
        addr, val = self.stack.pop(), self.stack.pop()
        self.heap[addr] = val

    def op_heap_load(self):
        if not self.stack: return
        self.stack.append(self.heap.get(self.stack.pop(), 0))

    def op_grid_get(self):
        if len(self.stack) < 2: return
        y, x = self.stack.pop(), self.stack.pop()
        val = self.program.get_item(x, y)
        self.stack.append(ord(val) if val else 0)

    def op_grid_put(self):
        if len(self.stack) < 3: return
        y, x, val = self.stack.pop(), self.stack.pop(), self.stack.pop()
        self.program.set_item(x, y, chr(val))

    def op_jump(self):
        if len(self.stack) < 2: return
        self.y, self.x = self.stack.pop(), self.stack.pop()
        return "JUMPED"

    def op_func_call(self):
        if len(self.stack) < 2: return
        y, x = self.stack.pop(), self.stack.pop()
        self.call_stack.append((self.x + self.direction[0], self.y + self.direction[1]))
        self.x, self.y = x, y
        return "JUMPED"

    def op_return(self):
        if self.call_stack:
            self.x, self.y = self.call_stack.pop()
            return "JUMPED"

    def op_merge(self):
        if len(self.stack) < 2: return
        y, x = self.stack.pop(), self.stack.pop()
        filename = self._pop_string()
        self.program.merge_grid(filename, x, y)

    def op_time(self):
        self.stack.append(int(time.time()))

    def op_wait(self):
        if self.stack: time.sleep(self.stack.pop())

    def op_vertical_mirror(self):
        if self.direction in ((-1, 0), (1, 0)): self.ignore_mode = True

    def op_horizontal_mirror(self):
        if self.direction in ((0, -1), (0, 1)): self.ignore_mode = True

    def op_mirror_slash(self):
        if not self.stack: return
        self.direction = TURN_LEFT[self.direction] if self.stack.pop() == 0 else TURN_RIGHT[self.direction]

    def op_mirror_backslash(self):
        if not self.stack: return
        val = self.stack.pop()
        self.direction = TURN_RIGHT[self.direction] if val == 0 else TURN_LEFT[self.direction]

    def op_exit(self): return False

    def op_quote(self): self.string_mode = True
"""

TEMPLATE = """from __future__ import annotations
import sys
import os
import random
import time
from typing import Any, Callable

{constants}

{gridmap}

{interpreter}

def cli_input():
    try:
        s = input()
        return s
    except (EOFError, KeyboardInterrupt):
        return ""

if __name__ == '__main__':
    program_code = {code_repr}

    interpreter = Interpreter(build_in_input=cli_input)
    interpreter.load_code(program_code)

    try:
        interpreter.run()
    except KeyboardInterrupt:
        pass
"""


def main():
    parser = argparse.ArgumentParser(description="Deolang Compiler")
    parser.add_argument("source", help="Path to the Deolang source file (.deo, .txt)")
    parser.add_argument("-o", "--output", help="Name of the output executable")
    parser.add_argument("--py", action="store_true", help="Output a .py file instead of .exe")

    args = parser.parse_args()

    source_path = args.source
    if not os.path.exists(source_path):
        print(f"Error: Source file '{source_path}' not found.")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(source_path))[0]
    final_output_name = args.output if args.output else base_name

    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        print(f"Error reading source file: {e}")
        sys.exit(1)

    full_script = TEMPLATE.format(
        constants=CONSTANTS_SRC,
        gridmap=GRIDMAP_SRC,
        interpreter=INTERPRETER_SRC_RAW,
        code_repr=repr(code_content)
    )

    if args.py:
        out_py = final_output_name if final_output_name.endswith('.py') else final_output_name + ".py"
        with open(out_py, 'w', encoding='utf-8') as f:
            f.write(full_script)
        print(f"Generated Python script: {out_py}")
        return

    temp_py_file = f"_deo_build_{base_name}.py"
    try:
        with open(temp_py_file, 'w', encoding='utf-8') as f:
            f.write(full_script)
    except Exception as e:
        print(f"Error writing temporary build file: {e}")
        sys.exit(1)

    print(f"Compiling '{source_path}' to executable...")

    try:
        import PyInstaller.__main__
    except ImportError:
        print("Error: PyInstaller is not installed.")
        print("Please run: pip install pyinstaller")
        os.remove(temp_py_file)
        sys.exit(1)

    try:
        PyInstaller.__main__.run([
            '--onefile',
            '--name', final_output_name,
            '--distpath', '.',
            '--workpath', './build',
            '--specpath', '.',
            temp_py_file
        ])
    except Exception as e:
        print(f"Compilation failed: {e}")
    finally:
        if os.path.exists(temp_py_file):
            os.remove(temp_py_file)

        if os.path.exists('build'):
            shutil.rmtree('build', ignore_errors=True)

        spec_file = f"{final_output_name}.spec"
        if os.path.exists(spec_file):
            os.remove(spec_file)

    exe_name = final_output_name + (".exe" if os.name == 'nt' else "")
    if os.path.exists(exe_name):
        print(f"Successfully created: {exe_name}")
    else:
        print("Error: Executable was not created.")


if __name__ == "__main__":
    main()