import pygame as pg
import sys, psutil
from os import path, getpid
from settings import *
from engine import *
from map import *
from exceptions import *

class Game:
    def __init__(self):
        pg.init()
        self.__screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.toggle_fullscreen()
        self.__font_name = pg.font.match_font('arial')
        self.__clock = pg.time.Clock()
        pg.display.set_caption(TITLE)
        pg.key.set_repeat(500, 100)
        self.load_data()
    def load_data(self):
        self.handler = Utils()
        self.dir = path.dirname(__file__)
        self.img_dir = path.join(self.dir, 'img')
        self.player_img = 'player.png'
        self.plat_img = 'grass_block.png'
        self.dirt_img = 'dirt_block.png'
        self.mob_img = 'mob.png'
        self.map = Map(path.join(self.dir, 'map.txt'))
    def new(self):
        self.all_sprites = pg.sprite.Group()
        self._blocks = pg.sprite.Group()
        self._bullets = pg.sprite.Group()
        self._mobs = pg.sprite.Group()
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    b = Block(self, self.plat_img, col, row)
                    self.all_sprites.add(b)
                    self._blocks.add(b)
                if tile == '0':
                    b = Block(self, self.dirt_img, col, row)
                    self.all_sprites.add(b)
                    self._blocks.add(b)
                if tile == 'P':
                    self.player = Player(self, self.player_img, col, row)
                if tile == 'M':
                    m = Mob(self, self.mob_img, col, row)
                    self.all_sprites.add(m)
                    self._mobs.add(m)
        self.all_sprites.add(self.player)
        self.camera = Camera(WIDTH + 200, HEIGHT + 200)
    def run(self):
        self.__playing = True
        while self.__playing:
            self.dt = self.__clock.tick(FPS) / 1000 # час одного тіку в секундах
            self.events()
            self.update()
            self.draw()
    @property
    def blocks(self):
        return self._blocks
    @property
    def bullets(self):
        return self._bullets
    @property
    def mobs(self):
        return self._mobs
    def quit(self):
        pg.quit()
        sys.exit()
    def update(self):
        self.all_sprites.update()
        self.camera.update(self.player)
    def draw(self):
        self.__screen.fill(BGCOLOR)
        for sprite in self.all_sprites:
            self.__screen.blit(sprite.image, self.camera.apply(sprite))
            #pg.draw.rect(self.__screen, pg.Color('white'), self.camera.apply(sprite), 3)
        self.draw_text(f'x: {round(self.player.pos.x, 2)}', 22, WHITE, 80, 40)
        self.draw_text(f'y: {round(self.player.pos.y, 2)}', 22, WHITE, 80, 80)
        self.draw_text(f'vel: {self.player.vel}', 22, WHITE, 80, 120)
        #self.draw_text(f'facing: {self.player.facing}', 22, WHITE, 80, 160)
        #self.draw_text(f'acc: {self.player.acc}', 22, WHITE, 80, 160)
        pg.display.flip()
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
    def draw_text(self, text, size, color, x, y):
        font = pg.font.Font(self.__font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.__screen.blit(text_surface, text_rect)
    def show_start_screen(self):
        pass
    def show_go_screen(self):
        pass

if __name__ == "__main__":
    svmem = psutil.virtual_memory()
    # якщо оперативної пам'яті менше, ніж 128мб
    try:
        ram = svmem.available
        if 128000000 > ram:
            raise DoesNotMeetRequirements('Not enough RAM!', ram)
    except DoesNotMeetRequirements as e:
        print(f'Error! {e.msg}\nYou have only {e.available} bytes available!')
        sys.exit()
    g = Game()
    g.show_start_screen()
    while True:
        g.new()
        g.run()
        g.show_go_screen()
