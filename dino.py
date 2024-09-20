import random
import time


def dino_game():
    columns = []
    last_cacti = 0
    dino_height = 0
    dino_direction = 1
    speed = 1
    while True:
        last_cacti += 1
        for _ in range(40 - len(columns)):
            col, has_cacti = generate_column(last_cacti)
            columns.append(col)
            if has_cacti:
                last_cacti = 0

        rendered = "\033[2J\033[H"  # Clear the screen

        # Check if the third column has a cacti
        if columns[4][0] == "X" or dino_height > 0:
            if dino_height == 0:
                rendered += "\x07"
            dino_height += dino_direction
            if dino_height > 2:
                dino_direction = -1
            elif dino_height <= 0:
                dino_direction = 1

        tmp_columns = [list(x) for x in columns]
        tmp_columns[2][dino_height] = "█"

        # Render the columns
        for y in range(10)[::-1]:
            for x in range(40):
                rendered += tmp_columns[x][y]
            rendered += "\n"

        yield rendered
        # Remove the first column
        columns.pop(0)
        time.sleep(0.1 / speed)
        speed += 0.0025


def generate_column(last_cacti):
    column = [" "] * 10
    # Add floor
    column[0] = "_"
    has_added_cacti = False

    # The longer it's been since the last cacti, the more likely it is to generate one
    should_generate_cacti = (random.randint(0, 100) // last_cacti) == 0
    if should_generate_cacti and last_cacti > 10:
        cacti_height = random.randint(1, 3)
        for i in range(cacti_height):
            column[i] = "X"
        has_added_cacti = True

    return column, has_added_cacti

