###NOTICES/INFORMATION###
#inspired by coder space on yt

#textures: https://www.doomworld.com/afterglow/textures/

"""
To make it easier to navigate, the code is seperated into sections with triple hashtag comments
Classes are more widely used to create simplicity
"""
###IMPORTS###

import pygame as pg
import sys
import math
import os
from collections import deque
from random import randint, random, choice, uniform
import json
import time
#import numpy as np

###BASIC FUNCTIONS###
#distance formula func
def distance_formula(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

#returns a list of numbers for the distance of each numbers in the input list from the input num
def number_distances(ar, num):
    return [abs(i-num) for i in ar]

def get_json(path):
    with open(path) as json_file:
        data = json.load(json_file)
    json_file.close()
    return data

#rotate an image
def rotate_image(image, angle):
    loc = image.get_rect().center
    rot_sprite = pg.transform.rotate(image, angle)
    rot_sprite.get_rect().center = loc
    return rot_sprite

###SETTINGS###

RANDOM_GENERATION = False #if true, portals will generate random mazes, else, player made mazes will be used(from levels.json)

# screen settings
RES = WIDTH, HEIGHT = 1600, 700 #1600, 700 is default, i might change it for simplicity sake

#statbar settings
STATBARRES = SWIDTH, SHEIGHT = WIDTH, 150 #WIDTH, 150 is default

# RES = WIDTH, HEIGHT = 1920, 1080
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 60

#player vars
PLAYER_POS = 1.5, 1.5  # cur_map
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 60
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_ARMOR = 100
RECOVERY_DELAY = 9999

QUEST_LIMIT = 3

#inventory
INVENTORY_SIZE = 9

#special ability vars
GAS_RECHARGE = 60 * 1000
GAS_RANGE = 5
GAS_DAMAGE = 50

#mouse vars
MOUSE_SENSITIVITY = 0.0003
MOUSE_MAX_REL = 40
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - MOUSE_BORDER_LEFT

#color of floor
FLOOR_COLOR = (30, 30, 30)

#fov stuff
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20

#scaling and screen distance
SCREEN_DIST = HALF_WIDTH / math.tan(HALF_FOV)
SCALE = WIDTH // NUM_RAYS

#texture variables
TEXTURE_SIZE = 256
HALF_TEXTURE_SIZE = TEXTURE_SIZE // 2

#icon vars
ICON_WIDTH, ICON_HEIGHT = 80, 80

#stats class for enemy npcs
class Stats: #just a class to store npc stats
    def __init__(self, attack_dist, speed, size, health, attack_dmg, accuracy):
        self.attack_dist = attack_dist
        self.speed = speed
        self.size = size
        self.health = health
        self.attack_damage = attack_dmg
        self.accuracy = accuracy


ENEMIES = {
    "basic": {
        "path" : 'resources/sprites/npc/basic/0.png',
        "scale": 0.6,
        "shift" : 0.38,
        "animation_time" : 180,
        "stats" : Stats(
            attack_dist = 2,
            speed = 0.04,
            size = 1,
            health = 150,
            attack_dmg = 15,
            accuracy = 0.6
        )
    },
    "zombie": {
        "path" : 'resources/sprites/npc/zombie/0.png',
        "scale": 1.75,
        "shift" : 0,
        "animation_time" : 200,
        "stats" : Stats(
            attack_dist = 2,
            speed = 0.03,
            size = 1.75,
            health = 200,
            attack_dmg = 20,
            accuracy = 0.5
        )
    },
    "gemdemon": {
        "path" : 'resources/sprites/npc/gemdemon/0.png',
        "scale": 1,
        "shift" : -0.15,
        "animation_time" : 200,
        "stats" : Stats(
            attack_dist = 2.5,
            speed = 0.05,
            size = 1,
            health = 200,
            attack_dmg = 18,
            accuracy = 0.6
        )
    },
    "tridemon": {
        "path": 'resources/sprites/npc/tridemon/0.png',
        "scale": 2,
        "shift": -0.05,
        "animation_time": 130,
        "stats" : Stats(
            attack_dist = 3,
            speed = 0.07,
            size = 2,
            health = 200,
            attack_dmg = 14,
            accuracy = 0.7
        )
    },
    "satansnovel": {
        "path": 'resources/sprites/npc/satansnovel/0.png',
        "scale": 1,
        "shift": -0.05,
        "animation_time": 120,
        "stats": Stats(
            attack_dist = 3,
            speed = 0.05,
            size = 1,
            health = 150,
            attack_dmg = 12,
            accuracy = 0.8
        )
    },
    "shadowslinger": {
        "path": 'resources/sprites/npc/shadowslinger/0.png',
        "scale": 1,
        "shift": 0.05,
        "animation_time": 130,
        "stats": Stats(
            attack_dist = 7.5,
            speed = 0.05,
            size = 1,
            health = 100,
            attack_dmg = 13,
            accuracy = 0.9
        )
    }
}


###PLAYER###


#player class
class Player:
    #define class variables when instanced
    def __init__(self, game):
        self.game = game
        self.x, self.y = BASE_DATA["spawn"][0], BASE_DATA["spawn"][1]
        self.angle = 1e-6
        self.rel = pg.mouse.get_rel()[0]
        self.shot = False
        self.health = PLAYER_MAX_HEALTH
        self.armor = PLAYER_MAX_ARMOR
        self.ammo = 500
        self.showWeapon = True
        self.time_prev = pg.time.get_ticks()
        self.canMove = True

        self.gas = False

        self.canGas = True
        self.gasCharge = 0
        self.lastGasUse = -59000

        self.current_quests = [] #lets just restrict it to three quests for now

        self.inventoryOpen = False

        self.onPortal = False

    def teleport(self, x, y = None):
        if type(x) == type(['a']):
            self.x = x[0]; self.y = x[1]
            return
        
        elif type(x) == type((1, 2)):
            self.x, self.y = x
            return

        self.x = x; self.y = y

    def portal_check(self):
        if distance_formula(PORTAL_X, PORTAL_Y, self.x, self.y) < 1.25:
            self.game.map.entered_portal()
            return True
        return False

    #check if player has ammo (if he does, show weapon)
    def checkWeaponShow(self):
        if self.ammo > 0:
            self.showWeapon = True
        else:
            if not self.shot:
                self.showWeapon = False

    #if recovery delay passed and health below max, revocer 1 hp
    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health += 1

    #function to heal player, return false if health is full
    def heal(self, num):
        if self.health < PLAYER_MAX_HEALTH:
            self.health += num
            if self.health > PLAYER_MAX_HEALTH:
                self.health = PLAYER_MAX_HEALTH
            return True
        return False
    
    def recover_armor(self, num):
        if self.armor < PLAYER_MAX_ARMOR:
            self.armor += num
            if self.armor > PLAYER_MAX_ARMOR:
                self.armor = PLAYER_MAX_ARMOR
            return True
        return False

    #return if recovery delay passed before last recovery
    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > RECOVERY_DELAY:
            self.time_prev = time_now
            return True

    #check if health is too low
    def check_game_over(self):
        if self.health < 1:
            self.game.object_renderer.game_over()
            pg.display.flip()

            pg.quit()

            #self.game.new_game()

    #function to lower health, show hurt screen, play hurt sound and check if health too low
    def get_damage(self, dmg):
        if self.armor <= 0:
            self.health -= dmg
        else:
            self.armor -= dmg
            if self.armor < 0:
                self.armor = 0

        self.game.object_renderer.player_damage()
        self.game.sound_player.play_sound("playerpain", loop=False)
        #self.check_game_over()

    #function to check if shot weapon
    def single_fire_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE and not self.shot and not self.game.weapon.reloading and self.showWeapon and self.ammo > 0 and not self.game.text_box.showing:
            #if event.button == 1 and not self.shot and not self.game.weapon.reloading:
                self.game.sound.shotgun.play()
                self.shot = True
                self.game.weapon.reloading = True
                self.ammo -= 1
                self.checkWeaponShow()

            elif event.key == pg.K_g and (self.gasCharge >= GAS_RECHARGE - 1) and self.canGas:
                #self.game.sound.gas.play()
                self.game.gas_attack.green_fade = 255
                self.gas = True
                self.game.gas_attack.gasing = True
                self.game.object_handler.damage_all_npc_in_range(self.x, self.y, GAS_RANGE, GAS_DAMAGE)
                self.gasCharge = 0
                self.lastGasUse = pg.time.get_ticks()

    #function to move player
    def movement(self):
        if not self.canMove or self.inventoryOpen:
            return

        #mesure trigonometric numbers
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        #define potential movement and set speed
        dx, dy = 0, 0

        #define dictionary with key statuses
        keys = self.game.keys

        if keys[pg.K_LSHIFT]:
            speed = PLAYER_SPEED * self.game.delta_time * 1.25 
        else:
            speed = PLAYER_SPEED * self.game.delta_time

        #speed times trig nums
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        #check key movements and add potential to potential movement on x and y axis
        if keys[pg.K_w]:
            dx += speed_cos
            dy += speed_sin
        if keys[pg.K_s]:
            dx -= speed_cos
            dy -= speed_sin
        if keys[pg.K_a]:
            dx += speed_sin
            dy -= speed_cos
        if keys[pg.K_d]:
            dx -= speed_sin
            dy += speed_cos

        #check that potential movement dosent go into wall
        self.check_wall_collision(dx, dy)

        #self.rel is used for rendering the sky

        #turning with arrows
        if keys[pg.K_LEFT]:
            self.angle -= PLAYER_ROT_SPEED * self.game.delta_time
        if keys[pg.K_RIGHT]:
            self.angle += PLAYER_ROT_SPEED * self.game.delta_time
        self.angle %= math.tau
        self.rel = self.angle * 5.1


    #function for checking if pos is wall
    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map and not (x, y) in ALL_EMPTY_COLLIDER
    
    #check if potential movement goes into wall
    def check_wall_collision(self, dx, dy):
        scale = PLAYER_SIZE_SCALE / self.game.delta_time

        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    #debug thingy
    def draw(self):
        def triangle_calc(pos, ang, sideL): #mesures vertices of a triangle thats centered and points with an angle
            return[(pos[0] + sideL * math.cos(ang), pos[1] + sideL * math.sin(ang)),
                   (pos[0] + sideL * math.cos(ang + 2*math.pi/3), pos[1] + sideL * math.sin(ang + 2*math.pi/3)),
                   (pos[0] + sideL * math.cos(ang + 4*math.pi/3), pos[1] + sideL * math.sin(ang + 4*math.pi/3))]

        #pg.draw.circle(self.game.screen, 'green', (100, 600), 8)

        points = triangle_calc([100, 600], self.angle, 10)

        #elongates one angle to show direction easier
        elon_poX, elon_poY = points[0]
        elon_poX += math.cos(self.angle) * 5; elon_poY += math.sin(self.angle) * 5
        points[0] = elon_poX, elon_poY

        pg.draw.polygon(self.game.screen, (255, 20, 20), [points[0], points[1], points[2]])

    #function for looking around with mouse (not used)
    def mouse_control(self):
        mx, my = pg.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
        self.rel = pg.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
        self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    #increases gas recharge
    def gasRecharge(self):
        if self.canGas and self.gasCharge < GAS_RECHARGE:
            self.gasCharge = pg.time.get_ticks() - self.lastGasUse
            if self.gasCharge > GAS_RECHARGE:
                self.gasCharge = GAS_RECHARGE

    #update function for player class
    def update(self):
        self.onPortal = self.portal_check()
        self.gasRecharge()
        self.movement()
        self.recover_health()
        #self.mouse_control()

    #check position
    @property #as i understand, this provides an easier way to retrieve class properties
    def pos(self):
        return self.x, self.y
    
    #check position on map
    @property
    def map_pos(self):
        return int(self.x), int(self.y)


###INVENTORY###


class Item:
    def __init__(self, name, icon, id, desc=""):
        self.id = id
        self.name = name
        self.desc = desc
        self.icon = icon

#contains all the possible items
ITEM_DICT = {
    1 : Item("Stomach Medicine", 'resources/sprites/items/stomachmedicine.png', 1, "the greatest stomach cleanser in the world, even a hellish one"),
    2 : Item("Demon Tears", 'resources/sprites/items/demontear.png', 2, "keep crying demons")
}

class InventorySystem:
    def __init__(self, game):
        self.game = game
        self.inventory = {} #a dictionary of Item's that would work as Item : quantity

    #get an item class by its id
    def get_item_by_id(self, id):
        return ITEM_DICT[id]
    
    #get an item class by its name
    def get_item_by_name(self, name):
        for itm in ITEM_DICT:
            if ITEM_DICT[itm].name.lower() == name.lower():
                return ITEM_DICT[itm]
        return None

    #check if item is in the inventory
    def in_inventory(self, item):
        if item in self.inventory:
            return True
        return False

    def num_in_inventory(self, item, quan):
        if item in self.inventory:
            if self.inventory[item] >= quan:
                return True
        return False

    #add an item to the inventory
    def add_item(self, itm, quan):
        if itm in self.inventory:
            self.inventory[itm] = self.inventory[itm] + quan
        else:
            self.inventory[itm] = quan
        return True #should return false in this function if no inventory space

    #remove an item from the inventory
    def remove_item(self, itm, quan):
        if not itm in self.inventory:
            return False
        
        if self.inventory[itm] > quan:
            self.inventory[itm] = self.inventory[itm] - quan
            return True

        elif self.inventory[itm] == quan:
            self.inventory.pop(itm)
            return True

        else:
            return False


###QUEST SYSTEM###


class Quest:
    #type - Escort/Kill/Gather, subtype - typeofenemy/locationtogoto/thingtocollect, goal_number - number of things to kill/gather, reward - what youll get
        #subtype for gather quests would consist of a number for the id of the item you need to find
    #source_tag is special tag of the npc that made the quest, used in case the npc has some lines to say or if you need to talk to him to finish the quest
    #reward will be money/health/special  ---  for money/health it will be ["health/money", number of either one], for special it will be ["special", the reward]
    def __init__(self, title, desc, type, subtype, goal_number, id, reward = None, source_tag = None, talk_to_finish = False, gather_remove = False):
        self.title = title
        self.description = desc
        self.type = type
        self.source_tag = source_tag
        self.talk_to_finish = talk_to_finish
        if self.type == "gather":
            self.gather_remove = gather_remove
        self.subtype = subtype
        self.goal_number = goal_number
        self.reward = reward
        self.id = id

QUEST_DICT = {
    1 : Quest("Get medicine", "get medicine for bloated goblin", "gather", 1, 1, 1, ['special', 'bloatedgoblin'], source_tag='bloatedgoblin', talk_to_finish=True, gather_remove=True)
}

class QuestManager:
    def __init__(self, game):
        self.game = game
        self.special_quest_manager = SpecialQuestManager(self.game)
        #array to hold the sprites you'll destory next time they talk
        self.del_sprite_tags = []

    #function to start a quest
    def request_quest(self, quest):
        if len(self.game.player.current_quests) < QUEST_LIMIT and not quest in self.game.player.current_quests:
            self.game.player.current_quests.append(quest)
            print("Started quest: " + quest.title)
            self.game.object_renderer.create_popup("Started quest: " + quest.title)
        else:
            return False

    def get_quest_by_id(self, id):
        return QUEST_DICT[id]

    def finish_quest(self, quest):
        if not quest.reward == None:
            if quest.reward[0] == 'money':
                pass
            elif quest.reward[0] == 'health':
                self.game.player.heal(quest.reward[1])

            elif quest.reward[0] == 'special':
                if quest.reward[1] == 'bloatedgoblin':
                    self.special_quest_manager.bloatedgoblin()

        print("Finished quest: " + quest.title)
        self.game.object_renderer.create_popup("Finished quest: " + quest.title)
        self.game.player.current_quests.remove(quest)


    #check if quests are done or not
    #source is the person who called the quest, if there was one
    def quest_watch(self, source = None):
        if len(self.game.player.current_quests) > 0:
            removed = False #if quest finished, finish it
            for quest in self.game.player.current_quests:
                #if you need to talk to finish the quest dont even check it
                if quest.talk_to_finish:
                    try:
                        if source.special_tag == quest.source_tag:
                            pass
                        else:
                            continue
                    except AttributeError:
                        continue
                        
                if quest.type == "kill":
                    pass
                elif quest.type == "gather":
                    if quest.goal_number == 1:
                        if self.game.inventory_system.in_inventory(self.game.inventory_system.get_item_by_id(quest.subtype)):
                            if quest.gather_remove:
                                self.game.inventory_system.remove_item(self.game.inventory_system.get_item_by_id(quest.subtype), 1)
                            removed = True
                    else:
                        if self.game.inventory_system.num_in_inventory(self.game.inventory_system.get_item_by_id(quest.subtype), quest.goal_number):
                            if quest.gather_remove:
                                self.game.inventory_system.remove_item(self.game.inventory_system.get_item_by_id(quest.subtype), quest.goal_number)
                            removed = True

                elif quest.type == "escort": #ig this is also a go to quest, you dont actually have to escort
                    pass
                else:
                    raise ValueError(quest.type + " in " + quest.title + " is not a valid quest type")
                
                if removed:
                    self.finish_quest(quest)

    def update(self):
        self.quest_watch()

#contains a repository of all special quest rewards as functions
class SpecialQuestManager:
    def __init__(self, game):
        self.game = game

    def bloatedgoblin(self):
        global ALL_EMPTY_COLLIDER

        ALL_EMPTY_COLLIDER.remove((14, 7))

        self.game.object_handler.get_special_passive('bloatedgoblin').nextlinequery.append("Wowza, thats for that I will have to take my leave now")

        self.game.quest_manager.del_sprite_tags.append('bloatedgoblin')


###MAP###

##MAZE GENERATION##

class MazeGenerator:
    def __init__(self):
        pass

    def generate_maze(self, w, h, diff): #diff is difficulty, 0 is peaceful, the higher, the harder
        def resetMaze(ar):
            nI = 0
            nJ = 0
            for r in ar:
                nI = 0
                for s in r:
                    ar[nJ][nI] = 1
                    nI+=1
                nJ+=1
            return ar

        def isMazeValid(ar, w_, h_, finder = False, startpos = (0,0)):
            #for y_ in range(h_):
            #    for x_ in range(w_)
            seen = set([startpos])
            queue = [startpos]

            while queue:
                i,j = queue.pop(0)
                seen.add((i, j))
                for di, dj in [(1,0),(-1,0),(0,1),(0,-1)]:
                    ni, nj = i+di, j+dj

                    if (ni, nj) in seen:
                        continue

                    if ni<0 or nj<0 or ni>=w_ or nj>=h_:
                        continue

                    if ar[ni][nj] == "p":
                        if finder:
                            return True, list(seen)
                        return True

                    if ar[ni][nj] == 1:
                        continue

                    if ar[ni][nj] == 0:
                        seen.add((ni,nj))
                        queue.append((ni,nj))
            
            return False
        
        def filter_seen_set(mz, st):
            ar = list(st)

            n = 0
            for (y, x) in ar:
                ar[n] = (x, y)
                n+=1

            outar = []

            for (x, y) in ar:
                if mz[y][x] == 0:
                    outar.append((x+1.5, y+1.5))

            return outar

        maze = []

        for y in range(h-2):
            addar = []
            for x in range(w-2):
                addar.append(1)
            maze.append(addar)

        x2, y2 = 0, 0

        ran = randint(0, (w-2)*(h-2)-1)
        x2, y2 = ran % (w-2), math.floor(ran/(w-2))
        maze[y2][x2] = "p"

        e = 0
        while not isMazeValid(maze, w-2, h-2):
            while not maze[y2][x2] == 1:
                ran = randint(0, (w-2)*(h-2)-1)
                x2, y2 = ran % (w-2), math.floor(ran/(w-2))
            maze[y2][x2] = 0
            e+=1

            if e >= round((w-2) * (h-2) * 0.75):
                maze = resetMaze(maze)
                x2, y2 = 0, 0

                ran = randint(0, (w-2)*(h-2)-1)
                x2, y2 = ran % (w-2), math.floor(ran/(w-2))
                maze[y2][x2] = "p"
                e = 0

        t, s = isMazeValid(maze, w-2, h-2, finder = True)
        empties = filter_seen_set(maze, s)

        spawn = choice(empties)

        x,y = spawn
        if not maze[int(y-1.5)][int(x-1.5)] == 0:
            while not maze[int(y-1.5)][int(x-1.5)] == 0:
                spawn = choice(empties)
                x,y = spawn

        empties.remove(spawn)

        n = 0
        for r in maze:
            n_r = [1]
            for s in r:
                n_r.append(s)
            n_r.append(1)
            maze[n] = n_r
            n+=1

        top_down_padding = []

        for x in range(w):
            top_down_padding.append(1)

        final_maze = [top_down_padding]

        for r in maze:
            final_maze.append(r)
        final_maze.append(top_down_padding)

        portal_loc = None

        for y, r in enumerate(final_maze):
            for x, v in enumerate(r):
                if final_maze[y][x] == "p":
                    portal_loc = x, y

        if diff == 0:
            return [final_maze, spawn, portal_loc, {}]

        spawns = {"npc": [], "pickups": []}

        enemy_names = list(ENEMIES.keys())
        good_items = ['ammo', 'health', 'armor']
        good_item_shifts_scales = {'ammo': [0.5, 0.5], 'health': [1, 0.4], 'armor': [0.8, 0.4]}
        good_item_pth = {'ammo': 'resources/sprites/static/onionbag.png', 'health': 'resources/sprites/static/health.png', 'armor': 'resources/sprites/static/armor.png'}
        good_item_ranges = {'ammo': [1, 9], 'health': [5, 100], 'armor': [10, 85]}

        real_diff = int(diff * uniform(0.1, 2))

        for x in range(real_diff):
            spawns["npc"].append([choice(enemy_names), choice(empties)])

        for x in range(int(real_diff * 0.75)):
            itm_type = choice(good_items)
            spawns["pickups"].append([choice(empties), itm_type, good_item_pth[itm_type],
                                       randint(good_item_ranges[itm_type][0], good_item_ranges[itm_type][1]), 
                                               good_item_shifts_scales[itm_type][0], good_item_shifts_scales[itm_type][1], ""])

        return [final_maze, spawn, portal_loc, spawns]


#define map
#false for nothing, numbers for different textures and "p"
_ = False
P = "p"
base_map = [
    [1, 1, 1, 1, 1, P, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, _, _, _, _, _, _, _, _, _, 3, 2, 2, 2, _, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, 3, 2, 2, 2, _, 1],
    [1, 1, _, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, _, 1],
    [3, _, _, _, _, _, _, 3, 1, _, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, 5, 1, _, _, _, _, _, _, 1],
    [5, _, _, _, _, _, _, 5, 1, _, _, _, _, _, _, 1],
    [5, _, _, _, _, _, _, 5, 1, _, _, _, _, _, _, 1],
    [5, _, _, _, _, _, _, 5, 1, _, _, _, _, _, _, 1],
    [5, _, _, _, _, _, _, 5, 1, _, _, _, _, _, _, 1],
    [5, _, _, _, _, _, _, 5, 1, _, _, _, _, _, _, 1],
    [1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    #0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
]

#info abt the bloated goblin that is removed with a stomach medicine
#btw you need an empty collider in the location of the bloated goblin and the coordaintes of that collider has to be set in the quest so that its correctly removed
"""{
    "name": "Bloated Goblin",
    "path": 'resources/sprites/passive/bellygoblin.png',
    "pos": [14.5, 7.5],
    "usetextbox": True,
    "myline": "Ohhhh, yesterday I ate a- something I wasn't supposed, now I have a terrrrible stomach ache",
    "pitch": "high",
    "scale": 1.25,
    "shift": 0.1,
    "special_tag": 'bloatedgoblin'
},"""

#map info for the spawn/base/home
BASE_DATA = {
    "map": base_map,
    "portal": [5, 1],
    "spawn": [1.5, 1.5],
    "spawns": {
        "npc": [
            ["satansnovel", [3.5, 2.5]]
        ],
        "passive": [
            {
                "name": "Johny",
                "path": 'resources/sprites/passive/johny.png',
                "pos": [1.5, 3.5],
                "usetextbox": True,
                "myline": "Hello Shrek, welcome to hell, I am Johny, you should probably beware of the demons patrolling around here, use your onions as a defense, there is a bag right there",
                "pitch": "deep",
                "scale": 1,
                "shift": 0.27,
                "special_tag": 'johny'
            },
            {"name":"Donkey Clone 1","path":"resources/sprites/passive/donkey.png","pos":[2.5,10.5],"usetextbox":True,"myline":"Donkey- clubb-","pitch":"mid","scale":0.8,"shift":0.2,"special_tag":None},
            {"name":"Donkey Clone 2","path":"resources/sprites/passive/donkey.png","pos":[5.5,10.5],"usetextbox":True,"myline":"Talk to Donkey","pitch":"mid","scale":0.8,"shift":0.2,"special_tag":None},
            {"name":"Donkey","path":"resources/sprites/passive/donkey.png","pos":[2.5,14.5],"usetextbox":True,"myline":"Hello Shrek, welcome to the cul- club, yes I meant club","pitch":"mid","scale":0.8,"shift":0.2,"special_tag":None},
            {"name":"Donkey Clone 3","path":"resources/sprites/passive/donkey.png","pos":[5.5,14.5],"usetextbox":True,"myline":"Ooooooooooooh","pitch":"mid","scale":0.8,"shift":0.2,"special_tag":None},
            {"name":"Donkey Clone 4","path":"resources/sprites/passive/donkey.png","pos":[3.5,12.5],"usetextbox":True,"myline":"I am donkey, we are donkey. You are donkey?","pitch":"mid","scale":0.8,"shift":0.2,"special_tag":None}
        ],
        "sprites": [
            #['resources/sprites/static/candlebra.png', [2.5, 2.5], 0.25, 1.4]
        ],
        "pickups": [
            [[6.5, 6.5], 'item', 'resources/sprites/items/stomachmedicine.png', 1, 0.25, 1.6, 1],
            [[6.5, 5.5], 'ammo', 'resources/sprites/static/onionbag.png', 5, 0.5, 0.7, ""]
        ]
    }
}

PORTAL_X, PORTAL_Y = 5, 1

cur_map = None

LEVEL_DATA = get_json('resources/json/levels.json')

#   for ALL_EMPTY_COLLIDERS, when adding an empty collider, you need to go into the game and check the position 
#   of where you actually want to put it because it sometimes registers differently then seen on map, LIKE ONE OFF ON THE X OR Y AXIS THEN WHAT IT LOOKS LIKE

#   if you want to be lazy, you can change the wall collision code in player class so that it considers the squares around an empty collider square also impermeable so that you dont have to check all of them

#   cough, cough, never mind the last three lines, idk if they actually apply because i kinda counted wrong when making the location for the empty collider square...

# need to add all empty colliders here, if there is a coordinate here, it will not be able to be walked through, do not forget coordinates start from 1, y increases downwards, x increases to the right
ALL_EMPTY_COLLIDER = []

#map class
class Map:
    #store some variables, this class is mostly used for fetching map vars
    def __init__(self, game):
        self.game = game

        #var to hold spawn dict until object handler is generated to actaully spawn them
        self.need_to_load = None
        self.load_base()

        #minimap offsets
        self.mmxoffset = 0
        self.mmyoffset = 0
        self.mmsurface = pg.Surface((100, 100))

        self.cur_map = cur_map
        self.world_map = {}
        self.rows = len(self.cur_map)
        self.cols = len(self.cur_map[0])
        self.current_level = 1
        self.inBase = True

        self.generator = MazeGenerator()

        self.get_map()

    def EXPIREMENTAL_GENERATION(self):
        synth_map, spwn, portal, spawn_dict = self.generator.generate_maze(30, 30, 7)
        self.game.object_handler.clear_entities(); self.game.object_handler.clear_entities()
        self.game.player.teleport(spwn)
        self.load_synthetic_map(synth_map, portal, spawn_dict)
        self.game.pathfinding.reset_pathfinding(self.cur_map)
        self.inBase = False

    def entered_portal(self):
        if RANDOM_GENERATION:
            self.EXPIREMENTAL_GENERATION(); return

        if self.inBase:
            self.game.player.teleport(LEVEL_DATA[str(self.current_level)]["spawn"])
            self.load_level(self.current_level)
            self.game.pathfinding.reset_pathfinding(self.cur_map)
            self.inBase = False
        else:
            self.game.player.teleport(BASE_DATA["spawn"])
            self.load_base()
            self.current_level += 1
            self.game.pathfinding.reset_pathfinding(self.cur_map)
            self.inBase = True

    def get_map(self):
        for j, row in enumerate(self.cur_map):
            for i, value in enumerate(row):
                if value or not value == 0:
                    self.world_map[(i, j)] = value

    def load_base(self):
        lvldata = BASE_DATA
        lvlmap, lvlspawn = lvldata["map"], lvldata["spawns"]

        global PORTAL_X, PORTAL_Y
        PORTAL_X, PORTAL_Y = BASE_DATA["portal"][0], BASE_DATA["portal"][1]

        self.change_map(lvlmap)
        try:
            self.game.object_handler.load_level_spawns(lvlspawn)
        except AttributeError:
            self.need_to_load = lvlspawn

    def change_map(self, newmap): #should update to new map
        global cur_map
        cur_map = newmap

        self.cur_map = cur_map
        self.world_map = {}
        self.rows = len(self.cur_map)
        self.cols = len(self.cur_map[0])

        self.get_map()
    
    def load_level(self, lvl_num):
        lvldata = LEVEL_DATA[str(lvl_num)]
        lvlmap, lvlspawn, portalLoc = lvldata["map"], lvldata["spawns"], lvldata["portal"]

        global PORTAL_X, PORTAL_Y
        PORTAL_X, PORTAL_Y = portalLoc[0], portalLoc[1]

        self.change_map(lvlmap)
        try:
            self.game.object_handler.load_level_spawns(lvlspawn)
        except AttributeError:
            self.need_to_load = lvlspawn

    def load_synthetic_map(self, synthmap, portal, spawndict): #for generated maps
        lvlmap = synthmap

        global PORTAL_X, PORTAL_Y
        PORTAL_X, PORTAL_Y = portal

        self.change_map(lvlmap)
        try:
            self.game.object_handler.load_level_spawns(spawndict)
        except AttributeError:
            self.need_to_load = spawndict

    #debug thinkgy
    def draw(self):
        self.mmsurface.fill('black')

        self.mmxoffset = -self.game.player.x; self.mmyoffset = -self.game.player.y

        [pg.draw.rect(self.mmsurface, 'darkgray', (pos[0] * 20 + self.mmxoffset * 20 + 50, pos[1] * 20 + self.mmyoffset * 20 + 50, 20, 20), 2) for pos in self.world_map]

        self.game.screen.blit(self.mmsurface, (50, 550))
        

###RAYCASTING###


#raycasting class
class RayCasting:
    #on init function, def vars
    def __init__(self, game):
        self.game = game
        self.ray_casting_result = []
        self.objects_to_render = []
        self.textures = self.game.object_renderer.wall_textures

    #function to compile list of things to render
    def get_objects_to_render(self):
        self.objects_to_render = []
        #propagates through rays and their results
        for ray, values in enumerate(self.ray_casting_result):
            depth, proj_height, texture, offset = values

            if proj_height < HEIGHT:
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, proj_height))
                wall_pos = (ray * SCALE, HALF_HEIGHT - proj_height // 2)
            else:
                texture_height = TEXTURE_SIZE * HEIGHT / proj_height
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), HALF_TEXTURE_SIZE - texture_height // 2,
                    SCALE, texture_height
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, HEIGHT))
                wall_pos = (ray * SCALE, 0)

            #adds to the list of things to render the piece of wall to render
            self.objects_to_render.append((depth, wall_column, wall_pos))

    #main raycasting func
    def ray_cast(self):
        #list of raycasting results, player pos and player pos on map
        self.ray_casting_result = []
        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        #vertical and horizontal for textures
        texture_vert, texture_hor = 1, 1

        #define first ray angle
        ray_angle = self.game.player.angle - HALF_FOV + 0.0001
        #loop for every ray emission
        #dx and dy are increments to move to the next grid horizontal/vertical line
        for ray in range(NUM_RAYS):
            #trig nums
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            #doing horizontal rays
            y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

            depth_hor = (y_hor - oy) / sin_a
            x_hor = ox + depth_hor * cos_a

            delta_depth = dy / sin_a
            dx = delta_depth * cos_a

            for i in range(MAX_DEPTH):
                tile_hor = int(x_hor), int(y_hor)
                if tile_hor in self.game.map.world_map:
                    texture_hor = self.game.map.world_map[tile_hor]
                    break
                x_hor += dx
                y_hor += dy
                depth_hor += delta_depth

            #doing vertical rays
            x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

            depth_vert = (x_vert - ox) / cos_a
            y_vert = oy + depth_vert * sin_a

            delta_depth = dx / cos_a
            dy = delta_depth * sin_a

            for i in range(MAX_DEPTH):
                tile_vert = int(x_vert), int(y_vert)
                if tile_vert in self.game.map.world_map:
                    texture_vert = self.game.map.world_map[tile_vert]
                    break
                x_vert += dx
                y_vert += dy
                depth_vert += delta_depth

            #depth, texture offset
            if depth_vert < depth_hor:
                depth, texture = depth_vert, texture_vert
                y_vert %= 1
                offset = y_vert if cos_a > 0 else (1 - y_vert)
            else:
                depth, texture = depth_hor, texture_hor
                x_hor %= 1
                offset = (1 - x_hor) if sin_a > 0 else x_hor

            #remove fisheye effect
            depth *= math.cos(self.game.player.angle - ray_angle)

            #debug thingy -> pg.draw.line(self.game.screen, 'yellow', (100 * ox, 100 * oy), (100 * ox + 100 * depth * cos_a, 100 * oy + 100 * depth * sin_a), 2)

            #mesure the height of the projection
            proj_height = SCREEN_DIST/(depth + 0.0001)

            #ray casting result appened to the array that will be drawn
            self.ray_casting_result.append((depth, proj_height, texture, offset))

            #add to angle to go to next ray's angle
            ray_angle += DELTA_ANGLE

    #update raycasting class
    def update(self):
        self.ray_cast()
        self.get_objects_to_render()


