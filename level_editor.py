import json
import pygame
import sys
from main import MazeGenerator

WIDTH, HEIGHT = 1600, 900

pygame.init()

class MenuButton:
    def __init__(self, menu, pos, width, height, text, functionToCall, colors = [(200, 200, 200), (255, 255, 255)]):
        self.menu = menu
        self.pos = pos; self.posx, self.posy = pos
        self.width = width
        self.height = height
        self.text = text
        self.functionToCall = functionToCall
        self.surf = pygame.Surface((self.width, self.height))

        self.button_txt = self.menu.font.render(self.text, False, 'black')

        self.colors = colors

        self.current_color = colors[0]

        self.mouse_over = False

        self.draw_button()

    def draw_button(self):
        self.surf.fill('black')
        pygame.draw.rect(self.surf, self.current_color, (0, 0, self.width, self.height), border_radius=5)

        self.surf.blit(self.button_txt, (self.width//2 - self.button_txt.get_width()//2, self.height//2 - self.button_txt.get_height()//2))

    def change_bright(self, mouseOver): #true/false
        if mouseOver:
            self.mouse_over = True
            self.current_color = self.colors[1]
        else:
            self.mouse_over = False
            self.current_color = self.colors[0]
        self.draw_button()

    def update(self):
        if (self.posx <= self.menu.mouseX <= self.posx + self.width) and (self.posy <= self.menu.mouseY <= self.posy + self.height):
            self.change_bright(True)
        else:
            self.change_bright(False)

        self.draw()

    def mouseClick(self):
        if self.mouse_over:
            self.functionToCall()

    def draw(self):
        self.menu.screen.blit(self.surf, self.pos)

    def changeHidden(self, hidden):
        self.hidden = hidden
        self.change_bright(False)

class Map:
    def __init__(self, editor):
        self.editor = editor

        self.map = [[1]]
        self.npcs = []

        self.width = 1
        self.height = 1

        self.Xoffset = 0
        self.Yoffset = 0

        self.zoom = 20
        self.thickness = 4

        self.lvlDict = {}

        self.selected = 1

        self.enemy_selected = "bob"

        self.maze_generator = MazeGenerator()

    def change_select(self, val):
        self.selected = val

    def change_Eselect(self, val):
        self.enemy_selected = val

    def add_width(self):
        self.width += 1

        for y, r in enumerate(self.map):
            self.map[y].append(0)

    def add_height(self):
        self.height += 1

        self.map.append([0] * self.width)

    def save_game(self):
        def findObject(map, obj):
            for y, r in enumerate(map):
                for x, v in enumerate(r):
                    if v == obj:
                        return [x, y]
            return None
        def getSpawn(npcs):
            for n in npcs:
                if n[0] == "spawn":
                    return n[1]
            return None

        self.lvlDict = {}

        self.lvlDict["map"] = self.map
        if not (v := findObject(self.map, "p")) == None:
            self.lvlDict["portal"] = v
        
        if not (v := getSpawn(self.npcs)) == None:
            self.lvlDict["spawn"] = v
            self.npcs.pop([v[0] for v in self.npcs].index("spawn"))

        self.lvlDict["spawns"] = {}
        self.lvlDict["spawns"]["npc"] = self.npcs

        with open('result.json', 'w') as fp:
            json.dump(self.lvlDict, fp)

        print("Map saved")

    def load_random(self):
        gen = self.maze_generator.generate_maze(30, 30, 0)

        self.map = gen[0]

        self.width = len(self.map[0])
        self.height = len(self.map)

        self.map = self.sl_reset(self.map)

        self.Xoffset = 0; self.Yoffset = 0

        self.width = len(self.map[0])
        self.height = len(self.map)

    def add_walls(self):
        maze = self.map

        n = 0
        for r in maze:
            n_r = [1]
            for s in r:
                n_r.append(s)
            n_r.append(1)
            maze[n] = n_r
            n+=1

        top_down_padding = []

        for x in range(self.width + 2):
            top_down_padding.append(1)

        final_maze = [top_down_padding]

        for r in maze:
            final_maze.append(r)
        final_maze.append(top_down_padding)

        self.map = final_maze
        self.width += 2
        self.height += 2

    def sl_reset(self, dict):
        td = dict
        return td

    def outlier_reset(self):
        shortest = float('inf')

        for x in self.map:
            shortest = min(shortest, len(x))

        ml = len(self.map)
        for y in range(ml):
            self.map[y] = self.map[y][:shortest]

        self.width = shortest

    def load_game(self):
        with open('result.json') as json_file:
            data = json.load(json_file)
        json_file.close()

        self.map = data["map"]
        if "spawns" in data:
            if "npc" in data["spawns"]:
                self.npcs = data["spawns"]["npc"]

        if "spawn" in data:
            self.npcs.append(["spawn", data["spawn"]])

        self.Xoffset = 0; self.Yoffset = 0

        self.width = len(self.map[0])
        self.height = len(self.map)

    def reset_map(self):
        self.map = [[1]]
        self.width = 1
        self.height = 1

        self.npcs = []

    def update(self):
        self.draw_map()

    def draw_map(self):
        def pos_color(val):
            if val == 0:
                return 'darkgray'
            elif val == 1:
                return 'red'
            elif val == 2:
                return 'orange'
            elif val == 3:
                return 'yellow'
            elif val == 4:
                return 'lightgreen'
            elif val == 5:
                return 'blue'
            elif val == "p":
                return 'purple'

        def enem_color(val):
            if val == "spawn":
                return 'white'
            elif val == "tridemon":
                return (170, 183, 20)
            elif val == "gemdemon":
                return (248, 11, 11)
            elif val == "shadowslinger":
                return (112, 18, 125)
            elif val == "zombie":
                return (41, 150, 16)
            elif val == "satansnovel":
                return (106, 55, 15)
            elif val == "hut":
                return (70, 51, 32)
            else:
                return 'red'

        map_draw = {}

        for j, row in enumerate(self.map):
            for i, value in enumerate(row):
                map_draw[(i, j)] = value

        [pygame.draw.rect(self.editor.screen, pos_color(map_draw[pos]), (pos[0] * self.zoom + self.Xoffset * self.zoom + 300, pos[1] * self.zoom + self.Yoffset * self.zoom + 300, self.zoom, self.zoom), self.thickness//2) for pos in map_draw]

        for npc in self.npcs:
            pygame.draw.circle(self.editor.screen, enem_color(npc[0]), (npc[1][0] * self.zoom + self.Xoffset * self.zoom + 300, npc[1][1] * self.zoom + self.Yoffset * self.zoom + 300), self.thickness)

    def mouseClick(self, mx, my, retVal = False):
        row = int((my - 300 - self.Yoffset * self.zoom) // self.zoom)
        col = int((mx - 300 - self.Xoffset * self.zoom) // self.zoom)

        if retVal:
            print(str((col, row)))
            return

        if (0 <= col <= self.width-1) and (0 <= row <= self.height-1):
            if self.map[row][col] == self.selected:
                self.map[row][col] = 0
            else:
                self.map[row][col] = self.selected

    def enemyClick(self, mx, my):
        row = int((my - 300 - self.Yoffset * self.zoom) // self.zoom)
        col = int((mx - 300 - self.Xoffset * self.zoom) // self.zoom)
        if not ((0 <= col <= self.width-1) and (0 <= row <= self.height-1)):
            return

        npc_pos = [v[1] for v in self.npcs]

        def npc_this_los(c, r, np):
            if (p := [c + 0.5, r + 0.5]) in np:
                return self.npcs[np.index(p)]
            return None

        if self.enemy_selected == None:
            if (p := [col + 0.5, row + 0.5]) in npc_pos:
                self.npcs.pop(npc_pos.index(p))
        else:
            v = npc_this_los(col, row, npc_pos)

            if v == None:
                self.npcs.append([self.enemy_selected, [col + 0.5, row + 0.5]])
            elif self.enemy_selected == v[0]:
                self.npcs.remove(v)
            elif not v == None and not v[0] == self.enemy_selected:
                self.npcs.remove(v)
                self.npcs.append([self.enemy_selected, [col + 0.5, row + 0.5]])

    def mouseDrag(self, mx, my):
        row = int((my - 300 - self.Yoffset * self.zoom) // self.zoom)
        col = int((mx - 300 - self.Xoffset * self.zoom) // self.zoom)

        if (0 <= col <= self.width-1) and (0 <= row <= self.height-1):
            if self.map[row][col] != self.selected:
                for r in range(row, row+1):
                    for c in range(col, col+1):
                        if (0 <= c <= self.width-1) and (0 <= r <= self.height-1):
                            self.map[r][c] = self.selected

class ValueSelector:
    def __init__(self, editor):
        self.editor = editor
        self.map = self.editor.map

    def portal(self):
        self.map.change_select("p")

    def wall1(self):
        self.map.change_select(1)
    def wall2(self):
        self.map.change_select(2)
    def wall3(self):
        self.map.change_select(3)
    def wall4(self):
        self.map.change_select(4)
    def wall5(self):
        self.map.change_select(5)

    def floor(self):
        self.map.change_select(0)


    def no_enemy(self):
        self.map.change_Eselect(None)

    def tridemon(self):
        self.map.change_Eselect("tridemon")
    
    def shadowslinger(self):
        self.map.change_Eselect("shadowslinger")

    def gemdemon(self):
        self.map.change_Eselect("gemdemon")

    def satansnovel(self):
        self.map.change_Eselect("satansnovel")

    def zombie(self):
        self.map.change_Eselect("zombie")

    def hut(self):
        self.map.change_Eselect("hut")

    #for ease of work, spawn is an enemy that just has different consideration factors
    def spawn(self):
        self.map.change_Eselect("spawn")


class MainEditor:
    def __init__(self):
        self.mouseX, self.mouseY = pygame.mouse.get_pos()
        self.font = pygame.font.Font(None, 30)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))#, pygame.FULLSCREEN)

        self.map = Map(self)

        self.mouseDown = False

        self.buttons = []

        self.movekeys = {
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False
        }

        self.value_selector = ValueSelector(self)

        self.buttons.append(MenuButton(self, (20, 20), 125, 55, "Add Width", self.map.add_width))
        self.buttons.append(MenuButton(self, (150, 20), 125, 55, "Add Height", self.map.add_height))
        self.buttons.append(MenuButton(self, (280, 20), 125, 55, "Add Walls", self.map.add_walls))

        self.buttons.append(MenuButton(self, (1490, 20), 100, 55, "Random", self.map.load_random))
        self.buttons.append(MenuButton(self, (1490, 80), 100, 55, "Save", self.map.save_game))
        self.buttons.append(MenuButton(self, (1490, 140), 100, 55, "Load", self.map.load_game))
        self.buttons.append(MenuButton(self, (1490, 200), 100, 55, "Reset", self.map.reset_map))
        self.buttons.append(MenuButton(self, (1490, 260), 100, 55, "Out-Clear", self.map.outlier_reset))

        self.buttons.append(MenuButton(self, (500, 20), 50, 50, "P", self.value_selector.portal, colors=[(65, 19, 60), (109, 26, 100)]))
        self.buttons.append(MenuButton(self, (555, 20), 50, 50, "S", self.value_selector.spawn, colors=[(6, 122, 11), (17, 203, 24)]))

        self.buttons.append(MenuButton(self, (610, 20), 50, 50, "W1", self.value_selector.wall1, colors=[(255, 0, 0), (233, 28, 28)]))
        self.buttons.append(MenuButton(self, (665, 20), 50, 50, "W2", self.value_selector.wall2, colors=[(255, 172, 0), (225, 170, 55)]))
        self.buttons.append(MenuButton(self, (720, 20), 50, 50, "W3", self.value_selector.wall3, colors=[(255, 249, 0), (228, 224, 72)]))
        self.buttons.append(MenuButton(self, (775, 20), 50, 50, "W4", self.value_selector.wall4, colors=[(81, 238, 52), (123, 234, 103)]))
        self.buttons.append(MenuButton(self, (830, 20), 50, 50, "W5", self.value_selector.wall5, colors=[(95, 99, 235), (137, 140, 240)]))

        self.buttons.append(MenuButton(self, (885, 20), 50, 50, "N", self.value_selector.floor, colors=[(108, 108, 108), (176, 176, 176)]))

        #                                                                                                           "dark" "light"
        self.buttons.append(MenuButton(self, (20, 820), 60, 60, "N", self.value_selector.no_enemy, colors=[(108, 108, 108), (176, 176, 176)]))
        self.buttons.append(MenuButton(self, (85, 820), 60, 60, "T", self.value_selector.tridemon, colors=[(111, 120, 12), (170, 183, 20)]))
        self.buttons.append(MenuButton(self, (150, 820), 60, 60, "G", self.value_selector.gemdemon, colors=[(142, 23, 23), (248, 11, 11)]))
        self.buttons.append(MenuButton(self, (215, 820), 60, 60, "S", self.value_selector.shadowslinger, colors=[(58, 9, 65), (112, 18, 125)]))
        self.buttons.append(MenuButton(self, (280, 820), 60, 60, "Z", self.value_selector.zombie, colors=[(21, 67, 10), (41, 150, 16)]))
        self.buttons.append(MenuButton(self, (345, 820), 60, 60, "B", self.value_selector.satansnovel, colors=[(65, 34, 10), (106, 55, 15)]))
        self.buttons.append(MenuButton(self, (410, 820), 60, 60, "H", self.value_selector.hut, colors=[(70, 51, 32), (136, 91, 45)]))

    def update(self):
        self.screen.fill('black')

        self.events()
        self.map.update()

        [but.update() for but in self.buttons]

        self.screen.blit(self.font.render("Selected: " + str(self.map.selected), False, (255, 255, 255)), (20, 80))
        self.screen.blit(self.font.render(str(self.map.width) + "x" + str(self.map.height), False, (255, 255, 255)), (20, 105))

        pygame.display.flip()

    def events(self):
        self.mouseX, self.mouseY = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouseDown = True
                    [but.mouseClick() for but in self.buttons]

                    self.map.mouseClick(self.mouseX, self.mouseY)

                elif event.button == 2:
                    self.map.mouseClick(self.mouseX, self.mouseY, retVal = True)

                elif event.button == 3:
                    self.map.enemyClick(self.mouseX, self.mouseY)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouseDown = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                else:
                    self.movekeys[event.key] = True

                    if event.key == pygame.K_e:
                        self.map.zoom += 3
                        self.map.thickness += 1
                    elif event.key == pygame.K_q:
                        self.map.zoom -= 3
                        self.map.thickness -= 1

            elif event.type == pygame.KEYUP:
                self.movekeys[event.key] = False

            elif event.type == pygame.MOUSEMOTION and self.mouseDown:
                self.map.mouseDrag(self.mouseX, self.mouseY)

        if self.movekeys[pygame.K_w]:
            self.map.Yoffset += 0.02
        elif self.movekeys[pygame.K_s]:
            self.map.Yoffset -= 0.02
        elif self.movekeys[pygame.K_a]:
            self.map.Xoffset += 0.02
        elif self.movekeys[pygame.K_d]:
            self.map.Xoffset -= 0.02

    def run(self):
        while True:
            self.update()


main_ = MainEditor()
main_.run()