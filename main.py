import math
from os import name
import blessed
import random

version = "v0.0.4" # > v0.0.5

term = blessed.Terminal()

fps = 30
mode = ""
viewx = -1
viewy = -1
camera = {"x": 0, "y": 0}
viewradius = 40

blueprints = {"player": {"name": "player", "icon": "@", "coll": True, "shadow": False, "light": 8, "fgcolor": (150, 90, 255), "entity": {"control": "gamer", "health": 100}},\
              "empty": {"name": "empty", "icon": ".", "fgcolor": (70, 70, 70)},\
              "npc": {"name": "john", "icon": "J", "coll": True, "shadow": False},\
              "wall": {"name": "wall", "icon": "#", "coll": True, "shadow": True}, \
              "inv_wall": {"name": "empty", "icon": ".", "coll": True, "shadow": False}, \
              "false_wall": {"name": "wall", "icon": "#", "coll": False, "shadow": True}, \
              "door": {"name": "door", "icon": "+", "coll": True, "shadow": True, "fgcolor": (230, 180, 140), "door_state": "closed"}, \
              "lightsource": {"name": "light", "icon": "3", "coll": False, "shadow": False, "light": 13, "fgcolor": (250, 220, 70)},\
              "fog": {"name": "fog", "icon": "*", "coll": False, "shadow": True, "fgcolor": (150, 150, 150)},\
              "stairs": {"name": "stairs", "icon": ">", "coll": False, "shadow": False, "fgcolor": (250, 160, 80), "to_level": -1}}

flags = {"state": "alive", "Level": -1, "fgcolor": (230, 230, 230), "bgcolor": (6,5,9), "lighted_bgcolor": (16, 16, 22)}
objects = {}
lights = {} # {"radius": int, "x": int, "y": int, "color": list}
coords = {}
actions = {}
entities = {} # {"aliance": str, "behavior": str, "health": int, ""}

items = {}

room_wall_cache = 0
fog_cnt = 0
fogs = {}

#### Flags
def set_flag(name: str, value) -> None:
    flags[name] = value

def get_flag(name: str):
    # if name in flags: ## will be returned in future
    return flags[name]
    # return None

#### Coord cache
def add_coords(point: list | tuple, name: str) -> None:
    point = tuple(point)
    if point not in coords:
        coords[point] = []
    coords[point].append(name)

def rm_coords(point: list | tuple, name: str) -> None:
    point = tuple(point)
    coords[point].remove(name)

def check_coords(point: list | tuple, prop: str) -> bool:
    point = tuple(point)
    if point in coords:
        for name in coords[point]:
            if get_object(name, prop) == True: ## works with bool typed props
                return True
    return False

def get_coord_with_prop(point: list | tuple, prop: str) -> dict:
    point = tuple(point)
    to_ret = {}
    if point in coords:
        for name in coords[point]:
            if obj_prop(name, prop):
                to_ret[name] = get_object(name, prop)
    return to_ret

#### Objects
def add_object(name: str, bp: str, x: int, y: int, params: dict = {}) -> None:
    objects[name] = blueprints[bp] | params
    objects[name]["x"] = x
    objects[name]["y"] = y
    add_coords((x, y), name)
    mod_light(name, x, y, get_light_prop(name))

def rm_object(name: str):
    if name in objects:
        x = get_object(name, "x")
        y = get_object(name, "y")
        del objects[name]
        rm_coords((x, y), name)
        if name in lights:
            del lights[name]

def ch_object(name: str, params: dict):
    objects[name] = objects[name] | params
    mod_light(name, get_object(name, "x"), get_object(name, "y"), get_light_prop(name))

def get_object(name: str, prop: str):
    return objects[name][prop]

def obj_prop(name: str, prop: str):
    if prop in objects[name]:
        return True
    return False

