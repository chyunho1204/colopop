import pygame, random, time, sys, os, json

ROWS, COLS = 15, 11
EMPTY_PROB = 0.18
COMBO_WINDOW = 0.5
ROUND_TIME = 100
PENALTY_ON_FAIL = 1

EMPTY = None
COLORS = {
    "R": (220, 50, 47), "Y": (253, 231, 76), "O": (255, 153, 51),
    "B": (38, 139, 210), "E": (38, 194, 129), "G": (150, 152, 157),
    "W": (139, 69, 19),  "P": (155, 89, 182),
}
COLOR_KEYS = list(COLORS.keys())

CELL = 42
GRID_W, GRID_H = COLS * CELL, ROWS * CELL
SIDE = 220
W, H = GRID_W + SIDE, GRID_H
BG = (25, 29, 33)
GRIDLINE = (50, 54, 60)
PANEL_BG = (32, 36, 41)
TEXT = (230, 230, 235)
BAD = (230, 80, 80)
OVER_BG = (0, 0, 0, 170)

SAVE_FILE = "highscore.json"

def load_high():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return int(json.load(f).get("high", 0))
        except Exception:
            return 0
    return 0

def save_high(high):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"high": int(high)}, f)
    except Exception:
        pass

def new_board():
    return [[(None if random.random() < EMPTY_PROB else random.choice(COLOR_KEYS))
             for _ in range(COLS)] for __ in range(ROWS)]

def blit_text(screen, text, size, x, y, color=TEXT, center=False):
    font = pygame.font.SysFont("arial", size)
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def draw_board(screen, grid, score, combo_level, moves_left, time_left, high, flash_bad=False):
    screen.fill(BG)
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * CELL, r * CELL
            rect = pygame.Rect(x+1, y+1, CELL-2, CELL-2)
            val = grid[r][c]
            if val is None:
                pygame.draw.rect(screen, BG, rect, border_radius=6)
            else:
                pygame.draw.rect(screen, COLORS[val], rect, border_radius=8)
            pygame.draw.rect(screen, GRIDLINE, (x, y, CELL, CELL), 1, border_radius=6)

    pygame.draw.rect(screen, PANEL_BG, (GRID_W, 0, SIDE, H))
    y = 24
    blit_text(screen, "Score", 18, GRID_W+20, y); blit_text(screen, f"{score}", 18, GRID_W+120, y); y += 28
    blit_text(screen, "Max", 18, GRID_W+20, y);   blit_text(screen, f"{high}", 18, GRID_W+120, y); y += 28
    blit_text(screen, "Combo", 18, GRID_W+20, y); blit_text(screen, f"{combo_level}", 18, GRID_W+120, y); y += 28
    blit_text(screen, "Time", 18, GRID_W+20, y, BAD if flash_bad else TEXT)
    blit_text(screen, f"{int(max(0, time_left))}", 18, GRID_W+120, y, BAD if flash_bad else TEXT); y += 34

    blit_text(screen, "Controls", 18, GRID_W+20, y); y += 24
    blit_text(screen, "Click empty cell", 16, GRID_W+20, y); y += 20
    blit_text(screen, "N new board", 16, GRID_W+20, y); y += 20
    blit_text(screen, "R reset round", 16, GRID_W+20, y); y += 20
    blit_text(screen, "ESC quit", 16, GRID_W+20, y); y += 26
    blit_text(screen, "Moves left", 16, GRID_W+20, y); blit_text(screen, f"{moves_left}", 16, GRID_W+140, y)

