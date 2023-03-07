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
import numpy as np

###BASIC FUNCTIONS###
#distance formula func
def distance_formula(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

#returns a list of numbers for the distance of each numbers in the input list from the input num
def number_distances(ar, num):
    return [abs(i-num) for i in ar]


###SETTINGS###

# screen settings
RES = WIDTH, HEIGHT = 1600, 700 #1600, 700 is default, i might change it for simplicity sake

#statbar settings
STATBARRES = SWIDTH, SHEIGHT = WIDTH, 150 #WIDTH, 150 is default

# RES = WIDTH, HEIGHT = 1920, 1080
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 60

#player vars
PLAYER_POS = 1.5, 1.5  # mini_map
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.0015
PLAYER_SIZE_SCALE = 60
PLAYER_MAX_HEALTH = 100
RECOVERY_DELAY = 3000

QUEST_LIMIT = 3

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
            attack_dmg = 8,
            accuracy = 0.15
        )
    }
}


###PLAYER###


#player class
class Player:
    #define class variables when instanced
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.rel = pg.mouse.get_rel()[0]
        self.shot = False
        self.health = PLAYER_MAX_HEALTH
        self.ammo = 3
        self.showWeapon = True
        self.time_prev = pg.time.get_ticks()
        #if in range to talk to johny
        self.johny_range = False
        self.canMove = True

        self.gas = False

        self.canGas = True
        self.gasCharge = 0
        self.lastGasUse = 0

        self.current_quests = [] #lets just restrict it to three quests for now

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

    #return if recovery delay passed before last recovery
    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > RECOVERY_DELAY:
            self.time_prev = time_now
            return True

    #check if health is too low
    def check_game_over(self):
        pass
        #if self.health < 1:
        #    self.game.object_renderer.game_over()
        #    pg.display.flip()
        #    pg.time.delay(1500)
        #    self.game.new_game()

    #function to lower health, show hurt screen, play hurt sound and check if health too low
    def get_damage(self, dmg):
        self.health -= dmg
        #self.game.object_renderer.player_damage()
        #self.game.sound.player_pain.play()
        self.check_game_over()

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
        if not self.canMove:
            return
        #mesure trigonometric numbers
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        #define potential movement and set speed
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time

        #speed times trig nums
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        #define dictionary with key statuses
        keys = self.game.keys

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

        #self.rel is used for rendering the sky, its not set to angle because angle has modulus on it which makes the sky choppy

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
        #pg.draw.line(self.game.screen, 'yellow', (self.x * 100, self.y * 100),
        #             (self.x * 100 + WIDTH * math.cos(self.angle),
        #              self.y * 100 + WIDTH * math.sin(self.angle)), 2)
        pg.draw.circle(self.game.screen, 'green', (self.x * 100, self.y * 100), 15)

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


###QUEST SYSTEM###


class Quest:
    #type - Escort/Kill/Gather, subtype - typeofenemy/locationtogoto/thingtocollect, goal_number - number of things to kill/gather, reward - what youll get
    def __init__(self, title, desc, type, subtype, goal_number, reward):
        self.title = title
        self.description = desc
        self.type = type
        self.subtype = subtype
        self.goal_number = goal_number
        self.reward = reward

QUEST_DICT = {

}

class QuestManager:
    def __init__(self, game):
        self.game = game

    #function to start a quest
    def request_quest(self, quest):
        if len(self.game.player.current_quests) < QUEST_LIMIT:
            self.game.player.current_quests.append(quest)

    #check if quests are done or not
    def quest_watch(self):
        if len(self.game.player.current_quests) > 0:
            for quest in self.game.player.current_quests:
                if quest.type == "kill":
                    pass
                elif quest.type == "gather":
                    pass
                elif quest.type == "escort": #ig this is also a go to quest, you dont actually have to escort
                    pass
                else:
                    raise ValueError(quest.type + " in " + quest.title + " is not a valid quest type")

    def update(self):
        self.quest_watch()


###MAP###