def move_object(name: str, xshift: int, yshift: int, ignore_coll = False):
    x = get_object(name, "x")
    y = get_object(name, "y")
    newx = x + xshift
    newy = y + yshift
    pair = [newx, newy]
    
    lvs = get_coord_with_prop(pair, "to_level")
    if lvs != {}:
        match lvs[list(lvs.keys())[0]]:
            case 1: load_level_1()
            case 2: load_level_2()
    elif not check_coords(pair, "coll") or ignore_coll:
        ch_object(name, {"x": newx, "y": newy})
        rm_coords((x, y), name)
        add_coords((newx, newy), name)
        if get_object(name, "light") != -1:
            mod_light(name, newx, newy, get_light_prop(name))
    else:
        doors = get_coord_with_prop(pair, "door_state")
        if doors != {}:
            ch_object(list(doors.keys())[0],\
                      {"icon": "-", "coll": False, "shadow": False, "door_state": "opened"})

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
        for seg in range(abs(y) + 1):
            points.append((xstart, ystart + seg * y / abs(y)))
    elif y == 0:
        for seg in range(abs(x) + 1):
            points.append((xstart + seg * x / abs(x), ystart))
    else:
        limit = max(abs(x), abs(y))

        dx = x/limit
        dy = y/limit

        for seg in range(limit + 1):
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
def get_light_prop(name: str) -> int:
    if "light" in objects[name]:
        return get_object(name, "light")
    return -1

def mod_light(name: str, x: int, y: int, radius: int):
    if radius != -1:
        lights[name] = {"x": x, "y": y, "radius": radius}
    else:
        if name in lights:
            del lights[name]

#### Items

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

#### Doors
def interact_door(id): ## Are you blind? use this func in v0.0.5!
    match get_object(id, "state"):
        case "closed":
            ch_object(id, {"icon": "-", "coll": False, "shadow": False})
        case "open":
            ch_object(id, {"icon": "+", "coll": True, "shadow": True})

## UI funcs
def update_screen():
    global viewx, viewy, buf
    viewx = term.width // 2
    viewy = term.height // 2
    buf = {}
    objectbuf = {}

    ## What objects COULD be displayed
    for object_name, Object in objects.items():
        x = Object["x"]
        y = Object["y"]

        if x > camera["x"] - viewx and x < camera["x"] + viewx and y > camera["y"] - viewy and y < camera["y"] + viewy:
            objectbuf[(x, y)] = {"name": object_name, "icon": Object["icon"], "shadow": Object["shadow"]}
            if "fgcolor" in Object:
                objectbuf[(x, y)]["fgcolor"] = Object["fgcolor"]
            else:
                objectbuf[(x, y)]["fgcolor"] = get_flag("fgcolor")

    objectbuf[(get_object("player", "x"), get_object("player", "y"))] = {"name": "player", "icon": get_object("player", "icon"), "shadow": False, "fgcolor": get_object("player", "fgcolor")}#"color": term.on_color_rgb(255,255,255) + term.color_rgb(0,0,0)}

    ## fov + darkness
    none = term.on_color_rgb(*get_flag("bgcolor")) + " "
    for screen_y, abs_y in enumerate(range(camera["y"] + viewy, camera["y"] + viewy - term.height + 2 ,  -1)):
        for screen_x, abs_x in enumerate(range(camera["x"] - viewx, camera["x"] - viewx + term.width - 1)):
            key = (abs_x, abs_y)
            if math.dist(camera.values(), key) <= viewradius: ## if point in viewradius
                if not any(check_coords(p, "shadow") for p in line_area(list(camera.values()), list(key))[1:-1]): ## if in player's viewfield
                    for Source in lights.values():
                        if Source["radius"] > math.dist([Source["x"], Source["y"]], key):
                            # if not any(check_coords(p, "shadow") for p in line_area([Source["x"], Source["y"]], list(camera.values()))[1:-1] ):
                            if not any(check_coords(p, "shadow") for p in line_area([Source["x"], Source["y"]], list(key))[1:-1]):
                                if key in objectbuf:
                                    buf[(screen_x, screen_y)] = term.color_rgb(*objectbuf[key]["fgcolor"]) + term.on_color_rgb(*get_flag("lighted_bgcolor")) + objectbuf[key]["icon"]
                                else:
                                    buf[(screen_x, screen_y)] = term.color_rgb(*blueprints["empty"]["fgcolor"]) + term.on_color_rgb(*get_flag("lighted_bgcolor")) + blueprints["empty"]["icon"]
                                break
                            else:
                                buf[(screen_x, screen_y)] = none
                    else:
                        buf[(screen_x, screen_y)] = none
                else:
                    buf[(screen_x, screen_y)] = none
            else:
                buf[(screen_x, screen_y)] = none
        buf[(screen_x, screen_y)] += "\n"

    add_text(1, 1, "Level: " + str(get_flag("Level")), (0, 0, 0), (230, 230, 230))
    add_text(1, 2, "x: " + str(camera["x"]), (250, 100, 90))
    add_text(1, 3, "y: " + str(camera["y"]), (250, 240, 90))

    print(term.home + term.clear + "".join(buf.values())) # Wow, I scrolled at the end of this func.