###TEXT BOX###


class TextBox:
    def __init__(self, game, x, y, width, height):
        self.pos = x, y

        self.rect = pg.Rect(x, y, width, height)
        self.game = game
        self.showing = False
        self.writing = False
        self.text = ""
        self.font = pg.font.Font('resources/textutil/textboxfont.ttf', 30)
        img = pg.image.load('resources/textutil/textbox.png').convert_alpha()
        self.back_img = pg.transform.scale(img, (width, height))
        self.goal_text = ""
        self.goal_array = []
        self.ar_pos = 0
        self.finish_typing = False

        self.current_pitch = ""

        self.talk_source = None

        #sound players for when you talk to person
        self.game.sound_player.load_sound('high', 'resources/sound/highmur.wav')
        self.game.sound_player.load_sound('mid', 'resources/sound/midmur.wav')
        self.game.sound_player.load_sound('deep', 'resources/sound/deepmur.wav')

        #mesures the time you stopped taking with textbox so that you arent stuck in a talking loop(after you finish talking, the person talks again when you clicked to close the textbox)
        self.last_talk = 0
        #time you cant talk again(purely for not getting stuck in a talk loop)
        self.last_talk_time_limit = 200

        self.line_character_limit = 54
        self.char_limit = 54 * 4 - 10

    def play_pitch_sound(self, pitch):
        if not pitch == None:
            self.game.sound_player.play_sound(pitch)

    #check if space bar was clicked
    def event_call(self, event):
        if self.showing:
            if event.key == pg.K_e:
                if self.writing:
                    if self.text == self.goal_text:
                        self.writing = False
                    else:
                        self.finish_typing = True
                else:
                    if self.ar_pos < len(self.goal_array):
                        self.text = ""
                        self.ar_pos += 1
                        self.play_pitch_sound(self.current_pitch)
                        try:
                            self.goal_text = self.goal_array[self.ar_pos]
                        except IndexError:
                            self.writing = False
                            self.showing = False
                            self.game.player.canMove = True
                            self.last_talk = pg.time.get_ticks() #maybe add this to the else part of "if self.ar_pos < len(self.goal_array):"
                            if not self.talk_source == None and self.talk_source.special_tag in self.game.quest_manager.del_sprite_tags:
                                self.talk_source.self_destruct()
                                self.game.quest_manager.del_sprite_tags.remove(self.talk_source.special_tag)

                            self.talk_source = None
                            return
                        self.writing = True
                    else:
                        self.showing = False
                        self.text = ""
                        self.goal_array = []
                        self.goal_text = ""

                        #if talk source special tag in del sprite tags in the quest manager, delete the sprite after talking to him
                        if not self.talk_source == None and self.talk_source.special_tag in self.game.quest_manager.del_sprite_tags:
                            self.talk_source.self_destruct()
                            self.game.quest_manager.del_sprite_tags.remove(self.talk_source.special_tag)

                        self.talk_source = None

    #wrap text so its not too long
    def wrap_text(self, text, limit):
        if not text or text == "":
            return ""

        words = text.split()
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            if len(current_line) + 1 + len(word) <= limit:
                # Add the word to the current line
                current_line += " " + word
            else:
                # Start a new line
                lines.append(current_line)
                current_line = word
        
        # Add the last line
        lines.append(current_line)

        return lines

    #func to start displaying txt
    #call_source is a parameter for the npc that started the conversation
    def display_text(self, text, pitch = None, call_source = None):
        #if text is longer than the character limit, turn it into an array
        if self.writing:
            return False
        
        if not call_source == None:
            self.talk_source = call_source

        #play the correct piteched sound for the character talking
        self.current_pitch = pitch
        self.play_pitch_sound(self.current_pitch)

        if len(text) > self.char_limit:
            #text = text[:self.char_limit]
            text = self.wrap_text(text, self.char_limit)
        else:
            text = [text]

        if type(text) == type("abc"):
            self.goal_text = text
            self.goal_array = []
        else:
            self.goal_array = text
            self.ar_pos = 0
            self.goal_text = self.goal_array[0]

        self.game.player.canMove = False
        self.showing = True
        self.writing = True

    def time_limit_done(self):
        if pg.time.get_ticks() - self.game.text_box.last_talk > self.game.text_box.last_talk_time_limit:
            return True
        return False

    #update the textbox
    def update(self):
        if self.showing:
            if self.writing:
                if self.text == self.goal_text:
                    self.writing = False
                else:
                    if self.finish_typing:
                        self.text = self.goal_text
                        self.finish_typing = False
                        self.writing = False
                    else:
                        if self.game.next_char_event:
                            try:
                                self.text += self.goal_text[len(self.text)]
                            except IndexError:
                                self.writing = False
            else:
                #if sound is playing but textbox not writing, stop playing
                [self.game.sound_player.stop_sound(pit) for pit in ["high", "mid", "deep"] if self.game.sound_player.is_sound_playing(pit)]
            

            self.game.screen.blit(self.back_img, self.pos)

            y_ = 15

            for t in self.wrap_text(self.text, self.line_character_limit):
                appliedTxt = self.font.render(t, False, 'black')

                x, y = self.pos

                self.game.screen.blit(appliedTxt, (x + 30, y + y_))

                y_ += 33
        else:
            #if sound is playing but textbox not writing, stop playing
            [self.game.sound_player.stop_sound(pit) for pit in ["high", "mid", "deep"] if self.game.sound_player.is_sound_playing(pit)]


