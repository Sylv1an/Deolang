import sys
import os
import warnings
import time
from typing import Dict, Any

from PyQt5.QtCore import Qt, QTimer, QSize, QEvent
from PyQt5.QtGui import QIcon, QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QKeyEvent
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QLineEdit, QSpinBox, QHBoxLayout, QVBoxLayout,
                             QLabel, QGroupBox, QPushButton, QListWidget, QSizePolicy, QAction, QFileDialog,
                             QMessageBox, QDialog, QDockWidget, QPlainTextEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget, QSplitter, QInputDialog, QAbstractItemView)

from deolang.gridmap import GridMap
from deolang.interpreter import Interpreter

warnings.filterwarnings("ignore")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CheatsheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cheatsheet")
        self.resize(500, 400)
        self.setStyleSheet("background-color: #000000; color: #ffffff;")

        layout = QVBoxLayout()
        text_edit = QPlainTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 11))
        text_edit.setStyleSheet("background-color: #000000; color: #ffffff; border: none;")

        msg = """
MOVEMENT
  ^ > < V  : Direction
  ?        : Random direction

MATH & LOGIC
  + - *    : Add, Sub, Mul
  : %      : Div, Mod
  & o x ~  : AND, OR, XOR, NOT
  = ( )    : Equal, Less, Greater

STACK
  0-9      : Push digit
  P        : Pop & discard
  S        : Swap top two
  C        : Copy top
  D        : Move to Aux Stack
  U        : Move from Aux Stack
  { }      : Rotate Left/Right
  L        : Stack Length
  Z        : Clear Stack

I/O
  N        : Print Number
  A        : Print Char
  I        : Input

MEMORY & GRID
  h H      : Heap Store/Load
  g p      : Grid Get/Put
  M        : Merge File

FLOW CONTROL
  F R      : Call/Return
  j        : Jump (y, x)
  @        : Exit
  | _      : Bridges (skip next)
  / \\      : Mirrors
  "        : String Mode (push ASCII)

TIME
  T        : Push Timestamp
  W        : Wait (seconds)
"""
        text_edit.setPlainText(msg)
        layout.addWidget(text_edit)

        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("background-color: #333; color: white; border: 1px solid #555; padding: 5px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)


class GridEditor(QTableWidget):
    def __init__(self, rows=20, cols=20, parent=None):
        super().__init__(rows, cols, parent)
        self.last_highlight = None

        self.setFont(QFont("Consolas", 12))
        self.setShowGrid(True)
        self.setGridStyle(Qt.DotLine)
        self.verticalHeader().setVisible(True)
        self.horizontalHeader().setVisible(True)

        self.horizontalHeader().setDefaultSectionSize(30)
        self.verticalHeader().setDefaultSectionSize(30)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.fill_empty_items()

    def fill_empty_items(self):
        for r in range(self.rowCount()):
            for c in range(self.columnCount()):
                if self.item(r, c) is None:
                    self.setItem(r, c, QTableWidgetItem(""))
                    self.item(r, c).setTextAlignment(Qt.AlignCenter)

    def set_dimensions(self, rows, cols):
        old_data = {}
        for r in range(self.rowCount()):
            for c in range(self.columnCount()):
                item = self.item(r, c)
                if item and item.text():
                    old_data[(r, c)] = item.text()

        self.setRowCount(rows)
        self.setColumnCount(cols)
        self.fill_empty_items()

        for (r, c), text in old_data.items():
            if r < rows and c < cols:
                self.item(r, c).setText(text)

    def get_content_as_string(self):
        lines = []
        for r in range(self.rowCount()):
            line_chars = []
            for c in range(self.columnCount()):
                item = self.item(r, c)
                char = item.text() if item and item.text() else " "
                line_chars.append(char)
            lines.append("".join(line_chars))
        return "\n".join(lines)

    def load_content_from_string(self, content):
        lines = content.splitlines()
        req_rows = len(lines)
        req_cols = max(len(l) for l in lines) if lines else 0

        current_rows = max(self.rowCount(), req_rows)
        current_cols = max(self.columnCount(), req_cols)

        self.setRowCount(current_rows)
        self.setColumnCount(current_cols)
        self.fill_empty_items()
        self.clear_grid_text()

        for r, line in enumerate(lines):
            for c, char in enumerate(line):
                self.item(r, c).setText(char)

    def clear_grid_text(self):
        for r in range(self.rowCount()):
            for c in range(self.columnCount()):
                if self.item(r, c):
                    self.item(r, c).setText("")

    def keyPressEvent(self, event: QKeyEvent):
        row = self.currentRow()
        col = self.currentColumn()

        if event.text() and event.text().isprintable():
            if self.currentItem():
                self.currentItem().setText(event.text())

            if col < self.columnCount() - 1:
                self.setCurrentCell(row, col + 1)
            elif row < self.rowCount() - 1:
                pass

        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if row < self.rowCount() - 1:
                self.setCurrentCell(row + 1, 0)

        elif event.key() == Qt.Key_Backspace:
            if self.currentItem():
                self.currentItem().setText("")
            if col > 0:
                self.setCurrentCell(row, col - 1)
            elif row > 0:
                self.setCurrentCell(row - 1, self.columnCount() - 1)

        else:
            super().keyPressEvent(event)

    def highlight_cell(self, x, y):
        if self.last_highlight:
            lr, lc = self.last_highlight
            if lr < self.rowCount() and lc < self.columnCount():
                item = self.item(lr, lc)
                if item:
                    item.setBackground(QColor("#1e1e1e"))
                    item.setForeground(QColor("#d4d4d4"))

        if 0 <= y < self.rowCount() and 0 <= x < self.columnCount():
            item = self.item(y, x)
            if item:
                item.setBackground(QColor("#228B22"))
                item.setForeground(QColor("#FFFFFF"))
                self.last_highlight = (y, x)
                self.scrollToItem(item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.interpreter = Interpreter(build_in_input=self.ask_input)
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowIcon(QIcon(resource_path("main_debugger.ico")))
        self.setWindowTitle("Deolang IDE")
        self.resize(1300, 850)
        self.setStyleSheet("""
            QMainWindow { background-color: #252526; color: #cccccc; }
            QDockWidget { background-color: #252526; color: #cccccc; border: 1px solid #333; }
            QDockWidget::title { background-color: #333333; padding: 5px; }
            QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; border: none; }
            QListWidget { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #333; }
            QTableWidget { background-color: #1e1e1e; color: #d4d4d4; gridline-color: #333; border: none; font-family: Consolas; }
            QTableWidget::item:selected { background-color: #094771; }
            QHeaderView::section { background-color: #333; color: #ccc; border: 1px solid #2d2d2d; padding: 4px; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 5px 10px; }
            QPushButton:hover { background-color: #1177bb; }
            QLabel { color: #cccccc; }
            QSpinBox { background-color: #3c3c3c; color: white; border: 1px solid #555; padding: 2px; }
        """)

        self.grid_editor = GridEditor(rows=20, cols=30)
        self.setCentralWidget(self.grid_editor)

        self.create_docks()
        self.create_toolbar()
        self.create_menu()

    def create_docks(self):
        self.dock_stack = QDockWidget("Controls & Memory", self)
        self.dock_stack.setAllowedAreas(Qt.RightDockWidgetArea)

        right_container = QWidget()
        right_layout = QVBoxLayout()

        grp_grid = QGroupBox("Grid Size")
        grp_grid.setStyleSheet(
            "QGroupBox { border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        grid_layout = QGridLayout()

        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 1000)
        self.spin_rows.setValue(20)
        self.spin_rows.valueChanged.connect(self.update_grid_size)

        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 1000)
        self.spin_cols.setValue(30)
        self.spin_cols.valueChanged.connect(self.update_grid_size)

        grid_layout.addWidget(QLabel("Rows:"), 0, 0)
        grid_layout.addWidget(self.spin_rows, 0, 1)
        grid_layout.addWidget(QLabel("Cols:"), 1, 0)
        grid_layout.addWidget(self.spin_cols, 1, 1)
        grp_grid.setLayout(grid_layout)

        right_layout.addWidget(grp_grid)

        self.list_stack = QListWidget()
        self.list_aux = QListWidget()
        self.table_heap = QTableWidget(0, 2)
        self.table_heap.setHorizontalHeaderLabels(["Addr", "Val"])
        self.table_heap.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_heap.verticalHeader().setVisible(False)

        splitter = QSplitter(Qt.Vertical)

        s1 = QWidget()
        l1 = QVBoxLayout()
        l1.addWidget(QLabel("Main Stack"))
        l1.addWidget(self.list_stack)
        s1.setLayout(l1)

        s2 = QWidget()
        l2 = QVBoxLayout()
        l2.addWidget(QLabel("Aux Stack"))
        l2.addWidget(self.list_aux)
        s2.setLayout(l2)

        s3 = QWidget()
        l3 = QVBoxLayout()
        l3.addWidget(QLabel("Heap"))
        l3.addWidget(self.table_heap)
        s3.setLayout(l3)

        splitter.addWidget(s1)
        splitter.addWidget(s2)
        splitter.addWidget(s3)

        right_layout.addWidget(splitter)
        right_container.setLayout(right_layout)

        self.dock_stack.setWidget(right_container)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_stack)

        self.dock_output = QDockWidget("Output & Log", self)
        self.dock_output.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.txt_output = QPlainTextEdit()
        self.txt_output.setReadOnly(True)
        self.dock_output.setWidget(self.txt_output)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_output)

    def create_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        act_run = QAction("Run", self)
        act_run.triggered.connect(self.run)
        toolbar.addAction(act_run)

        act_step = QAction("Step", self)
        act_step.triggered.connect(self.step)
        toolbar.addAction(act_step)

        act_stop = QAction("Stop", self)
        act_stop.triggered.connect(self.stop)
        toolbar.addAction(act_stop)

        act_reset = QAction("Reset", self)
        act_reset.triggered.connect(self.reset)
        toolbar.addAction(act_reset)

        toolbar.addSeparator()

        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(1, 1000)
        self.spin_speed.setValue(10)
        self.spin_speed.setSuffix(" Hz")
        self.spin_speed.setPrefix("Speed: ")
        self.spin_speed.setStyleSheet("background-color: #3c3c3c; color: white;")
        toolbar.addWidget(self.spin_speed)

    def create_menu(self):
        menu = self.menuBar().addMenu("File")
        act_open = QAction("Open", self)
        act_open.triggered.connect(self.open_file)
        menu.addAction(act_open)

        act_save = QAction("Save", self)
        act_save.triggered.connect(self.save_file)
        menu.addAction(act_save)

        help_menu = self.menuBar().addMenu("Help")
        act_cheatsheet = QAction("Cheatsheet", self)
        act_cheatsheet.triggered.connect(self.show_cheatsheet)
        help_menu.addAction(act_cheatsheet)

    def update_grid_size(self):
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()
        self.grid_editor.set_dimensions(rows, cols)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Deolang Files (*.deo);;Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    self.grid_editor.load_content_from_string(content)
                    self.spin_rows.setValue(self.grid_editor.rowCount())
                    self.spin_cols.setValue(self.grid_editor.columnCount())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Deolang Files (*.deo);;Text Files (*.txt)")
        if path:
            with open(path, 'w') as f:
                f.write(self.grid_editor.get_content_as_string())

    def show_cheatsheet(self):
        dlg = CheatsheetDialog(self)
        dlg.exec_()

    def ask_input(self):
        text, ok = QInputDialog.getText(self, "Input", "Enter value:")
        if ok: return text
        return ""

    def run(self):
        self.reset()
        self.load_code()
        self.timer.start(1000 // self.spin_speed.value())

    def stop(self):
        self.timer.stop()

    def step(self):
        if not self.interpreter.program:
            self.load_code()

        if not self.interpreter.run(1):
            self.stop()
            self.txt_output.appendPlainText("\n--- Program Finished ---")

        self.update_debug_view()

    def reset(self):
        self.interpreter.reset()
        self.txt_output.clear()

        if self.grid_editor.last_highlight:
            self.grid_editor.highlight_cell(-1, -1)

        self.update_debug_view()

    def load_code(self):
        code = self.grid_editor.get_content_as_string()
        self.interpreter.load_code(code)

    def update_debug_view(self):
        info = self.interpreter.get_information()

        self.list_stack.clear()
        for item in reversed(info['stack']):
            self.list_stack.addItem(str(item))

        self.list_aux.clear()
        for item in reversed(info['addition_stack']):
            self.list_aux.addItem(str(item))

        self.table_heap.setRowCount(len(info['heap']))
        for i, (k, v) in enumerate(info['heap'].items()):
            self.table_heap.setItem(i, 0, QTableWidgetItem(str(k)))
            self.table_heap.setItem(i, 1, QTableWidgetItem(str(v)))

        out_text = info['output']
        current_ui_text = self.txt_output.toPlainText().replace("\n--- Program Finished ---", "")

        if out_text != current_ui_text:
            self.txt_output.setPlainText(out_text)

        pos = info['position']
        self.grid_editor.highlight_cell(pos[0], pos[1])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())