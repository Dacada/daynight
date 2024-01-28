import math
from typing import Optional

import pygame
from pygame.math import Vector2
from pygame import Rect

WINX = 500
WINY = 500
GRIDX = 10
GRIDY = 10
RECTSIZE = 25.0
BALLSIZE = 10.0
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (127, 127, 127)
FRAMERATE = 60
BALLSPEED = 0.5


class GameState:
    def __init__(self):
        self.running = True
        self.paused = True

        self.grid = [[None]*GRIDY for _ in range(GRIDX)]
        r = Rect(0, 0, RECTSIZE, RECTSIZE)
        for j in range(GRIDY):
            for i in range(GRIDX):
                rect = r.move(RECTSIZE*i, RECTSIZE*j)
                self.grid[j][i] = (rect, i < GRIDX/2)

        gridsize = Vector2(GRIDX*RECTSIZE, GRIDY*RECTSIZE)
        self.dayball = gridsize/2
        self.nightball = gridsize/2
        self.dayball.x += gridsize.x/4
        self.nightball.x -= gridsize.x/4

        self.dayball_direction = Vector2(1, 1).normalize()
        self.nightball_direction = Vector2(-1, -1).normalize()


def process_events(state: GameState):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                state.paused = not state.paused


def draw(screen: pygame.Surface, state: GameState):
    screen.fill(GREY)

    displacement = Vector2(
        WINX//2-GRIDX*RECTSIZE//2,
        WINY//2-GRIDY*RECTSIZE//2
    )

    for j in range(GRIDY):
        for i in range(GRIDX):
            rect, daynight = state.grid[j][i]
            color = WHITE if daynight else BLACK
            rect = rect.move(displacement)
            pygame.draw.rect(screen, color, rect)

    pygame.draw.circle(screen, WHITE, state.dayball + displacement, BALLSIZE)
    pygame.draw.circle(screen, BLACK, state.nightball + displacement, BALLSIZE)


def advance_point(
    point: Vector2,
    direction: Vector2,
    speed: Vector2,
    dt: float
) -> Vector2:
    return point + direction * speed * dt


def ball_rect_collision(
    center: Vector2,
    radius: float,
    rect: Rect,
) -> Optional[Vector2]:
    # based on https://www.jeffreythompson.org/collision-detection/circle-rect.php
    test_x = center.x
    test_y = center.y

    xnormal = None
    if center.x < rect.left:
        test_x = rect.left
        xnormal = Vector2(-1, 0)
    elif center.x > rect.right:
        test_x = rect.right
        xnormal = Vector2(1, 0)

    ynormal = None
    if center.y < rect.top:
        test_y = rect.top
        ynormal = Vector2(1, 0)
    elif center.y > rect.bottom:
        test_y = rect.bottom
        ynormal = Vector2(-1, 0)

    dist_x = center.x - test_x
    dist_y = center.y - test_y
    distance = math.sqrt(dist_x*dist_x + dist_y*dist_y)

    if distance > radius:
        return None

    normal = None
    if rect.left <= center.x <= rect.right:
        normal = ynormal
    elif rect.top <= center.y <= rect.bottom:
        normal = xnormal

    # Fallback
    if normal is None:
        normal = Vector2(1, 0)

    return normal


def run_ball(
    center: Vector2,
    direction: Vector2,
    grid: list[list[tuple[Rect, bool]]],
    ball_type: bool,
    dt: float,
) -> tuple[Vector2, Vector2]:
    new_center = advance_point(center, direction, BALLSPEED, dt)
    new_direction = direction

    normal = None
    if new_center.x - BALLSIZE < 0:
        normal = Vector2(1, 0).normalize()
    elif new_center.y - BALLSIZE < 0:
        normal = Vector2(0, -1).normalize()
    elif new_center.x + BALLSIZE > RECTSIZE*GRIDX:
        normal = Vector2(-1, 0).normalize()
    elif new_center.y + BALLSIZE > RECTSIZE*GRIDY:
        normal = Vector2(0, 1).normalize()

    if normal is not None:
        new_direction = new_direction.reflect(normal)
        new_center = advance_point(center, new_direction, BALLSPEED, dt)

    for j in range(GRIDY):
        for i in range(GRIDX):
            rect, cell_type = grid[j][i]
            if cell_type != ball_type:
                continue
            normal = ball_rect_collision(center, BALLSIZE, rect)
            if normal is not None:
                new_direction = new_direction.reflect(normal)
                new_center = advance_point(center, new_direction, BALLSPEED, dt)
                grid[j][i] = (rect, not cell_type)
                break

    return new_center, new_direction


def run(state: GameState, dt: int):
    if state.paused:
        return
    state.dayball, state.dayball_direction = run_ball(
        state.dayball, state.dayball_direction, state.grid, True, dt
    )
    state.nightball, state.nightball_direction = run_ball(
        state.nightball, state.nightball_direction, state.grid, False, dt
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode([WINX, WINY])
    clock = pygame.time.Clock()
    state = GameState()

    dt = 1//FRAMERATE*1000
    while state.running:
        process_events(state)
        run(state, dt)
        draw(screen, state)
        pygame.display.flip()
        dt = clock.tick(FRAMERATE)

    pygame.quit()
    return 0


if __name__ == '__main__':
    exit(main())
