import json
import pygame
import sys
from projectgame3 import MazeGenerator

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

        self.width = 1
        self.height = 1

        self.Xoffset = 0
        self.Yoffset = 0

        self.zoom = 20
        self.thickness = 2

        self.lvlDict = {}

        self.selected = 1

        self.maze_generator = MazeGenerator()

    def change_select(self, val):
        self.selected = val

    def add_width(self):
        self.width += 1

        for y, r in enumerate(self.map):
            self.map[y].append(0)

    def add_height(self):
        self.height += 1

        self.map.append([0] * self.width)

    def save_game(self):
        self.lvlDict["map"] = self.map

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

    def load_game(self):
        with open('result.json') as json_file:
            data = json.load(json_file)
        json_file.close()

        self.map = data["map"]

        self.Xoffset = 0; self.Yoffset = 0

        self.width = len(self.map[0])
        self.height = len(self.map)

    def reset_map(self):
        self.map = [[1]]
        self.width = 1
        self.height = 1

    def update(self):
        self.draw_map()

    def draw_map(self):
        def pos_color(val):
            if val == 0:
                return 'darkgray'
            elif val == 1:
                return 'yellow'
            elif val == "p":
                return 'purple'

        map_draw = {}

        for j, row in enumerate(self.map):
            for i, value in enumerate(row):
                map_draw[(i, j)] = value

        [pygame.draw.rect(self.editor.screen, pos_color(map_draw[pos]), (pos[0] * self.zoom + self.Xoffset * self.zoom + 300, pos[1] * self.zoom + self.Yoffset * self.zoom + 300, self.zoom, self.zoom), self.thickness) for pos in map_draw]

    def mouseClick(self, mx, my):
        row = int((my - 300 - self.Yoffset * self.zoom) // self.zoom)
        col = int((mx - 300 - self.Xoffset * self.zoom) // self.zoom)

        if (0 <= col <= self.width-1) and (0 <= row <= self.height-1):
            if self.map[row][col] == self.selected:
                self.map[row][col] = 0
            else:
                self.map[row][col] = self.selected

class ValueSelector:
    def __init__(self, editor):
        self.editor = editor
        self.map = self.editor.map

    def portal(self):
        self.map.change_select("p")

    def wall(self):
        self.map.change_select(1)

class MainEditor:
    def __init__(self):
        self.mouseX, self.mouseY = pygame.mouse.get_pos()
        self.font = pygame.font.Font(None, 30)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.map = Map(self)

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

        self.buttons.append(MenuButton(self, (500, 20), 50, 50, "P", self.value_selector.portal, colors=[(65, 19, 60), (109, 26, 100)]))
        self.buttons.append(MenuButton(self, (555, 20), 50, 50, "W", self.value_selector.wall, colors=[(194, 186, 16), (226, 216, 11)]))

    def update(self):
        self.screen.fill('black')

        self.events()
        self.map.update()

        [but.update() for but in self.buttons]

        self.screen.blit(self.font.render("Selected: " + str(self.map.selected), False, (255, 255, 255)), (20, 80))

        pygame.display.flip()

    def events(self):
        self.mouseX, self.mouseY = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                [but.mouseClick() for but in self.buttons]

                self.map.mouseClick(self.mouseX, self.mouseY)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                else:
                    self.movekeys[event.key] = True

                    if event.key == pygame.K_e:
                        self.map.zoom += 3
                    elif event.key == pygame.K_q:
                        self.map.zoom -= 3

            elif event.type == pygame.KEYUP:
                self.movekeys[event.key] = False

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