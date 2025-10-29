import math
import blessed
import random

version = "v0.0.1"
term = blessed.Terminal()

fps = 30
mode = ""
viewx = -1
viewy = -1
camera = {"x": 0, "y": 0}
viewradius = 28

blueprints = {"player": {"name": "player", "sym": "@", "coll": True, "shadow": False}, "wall": {"name": "wall", "sym": "#", "coll": True, "shadow": True}}

flags = {}
objects = {}

def set_flag(name: str, value) -> None:
    flags[name] = value

def get_flag(name: str):
    return flags[name]

def add_object(name: str, bp: str, x: int, y: int, params: dict = {}) -> None:
    objects[name] = blueprints[bp] | params
    objects[name]["x"] = x
    objects[name]["y"] = y

def rm_object(name: str):
    del objects[name]

def ch_object(name: str, params: dict):
    objects[name] = objects[name] | params

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

def update_screen():
    global viewx, viewy
    viewx = term.width // 2
    viewy = term.height // 2
    buf = ""
    objectbuf = {}
    viewbuf = {}

    for object in objects:
        x = get_object(object, "x")
        y = get_object(object, "y")
        if object == "player":
            ...
        if x > camera["x"] - viewx and x < camera["x"] + viewx and y > camera["y"] - viewy and y < camera["y"] + viewy:
            objectbuf[(x, y)] = {"name": object, "sym": get_object(object, "sym"), "shadow": get_object(object, "shadow")}

    for angle in range(-180, 181):
        xcof = math.cos(math.radians(angle))
        ycof = math.sin(math.radians(angle))
        for d in range(1, viewradius):
            x = round(camera["x"] + d * xcof)
            y = round(camera["y"] + d * ycof)
            key = (x, y)
            color = round(255 * (1 - 1 / viewradius * d))
            bgcolor = term.on_color_rgb(*[color] * 3)
            fgcolor = term.color_rgb(*[255 if color < 128 else 0] * 3)
            if key in objectbuf:
                object = objectbuf[key]
                viewbuf[key] = object | {"color": bgcolor + fgcolor}
                if object["shadow"]:
                    break
            else:
                viewbuf[key] = {"name": "emptyness", "sym": ".", "color": bgcolor+ fgcolor}

    viewbuf[(get_object("player", "x"), get_object("player", "y"))] = {"name": "player", "sym": get_object("player", "sym"), "color": term.on_color_rgb(255,255,255) + term.color_rgb(0,0,0)}


    # print(viewbuf)
    even_x_shift = 0 if term.width % 2 == 1 else -1
    even_y_shift = 0 if term.height % 2 == 1 else 1
    for y in range(camera["y"] + viewy, camera["y"] - viewy + even_y_shift,  -1):
        for x in range(camera["x"] - viewx, camera["x"] + viewx + 1 + even_x_shift):
            if (x, y) in viewbuf:
                buf += viewbuf[(x, y)]["color"] + viewbuf[(x, y)]["sym"]
            else:
                buf += term.on_color_rgb(0,0,0) + " "
        buf += "\n"

    print(term.home + term.clear + buf)

mode = "rpg"
add_object("player", "player", 0, 0)
add_object("wall0", "wall", 2, 0)
add_object("wall1", "wall", -1, 2)
add_object("wall2", "wall", 0, -1)

with term.hidden_cursor(), term.cbreak():
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
                        case "q":
                            exit(0)
                    if move != [0,0]:
                        move_object("player", move[0], move[1])
                        camera["x"] = get_object("player", "x")
                        camera["y"] = get_object("player", "y")
            case "art":
                ...