###OBJECT RENDERER###  


#object renderer class, for renderering objects, sprites, etc
class ObjectRenderer:
    #def vars and init func
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.wall_textures = self.load_wall_textures()
        self.sky_image = self.get_texture('resources/textures/sky.png', (WIDTH, HALF_HEIGHT))
        self.sky_offset = 0
        self.blood_screen = pg.transform.scale(pg.image.load('resources/sprites/blood.png'), (WIDTH, HEIGHT)); self.blood_screen.set_alpha(100)
        #self.gameoverImg = 
        self.portal_frames = [self.get_texture('resources/textures/portal/0.png'), self.get_texture('resources/textures/portal/1.png'), 
                              self.get_texture('resources/textures/portal/2.png'), self.get_texture('resources/textures/portal/3.png')]
        self.portal_frame_n = 0

        self.popup_list = []

        self.doom_font = pg.font.Font(None, 20)

        self.y_gap = 10 #gap between popups

        self.gameoverImg = pg.transform.scale(pg.image.load("resources/sprites/gameover.png"), (WIDTH, HEIGHT))

    def create_popup(self, txt):
        y = self.next_popup_pos()
        self.popup_list.append(Popup(self.game, txt, y))

    #basically i want to work on something else rn so ill make a makeshift sysmtem, popups append their "last position" and the next popup will be placed a certain amount under the previous message's "last position"
    #the downside of this makeshift system is that if new messages are constantly being created without a moment of no messages, the messages will continually go further and further down because the poss array will always have a value preventing a reset to 0
    def next_popup_pos(self):
        poss = []
        for p in self.popup_list:
            poss.append(p.pos_y + p.surf_y)

        if len(poss) == 0:
            return 0
        else:
            return (poss[-1] + self.y_gap)

    def popup_update(self):
        pops = {p : p.update() for p in self.popup_list}

        for p in pops:
            self.screen.blit(pops[p], (10, p.pos_y))

    #function to draw background(sky) and to render all game objects
    def draw(self):
        self.draw_background()
        self.render_game_objects()

    def next_portal_frame(self):
        px, py = self.game.player.map_pos
        if distance_formula(PORTAL_X, PORTAL_Y, px, py) < 10:
            self.portal_frame_n += 1; self.portal_frame_n %= 4
            self.wall_textures["p"] = self.portal_frames[self.portal_frame_n]

    #if you lost, show lose screen
    def game_over(self):
        self.screen.blit(self.gameoverImg, (0, 0))

    #show hurt screen
    def player_damage(self):
        self.screen.blit(self.blood_screen, (0, 0))

    #draw sky and floor, not currently used
    def draw_background(self):
        self.sky_offset = (100 * self.game.player.rel) % WIDTH
        self.screen.fill('black')
        
        self.screen.blit(self.sky_image, (-self.sky_offset, 0))
        self.screen.blit(self.sky_image, (-self.sky_offset + WIDTH, 0))
        #floor
        pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))

    def show_exclaim(self, x, y, dist):
        if dist > 5:
            return
        else:
            font_size = (6-dist) * 10

        doom_font = pg.font.Font('resources/textutil/doomfont.ttf', int(font_size*2))

        excl = doom_font.render("!", False, (255, 0, 0))

        self.screen.blit(excl, (x, y))

    #loop through objects to render, render them
    def render_game_objects(self):
        list_objects = sorted(self.game.raycasting.objects_to_render, key=lambda t: t[0], reverse = True)
        for depth, image, pos in list_objects:
            self.screen.blit(image, pos)

    #a static method to get the texture of a file
    @staticmethod
    def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
        texture = pg.image.load(path).convert_alpha()
        return pg.transform.scale(texture, res)
    
    #dictionary to store the textures of walls
    def load_wall_textures(self):
        #for every item in the textures dir that ends with .png and whos name is numeric, add it to the directory as a value with its number as its key
        out_dict = {int(pth.replace('.png', '')) : self.get_texture(f'resources/textures/' + pth) for pth in os.listdir('resources/textures') if pth.endswith('.png') and pth.replace('.png', '').isnumeric()}
        out_dict["p"] = self.get_texture('resources/textures/portal/0.png')
        return out_dict

        return {
            1: self.get_texture('resources/textures/1.png'),
            2: self.get_texture('resources/textures/2.png'),
            3: self.get_texture('resources/textures/3.png'),
            4: self.get_texture('resources/textures/4.png'),
            5: self.get_texture('resources/textures/5.png'),
            "p": self.get_texture('resources/textures/portal/0.png')
        }