#define map
_ = False
mini_map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, _, _, _, _, _, _, _, _, _, 3, 2, 2, 2, _, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, 2, 1],
    [1, _, _, _, _, _, _, _, _, _, 2, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, 3, 2, 2, 2, _, 1],
    [1, 1, _, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, _, 1],
    [3, _, _, _, _, _, _, 3, _, _, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, 5, _, _, _, _, _, _, _, 1],
    [5, _, _, _, _, _, _, 5, _, _, _, _, _, _, _, 1],
    [1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    #0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
]

#   for ALL_EMPTY_COLLIDERS, when adding an empty collider, you need to go into the game and check the position 
#   of where you actually want to put it because it sometimes registers differently then seen on map, LIKE ONE OFF ON THE X OR Y AXIS THEN WHAT IT LOOKS LIKE

#   if you want to be lazy, you can change the wall collision code in player class so that it considers the squares around an empty collider square also impermeable so that you dont have to check all of them

#   cough, cough, never mind the last three lines, idk if they actually apply because i kinda counted wrong when making the location for the empty collider square...

# need to add all empty colliders here, if there is a coordinate here, it will not be able to be walked through, do not forget coordinates start from 1, y increases downwards, x increases to the right
ALL_EMPTY_COLLIDER = [(14, 7)]


#map class
"""
EXTRA_MAP_DATA = {
    "fog" : [(9, 8), (15, 23)] #top left coord and bottom right coord
}
"""

