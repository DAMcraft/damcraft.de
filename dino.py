import random
import time
from typing import List, Generator, Tuple


class GameState:
    columns: List[List[str]]
    last_cacti: int = 0
    dino_height: int = 0
    dino_direction: int = 1
    speed: float = 1.0
    bell_triggered: bool = False

    def __init__(self):
        self.columns = []


SCREEN_WIDTH = 40
SCREEN_HEIGHT = 10
DINO_POSITION = 2
MAX_JUMP_HEIGHT = 2
MIN_CACTI_DISTANCE = 10
SPEED_INCREMENT = 0.0025
CLEAR_SCREEN = "\033[J\033[H"
DINO_CHAR = "█"
CACTI_CHAR = "X"
FLOOR_CHAR = "_"
EMPTY_CHAR = " "
BELL_CHAR = "\x07"


def generate_column(last_cacti: int) -> Tuple[List[str], bool]:
    column = [EMPTY_CHAR] * SCREEN_HEIGHT
    column[0] = FLOOR_CHAR

    if (last_cacti > MIN_CACTI_DISTANCE and
            random.random() < 1 / max(1, last_cacti)):
        height = random.randint(1, 3)
        for i in range(height):
            column[i] = CACTI_CHAR
        return column, True
    return column, False


def update_dino_state(state: GameState) -> None:
    if state.columns[4][0] == CACTI_CHAR or state.dino_height > 0:
        if state.dino_height == 0:
            state.bell_triggered = True

        state.dino_height += state.dino_direction
        if state.dino_height > MAX_JUMP_HEIGHT:
            state.dino_direction = -1
        elif state.dino_height <= 0:
            state.dino_direction = 1


def render_frame(state: GameState) -> str:
    tmp_columns = [list(col) for col in state.columns]
    tmp_columns[DINO_POSITION][state.dino_height] = DINO_CHAR

    frame = [CLEAR_SCREEN]
    if state.bell_triggered:
        frame.append(BELL_CHAR)
        state.bell_triggered = False

    frame.extend(
        ''.join(tmp_columns[x][y] for x in range(SCREEN_WIDTH)) + '\n'
        for y in range(SCREEN_HEIGHT - 1, -1, -1)
    )
    return ''.join(frame)


def dino_game() -> Generator[str, None, None]:
    state = GameState()

    while True:
        state.last_cacti += 1

        # generate new columns
        needed_columns = SCREEN_WIDTH - len(state.columns)
        for _ in range(needed_columns):
            col, has_cacti = generate_column(state.last_cacti)
            state.columns.append(col)
            if has_cacti:
                state.last_cacti = 0

        # dino movement logic
        update_dino_state(state)

        # render and yield frame
        yield render_frame(state)

        # update game state
        state.columns.pop(0)
        time.sleep(0.1 / state.speed)
        state.speed += SPEED_INCREMENT
