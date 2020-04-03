import pygame as pg
import sys
from os import path
from settings import *
from engine import *

class Game:
    def __init__(self):
        pg.init()
        self.__screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.__font_name = pg.font.match_font('arial')
        self.__clock = pg.time.Clock()
        pg.display.set_caption(TITLE)
        pg.key.set_repeat(500, 100)
        self.load_data()
    def load_data(self):
    	self.dir = path.dirname(__file__)
    	self.img_dir = path.join(self.dir, 'img')
    	self.player_img = 'totoro.png'
    	self.plat_img = 'block.png'
    def new(self):
        self.all_sprites = pg.sprite.Group()
        self.blocks = pg.sprite.Group()
        self.player = Player(self, self.player_img, WIDTH / 2, HEIGHT / 2)
        for i in [WIDTH / 2 - 3*64, WIDTH / 2 - 2*64, WIDTH / 2 - 64, WIDTH / 2, WIDTH / 2 + 64, WIDTH / 2 + 2*64, WIDTH / 2 + 3*64]:
            p = Block(self, self.plat_img, i, 700)
            self.all_sprites.add(p)
            self.blocks.add(p)
        self.all_sprites.add(self.player)
        self.camera = Camera(WIDTH + 200, HEIGHT + 200)
    def run(self):
        self.__playing = True
        while self.__playing:
            self.dt = self.__clock.tick(FPS) / 1000 # час одного тіку в секундах
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # updates
        self.all_sprites.update()
        self.camera.update(self.player)
    def draw(self):
    	self.__screen.fill(BGCOLOR)
    	for sprite in self.all_sprites:
    		self.__screen.blit(sprite.image, self.camera.apply(sprite))
    	self.draw_text(f'x: {round(self.player.pos.x, 2)}', 22, WHITE, 80, 40)
    	self.draw_text(f'y: {round(self.player.pos.y, 2)}', 22, WHITE, 80, 80)
    	self.draw_text(f'vel: {self.player.vel}', 22, WHITE, 80, 120)
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
	g = Game()
	g.show_start_screen()
	while True:
		g.new()
		g.run()
		g.show_go_screen()
