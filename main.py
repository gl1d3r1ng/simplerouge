import math
import blessed
import random

version = "v0.0.2" # > v0.0.3
term = blessed.Terminal()

fps = 30
mode = ""
viewx = -1
viewy = -1
camera = {"x": 0, "y": 0}
viewradius = 30

blueprints = {"player": {"name": "player", "sym": "@", "coll": True, "shadow": False, "light": 8},\
              "wall": {"name": "wall", "sym": "#", "coll": True, "shadow": True, "light": -1}, \
              "inv_wall": {"name": "empty", "sym": ".", "coll": True, "shadow": False, "light": -1}, \
              "false_wall": {"name": "wall", "sym": "#", "coll": False, "shadow": True, "light": -1}, \
            "lightsource": {"name": "light", "sym": "3", "coll": False, "shadow": False, "light": 16},\
              "fog": {"name": "fog", "sym": "*", "coll": False, "shadow": True, "light": -1}}

flags = {}
objects = {}
lights = {} # {"radius": int, "x": int, "y": int, "color": list}
actions = {}
entities = {} # {"aliance": str, "behavior": str, "health": int, ""}

fog_cnt = 0
fogs = {}

#### Flags
def set_flag(name: str, value) -> None:
    flags[name] = value

def get_flag(name: str):
    # if name in flags:
    return flags[name]
    # return None

#### Objects
def add_object(name: str, bp: str, x: int, y: int, params: dict = {}) -> None:
    objects[name] = blueprints[bp] | params
    objects[name]["x"] = x
    objects[name]["y"] = y
    mod_light(name, x, y, get_object(name, "light"))

def rm_object(name: str):
    if name in objects:
        del objects[name]
        if name in lights:
            del lights[name]

def ch_object(name: str, params: dict):
    objects[name] = objects[name] | params
    mod_light(name, get_object(name, "x"), get_object(name, "y"), get_object(name, "light"))

def get_object(name: str, prop: str):
    return objects[name][prop]

def move_object(name: str, x: int, y: int, ignore_coll = False):
    newx = get_object(name, "x") + x
    newy = get_object(name, "y") + y
    for object in objects:
        if get_object(object, "x") == newx and get_object(object, "y") == newy:
            if get_object(object, "coll") and not ignore_coll:
                break
    else:
        ch_object(name, {"x": newx, "y": newy})
        if get_object(name, "light") != -1:
            mod_light(name, newx, newy, get_object(name, "light"))

#### Areas
def line_area(p1: list, p2: list) -> list:
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]

    xstart = float(p1[0])
    ystart = float(p1[1])

    points = []

    if y == x and x == 0:
        pass
    elif x == 0:
        for seg in range(1, abs(y) + 1):
            points.append((xstart, ystart + seg * y / abs(y)))
    elif y == 0:
        for seg in range(1, abs(x) + 1):
            points.append((xstart + seg * x / abs(x), ystart))
    else:
        limit = max(abs(x), abs(y))

        dx = x/limit
        dy = y/limit

        for seg in range(1, limit + 1):
            points.append((round(xstart + dx*seg), round(ystart + dy*seg)))
    return points

def circle_area(center: list, radius: int) -> list:
    points = []
    for y in range(center[1] - radius, center[1] + radius + 1):
        for x in range(center[0] - radius, center[0] + radius + 1):
            if math.dist(center, [x,y]) <= radius:
                points.append((x, y))
    return points

def square_area(xstart: int, ystart: int, xsize: int, ysize: int) -> list:
    points = []
    for y in range(min(0, ysize), max(0, ysize)):
        y = ystart + y
        for x in range(min(0, xsize), max(0, xsize)):
            points.append((xstart + x, y))
    return points

def xor_areas(area1: list, area2: list) -> list:
    area = area1 + area2
    for i in set(area1).intersection(set(area2)):
        while i in area:
            area.remove(i)
    return area

#### Light
def mod_light(name: str, x: int, y: int, radius: int):
    if radius != -1:
        lights[name] = {"x": x, "y": y, "radius": radius}
    else:
        if name in lights:
            del lights[name]

#### Fog
def fogs_update():
    global fog_cnt
    for i in range(random.randint(0, 4)): ## make make_fog func
        name = "fog" + str(fog_cnt)
        add_object(name, "fog", 6 + random.randint(-2, 2), 6 + random.randint(-2, 2))
        fogs[name] = {"ttl": random.randint(1, 5)}
        fog_cnt += 1
        if fog_cnt >= 10000:
            fog_cnt = 0
    
    to_remove = []
    
    for name in fogs:
        value = fogs[name]
        if value["ttl"] == 1:
            to_remove.append(name)
        else:
            value["ttl"] -= 1

    for name in to_remove: 
        fogs.pop(name)
        rm_object(name)


