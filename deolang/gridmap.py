import os

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
