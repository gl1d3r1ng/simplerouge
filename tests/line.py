import math
import random
import blessed

term = blessed.Terminal()

def create_line(p1: list, p2: list) -> tuple[float, float, int, int]:
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]

    if x == y == 0:
        return 0, 0, p1[0], p1[1]
    r = math.dist(p1, p2)
    if x == 0:
        if y > 0: 
            a = math.radians(90)
        else:
            a = math.radians(270)
    else:
        a = math.atan(y/x)
        if x < 0:
            a += math.pi
        a = round(a, 4)

    return r, a, p1[0], p1[1]

def get_from_line(seg: int, a: float | int, xstart: int, ystart: int) -> tuple[int | float, int | float]:
    x = round(math.cos(a) * seg) + xstart
    y = round(math.sin(a) * seg) + ystart
    return x, y

def get_all_from_line_trig(r: float | int, a: float | int, xstart: int, ystart: int) -> list:
    points = []
    for seg in range(1, round(r) + 1):
        points.append(get_from_line(seg, a, xstart, ystart))
    return points

def alt_get_all_line_1(p1: list, p2: list) -> list: ## not working, as i remember
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]

    points = []
    
    if x == 0:
        for i in range(1, y + 1):
            points.append((p1[0], p1[1] + i))
        return points 
    ta = y / x
    if -1 <= ta <= 1:
        for i in range(min(p1[0], p2[0]) + 1, max(p1[0], p2[0])+ 2):
            points.append((p1[0] + i, p1[1] + round(ta * i)))
    else:
        for i in range(min(p1[1], p2[1]) + 1, max(p1[1], p2[1])+ 2):
            points.append((p1[0] + round(ta ** -1 * i), p1[1] + i))

    return points

def get_from_all_line(p1: list, p2: list) -> list:
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]

    startx = float(p1[0])
    starty = float(p1[1])

    points = []

    if y == x and x == 0:
        pass
    elif x == 0:
        for seg in range(1, abs(y) + 1):
            points.append((startx, starty + seg * y / abs(y)))
    elif y == 0:
        for seg in range(1, abs(x) + 1):
            points.append((startx + seg * x / abs(x), starty))
    else:
        limit = max(abs(x), abs(y))

        dx = x/limit
        dy = y/limit

        for seg in range(1, limit + 1):
            points.append((round(startx + dx*seg), round(starty + dy*seg)))
    return points

p1 = [1, 2]
p2 = [3, 2]

with term.fullscreen(), term.cbreak():
    while True:
        #r, a, xstart, ystart = create_line(p1, p2)
        #print(r, a, xstart, ystart)
        # points = get_all_from_line(r, a, xstart, ystart)
        points = alt_get_all_line_1(p1, p2)
        print(points)

        buffer = ""
        sx = abs(p1[0] - p2[0])
        sy = abs(p1[1] - p2[1])
        for y in range(20, -20, -1):
            for x in range(-20, 20):
                key = (x, y)
                if key == tuple(p1):
                    buffer += "@"
                elif key == tuple(p2):
                    buffer += "%"
                elif key in points:
                    buffer += "*"
                elif key == (0, 0):
                    buffer += "0"
                else:
                    buffer += "."
            buffer += "\n"

        inp = term.inkey(timeout=1/30)
        match inp:
            case "h": p1[0] -= 1
            case "l": p1[0] += 1
            case "j": p1[1] -= 1
            case "k": p1[1] += 1
            case "a": p2[0] -= 1
            case "d": p2[0] += 1
            case "s": p2[1] -= 1
            case "w": p2[1] += 1
            case "q": exit()
        print(term.home + term.clear() + buffer)