## UI funcs
def update_screen():
    global viewx, viewy, buf
    viewx = term.width // 2
    viewy = term.height // 2
    buf = {}
    objectbuf = {}
    viewbuf = {}

    ## What objects COULD be displayed
    for object in objects:
        x = get_object(object, "x")
        y = get_object(object, "y")

        if x > camera["x"] - viewx and x < camera["x"] + viewx and y > camera["y"] - viewy and y < camera["y"] + viewy:
            objectbuf[(x, y)] = {"name": object, "sym": get_object(object, "sym"), "shadow": get_object(object, "shadow")}

    ## remove object not in players field of view
    for angle in range(-180 * 3, 180 * 3 + 1):
        angle //= 3
        xcof = math.cos(math.radians(angle))
        ycof = math.sin(math.radians(angle))
        for d in range(1, viewradius):
            x = round(camera["x"] + d * xcof)
            y = round(camera["y"] + d * ycof)
            key = (x, y)
            # color = round(255 * (1 - 1 / viewradius * d))
            if key in objectbuf:
                object = objectbuf[key]
                viewbuf[key] = object #| {"color": bgcolor + fgcolor}
                if object["shadow"]:
                    break
            else:
                viewbuf[key] = {"name": "emptyness", "sym": "."}#, "color": bgcolor+ fgcolor}

    viewbuf[(get_object("player", "x"), get_object("player", "y"))] = {"name": "player", "sym": get_object("player", "sym")}#"color": term.on_color_rgb(255,255,255) + term.color_rgb(0,0,0)}

    ## final steps + darkness
    for screen_y, abs_y in enumerate(range(camera["y"] + viewy, camera["y"] + viewy - term.height + 2 ,  -1)):
        for screen_x, abs_x in enumerate(range(camera["x"] - viewx, camera["x"] - viewx + term.width - 1)):
            key = (abs_x, abs_y)
            if key in viewbuf:
                # buf += viewbuf[(x, y)]["color"] + viewbuf[(x, y)]["sym"]
                for source, Source in lights.items():
                    if Source["radius"] >= math.dist([Source["x"], Source["y"]], key):
                        buf[(screen_x, screen_y)] = viewbuf[key]["sym"]
                        break
                else:
                    buf[(screen_x, screen_y)] = " "
            else:
                buf[(screen_x, screen_y)] = " "# term.on_color_rgb(0,0,0) + " "
        buf[(screen_x, screen_y)] += "\n"

    add_text(1, 1, "Text")

    print(term.home + term.clear + "".join(buf.values())) # Wow, I scrolled at the end of this func.

def add_text(x: int, y: int, text: str) -> None:
    global buf
    for num, symbol in enumerate(text):
        buf[(x + num, y)] = symbol

#### Actions
def action_update():
    for action in actions:
        ...

#### Entities
...

## Main code
if __name__ == "__main__":
    mode = "rpg"
    add_object("player", "player", 0, 0)
    add_object("wall0", "wall", 2, 0)
    add_object("wall1", "wall", -1, 2)
    add_object("wall2", "wall", 0, -1)
    add_object("light0", "lightsource", -7, 7)
    add_object("light1", "lightsource", -14, -14)
    for num, p in enumerate(\
                xor_areas(\
                    xor_areas(square_area(-18, -18, 9, 9), square_area(-17, -17, 7, 7)),\
                    square_area(-15, -10, 1, 1))):
        add_object("room_wall" + str(num), "wall", *p)

    # print(lights); exit()
    with term.cbreak(), term.fullscreen(), term.hidden_cursor():
        while 1:
            match mode:
                case "rpg":
                    update_screen()
                    inp = term.inkey(timeout=1/fps)
                    if inp:
                        move = [0, 0]
                        match inp:
                            case "h": move[0] = -1
                            case "l": move[0] = 1
                            case "k": move[1] = 1
                            case "j": move[1] = -1
                            case "y": move = [-1, 1]
                            case "u": move = [1, 1]
                            case "b": move = [-1, -1]
                            case "n": move = [1, -1]
                            case "w": fogs_update()
                            case "q":
                                exit(0)
                        if move != [0,0]:
                            move_object("player", move[0], move[1])
                            camera["x"] = get_object("player", "x")
                            camera["y"] = get_object("player", "y")
                            fogs_update()
                case "art":
                    ...