###SPRITE OBJECTS###


#class for a sprite, an in game object thats not a wall
class SpriteObject:
    #def vars, init func
    def __init__(self, game, path = 'resources/sprites/static/candlebra.png', 
                 pos=(10.5, 3.5), scale = 0.25, shift = 1.4):
        self.game = game
        self.player = game.player
        self.x, self.y = pos
        self.image = pg.image.load(path).convert_alpha()
        self.IMAGE_WIDTH = self.image.get_width()
        self.IMAGE_HALF_WIDTH = self.image.get_width() // 2
        self.IMAGE_RATIO = self.IMAGE_WIDTH / self.image.get_height()
        self.dx, self.dy, self.theta, self.screen_x, self.dist, self.norm_dist = 0,0,0,0,1,1
        self.sprite_half_width = 0
        self.SPRITE_SCALE = scale
        self.SPRITE_HEIGHT_SHIFT = shift
        self.img_angle = 0

    #mesure the sprite's projections, add itself to objects to render with its normalized distance, actual image and position
    def get_sprite_projection(self):
        proj = SCREEN_DIST / self.norm_dist * self.SPRITE_SCALE
        proj_width, proj_height = proj * self.IMAGE_RATIO, proj
        

        image = pg.transform.scale(self.image, (proj_width, proj_height))

        if not self.img_angle == 0:
            image = rotate_image(image, self.img_angle)

        self.sprite_half_width = proj_width // 2
        height_shift = proj_height * self.SPRITE_HEIGHT_SHIFT
        pos = self.screen_x - self.sprite_half_width, HALF_HEIGHT - proj_height //2 + height_shift

        self.game.raycasting.objects_to_render.append((self.norm_dist, image, pos))

    #function to get sprite
    def get_sprite(self):
        dx = self.x - self.player.x
        dy = self.y - self.player.y
        self.dx, self.dy = dx, dy
        self.theta = math.atan2(dy, dx)

        delta = self.theta - self.player.angle
        if (dx > 0 and self.player.angle > math.pi) or (dx < 0 and dy < 0):
            delta += math.tau

        delta_rays = delta / DELTA_ANGLE
        self.screen_x = (HALF_NUM_RAYS + delta_rays) * SCALE

        self.dist = math.hypot(dx, dy)
        self.norm_dist = self.dist * math.cos(delta)
        if -self.IMAGE_HALF_WIDTH < self.screen_x < (WIDTH + self.IMAGE_HALF_WIDTH) and self.norm_dist > 0.5:
            self.get_sprite_projection()

    def self_destruct(self):
        self.game.object_handler.sprite_list.remove(self)
        del self

    #update sprite
    def update(self):
        self.get_sprite()