class Map:
    #store some variables, this class is mostly used for fetching map vars
    def __init__(self, game):
        self.game = game
        self.mini_map = mini_map
        self.world_map = {}
        self.rows = len(self.mini_map)
        self.cols = len(self.mini_map[0])
        self.get_map()

    def get_map(self):
        for j, row in enumerate(self.mini_map):
            for i, value in enumerate(row):
                if value:
                    self.world_map[(i, j)] = value

    #debug thinkgy
    def draw(self):
        [pg.draw.rect(self.game.screen, 'darkgray', (pos[0] * 100, pos[1] * 100, 100, 100), 2)
         for pos in self.world_map]
        

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
                            self.last_talk = pg.time.get_ticks()
                            return
                        self.writing = True
                    else:
                        self.showing = False
                        self.text = ""
                        self.goal_array = []
                        self.goal_text = ""

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
    def display_text(self, text, pitch = None):
        #if text is longer than the character limit, turn it into an array
        if self.writing:
            return False
        
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
        #self.blood_screen = 
        #self.gameoverImg = 
        

    #function to draw background(sky) and to render all game objects
    def draw(self):
        self.draw_background()
        self.render_game_objects()

    #if you lost, show lose screen
    def game_over(self):
        #self.screen.blit(gameoverImg, (0, 0))
        pass

    #show hurt screen
    def player_damage(self):
        #self.screen.blit(self.blood_screen, (0, 0))
        pass


    #draw sky and floor, not currently used
    def draw_background(self):
        self.sky_offset = (100*self.game.player.rel) % WIDTH
        self.screen.fill('black')
        
        self.screen.blit(self.sky_image, (-self.sky_offset, 0))
        self.screen.blit(self.sky_image, (-self.sky_offset + WIDTH, 0))
        #floor
        pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))

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
        return {
            1: self.get_texture('resources/textures/1.png'),
            2: self.get_texture('resources/textures/2.png'),
            3: self.get_texture('resources/textures/3.png'),
            4: self.get_texture('resources/textures/4.png'),
            5: self.get_texture('resources/textures/5.png'),
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

    #mesure the sprite's projections, add itself to objects to render with its normalized distance, actual image and position
    def get_sprite_projection(self):
        proj = SCREEN_DIST / self.norm_dist * self.SPRITE_SCALE
        proj_width, proj_height = proj * self.IMAGE_RATIO, proj

        image = pg.transform.scale(self.image, (proj_width, proj_height))

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

    #update sprite
    def update(self):
        self.get_sprite()

"""
class SuperStaticSprite(SpriteObject):
    def __init__(self, game, path='resources/sprites/static/candlebra.png', pos=(10.5, 3.5), scale=0.25, shift=1.4):
        super().__init__(game, path, pos, scale, shift)
"""

class Pickup(SpriteObject):
    #type would be money/armor/ammo/special(for quests)/etc, subtype would really be for special type, number is for the number of the thing you pickup
    def __init__(self, game, path, pos, type, number=1, scale=0.25, shift=0, subtype = ""):
        super().__init__(game, path, pos, scale, shift)
        self.type = type
        self.subtype = subtype
        self.number = number
        self.pickup_range = 1

    def in_player_range(self):
        sx, sy = self.pos
        px, py = self.game.player.map_pos
        return distance_formula(sx, sy, px, py) <= self.pickup_range
    
    def update_sub(self):
        removed = False
        if self.in_player_range():
            if self.type == "money":
                pass

            elif self.type == "armor":
                pass

            elif self.type == "health":
                if self.game.player.heal(self.number):
                    removed = True

            elif self.type == "ammo":
                self.game.player.ammo += self.number
                removed = True

            elif self.type == "special":
                if self.subtype == "stomachmedicine":
                    pass

                else:
                    raise ValueError(self.subtype + "is an invalid pickup subtype")
                
            else:
                raise ValueError(self.type + " is an invalid pickup type")
            
        if removed:
            self.game.object_handler.disable_pickup(self)
            del self

#class for johny
class Johny(SpriteObject):
    def __init__(self, game, path='resources/sprites/static/johny.png', pos=(10.5, 3.5), scale=1, shift=0.27):
        super().__init__(game, path, pos, scale, shift)
        self.pitch = "deep"
        self.talkrange = 2.5
        self.pos = pos

    def event_call(self, event):
        if self.game.player.johny_range:
            if event.key == pg.K_e and not self.game.text_box.showing and self.game.text_box.time_limit_done():
                self.game.text_box.display_text("Hello Shrek, welcome to hell, I am Johny, you should probably beware of the demons patrolling around here, use your onions as a defense, there is a bag right there", self.pitch)

    def update_sub(self):
        mx, my = self.pos
        px, py = self.game.player.map_pos

        #if within range, allow talk
        if distance_formula(mx, my, px, py) <= self.talkrange:
            self.game.player.johny_range = True
            if not self.game.text_box.showing:
                needTalk_font = pg.font.Font('resources/textutil/textboxfont.ttf', 30)

                needTalk = needTalk_font.render("E to talk to Johny", False, (255, 255, 255))

                self.game.screen.blit(needTalk, (self.screen_x - 200, HEIGHT))
        else:
            self.game.player.johny_range = False
            
class BasicPassiveNPC(SpriteObject): #NEED TO MAKE A METHOD TO ONLY ALLOW PLAYER TO SPEAK TO ONE NPC AT A TIME AND NOT HAVE MULTIPLE MESSAGES FOR PRESS SPACE TO TALK APPEAR
    def __init__(self, game, path='resources/sprites/passive/ghost.png', pos=(10.5, 3.5), usetextbox=True, myline="hello", name="character", pitch="high", scale=0.75, shift=0): #pitch: high/mid/deep
        super().__init__(game, path, pos, scale, shift)
        self.talkrange = 2.5
        self.pos = pos
        #trigger text box for his line or just make text float above him
        self.use_textbox = usetextbox
        self.myline = myline
        self.myname = name
        self.pitch = pitch
        self.interact_enabled = True

    def player_in_range(self):
        sx, sy = self.pos
        px, py = self.game.player.map_pos
        return distance_formula(sx, sy, px, py) <= self.talkrange

    def event_call(self, event):
        if self.player_in_range() and self.interact_enabled:
            if event.key == pg.K_e and not self.game.text_box.showing and self.game.text_box.time_limit_done() and self.use_textbox:
                self.game.text_box.display_text(self.myline, self.pitch)

    def update_sub(self):
        #if within range, allow talk
        if self.player_in_range() and self.interact_enabled:
            if not self.game.text_box.showing:
                needTalk_font = pg.font.Font('resources/textutil/textboxfont.ttf', 30)

                needTalk = needTalk_font.render("E to talk to " + self.myname, False, (255, 255, 255))

                self.game.screen.blit(needTalk, (self.screen_x - 200, HEIGHT))


#sub class for a static sprite for ammo recharge
class OnionBag(SpriteObject):
    def __init__(self, game, path='resources/sprites/static/onionbag.png', pos=(2.0, 2.0), scale=0.5, shift=0.7):
        super().__init__(game, path, pos, scale, shift)
        self.pos = pos
        self.onion_number = 5
        self.range = 1.5

    def update_sub(self):
        mx, my = self.pos
        px, py = self.game.player.map_pos

        if distance_formula(mx, my, px, py) <= self.range:
            self.game.player.ammo += self.onion_number
            self.game.player.checkWeaponShow()
            self.game.object_handler.sprite_list.remove(self)
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
        images = deque()
        for file_name in os.listdir(path):
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
        add_sprite = self.add_sprite
        add_npc = self.add_npc
        add_pass = self.add_passive
        add_pickup = self.add_pickup

        #dictionary of npc positions
        self.npc_positions = {}

        #dictionary of basicpassivenpcs' and how centered they are, the more center the more priority for talking to him
        self.passive_centered = {}

        #Create static sprites
        add_sprite(OnionBag(game, pos=(5.5,5.5)))

        #add_sprite(SpriteObject(game, path="resources/sprites/static/cursedtree.png", pos=(9.5, 10.0), scale=1.2, shift=-0.12))

        #Create special characters
        self.johny = Johny(game, pos=(1.5, 4.5))
        add_sprite(self.johny)

        #Create npcs
        add_npc(NPC(game, pos=(1.5, 3.5)))
        #add_npc(NPC(game, pos=(9.5,5.5)))
        #add_npc(NPC(game, pos=(9.5,5.5)))
        #add_npc(NPC(game, pos=(9.5,5.5)))

        add_pass(BasicPassiveNPC(game, path='resources/sprites/passive/bellygoblin.png' , pos=(14.5, 7.5), myline="Ohhhh, yesterday I ate a- something I wasn't supposed, now I have a terrrrible stomach ache", name="bloated goblin", pitch="high", scale=1.25, shift=0.1))

        #Create passive npcs
        add_pass(BasicPassiveNPC(game, pos=(13.5, 4.5), myline="Hello, I run politics", name="friendly ghost", shift=0.2))

        add_pass(BasicPassiveNPC(game, path='resources/sprites/passive/donkey.png', pos=(3.5, 9.5), myline="Hello Shrek, welcome to the cul- club, yes I meant club", name="donkey", pitch="mid", shift=0.3))
        add_pass(BasicPassiveNPC(game, path='resources/sprites/passive/donkey.png', pos=(5.5, 9.5), myline="...", name="donkey clone", pitch=None, shift=0.3))
        

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
    def __init__(self, game, path = 'resources/sprites/weapon/hand/0.png', scale = 1.75, animation_time = 75):
        super().__init__(game=game, path=path, scale=scale, animation_time=animation_time)
        self.images = deque(
            [pg.transform.smoothscale(img, (self.image.get_width() * scale, self.image.get_height() * scale)) for img in self.images])
        self.weapon_pos = (HALF_WIDTH - self.images[0].get_width() // 2, HEIGHT - self.images[0].get_height())
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
        #gets all its animations's frames
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.pain_images = self.get_images(self.path + '/pain')
        self.walk_images = self.get_images(self.path + '/walk')

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
        self.pain = True
        self.check_health()

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
                #self.game.sound.npc_pain.play()
                self.game.player.shot = False
                self.pain = True
                self.health -= self.game.weapon.damage
                self.check_health()

    #check if npc died yet
    def check_health(self):
        if self.health < 1:
            self.alive = False
            #self.game.sound.npc_death.play()

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
                    self.animate(self.attack_images)
                    self.attack()
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
        self.map = game.map.mini_map
        self.ways = [-1, 0], [0, -1], [1, 0], [0, 1], [-1, -1], [1, -1], [1, 1], [-1, 1]
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


###STATBAR###


class StatBar:
    def __init__(self, game):
        self.game = game
        self.screen = game.statscreen
        self.gas_image = self.game.object_renderer.get_texture('resources/extras/gas.png', res = (ICON_WIDTH, ICON_HEIGHT))

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

        # display the icon on the screen
        self.screen.blit(icon_surface, (1500, HEIGHT + 20))

    def draw(self):
        #pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))
        pg.draw.rect(self.screen, 'black', (0, HEIGHT, WIDTH, SHEIGHT))

        doom_font = pg.font.Font('resources/textutil/doomfont.ttf', int(90 * HEIGHT/900))

        health = doom_font.render("Health:" + str(self.game.player.health), False, (255, 0, 0))

        self.screen.blit(health, (20, HEIGHT + 20))

        ammo = doom_font.render("Ammo:" + str(self.game.player.ammo), False, (255, 0, 0))

        self.screen.blit(ammo, (350, HEIGHT + 20))

        armor = doom_font.render("Armor: 100", False, (255, 0, 0))

        self.screen.blit(armor, (590, HEIGHT + 20))

        self.drawGasIcon()


###GAME CODE###


SC_SCREEN = SC_SCREENX, SC_SCREENY = 1000, 450
SC_ST_SCREEN = SC_ST_SCREENX, SC_ST_SCREENY = SC_SCREENX, 100
#game class, the most important in the script, all function stem from this class, controls everything, basically god
class Game:
    #def vars, init func
    def __init__(self):
        pg.init()
        self.mainscreen = pg.display.set_mode((SC_SCREENX, SC_SCREENY + SC_ST_SCREENY))
        self.screen = pg.Surface((WIDTH, HEIGHT))
        self.statscreen = pg.Surface((WIDTH, SHEIGHT))

        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0

        self.next_char_trigger = False
        self.next_char_event = pg.USEREVENT + 1

        pg.time.set_timer(self.global_event, 40)
        pg.time.set_timer(self.next_char_event, 10)
        #dictionary of key isPressed?
        self.keys = {
            pg.K_w: False,
            pg.K_s: False,
            pg.K_a: False,
            pg.K_d: False,
            pg.K_LEFT: False,
            pg.K_RIGHT: False
        }
        self.new_game()

    #creates instances of all neccesary classes and starts of the game
    def new_game(self):
        self.sound_player = SoundPlayer(); self.sound_player.load_sound("theme", 'resources/sound/theme.wav'); self.sound_player.play_sound("theme", volume=0.25, loop=True)
        self.map = Map(self)
        self.player = Player(self)
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

    #updates everything that needs updating
    def update(self):
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        self.gas_attack.update()
        self.text_box.update()
        #self.quest_manager.update()
        #self.animated_sprite.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'SHROOM - {self.clock.get_fps() :.1f}')

    #draws stuff
    def draw(self):
        self.object_renderer.draw()
        self.weapon.draw()
        self.gas_attack.draw()
        self.statbar.draw()

        scaled_screen = pg.transform.scale(self.screen, SC_SCREEN)
        scaled_stscreen = pg.transform.scale(self.statscreen, SC_ST_SCREEN)

        self.mainscreen.blit(scaled_screen, (0, 0))
        self.mainscreen.blit(scaled_stscreen, (0, SC_SCREENY))
        #pg.display.flip()

        #debugin thingy
        #self.map.draw()
        #self.player.draw()

    #checks pygame events for key pressed and quits
    def check_events(self):
        self.global_trigger = False
        self.next_char_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == self.global_event:
                self.global_trigger = True
                self.player.checkWeaponShow()
            if event.type == self.next_char_event:
                self.next_char_trigger = True
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
                else:
                    self.keys[event.key] = True
                self.text_box.event_call(event)
                self.object_handler.johny.event_call(event)
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
    game = Game()
    game.run()