def add_text(x: int, y: int, text: str, fgcolor: tuple = get_flag("fgcolor"), bgcolor: tuple = get_flag("bgcolor")) -> None:
    global buf
    for num, iconbol in enumerate(text):
        buf[(x + num, y)] = term.color_rgb(*fgcolor) + term.on_color_rgb(*bgcolor) + iconbol

def paint():
    ...
#### Actions
def action_update():
    for action in actions:
        ...

#### Entities
...

#### Levels
def init_data(level_num: int):
    global objects, coords, lights, actions, entities, camera
    objects = {}
    lights = {}
    coords = {}
    actions = {}
    entities = {}
    camera = {"x": 0, "y": 0}
    set_flag("Level", level_num)

def add_room(xstart, ystart, width, height, enter: list | tuple):
    global room_wall_cache
    for num, p in enumerate(\
                xor_areas(\
                    xor_areas(square_area(xstart, ystart, width, height), square_area(xstart + 1, ystart + 1, width - 2, width - 2)),\
                    square_area(enter[0], enter[1], 1, 1))):
        add_object("room_wall_" + str(room_wall_cache + num), "wall", *p)
    room_wall_cache = num + room_wall_cache + 1

def load_level_1():
    init_data(1)
    add_object("player", "player", 0, 0)
    add_object("wall0", "wall", 3, 0)
    add_object("wall1", "wall", -2, 4)
    add_object("light2", "lightsource", 9, -3)
    add_object("wall2", "wall", 0, -4)
    add_object("light0", "lightsource", -12, 8)
    add_object("light1", "lightsource", -16, -16)
    add_object("stairs_to_l2", "stairs", 21, 35, {"to_level": 2})
    add_room(18, 32, 8, 8, [21, 32])
    add_object("door0", "door", 21, 32)
    add_room(-20, -20, 11, 11, [-15, -10])
    add_object("door1", "door", -15, -10)
    add_room(30, 10, 10, 10, [30, 15])
    add_object("door2", "door", 30, 15)
    for num in range(9):
        add_object("fog_area" + str(num), "fog", -7 - num % 3, 3 + num // 3)
    # for num, p in enumerate(\
    #             xor_areas(\
    #                 xor_areas(square_area(-20, -20, 11, 11), square_area(-19, -19, 9, 9)),\
    #                 square_area(-15, -10, 1, 1))):
    #     add_object("room_wall" + str(num), "wall", *p)

def load_level_2():
    init_data(2)
    add_object("player", "player", 0, 0)

## Main code
if __name__ == "__main__":
    mode = "rpg"
    load_level_1()
    set_flag("level_dbg", "0")

    with term.cbreak(), term.fullscreen(), term.hidden_cursor():
        while 1:
            match mode:
                case "rpg":
                    update_screen()
                    inp = term.inkey(timeout=1/fps)
                    if inp:
                        move = [0, 0]
                        match inp:
                            case "d": mode = "debug_objects"
                            case "f": mode = "debug_flags"
                            case "h": move[0] = -1
                            case "l": move[0] = 1
                            case "k": move[1] = 1
                            case "j": move[1] = -1
                            case "y": move = [-1, 1]
                            case "u": move = [1, 1]
                            case "b": move = [-1, -1]
                            case "n": move = [1, -1]
                            case "w": fogs_update()
                            case "1": load_level_1()
                            case "2": load_level_2()
                            case "q": exit(0)
                        if move != [0,0]:
                            move_object("player", move[0], move[1])
                            camera["x"] = get_object("player", "x")
                            camera["y"] = get_object("player", "y")
                            fogs_update()
                case "item_menu":
                    ...
                case "art":
                    ...
                case "debug_objects":
                    print(term.normal + term.home + term.clear + str(list(objects.keys())))
                    inp = input() #term.inkey(timeout=1/fps)
                    match inp:
                        case "q": mode = "rpg"
                        case _:
                            if inp in list(objects.keys()):
                                print(term.home + term.clear + inp + " :: " + str(objects[inp]))
                                input()
                case "debug_flags":
                    print(term.normal + term.home + term.clear + str(flags))
                    inp = input() #term.inkey(timeout=1/fps)
                    mode = "rpg"