"""
class SuperStaticSprite(SpriteObject):
    def __init__(self, game, path='resources/sprites/static/candlebra.png', pos=(10.5, 3.5), scale=0.25, shift=1.4):
        super().__init__(game, path, pos, scale, shift)
"""

class Pickup(SpriteObject):
    #type would be item/money/armor/ammo/special(for quests)/etc, subtype would really be for special type, number is for the number of the thing you pickup, subtype will be the id of item if the type is item
    def __init__(self, game, pos, type, path=None, number=1, scale=0.25, shift=1.6, subtype = ""):
        if path == None and type == 'item':
            #its purposefully game and not self.game because super is called after and game is the same and this needs to be before super init
            path = game.inventory_system.get_item_by_id(subtype).icon
        super().__init__(game, path, pos, scale, shift)
        self.type = type
        self.subtype = subtype
        self.number = number
        self.pickup_range = 1

    def in_player_range(self):
        sx, sy = self.x, self.y
        px, py = self.game.player.map_pos
        return distance_formula(sx, sy, px, py) <= self.pickup_range
    
    def self_destruct(self):
        self.game.object_handler.pickup_list.remove(self)
        del self

    def update_sub(self):
        removed = False
        if self.in_player_range():
            if self.type == "money":
                pass

            elif self.type == "armor":
                if self.game.player.recover_armor(self.number):
                    self.game.sound_player.play_sound("armor", loop=False)
                    self.game.object_renderer.create_popup("Picked-up armor")
                    removed = True

            elif self.type == "health":
                if self.game.player.heal(self.number):
                    self.game.sound_player.play_sound("heal", loop=False)
                    self.game.object_renderer.create_popup("Picked-up health")
                    removed = True

            elif self.type == "ammo":
                self.game.player.ammo += self.number
                self.game.sound_player.play_sound("reload", loop=False)
                self.game.object_renderer.create_popup("Picked-up ammo")
                removed = True

            elif self.type == "item":
                self.game.inventory_system.add_item(self.game.inventory_system.get_item_by_id(self.subtype), self.number)
                self.game.object_renderer.create_popup(f"Gained {str(self.number)} {self.game.inventory_system.get_item_by_id(self.subtype).name}'s")
                self.game.sound_player.play_sound("pickup", loop=False)
                removed = True

            elif self.type == "special":
                #if self.subtype == "stomachmedicine":
                    #self.game.inventory_system.add_item(self.game.inventory_system.get_item_by_id(1))
                    #self.game.object_renderer.create_popup("Gained stomach medicine")
                    #self.game.sound_player.play_sound("pickup", loop=False)
                    #removed = True
                pass

                #else:
                    #raise ValueError(self.subtype + "is an invalid pickup subtype")
                
            else:
                raise ValueError(self.type + " is an invalid pickup type")
            
        if removed:
            self.game.object_handler.disable_pickup(self)
            del self
            
class BasicPassiveNPC(SpriteObject): #NEED TO MAKE A METHOD TO ONLY ALLOW PLAYER TO SPEAK TO ONE NPC AT A TIME AND NOT HAVE MULTIPLE MESSAGES FOR PRESS SPACE TO TALK APPEAR
    def __init__(self, game, path='resources/sprites/passive/ghost.png', pos=(10.5, 3.5), usetextbox=True, myline="hello", 
                 name="character", pitch="high", scale=0.75, shift=0, special_tag = None): #pitch: high/mid/deep
        super().__init__(game, path, pos, scale, shift)
        self.talkrange = 2.5
        self.pos = pos
        #trigger text box for his line or just make text float above him
        self.use_textbox = usetextbox
        self.myline = myline
        self.myname = name
        self.pitch = pitch
        self.interact_enabled = True
        self.special_tag = special_tag

        self.exclamation = False

        self.nextlinequery = []

    def player_in_range(self):
        sx, sy = self.pos
        px, py = self.game.player.map_pos
        return distance_formula(sx, sy, px, py) <= self.talkrange

    #NEED TO ADD AN EXCLAMATION AND A FUNC TO ASK PASSIVES FOR THEIR NEXT TALK

    def event_call(self, event):
        if self.player_in_range() and self.interact_enabled:
            if event.key == pg.K_e and not self.game.text_box.showing and self.game.text_box.time_limit_done() and self.use_textbox: #maybe add a self.screen_x req so that you cant talk to people behind you
                self.special_check()
                if not self.special_tag == None:
                    self.game.quest_manager.quest_watch(self)
                if len(self.nextlinequery) == 0:
                    self.game.text_box.display_text(self.myline, self.pitch, call_source=self)
                else:
                    self.game.text_box.display_text(self.nextlinequery[0], self.pitch, call_source=self)
                    self.nextlinequery.pop(0)

    def update_sub(self):
        if self.exclamation:
            #buncha math to mesure the y axis to place the exclamation
            proj_height = SCREEN_DIST / self.norm_dist * self.SPRITE_SCALE
            posy = HALF_HEIGHT - proj_height //2 + proj_height * self.SPRITE_HEIGHT_SHIFT
            self.game.object_renderer.show_exclaim(self.screen_x, posy, distance_formula(self.game.player.x, self.game.player.y, self.x, self.y))

        #if within range, allow talk
        if self.player_in_range() and self.interact_enabled:
            if not self.game.text_box.showing:
                needTalk_font = pg.font.Font('resources/textutil/textboxfont.ttf', 30)

                needTalk = needTalk_font.render("E to talk to " + self.myname, False, (255, 255, 255))

                self.game.screen.blit(needTalk, (self.screen_x - 200, HEIGHT))

    def special_check(self): #maybe make another one for special checks in update for some cases
        #place to special things for special tags
        if not self.special_tag == None:
            if self.special_tag == 'bloatedgoblin':
                self.game.quest_manager.request_quest(self.game.quest_manager.get_quest_by_id(1))

    def add_next_line(self, line):
        self.nextlinequery.append(line)

    def self_destruct(self):
        self.game.object_handler.passive_list.remove(self)
        del self


#a class piggybacking off the spriteobject that contains animation
class AnimatedSprite(SpriteObject):
    def __init__(self, game, path='resources/sprites/static/johny.png', pos=(10.5, 3.5), scale=1, shift=0.27, animation_time=120):
        super().__init__(game, path, pos, scale, shift)
        self.animation_time = animation_time
        self.path = path.rsplit('/', 1)[0]
        self.images = self.get_images(self.path)
        self.animation_time_prev = pg.time.get_ticks()
        self.animation_trigger = False

    #update itself
    def update(self):
        super().update()
        self.check_animation_time()
        self.animate(self.images)

    #function to play animation
    def animate(self, images):
        if self.animation_trigger:
            images.rotate(-1)
            self.image = images[0]

    #function to check the animation's time and change the animation trigger
    def check_animation_time(self):
        self.animation_trigger = False
        time_now = pg.time.get_ticks()
        if time_now - self.animation_time_prev > self.animation_time:
            self.animation_time_prev = time_now
            self.animation_trigger = True

    #function to get all the images in a folder for animating
    def get_images(self, path):
        #func to sort an array of image paths(i.e. 0.png, 1.png, etc) by their first number to prevent os from ordering them wrong
        def spec_sort(ar):
            return [x for _, x in sorted(zip([int(val.replace('.png', '')) for val in ar], ar))]

        images = deque()

        if len(os.listdir(path)) > 10:
            searchpath = spec_sort(os.listdir(path))
        else:
            searchpath = os.listdir(path)

        for file_name in searchpath:
            if os.path.isfile(os.path.join(path, file_name)):
                img = pg.image.load(path + "/" + file_name).convert_alpha()
                images.append(img)
        return images


###OBJECT HANDLER###


#object handler class, basically manages objects and some interactions/functions
class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_list = []
        self.npc_list = []
        self.passive_list = []
        self.pickup_list = []

        self.npc_sprite_path = 'resources/sprites/npc'
        self.static_sprite_path = 'resources/sprites/static/'
        self.anim_sprite_path = 'resources/sprites/animated'

        #dictionary of npc positions
        self.npc_positions = {}

        #dictionary of basicpassivenpcs' and how centered they are, the more center the more priority for talking to him
        self.passive_centered = {}

        if not self.game.map.need_to_load == None:
            self.load_level_spawns(self.game.map.need_to_load)
            self.game.map.need_to_load = None    

    #update all individual sprites and npcs
    def update(self):
        self.npc_positions = {npc.map_pos for npc in self.npc_list if npc.alive}

        #creates a dict of the passive npcs and their "centeredness"
        self.passive_centered = {passive : abs(passive.screen_x - HALF_WIDTH) for passive in self.passive_list if passive.player_in_range()}

        #if there is one passive npc on the screen and in range of the player, only allow the player to talk to him
        if len(self.passive_centered) == 1:
            list(self.passive_centered.keys())[0].interact_enabled = True
        #if there is more than one passive npcs on the screen/in range, only allow the most centered one of them all to talk to the player
        elif len(self.passive_centered) > 1:
            self.passive_centered = dict(sorted(self.passive_centered.items(), key=lambda x: int(x[1])))
            passive_keys = list(self.passive_centered.keys())
            passive_keysl = len(passive_keys)
            passive_keys[0].interact_enabled = True
            for x in range(1, passive_keysl):
                passive_keys[x].interact_enabled = False

        [sprite.update() for sprite in self.sprite_list]
        [npc.update() for npc in self.npc_list]
        [passive.update() for passive in self.passive_list]; [passive.update_sub() for passive in self.passive_list]
        [pickup.update() for pickup in self.pickup_list]; [pickup.update_sub() for pickup in self.pickup_list]

        #go through every sprite and if it has the update_sub function, run it (This will be used for subclasses that have extra abilities that will all be run with update_sub)
        [sprite.update_sub() for sprite in self.sprite_list if callable(getattr(sprite, "update_sub", None))]

    def clear_entities(self):
        arl = len(self.sprite_list)
        for x in range(arl):
            self.sprite_list[0].self_destruct()

        arl = len(self.npc_list)
        for x in range(arl):
            self.npc_list[0].self_destruct()

        arl = len(self.passive_list)
        for x in range(arl):
            self.passive_list[0].self_destruct()

        arl = len(self.pickup_list)
        for x in range(arl):
            self.pickup_list[0].self_destruct()

    def load_level_spawns(self, spawndict):    
        self.clear_entities()

        if "npc" in spawndict:
            npcar = spawndict["npc"]

            for npc in npcar:
                npctype = npc[0]
                npcspawn = npc[1][0], npc[1][1]

                enemy_data = ENEMIES[npctype]

                self.add_npc(NPC(self.game, enemy_data["path"], npcspawn, enemy_data["scale"], enemy_data["shift"], enemy_data["animation_time"], enemy_data["stats"]))

        if "passive" in spawndict:
            passar = spawndict["passive"]

            for passive in passar:
                self.add_passive(BasicPassiveNPC(self.game, passive["path"], (passive["pos"][0], passive["pos"][1]), passive["usetextbox"], passive["myline"], 
                                                 passive["name"], passive["pitch"], passive["scale"], passive["shift"], passive["special_tag"]))

        if "sprites" in spawndict:
            spritar = spawndict["sprites"]

            for sprit in spritar:
                self.add_sprite(SpriteObject(self.game, sprit[0], (sprit[1][0], sprit[1][1]), sprit[2], sprit[3]))

        if "pickups" in spawndict:
            pickar = spawndict["pickups"]

            for pick in pickar:
                self.add_pickup(Pickup(self.game, (pick[0][0], pick[0][1]), pick[1], pick[2], pick[3], pick[4], pick[5], pick[6]))

    #function to add an npc
    def add_npc(self, npc):
        self.npc_list.append(npc)
    def damage_all_npc_in_range(self, x, y, range, dmg):
        for _npc in self.npc_list:
            nx, ny = _npc.map_pos
            if distance_formula(x, y, nx, ny) < range:
                _npc.get_damaged(dmg)

    #function to create a static sprite
    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)

    def add_passive(self, passive):
        self.passive_list.append(passive)
    def get_special_passive(self, special_tag): #func to get the passive npc with the correct special tag
        for passive in self.passive_list:
            if passive.special_tag == special_tag:
                return passive
        return None

    def add_pickup(self, pickup):
        self.pickup_list.append(pickup)
    def disable_pickup(self, pickup):
        self.pickup_list.remove(pickup)


