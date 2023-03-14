import json
import pygame
import sys

WIDTH, HEIGHT = 1600, 900

pygame.init()

class MenuButton:
    def __init__(self, menu, pos, width, height, text, functionToCall):
        self.menu = menu
        self.pos = pos; self.posx, self.posy = pos
        self.width = width
        self.height = height
        self.text = text
        self.functionToCall = functionToCall
        self.surf = pygame.Surface((self.width, self.height))

        self.button_txt = self.menu.font.render(self.text, False, 'black')

        self.current_color = (200, 200, 200)

        self.mouse_over = False

        self.draw_button()

    def draw_button(self):
        self.surf.fill('black')
        pygame.draw.rect(self.surf, self.current_color, (0, 0, self.width, self.height), border_radius=5)

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

        self.lvlDict = {}

    def add_width(self):
        self.width += 1

        for y in range(self.height):
            self.map[y].append(0)

    def add_height(self):
        self.height += 1

        self.map.append([0] * self.width)

    def save_game(self):
        self.lvlDict["map"] = self.map

        with open('result.json', 'w') as fp:
            json.dump(self.lvlDict, fp)

        print("Map saved")

    def load_game(self):
        with open('result.json') as json_file:
            data = json.load(json_file)
        json_file.close()

        self.map = data["map"]

        self.Xoffset = 0; self.Yoffset = 0

        self.width = len(self.map[0])
        self.height = len(self.map)

    def update(self):
        self.draw_map()

    def draw_map(self):
        map_draw = {}

        for j, row in enumerate(self.map):
            for i, value in enumerate(row):
                map_draw[(i, j)] = value

        [pygame.draw.rect(self.editor.screen, ('darkgray' if map_draw[pos] == 0 else 'yellow'), (pos[0] * 20 + self.Xoffset * 20 + 300, pos[1] * 20 + self.Yoffset * 20 + 300, 20, 20), 2) for pos in map_draw]

    def mouseClick(self, mx, my):
        row = (my - 300 - self.Yoffset * 20) // 20
        col = (mx - 300 - self.Xoffset * 20) // 20

        if (0 <= col <= self.width-1) and (0 <= row <= self.height-1):
            if self.map[row][col] == 0:
                self.map[row][col] = 1
            else:
                self.map[row][col] = 0

class ButtonFunctions:
    def __init__(self, editor):
        self.editor = editor

class MainEditor:
    def __init__(self):
        self.mouseX, self.mouseY = pygame.mouse.get_pos()
        self.font = pygame.font.Font(None, 30)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.buttonFuncs = ButtonFunctions(self)
        self.map = Map(self)

        self.buttons = []

        self.movekeys = {
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False
        }

        self.buttons.append(MenuButton(self, (20, 20), 125, 55, "Add Width", self.map.add_width))
        self.buttons.append(MenuButton(self, (150, 20), 125, 55, "Add Height", self.map.add_height))
        self.buttons.append(MenuButton(self, (1495, 20), 100, 55, "Save", self.map.save_game))
        self.buttons.append(MenuButton(self, (1495, 80), 100, 55, "Load", self.map.load_game))

    def update(self):
        self.screen.fill('black')

        self.events()
        self.map.update()

        [but.update() for but in self.buttons]

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

            elif event.type == pygame.KEYUP:
                self.movekeys[event.key] = False

        if self.movekeys[pygame.K_w]:
            self.map.Yoffset += 0.01
        elif self.movekeys[pygame.K_s]:
            self.map.Yoffset -= 0.01
        elif self.movekeys[pygame.K_a]:
            self.map.Xoffset += 0.01
        elif self.movekeys[pygame.K_d]:
            self.map.Xoffset -= 0.01

    def run(self):
        while True:
            self.update()


main_ = MainEditor()
main_.run()