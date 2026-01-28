# Deolang

A two-dimensional esoteric programming language.

Created by Deolta and Sylv1an.

## About

Deolang is an esoteric programming language where the code is placed on a two-dimensional grid. An instruction pointer moves across this grid, executing the commands it encounters.

The language is stack-based and includes a variety of commands for:
*   Arithmetic and logic
*   Stack manipulation
*   Memory control (Heap)
*   I/O operations
*   Flow control through mirrors, jumps, and function calls

---

## IDE & Debugger

This project includes a powerful IDE and debugger to help you write and test your `.deo` programs.

### Features
*   **Grid Editor:** Specialized editor for 2D code placement.
*   **Live Debugging:** Real-time visualization of the main stack, auxiliary stack, and heap memory.
*   **Execution Controls:** Run, step, stop, and reset functionality.
*   **Variable Speed:** Adjustable execution frequency (Hz).
*   **Integrated Cheatsheet:** Quick access to all language commands.

### How to Run
Launch the IDE by running:
```bash
python debugger.py
```

---

## Compiler (`deolangc.py`)

Deolang features a dedicated compiler that allows you to turn your `.deo` source files into standalone, executable programs.

### Features
*   **Standalone Binaries:** Bundles the interpreter and your code into a single `.exe` (Windows) or binary (Linux/macOS).
*   **Real-time I/O:** Compiled programs support immediate console output and standard input.
*   **Optimized Runtime:** Patched to handle infinite execution loops efficiently.

### Prerequisites
To compile to an executable, you must have `PyInstaller` installed:
```bash
pip install pyinstaller
```

### Usage
To compile a Deolang file to a native executable:
```bash
python deolangc.py your_program.deo
```

To just generate a bundled Python script without building an `.exe`:
```bash
python deolangc.py your_program.deo --py
```

---

## File Extensions
*   `.deo`: Standard Deolang source file.
*   `.txt`: Alternative text format supported by the IDE.
```