###SPAWNER###


class Spawner: #(invisible)
    def __init__(self, game, pos):
        self.game = game
        self.x, self.y = pos

    def spawn(self, npc_name, number, location = None):
        if location == None:
            location = self.x, self.y

        npc_data = ENEMIES[npc_name]
        npc = None

        for x in range(number):
            npc = NPC(self.game, npc_data['path'], location, npc_data['scale'], npc_data['shift'], npc_data['animation_time'], npc_data['stats'])

            self.game.object_handler.add_npc(npc)


###WEAPON###


#weapon class, mostly manages visuals/weapon animations
class Weapon(AnimatedSprite):
    def __init__(self, game, path = 'resources/sprites/weapon/hand/0.png', scale = 1.75, animation_time = 50):
        super().__init__(game=game, path=path, scale=scale, animation_time=animation_time)
        self.images = deque(
            [pg.transform.smoothscale(img, (self.image.get_width() * scale, self.image.get_height() * scale)) for img in self.images])
        self.weapon_pos = (HALF_WIDTH - self.images[0].get_width() // 2 + 125, HEIGHT - self.images[0].get_height())
        self.reloading = False
        self.num_images = len(self.images)
        self.frame_counter = 0
        self.damage = 50

    #function to animate the working of the weapon
    def animate_shot(self):
        if self.reloading:
            self.game.player.shot = False
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image = self.images[0]
                self.frame_counter += 1
                if self.frame_counter == self.num_images:
                    self.reloading = False
                    self.frame_counter = 0

    #draws the weapon on screen
    def draw(self):
        if self.game.player.showWeapon:
            self.game.screen.blit(self.images[0], self.weapon_pos)

    #updates weapon
    def update(self):
        self.check_animation_time()
        self.animate_shot()

class GasAttack(AnimatedSprite):
    def __init__(self, game, path='resources/extras/gas/0.png', scale=2, animation_time=150):
        super().__init__(game=game, path=path, scale=scale, animation_time=animation_time)
        self.images = deque(
            [pg.transform.smoothscale(img, (self.image.get_width() * scale, self.image.get_height() * scale)) for img in self.images])

        n = 0
        for im in self.images:    
            self.images[n].set_alpha(200)
            n+=1

        self.images *= 2
    
        self.weapon_pos = 0, HEIGHT - self.images[0].get_height()
        self.gasing = False
        self.num_images = len(self.images)
        self.frame_counter = 0
        self.damage = GAS_DAMAGE

        self.green_fade = 175

    def animate_shot(self):
        if self.gasing:
            self.game.player.gas = False
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image = self.images[0]
                self.frame_counter += 1
                if self.frame_counter == self.num_images:
                    self.gasing = False
                    self.frame_counter = 0

    def draw(self):
        if self.gasing:
            s = pg.Surface((WIDTH, HEIGHT))
            s.set_alpha(self.green_fade)
            s.fill((60, 243, 60))
            self.game.screen.blit(s, (0,0))

            alph = self.game.gas_attack.green_fade * 2
            alph = 255 if alph > 255 else alph

            self.images[0].set_alpha(alph)

            self.game.screen.blit(self.images[0], self.weapon_pos)
            self.images[-1].set_alpha(200)

            self.green_fade -= 3

    def update(self):
        self.check_animation_time()
        self.animate_shot()


###SOUND###


#sound function, inits the pygame mixer and holds the sounds
class Sound:
    def __init__(self, game):
        self.game = game
        pg.mixer.init()
        self.path = 'resources/sound/'
        self.shotgun = pg.mixer.Sound(self.path + 'throw.wav')
        #self.npc_pain = pg.mixer.Sound(
        #self.npc_death = pg.mixer.Sound(
        #self.npc_shot = pg.mixer.Sound(
        #self.player_pain = pg.mixer.Sound(
        #self.theme = pg.mixer.Sound(self.path + 'theme.mp3')

class SoundPlayer:
    def __init__(self):
        pg.mixer.init()
        self.sounds = {}

        self.load_sound("theme", 'resources/sound/theme.wav')
        self.load_sound("armor", "resources/sound/armor.wav")
        self.load_sound("heal", "resources/sound/chew.wav")
        self.load_sound("reload", "resources/sound/reload.wav")
        self.load_sound("pickup", "resources/sound/pickup.wav")
        self.load_sound("playerpain", "resources/sound/umph.wav")
        self.load_sound("enemypain", "resources/sound/enemypain.wav")

    def load_sound(self, sound_name, sound_file_path):
        self.sounds[sound_name] = pg.mixer.Sound(sound_file_path)

    def play_sound(self, sound_name, volume=None, loop=True):
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            if volume is not None:
                sound.set_volume(volume)
            sound.play(loops=-1 if loop else 0)

    def stop_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].stop()

    def is_sound_playing(self, sound_name):
        if sound_name in self.sounds:
            return self.sounds[sound_name].get_num_channels() > 0
        return False


###NPC###


#non player character class, manages its npc's interaction/movement/work and its graphics
class NPC(AnimatedSprite):
    def __init__(self, game, path='resources/sprites/npc/basic/0.png', pos=(10.5, 5.5), scale = 0.6, shift = 0.38, animation_time=180, stats = None): #stats is an optional stats class that defines the enemy's stats
        super().__init__(game, path, pos, scale, shift, animation_time)

        #get list of lists of all attack anims
        self.attack_animations = [self.get_images(self.path + '/' + pth) for pth in os.listdir(self.path) if pth.startswith('attack')]
        #list of all last attack frames
        self.last_atk_frames = [ar[-1] for ar in self.attack_animations]

        self.current_atk = None

        #gets all its animations's frames
        self.attack_images = None#self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.pain_images = self.get_images(self.path + '/pain')
        self.walk_images = self.get_images(self.path + '/walk')

        self.last_atk_frame = None#self.attack_images[-1]

        #defines this npc's constants
        if stats == None:
            self.attack_dist = 2
            self.speed = 0.03
            self.size = 1
            self.health = 100
            self.attack_damage = 10
            self.accuracy = 0.15
        else:
            self.attack_dist = stats.attack_dist
            self.speed = stats.speed
            self.size = stats.size
            self.health = stats.health
            self.attack_damage = stats.attack_damage
            self.accuracy = stats.accuracy

        self.alive = True
        self.pain = False
        self.ray_cast_value = False
        self.frame_counter = 0

        #1. the time this npc died, 2.time before the npc will delete himself - if time_now - time_died > time_before_del: delete himself
        self.time_died = 0
        self.time_before_del = 5000

        #trigger to use pathfinding to hunt player down
        self.player_search_trigger = False

    def get_damaged(self, dmg):
        self.health -= dmg
        self.game.sound_player.play_sound("enemypain", loop=False)
        self.pain = True
        self.check_health()

    def self_destruct(self):
        self.game.object_handler.npc_list.remove(self)
        del self

    #update npc
    def update(self):
        self.check_animation_time()
        self.get_sprite()
        self.run_logic()

    #check if location is wall
    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map
    
    #check if potential movement goes into wall
    def check_wall_collision(self, dx, dy):
        if self.check_wall(int(self.x + dx * self.size), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * self.size)):
            self.y += dy

    #manage all npc movement
    def movement(self):
        #use pathfinding algo to find next location
        next_pos = self.game.pathfinding.get_path(self.map_pos, self.game.player.map_pos)
        next_x, next_y = next_pos

        #dont move there if there is already an npc standing in that square
        if next_pos not in self.game.object_handler.npc_positions:
            #mesure angle torward player and mesure potential movement
            angle = math.atan2(next_y + 0.5 - self.y, next_x + 0.5 - self.x)
            dx = math.cos(angle) * self.speed
            dy = math.sin(angle) * self.speed
            self.check_wall_collision(dx, dy)

    #attack player, lower health
    def attack(self):
        if self.animation_trigger:
            #self.game.sound.npc_shot.play()
            if random() < self.accuracy:
                self.game.player.get_damage(self.attack_damage)

    #if npc dies, play animation
    def animate_death(self):
        if not self.alive:
            if self.game.global_trigger and self.frame_counter < len(self.death_images) - 1:
                self.death_images.rotate(-1)
                self.image = self.death_images[0]
                self.frame_counter += 1
                if self.frame_counter == len(self.death_images) - 1:
                    self.time_died = pg.time.get_ticks()
            if not self.frame_counter < len(self.death_images) - 1:
                if pg.time.get_ticks() - self.time_died > self.time_before_del:
                    self.game.object_handler.npc_list.remove(self)
                    del self

    #if npc hurt, play animation
    def animate_pain(self):
        self.animate(self.pain_images)
        if self.animation_trigger:
            self.pain = False

    #check if npc was hit, check if player shot and check if the npc is in the middle of the players screen
    def check_hit_in_npc(self):
        if self.ray_cast_value and self.game.player.shot:
            if HALF_WIDTH - self.sprite_half_width - 100 < self.screen_x < HALF_WIDTH + self.sprite_half_width - 100:
                self.game.player.shot = False
                self.get_damaged(self.game.weapon.damage)

    #check if npc died yet
    def check_health(self):
        if self.health < 1:
            self.alive = False
            #self.game.sound.npc_death.play()

    def attack_animate(self):
        if self.current_atk == None:
            self.current_atk = randint(0, len(self.attack_animations) - 1)
            self.attack_images = self.attack_animations[self.current_atk]
            self.last_atk_frame = self.last_atk_frames[self.current_atk]

        self.animate(self.attack_images)

        if self.image == self.last_atk_frame:
            self.attack()
            self.current_atk = None

    #main logic runner for npc
    def run_logic(self):
        if self.alive:
            #check if there is a clear line of sight between player and npc
            self.ray_cast_value = self.ray_cast_player_npc()
            self.check_hit_in_npc()
            if self.pain:
                self.animate_pain()

            #if saw player, start hunting him down and moving torwards him, starts pathfinding algo
            elif self.ray_cast_value:
                self.player_search_trigger = True

                #if close enough attack, if not walk
                if self.dist < self.attack_dist:
                    self.attack_animate()
                else:
                    self.animate(self.walk_images)
                    self.movement()

            elif self.player_search_trigger:
                self.animate(self.walk_images)
                self.movement()

            else:
                self.animate(self.idle_images)
        else:
            self.animate_death()

    #class property of position on map
    @property
    def map_pos(self):
        return int(self.x), int(self.y)
    
    #check if there is a clear line of sight b/w player and npc using raycasting similar to the players one
    def ray_cast_player_npc(self):
        if self.game.player.map_pos == self.map_pos:
            return True
        
        wall_dist_v, wall_dist_h = 0, 0
        player_dist_v, player_dist_h = 0, 0

        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        ray_angle = self.theta
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        #horizontals
        y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

        depth_hor = (y_hor - oy) / sin_a
        x_hor = ox + depth_hor * cos_a

        delta_depth = dy / sin_a
        dx = delta_depth * cos_a

        for i in range(MAX_DEPTH):
            tile_hor = int(x_hor), int(y_hor)
            if tile_hor == self.map_pos:
                player_dist_h = depth_hor
                break
            if tile_hor in self.game.map.world_map:
                wall_dist_h = depth_hor
                break
            x_hor += dx
            y_hor += dy
            depth_hor += delta_depth

        #verticals
        x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

        depth_vert = (x_vert - ox) / cos_a
        y_vert = oy + depth_vert * sin_a

        delta_depth = dx / cos_a
        dy = delta_depth * sin_a

        for i in range(MAX_DEPTH):
            tile_vert = int(x_vert), int(y_vert)
            if tile_vert == self.map_pos:
                player_dist_v = depth_vert
                break
            if tile_vert in self.game.map.world_map:
                wall_dist_v = depth_vert
                break
            x_vert += dx
            y_vert += dy
            depth_vert += delta_depth

        player_dist = max(player_dist_h, player_dist_v)
        wall_dist = max(wall_dist_h, wall_dist_v)

        #if there is a clear line of sight between player and enemy
        if 0 < player_dist < wall_dist or not wall_dist:
            return True
        return False

        
