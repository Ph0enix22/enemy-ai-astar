import pygame
import heapq
import sys

# Window & grid settings
TILE_SIZE = 32
COLS = 20
ROWS = 20
WIN_W = COLS*TILE_SIZE
WIN_H = ROWS*TILE_SIZE
FPS = 30
MOVE_RATE = 8

# Colour palette
BG_COLOR = (15, 15, 25)
WALL_COLOR = (55, 55, 75)
FLOOR_COLOR = (28, 28, 42)
PLAYER_COLOR = (80, 220, 100)
ENEMY_COLOR = (220, 55, 55)
PATH_COLOR = (60, 120, 200, 100)
HUD_BG = (10, 10, 20)
TEXT_COLOR = (200, 200, 220)
CAUGHT_COLOR = (255, 80, 80)

# Map (0=floor, 1=wall/obstacle)
GRID = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,0,1,1,1,0,1,1,0,1,0,1,1,1,0,1,1,0],
    [0,0,1,0,0,0,1,0,1,0,0,1,0,0,0,1,0,0,0,0],
    [0,0,1,1,1,0,1,0,1,0,1,1,1,1,0,1,1,1,0,0],
    [0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0],
    [0,1,1,0,1,1,1,1,1,0,1,1,0,1,1,1,0,1,0,0],
    [0,1,0,0,0,0,0,0,1,0,1,0,0,0,0,1,0,1,0,0],
    [0,1,0,1,1,1,1,0,1,0,1,0,1,1,0,1,0,0,0,0],
    [0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,1,0],
    [0,1,1,1,0,1,1,1,1,1,1,0,1,0,1,1,0,1,0,0],
    [0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,1,0,0],
    [0,1,1,1,0,1,0,1,1,0,1,1,1,0,1,0,1,1,0,0],
    [0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0],
    [0,1,0,1,1,1,0,1,0,1,1,0,1,1,1,0,1,0,1,0],
    [0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0],
    [0,1,1,1,0,1,1,1,0,1,0,1,1,0,1,1,1,0,1,0],
    [0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0,1,0],
    [0,1,1,0,1,1,0,1,1,1,0,1,0,1,1,0,1,0,1,0],
    [0,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# A* search
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(grid, start, goal):
    rows = len(grid)
    cols = len(grid[0])

    # Min-heap entries are (f_score, cell)
    open_heap = [(0, start)]
    open_set  = {start}

    came_from = {}
    g = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        open_set.discard(current)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        r, c = current
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] != 0:
                continue

            neighbor = (nr, nc)
            new_g = g[current] + 1

            if new_g < g.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g[neighbor] = new_g
                f = new_g + manhattan(neighbor, goal)
                if neighbor not in open_set:
                    heapq.heappush(open_heap, (f, neighbor))
                    open_set.add(neighbor)

    return []   # no path found

# Rendering helpers
def draw_grid(surface, grid, path_cells):
    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            color = WALL_COLOR if grid[row][col] == 1 else FLOOR_COLOR
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BG_COLOR, rect, 1)

    if path_cells:
        tile_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        tile_surf.fill(PATH_COLOR)
        for (r, c) in path_cells:
            surface.blit(tile_surf, (c * TILE_SIZE, r * TILE_SIZE))

def draw_circle_entity(surface, pos, color):
    row, col = pos
    cx = col * TILE_SIZE + TILE_SIZE // 2
    cy = row * TILE_SIZE + TILE_SIZE // 2
    radius = TILE_SIZE // 2 - 3
    pygame.draw.circle(surface, color, (cx, cy), radius)
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius, 2)

def draw_hud(surface, font, message, step_count):
    hud_rect = pygame.Rect(0, WIN_H, WIN_W, 28)
    pygame.draw.rect(surface, HUD_BG, hud_rect)
    label = font.render(
        f"WASD / Arrows: Move   |   Steps: {step_count}   |   {message}",
        True, TEXT_COLOR
    )
    surface.blit(label, (8, WIN_H + 5))

# Main game loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H + 28))
    pygame.display.set_caption("Enemy AI ~ A* Pathfinding")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 14)

    # Spawn corners so the enemy has a long initial chase
    player = [19, 0]
    enemy = [0, 19]

    path = []
    frame = 0
    steps = 0
    game_over = False
    status = "Survive!"

    while True:
        clock.tick(FPS)
        frame += 1

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        main()
                        return
                    continue

                dr, dc = 0, 0
                if event.key in (pygame.K_w, pygame.K_UP):    dr = -1
                if event.key in (pygame.K_s, pygame.K_DOWN):  dr =  1
                if event.key in (pygame.K_a, pygame.K_LEFT):  dc = -1
                if event.key in (pygame.K_d, pygame.K_RIGHT): dc =  1

                nr, nc = player[0] + dr, player[1] + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and GRID[nr][nc] == 0:
                    player[0], player[1] = nr, nc
                    steps += 1

        if not game_over:
            # A* recalculation + enemy step
            if frame % MOVE_RATE == 0:
                path = astar(GRID, tuple(enemy), tuple(player))
                if path:
                    enemy[0], enemy[1] = path[0]

            # Catch check
            if enemy == player:
                game_over = True
                status = "CAUGHT!  Press R to restart"

        # Draw
        screen.fill(BG_COLOR)

        visible_path = set(path[1:]) if path else set()
        draw_grid(screen, GRID, visible_path)
        draw_circle_entity(screen, tuple(player), PLAYER_COLOR)
        draw_circle_entity(screen, tuple(enemy),  ENEMY_COLOR)

        if game_over:
            msg = font.render("CAUGHT!  Press R to restart", True, CAUGHT_COLOR)
            screen.blit(msg, (WIN_W // 2 - msg.get_width() // 2, WIN_H // 2))

        draw_hud(screen, font, status, steps)
        pygame.display.flip()

if __name__ == "__main__":
    main()