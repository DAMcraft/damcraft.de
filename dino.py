import random
import time
from collections import deque


def dino_game():
    columns = deque(maxlen=40)
    last_cacti = 0
    dino_height = 0
    dino_direction = 1
    speed = 1
    reversed_rows = list(range(10))[::-1]  # Precompute reversed rows for rendering

    while True:
        last_cacti += 1

        # Generate new columns if needed
        while len(columns) < 40:
            col_str, has_cacti = generate_column(last_cacti)
            columns.append(col_str)
            if has_cacti:
                last_cacti = 0

        # Collision detection and dino movement
        if (len(columns) > 4 and columns[4][0] == 'X') or dino_height > 0:
            if dino_height == 0:
                beep = "\x07"
            else:
                beep = ""
            dino_height += dino_direction
            if dino_height > 2:
                dino_direction = -1
            elif dino_height <= 0:
                dino_direction = 1
        else:
            beep = ""

        # Build frame output
        frame = [f"\033[2J\033[H{beep}"]
        for y in reversed_rows:
            line = []
            for x in range(40):
                if x == 2 and y == dino_height:
                    line.append('█')
                else:
                    line.append(columns[x][y])
            frame.append(''.join(line))

        yield '\n'.join(frame)

        # Update game state
        columns.popleft()
        time.sleep(0.1 / speed)
        speed += 0.0025


def generate_column(last_cacti):
    # Create column with floor
    column = ['_'] + [' '] * 9
    has_added_cacti = False

    if last_cacti > 10 and random.random() < (0.3 / (last_cacti // 10 + 1)):
        cacti_height = random.randint(1, 3)
        for i in range(cacti_height):
            column[i] = 'X'
        has_added_cacti = True

    return ''.join(column), has_added_cacti