###PATHFINDING ###


#pathfind class, uses simple pathfinding algo for all npcs to use
class PathFinding:
    def __init__(self, game):
        self.game = game
        self.map = game.map.cur_map
        self.ways = [-1, 0], [0, -1], [1, 0], [0, 1], [-1, -1], [1, -1], [1, 1], [-1, 1]
        self.graph = {}
        self.get_graph()

    def reset_pathfinding(self, newmap):
        self.map = newmap
        self.graph = {}
        self.get_graph()

    #main function, returns the next square to move to, to optimally reach goal from start
    def get_path(self, start, goal):
        #creates collection of already visited squares
        self.visited = self.bfs(start, goal, self.graph)
        path = [goal]
        step = self.visited.get(goal, start)

        #while not reached goal continue
        while step and step != start:
            path.append(step)
            step = self.visited[step]
        return path[-1]

    #pathfinding algo
    def bfs(self, start, goal, graph):
        queue = deque([start])
        visited = {start: None}

        while queue:
            cur_node = queue.popleft()
            if cur_node == goal:
                break
            next_nodes = graph[cur_node]

            for next_node in next_nodes:
                if next_node not in visited and next_node not in self.game.object_handler.npc_positions:
                    queue.append(next_node)
                    visited[next_node] = cur_node
        return visited

    #returns nearby nodes
    def get_next_nodes(self, x, y):
        return [(x + dx, y + dy) for dx, dy in self.ways if (x + dx, y + dy) not in self.game.map.world_map]

    #something
    def get_graph(self):
        for y, row in enumerate(self.map):
            for x, col in enumerate(row):
                if not col:
                    self.graph[(x, y)] = self.graph.get((x, y), []) + self.get_next_nodes(x, y)


###DISPLAY MENU###


DISPLAY_RES = DISPLAY_X, DISPLAY_Y = 600, 450
SLOT_SIZE = SLOT_X, SLOT_Y = 75, 75

#class for inventory icons, creates one per item in inventory
class InventoryIcon:
    def __init__(self, game, id):
        self.game = game
        self.id = id
        self.icon = ""
        self.quantity = 0
    
    def update_id(self, id):
        self.id = id

    def update(self):
        #function to update self.icon and self.quantity to the position of self.id in the inventory
        myitem = self.game.display_menu.item_list[self.id]
        self.icon = myitem.icon
        self.quantity = self.game.inventory_system.inventory[myitem]

        return self.draw()

    def draw(self):
        icon_size = SLOT_SIZE

        my_surface = pg.Surface(icon_size)

        white_bck = pg.Rect(3, 3, SLOT_X - 6, SLOT_Y - 6)
        pg.draw.rect(my_surface, (255, 255, 255), white_bck)

        icon_img = pg.image.load(self.icon)

        icon_img = pg.transform.scale(icon_img, (SLOT_X - 6, SLOT_Y - 6))

        doom_font = pg.font.Font('resources/textutil/doomfont.ttf', 25)

        if self.quantity > 1:
            quantity_txt = doom_font.render(str(self.quantity), False, (0, 0, 0))

        my_surface.blit(icon_img, (2, 3))
        if self.quantity > 1:
            my_surface.blit(quantity_txt, (SLOT_X - quantity_txt.get_width() - 5, SLOT_Y - quantity_txt.get_height())) ##NEED TO FIX QUANTITY TEXT

        #return a finished icon surface

        return my_surface

QUEST_RES = QUEST_X, QUEST_Y = 270, 100

class QuestIcon:
    def __init__(self, game, id):
        self.game = game
        self.id = id
        self.title = ""
        self.description = ""
        self.quantity = 0
    
    def update_id(self, id):
        self.id = id

    def update(self):
        #function to update self.icon and self.quantity to the position of self.id in the inventory
        myquest = self.game.display_menu.quest_list[self.id]
        self.title = myquest.title
        self.description = myquest.description

        return self.draw()

    def draw(self):
        icon_size = QUEST_RES

        my_surface = pg.Surface(icon_size)
        pg.draw.rect(my_surface, (255, 255, 255), pg.Rect(3, 3, QUEST_X - 6, QUEST_Y - 6))

        doom_font = pg.font.Font('resources/textutil/doomfont.ttf', 30)

        title_txt = doom_font.render(self.title, False, (0, 0, 0))

        ycor = 40
        for desctxt in self.game.text_box.wrap_text(self.description, 30):
            desc_txt = doom_font.render(desctxt, False, (0, 0, 0))
            my_surface.blit(desc_txt, (15, ycor))
            ycor += 20

        my_surface.blit(title_txt, (15, 15))

        #return a finished icon surface

        return my_surface

#class for showing active quests and inventory
SLOT_HOR_LIMIT = 6