def draw_gameover(screen, score, high):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill(OVER_BG)
    screen.blit(overlay, (0, 0))
    blit_text(screen, "Time is up", 36, W//2, H//2 - 60, color=TEXT, center=True)
    blit_text(screen, f"Score  {score}", 28, W//2, H//2 - 10, color=TEXT, center=True)
    blit_text(screen, f"Max    {high}", 24, W//2, H//2 + 30, color=TEXT, center=True)
    blit_text(screen, "Press Enter to play again, Esc to quit", 20, W//2, H//2 + 80, color=TEXT, center=True)

def nearest_nonempty_in_row(grid, r, c):
    lc = c - 1
    while lc >= 0 and grid[r][lc] is None:
        lc -= 1
    rc = c + 1
    while rc < COLS and grid[r][rc] is None:
        rc += 1
    return lc, rc

def nearest_nonempty_in_col(grid, r, c):
    ur = r - 1
    while ur >= 0 and grid[ur][c] is None:
        ur -= 1
    dr = r + 1
    while dr < ROWS and grid[dr][c] is None:
        dr += 1
    return ur, dr

def try_clear_at(grid, r, c):
    if not (0 <= r < ROWS and 0 <= c < COLS): return [], 0
    if grid[r][c] is not None: return [], 0

    dirs = []
    lc, rc = nearest_nonempty_in_row(grid, r, c)
    if lc >= 0 and grid[r][lc] is not None: dirs.append(((r, lc), grid[r][lc]))
    if rc < COLS and grid[r][rc] is not None: dirs.append(((r, rc), grid[r][rc]))
    ur, dr = nearest_nonempty_in_col(grid, r, c)
    if ur >= 0 and grid[ur][c] is not None: dirs.append(((ur, c), grid[ur][c]))
    if dr < ROWS and grid[dr][c] is not None: dirs.append(((dr, c), grid[dr][c]))

    by_color = {}
    for coord, col in dirs:
        by_color.setdefault(col, []).append(coord)

    removed = set()
    pairs = 0
    for col, coords in by_color.items():
        if len(coords) >= 2:
            removed.update(coords)
            pairs += len(coords) // 2

    for rr, cc in removed:
        grid[rr][cc] = None
    return list(removed), pairs

def any_moves_exist(grid):
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] is not None: continue
            dirs = []
            lc, rc = nearest_nonempty_in_row(grid, r, c)
            if lc >= 0 and grid[r][lc] is not None: dirs.append(grid[r][lc])
            if rc < COLS and grid[r][rc] is not None: dirs.append(grid[r][rc])
            ur, dr = nearest_nonempty_in_col(grid, r, c)
            if ur >= 0 and grid[ur][c] is not None: dirs.append(grid[ur][c])
            if dr < ROWS and grid[dr][c] is not None: dirs.append(grid[dr][c])
            for col in set(dirs):
                if dirs.count(col) >= 2:
                    return True
    return False

def board_empty(grid):
    return all(grid[r][c] is None for r in range(ROWS) for c in range(COLS))

def moves_count(grid):
    cnt = 0
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] is not None: continue
            dirs = []
            lc, rc = nearest_nonempty_in_row(grid, r, c)
            if lc >= 0 and grid[r][lc] is not None: dirs.append(grid[r][lc])
            if rc < COLS and grid[r][rc] is not None: dirs.append(grid[r][rc])
            ur, dr = nearest_nonempty_in_col(grid, r, c)
            if ur >= 0 and grid[ur][c] is not None: dirs.append(grid[ur][c])
            if dr < ROWS and grid[dr][c] is not None: dirs.append(grid[dr][c])
            if any(dirs.count(col) >= 2 for col in set(dirs)):
                cnt += 1
    return cnt

def reset_round():
    return new_board(), 0.0, 0, ROUND_TIME

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Match Pairs")
    clock = pygame.time.Clock()

    grid = new_board()
    score = 0
    high = load_high()
    last_clear_ts = 0.0
    combo_level = 0
    time_left = ROUND_TIME
    last_tick = time.time()
    flash_bad_until = 0.0
    state = "playing"

    running = True
    while running:
        now = time.time()
        dt = now - last_tick
        last_tick = now

        if state == "playing":
            time_left -= dt
            if time_left <= 0:
                high = max(high, score)
                save_high(high)
                state = "gameover"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: running = False
                    elif event.key == pygame.K_n:
                        grid, last_clear_ts, combo_level, _ = reset_round()
                    elif event.key == pygame.K_r:
                        grid, last_clear_ts, combo_level, time_left = reset_round()
                        score = 0
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if mx < GRID_W and my < GRID_H:
                        c, r = mx // CELL, my // CELL
                        removed, pairs = try_clear_at(grid, r, c)
                        if pairs > 0:
                            if last_clear_ts and (now - last_clear_ts) <= COMBO_WINDOW:
                                combo_level += 1
                            else:
                                combo_level = 0
                            last_clear_ts = now
                            local_combo = combo_level
                            gained = 0
                            for _ in range(pairs):
                                gained += 1 + local_combo
                                local_combo += 1
                            score += gained
                        else:
                            time_left = max(0.0, time_left - PENALTY_ON_FAIL)
                            flash_bad_until = now + 0.15
            else:  
                # gameover
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    #restart
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER): 
                        grid, last_clear_ts, combo_level, time_left = reset_round()
                        score = 0
                        state = "playing"

        if state == "playing":
            if board_empty(grid) or not any_moves_exist(grid):
                grid, last_clear_ts, combo_level, _ = reset_round()
            draw_board(screen, grid, score, combo_level,
                       moves_left=moves_count(grid),
                       time_left=time_left, high=high,
                       flash_bad=(now < flash_bad_until))
        else:
            draw_board(screen, grid, score, combo_level,
                       moves_left=0, time_left=0, high=high)
            draw_gameover(screen, score, high)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
