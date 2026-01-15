import pyxel
import random
from collections import deque
import time

# ---------- 定数 ----------
CELL_SIZE = 8
MAZE_W = 32
MAZE_H = 30
UI_H = 16
SCREEN_W = 256
SCREEN_H = MAZE_H * CELL_SIZE + UI_H

WALL = 1
ROAD = 0

COUNTDOWN_TIME = 3.0
HOLD_MOVE_INTERVAL = 0.08  # 長押し移動速度


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Maze Time Trial")
        pyxel.load("wallandfloor.pyxres")

        # ---------- ゴール効果音 ----------
        pyxel.sound(1).set("c3e3g3c4", "t", "7777", "n", 12)

        # ---------- ダークBGM ----------
        # 低音＋ゆっくり＋短調風
        pyxel.sound(2).set(
            "c2 d2 e2 g2 e2 d2 c2 d2",
            "n",
            "44444444",
            "n",
            18   # ←テンポを遅く
        )

        pyxel.sound(3).set(
            "c1 c1 g1 g1 c1 c1 g1 g1",
            "n",
            "22222222",
            "n",
            18
        )

        pyxel.sound(4).set(
            "r r g2 r r g2 r r",
            "n",
            "0 0 3 0 0 3 0 0",
            "n",
            18
        )

        pyxel.music(0).set([2], [3], [4], [])

        self.start_new_maze()
        pyxel.run(self.update, self.draw)

    # ----------------------
    # 新しい迷路開始
    # ----------------------
    def start_new_maze(self):
        self.generate_maze()
        self.set_goal()
        self.set_fake_walls()

        self.px, self.py = 1, 1

        self.countdown_start = time.time()
        self.start_time = None
        self.clear_time = 0

        self.last_move_time = 0
        self.state = "COUNTDOWN"   # COUNTDOWN / PLAY / CLEAR

        # BGM再生
        pyxel.playm(0, loop=True)

    # ----------------------
    # 迷路生成（DFS）
    # ----------------------
    def generate_maze(self):
        self.maze = [[WALL for _ in range(MAZE_W)] for _ in range(MAZE_H)]

        def dfs(x, y):
            self.maze[y][x] = ROAD
            dirs = [(2,0),(-2,0),(0,2),(0,-2)]
            random.shuffle(dirs)

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < MAZE_W-1 and 1 <= ny < MAZE_H-1:
                    if self.maze[ny][nx] == WALL:
                        self.maze[y + dy//2][x + dx//2] = ROAD
                        dfs(nx, ny)

        dfs(1, 1)

    # ----------------------
    # ゴールを最遠地点に設定
    # ----------------------
    def set_goal(self):
        queue = deque()
        visited = [[False]*MAZE_W for _ in range(MAZE_H)]

        queue.append((1, 1))
        visited[1][1] = True
        farthest = (1, 1)

        while queue:
            x, y = queue.popleft()
            farthest = (x, y)

            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < MAZE_W and 0 <= ny < MAZE_H:
                    if not visited[ny][nx] and self.maze[ny][nx] == ROAD:
                        visited[ny][nx] = True
                        queue.append((nx, ny))

        self.gx, self.gy = farthest

    # ----------------------
    # フェイク壁配置
    # ----------------------
    def set_fake_walls(self):
        candidates = []
        for y in range(1, MAZE_H-1):
            for x in range(1, MAZE_W-1):
                if self.maze[y][x] == ROAD and (x, y) != (1, 1) and (x, y) != (self.gx, self.gy):
                    candidates.append((x, y))

        fake_count = random.randint(5, 10)
        self.fake_walls = set(random.sample(candidates, fake_count))

    def is_revealed(self, fx, fy):
        return abs(fx - self.px) + abs(fy - self.py) == 1

    # ----------------------
    # 更新処理
    # ----------------------
    def update(self):

        if self.state == "COUNTDOWN":
            if time.time() - self.countdown_start >= COUNTDOWN_TIME:
                self.start_time = time.time()
                self.state = "PLAY"
            return

        if self.state == "CLEAR":
            if pyxel.btnp(pyxel.KEY_R):
                self.start_new_maze()
            if pyxel.btnp(pyxel.KEY_Q):
                pyxel.quit()
            return

        now = time.time()
        dx, dy = 0, 0
        moved = False

        # 単押し
        if pyxel.btnp(pyxel.KEY_UP): dy = -1
        elif pyxel.btnp(pyxel.KEY_DOWN): dy = 1
        elif pyxel.btnp(pyxel.KEY_LEFT): dx = -1
        elif pyxel.btnp(pyxel.KEY_RIGHT): dx = 1

        if dx != 0 or dy != 0:
            nx, ny = self.px + dx, self.py + dy
            if self.maze[ny][nx] == ROAD:
                self.px, self.py = nx, ny
                moved = True

        # 長押し
        if not moved and now - self.last_move_time >= HOLD_MOVE_INTERVAL:
            dx, dy = 0, 0
            if pyxel.btn(pyxel.KEY_UP): dy = -1
            elif pyxel.btn(pyxel.KEY_DOWN): dy = 1
            elif pyxel.btn(pyxel.KEY_LEFT): dx = -1
            elif pyxel.btn(pyxel.KEY_RIGHT): dx = 1

            if dx != 0 or dy != 0:
                nx, ny = self.px + dx, self.py + dy
                if self.maze[ny][nx] == ROAD:
                    self.px, self.py = nx, ny
                self.last_move_time = now

        # ゴール判定
        if (self.px, self.py) == (self.gx, self.gy):
            self.clear_time = time.time() - self.start_time
            pyxel.stop()
            pyxel.play(0, 1)
            self.state = "CLEAR"

    # ----------------------
    # 描画処理
    # ----------------------
    def draw(self):
        pyxel.cls(0)

        if self.state == "COUNTDOWN":
            remain = int(COUNTDOWN_TIME - (time.time() - self.countdown_start)) + 1
            if remain > 0:
                pyxel.text(110, 120, f"START IN {remain}", 10)
            else:
                pyxel.text(115, 120, "START!", 10)
            return

        if self.state == "CLEAR":
            pyxel.text(70, 80, "MAZE  CLEAR", 10)
            pyxel.text(60, 110, f"TIME  {self.clear_time:.2f}  SEC", 7)
            pyxel.text(50, 150, "PRESS  R  NEXT", 6)
            pyxel.text(50, 170, "PRESS  Q  QUIT", 6)
            return

        # 迷路描画
        for y in range(MAZE_H):
            for x in range(MAZE_W):
                draw_y = y * CELL_SIZE

                if (x, y) in self.fake_walls:
                    if self.is_revealed(x, y):
                        pyxel.blt(x*CELL_SIZE, draw_y, 0, 0, 0, 8, 8)
                    else:
                        pyxel.blt(x*CELL_SIZE, draw_y, 0, 8, 8, 8, 8)

                elif self.maze[y][x] == WALL:
                    pyxel.blt(x*CELL_SIZE, draw_y, 0, 8, 8, 8, 8)

                else:
                    pyxel.blt(x*CELL_SIZE, draw_y, 0, 0, 0, 8, 8)

        # ゴール
        pyxel.rect(self.gx*CELL_SIZE, self.gy*CELL_SIZE, 8, 8, 11)

        # プレイヤー
        pyxel.rect(self.px*CELL_SIZE, self.py*CELL_SIZE, 8, 8, 8)

        # UIバー
        pyxel.rect(0, MAZE_H*CELL_SIZE, SCREEN_W, UI_H, 1)
        elapsed = time.time() - self.start_time
        pyxel.text(5, MAZE_H*CELL_SIZE + 4, f"TIME: {elapsed:.2f} sec", 7)


App()