class DisplayMenu:
    def __init__(self, game):
        self.game = game

        self.screen = self.game.screen

        self.showing = False

        self.quest_list = []
        self.item_list = []
        self.inventory_icons = []
        self.quest_icons = []

        self.inven_surface = None

    def draw(self):
        if self.showing:
            self.inven_surface = pg.Surface(DISPLAY_RES)

            pg.draw.rect(self.inven_surface, 'white', (5, 5, DISPLAY_X - 10, DISPLAY_Y - 10))

            self.inven_surface.set_alpha(210)

            self.draw_inventory()

            quest_surface = self.draw_quests()

            self.screen.blit(quest_surface, (int(DISPLAY_X * 1.3), 80))

            self.screen.blit(self.inven_surface, (80, 80))

    def event_call(self, event):
        if event.key == pg.K_TAB:
            self.showing = not self.showing

    def draw_quests(self):
        quest_surface = pg.Surface((int(QUEST_X * 1.5), DISPLAY_Y))

        quest_surface.set_alpha(100)

        doom_font = pg.font.Font('resources/textutil/doomfont.ttf', 60)

        curquests = doom_font.render("Quests", False, (255, 255, 255))

        quest_surface.blit(curquests, (int(QUEST_X * 1.5)//2 - 75, 10))

        self.quest_list = []
        for quest in self.game.player.current_quests:
            self.quest_list.append(quest)

        missing_quests = len(self.quest_list) - len(self.quest_icons)

        if missing_quests > 0:
            for x in range(missing_quests):
                self.quest_icons.append(QuestIcon(self.game, len(self.quest_icons)))
        elif missing_quests < 0:
            for x in range(abs(missing_quests)):
                self.quest_icons.pop(-1)

            n = 0
            for icon in self.quest_icons:
                icon.update_id(n)
                n+=1

        pos = 0
        for icon in self.quest_icons:
            slot = icon.update()

            x_padding, y_padding = 0, 30

            quest_surface.blit(slot, (int(QUEST_Y * 0.5), pos * SLOT_Y + y_padding * math.floor(pos / SLOT_HOR_LIMIT) + 75))

            pos+=1
        
        return quest_surface

    def draw_inventory(self):
        self.item_list = []
        for itm in self.game.inventory_system.inventory:
            self.item_list.append(itm)

        missing_icon_n = len(self.item_list) - len(self.inventory_icons)

        if missing_icon_n > 0:
            for x in range(missing_icon_n):
                self.inventory_icons.append(InventoryIcon(self.game, len(self.inventory_icons)))
        elif missing_icon_n < 0:
            for x in range(abs(missing_icon_n)):
                self.inventory_icons.pop(-1)

            n = 0
            for icon in self.inventory_icons:
                icon.update_id(n)
                n+=1

        pos = 0
        for icon in self.inventory_icons:
            slot = icon.update()

            x_padding, y_padding = 10, 10

            self.inven_surface.blit(slot, ((pos % SLOT_HOR_LIMIT) * SLOT_X + x_padding * pos + 30, (math.floor(pos / SLOT_HOR_LIMIT)) * SLOT_Y + y_padding * math.floor(pos / SLOT_HOR_LIMIT) + 30))

            pos+=1

    def update(self):
        if self.showing:
            self.game.player.inventoryOpen = True
        else:
            self.game.player.inventoryOpen = False


###POPUP MESSAGE###


class Popup:
    def __init__(self, game, msg, y):
        self.game = game
        self.text = msg
        self.fade = 255
        self.pos_y = y
        #need to scale the y-axis using the number of chars and some formula
        self.surf_y = 15 + 15 * len(self.game.text_box.wrap_text(self.text, 34))#mesure the y coordinates

        self.mysurface = pg.Surface((250, self.surf_y))

        self.create()

    def create(self):
        pg.draw.rect(self.mysurface, 'white', (0, 0, 250, self.surf_y), border_radius=4)

        y_cor = 10

        for txt in self.game.text_box.wrap_text(self.text, 34):
            self.mysurface.blit(self.game.object_renderer.doom_font.render(txt, False, (0, 0, 0)), (10, y_cor))
            y_cor += 15

        #self.mysurface.set_alpha(self.fade)
    
    def update(self):
        self.fade -= 1
        if self.fade <= 0:
            self.self_destruct()
        #self.mysurface.set_alpha(self.fade) #IF YOU ENABLE THIS, this will enable popup messages to FADE OUT!!
        return self.mysurface

    def self_destruct(self):
        self.game.object_renderer.popup_list.remove(self)
        del self
        return


###CROSSBAR###


class Crossbar:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.line_col = (200, 200, 200)  # white
        self.line_length = 50
        self.line_length = self.line_length//2
        self.line_width = 3
        
    def draw(self):
        pg.draw.line(self.screen, self.line_col, (HALF_WIDTH-self.line_length, HALF_HEIGHT), (HALF_WIDTH + self.line_length, HALF_HEIGHT), self.line_width) #left to right
        pg.draw.line(self.screen, self.line_col, (HALF_WIDTH, HALF_HEIGHT-self.line_length), (HALF_WIDTH, HALF_HEIGHT+self.line_length), self.line_width) #up to down


###STATBAR###


class StatBar:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.gas_image = self.game.object_renderer.get_texture('resources/extras/gas.png', res = (ICON_WIDTH, ICON_HEIGHT))
        #self.gas_icon_G = pg.font.Font(None, 90).render("G", False, (255, 255, 255))
        self.doom_font = pg.font.Font('resources/textutil/doomfont.ttf', 80)

    def drawGasIcon(self):
        icon_surface = pg.Surface((ICON_WIDTH, ICON_HEIGHT))

        # draw the gas image onto the icon surface
        icon_surface.blit(self.gas_image, (0, 0))

        # calculate the width of the filled rectangle based on the recharge level
        filled_rect_width = int(ICON_WIDTH * (1 - (self.game.player.gasCharge)/GAS_RECHARGE))

        # create a new surface for the filled rectangle
        filled_surface = pg.Surface((filled_rect_width, ICON_HEIGHT))

        filled_surface.set_alpha(175)  # set the transparency of the surface

        # draw a filled rectangle onto the surface
        filled_rect_color = (200, 200, 200)  # white
        filled_rect_rect = pg.Rect((0, 0), (filled_rect_width, ICON_HEIGHT))
        pg.draw.rect(filled_surface, filled_rect_color, filled_rect_rect)

        # overlay the filled rectangle surface onto the icon surface
        icon_surface.blit(filled_surface, (0, 0))

        #icon_surface.blit(self.gas_icon_G, ((icon_surface.get_width() - self.gas_icon_G.get_width())//2, (icon_surface.get_height() - self.gas_icon_G.get_height())//2 + 5))

        # display the icon on the screen
        self.screen.blit(icon_surface, (1500, HEIGHT + 20))

    def draw(self):
        #pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))
        pg.draw.rect(self.screen, 'black', (0, HEIGHT, WIDTH, SHEIGHT))

        doom_font = self.doom_font

        health = doom_font.render("Health:" + str(self.game.player.health), False, (255, 0, 0))
        self.screen.blit(health, (20, HEIGHT + 20))

        ammo = doom_font.render("Ammo:" + str(self.game.player.ammo), False, (255, 0, 0))
        self.screen.blit(ammo, (320, HEIGHT + 20))

        armor = doom_font.render("Armor:" + str(self.game.player.armor), False, (255, 0, 0))
        self.screen.blit(armor, (590, HEIGHT + 20))

        self.drawGasIcon()

###LORE###

class Lore:
    def __init__(self):
        print("1")
        self.screen = pg.display.set_mode((WIDTH, HEIGHT + SHEIGHT))
        print("2")
        self.clock = pg.time.Clock()
        print("3")
        self.img_dict = self.make_dict()
        print("4")
        self.actually_run()
        print("5")
    
    @staticmethod
    def get_texture(path):
        image = pg.image.load(path).convert_alpha()
        width, height = image.get_width(), image.get_height()
        if width >= height:
            wh_ratio = width/height

            width = WIDTH; height = HEIGHT / wh_ratio
        else:
            wh_ratio = height/width

            height = HEIGHT; width = WIDTH / wh_ratio

        print("returned")
        return pg.transform.scale(image, (width, height))
    
    def make_dict(self):
        out_ar = [self.get_texture('resources/lore/' + pth) for pth in os.listdir('resources/lore/')]
        print("made_dirs")
        return out_ar

    def actually_run(self):
        for obj in self.img_dict:
            print("ran")
            self.screen.fill('black')
            self.screen.blit(obj, obj.get_rect())
            pg.display.flip()
            pg.time.delay(3000)


###START MENU###


class MenuButton:
    def __init__(self, menu, pos, width, height, text, functionToCall):
        self.menu = menu
        self.pos = pos; self.posx, self.posy = pos
        self.width = width
        self.height = height
        self.text = text
        self.functionToCall = functionToCall
        self.surf = pg.Surface((self.width, self.height))

        self.button_txt = self.menu.font.render(self.text, False, 'black')

        self.current_color = (200, 200, 200)

        self.mouse_over = False

        self.hidden = False

        self.draw_button()

    def draw_button(self):
        self.surf.fill('black')
        pg.draw.rect(self.surf, self.current_color, (0, 0, self.width, self.height), border_radius=5)

        self.surf.blit(self.button_txt, (self.width//2 - self.button_txt.get_width()//2, self.height//2 - self.button_txt.get_height()//2))

    def change_bright(self, mouseOver): #true/false
        if mouseOver:
            self.mouse_over = True
            self.current_color = (255, 255, 255)
        else:
            self.mouse_over = False
            self.current_color = (200, 200, 200)
        self.draw_button()

    def update(self):
        if (self.posx <= self.menu.mouseX <= self.posx + self.width) and (self.posy <= self.menu.mouseY <= self.posy + self.height):
            self.change_bright(True)
        else:
            self.change_bright(False)

    def mouseClick(self):
        if self.mouse_over and not self.hidden:
            self.functionToCall()

    def draw(self):
        if not self.hidden:
            self.menu.screen.blit(self.surf, self.pos)

    def changeHidden(self, hidden):
        self.hidden = hidden
        self.change_bright(False)

class StartMenu:
    def __init__(self):
        self.screen = pg.display.set_mode((WIDTH, HEIGHT + SHEIGHT))
        self.in_menu = True
        self.font = pg.font.Font(None, 65)
        self.mouseX, self.mouseY = pg.mouse.get_pos()
        self.buttons = []
        self.inCredits = False
        self.credits = pg.image.load('resources/sprites/credits.png')

    def update(self):
        self.mouseX, self.mouseY = pg.mouse.get_pos()

    def get_button(self, buttonFunc):
        for but in self.buttons:
            if but.functionToCall == buttonFunc:
                return but

    def run(self):
        self.buttons.append(MenuButton(self, (HALF_WIDTH - 75, 600), 150, 75, "Exit", self.exit_button))
        self.buttons.append(MenuButton(self, (HALF_WIDTH - 100, 500), 200, 75, "Credits", self.credits_button))
        self.buttons.append(MenuButton(self, (1300, 75), 50, 50, "X", self.X_credits_button))
        self.buttons.append(MenuButton(self, (HALF_WIDTH - 75, 400), 150, 75, "Play", self.play_button))

        self.get_button(self.X_credits_button).changeHidden(True)

        while self.in_menu:
            if self.inCredits:
                self.update()
                self.screen.blit(self.credits, (HALF_WIDTH - self.credits.get_width()//2, HALF_HEIGHT - self.credits.get_height()//2))
                self.get_button(self.X_credits_button).update(); self.get_button(self.X_credits_button).draw()
                self.click_checks()
                pg.display.flip()
                continue

            self.update()
            [but.update() for but in self.buttons]
            [but.draw() for but in self.buttons]
            self.click_checks()
            pg.display.flip()
            
    def click_checks(self):
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                [but.mouseClick() for but in self.buttons]

    def play_lore(self):
        self.lore = Lore()
        self.lore.actually_run()

    def exit_button(self):
        pg.quit()
        sys.exit()

    def play_button(self):
        self.in_menu = False

    def credits_button(self):
        self.screen.fill('black')

        self.inCredits = True
        [but.changeHidden(True) for but in self.buttons]
        self.get_button(self.X_credits_button).changeHidden(False)

        [but.update() for but in self.buttons]
        [but.draw() for but in self.buttons]

        pg.display.flip()

    def X_credits_button(self):
        self.screen.fill('black')

        self.inCredits = False
        [but.changeHidden(False) for but in self.buttons]
        self.get_button(self.X_credits_button).changeHidden(True)

        [but.update() for but in self.buttons]
        [but.draw() for but in self.buttons]

        pg.display.flip()


###GAME CODE###


#game class, the most important in the script, all function stem from this class, controls everything, basically god
class Game:
    #def vars, init func
    def __init__(self):
        self.screen = pg.display.set_mode((WIDTH, HEIGHT + SHEIGHT))
        self.clock = pg.time.Clock()
        self.delta_time = 1
        
        #event for animation i think
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0

        #event for adding chars to the textbox
        self.next_char_trigger = False
        self.next_char_event = pg.USEREVENT + 1

        #event for turning portal
        self.portal_event = pg.USEREVENT + 2

        pg.time.set_timer(self.global_event, 40)
        pg.time.set_timer(self.next_char_event, 10)
        pg.time.set_timer(self.portal_event, 200)
        #dictionary of key isPressed?
        self.keys = {
            pg.K_w: False,
            pg.K_s: False,
            pg.K_a: False,
            pg.K_d: False,
            pg.K_LEFT: False,
            pg.K_RIGHT: False,
            pg.K_LSHIFT: False
        }
        self.new_game()

    #creates instances of all neccesary classes and starts of the game
    def new_game(self):
        self.sound_player = SoundPlayer(); self.sound_player.play_sound("theme", volume=0.2, loop=True)
        self.map = Map(self)
        self.player = Player(self)
        self.inventory_system = InventorySystem(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.gas_attack = GasAttack(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        self.statbar = StatBar(self)
        self.text_box = TextBox(self, 200, HALF_HEIGHT + HALF_HEIGHT // 2, HALF_WIDTH + HALF_WIDTH // 2, HALF_HEIGHT // 2)
        self.quest_manager = QuestManager(self)
        self.display_menu = DisplayMenu(self)
        self.crossbar = Crossbar(self)

    #updates everything that needs updating
    def update(self):
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        self.gas_attack.update()
        self.text_box.update()
        self.display_menu.update()
        self.quest_manager.update()
        #self.animated_sprite.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'SHROOM - {self.clock.get_fps() :.1f}')
        pg.display.set_icon(pg.image.load('resources/sprites/logo.png'))

    #draws stuff
    def draw(self):
        self.object_renderer.draw()
        self.weapon.draw()
        self.gas_attack.draw()
        self.statbar.draw()
        self.display_menu.draw()
        self.crossbar.draw()

        #debugin thingy
        self.map.draw()
        self.player.draw()

    #checks pygame events for key pressed and quits
    def check_events(self):
        self.global_trigger = False
        self.next_char_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            #an event that is triggered every... i think 40 ms...
            if event.type == self.global_event:
                self.global_trigger = True
                self.player.checkWeaponShow()

            elif event.type == self.next_char_event:
                self.next_char_trigger = True
                self.object_renderer.popup_update()

            elif event.type == self.portal_event:
                self.object_renderer.next_portal_frame()

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
                else:
                    self.keys[event.key] = True
                self.text_box.event_call(event)
                self.display_menu.event_call(event)
                [passive.event_call(event) for passive in self.object_handler.passive_list]
            if event.type == pg.KEYUP:
                self.keys[event.key] = False
            self.player.single_fire_event(event)

    #main run loop
    def run(self):
        while 1:
            self.check_events()
            self.update()
            self.draw()

#starts the game
if __name__ == '__main__':
    pg.init()

    start_menu = StartMenu()
    start_menu.run()
    
    game = Game()
    game.run()