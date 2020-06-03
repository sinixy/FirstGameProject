import pygame as pg
import sys, psutil
from os import path, getpid
from settings import *
from engine import *
from map import *
from exceptions import *

class Game:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Game, cls).__new__(cls)
        return cls.instance
    def __init__(self):
        pg.init()
        self.__screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.toggle_fullscreen()
        self.__font_name = pg.font.match_font('arial')
        self.__clock = pg.time.Clock()
        self.dt = 1
        pg.display.set_caption(TITLE)
        pg.key.set_repeat(500, 100)
        self.load_data()
    def load_data(self):
        self.dir = path.dirname(__file__)
        self.img_dir = path.join(self.dir, 'img')
        self.player_img = 'player.png'
        self.plat_img = 'block.png'
        self.map = Map(path.join(self.dir, 'map.txt'))
    def new(self):
        self.all_sprites = pg.sprite.Group()
        self._blocks = pg.sprite.Group()
        self._bullets = pg.sprite.Group()
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    b = Block(self.plat_img, col, row)
                    self.all_sprites.add(b)
                    self.blocks.add(b)
                if tile == 'P':
                    self.player = Player(self.player_img, col, row)
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
    print("Object g created", g)
    '''
    Singleton pattern test
    print("Object g created", g)
    w = Game()
    print("Object w created", w)
    '''
    g.show_start_screen()
    while True:
        g.new()
        g.run()
        g.show_go_screen()














import pygame as pg
from os import path
from settings import *
from game import Game
from abc import ABC, abstractmethod
vec = pg.math.Vector2

class IUpdate(ABC):
	@abstractmethod
	def update(self):
		pass
	@abstractmethod
	def animate(self):
		pass

class IFire(ABC):
	@abstractmethod
	def fire(self):
		pass
	@abstractmethod
	def reload(self):
		pass

def load_image(filename):
	image = pg.image.load(filename).convert_alpha()
	image.set_colorkey((0, 0, 0))
	return image
def load_animation(baseFilename, count):
	animation = []
	for i in range(1, count + 1):
		animation.append(
			load_image(f'{baseFilename}{i}.png')
			)
	return animation
def flip_animation(animation):
	for i in range(0, len(animation)):
		animation[i] = pg.transform.flip(animation[i], True, False)
	return animation

class Physics_Object(pg.sprite.Sprite):
	def __init__(self, image, x, y):
		pg.sprite.Sprite.__init__(self)
		self.game = Game()
		print("Object g created", self.game)
		self.image = load_image(path.join(self.game.img_dir, image))
		self.rect = self.image.get_rect()
		self.rect.midbottom = (x * TILESIZE, y * TILESIZE)
		self.pos = vec(x * TILESIZE, y * TILESIZE)

class Block(Physics_Object):
	def __init__(self, image, x, y):
		super().__init__(image, x, y)

class MusicBlock(Block, pg.mixer.Sound):
	def __init__(self, image, x, y, filename):
		Block.__init__(self, image, x, y)
		pg.mixer.Sound.__init__(self, filename)
		self.filename = filename
		self.duration = 500
		self.fadeout = 100
	def update(self):
		hits = pg.sprite.spritecollide(self, self.game.player, False)
		if hits:
			self.play(max_time=self.duration, fade_ms=self.fadeout)

class Entity(Physics_Object):
	def __init__(self, image, x, y):
		super().__init__(image, x, y)
		self._gravity = 600
	def onBlock(self):
		self.rect.y += 1
		hits = pg.sprite.spritecollide(self, self.game.blocks, False)
		self.rect.y -= 1
		if hits:
			lowest = hits[0]
			for hit in hits:
				if hit.rect.bottom > lowest.rect.bottom:
					lowest = hit
			return lowest
		return False
	@property
	def gravity(self):
		return self._gravity
	@gravity.setter
	def gravity(self, gravity):
		if gravity < -1000:
			self._gravity = -1000
		elif gravity > 1000:
			self._gravity = 1000
		else:
			self._gravity = gravity
	

class ActiveEntity(Entity):
	def __init__(self, image, x, y):
		super().__init__(image, x, y)
		self.vel = vec(0, 0)
		self.acc = vec(0, 0)
		self.jumping = False
		self.running = False
		self.facing = 1 # 1 Right; -1 Left
	def move(self, maxVel):
		acc_x = maxVel / (self.game.dt * 9) # На 10-м фреймі швидкість буде максимальна
		self.acc = vec(acc_x, self.gravity)
		v0 = self.vel
		self.vel += self.acc * self.game.dt

		block = self.onBlock()
		if block and not self.jumping:
			self.pos.y = block.rect.top + 1
			self.vel.y = 0

		if abs(self.vel.x) > abs(maxVel):
			self.vel.x = maxVel
		if abs(self.vel.x) < 10:
			self.vel.x = 0

		if self.vel.x:
			self.pos.x += (v0.x + self.vel.x) * self.game.dt * 0.5
		if self.vel.y:
			self.pos.y += 0.5 * self.gravity * self.game.dt ** 2 + self.vel.y * self.game.dt

		self.rect.midbottom = self.pos
	def jump(self):
		if self.onBlock() and not self.jumping:
		    self.jumping = True
		    self.vel.y = -400
	@property
	def status(self):
		return '''Cords: {}
Velocity: {}
Jumping: {}'''.format(self.pos, self.vel, self.jumping)

class Player(ActiveEntity, IUpdate, IFire):
	def __init__(self, image, x, y):
		super().__init__(image, x, y)
		self.holding_weapon = {
								'pistol': False,
								'rifle': False,
								'minigun': False
							   }
		self.weapon = None
		self.currentFrame = 0
		self.last_update = 0
		self.last_shot = 0
		self.idle = True
		self.load_images()
		self.pickup_weapon()
		print('Player', self.rect)
	def load_images(self):
		try:
			self.idle_frames_r = load_animation(path.join(self.game.img_dir, 'player_idle'), 2)
			self.idle_frames_l = flip_animation(self.idle_frames_r.copy())
			self.run_frames_r = load_animation(path.join(self.game.img_dir,'player_run'), 8)
			self.run_frames_l = flip_animation(self.run_frames_r.copy())
			self.jump_frame_r = load_image(path.join(self.game.img_dir,'player_jump.png'))
			self.jump_frame_l = pg.transform.flip(self.jump_frame_r.copy(), True, False)
			self.pistol_run_r = load_animation(path.join(self.game.img_dir, 'player_run_pistol'), 8)
			self.pistol_run_l = flip_animation(self.pistol_run_r.copy())
			self.pistol_idle_r = load_animation(path.join(self.game.img_dir, 'player_idle_pistol'), 2)
			self.pistol_idle_l = flip_animation(self.pistol_idle_r.copy())
			self.pistol_jump_r = load_image(path.join(self.game.img_dir, 'player_jump_pistol.png'))
			self.pistol_jump_l = pg.transform.flip(self.pistol_jump_r.copy(), True, False)
		except Exception as e:
			print(f'Error occured!\n{e}')
			self.game.quit()
	def update(self):
		if self.jumping:
			if self.onBlock():
				self.jumping = False
		force = 0
		keystate = pg.key.get_pressed()
		if keystate[pg.K_a]:
			if self.facing == 1:
				self.facing = -1
			force = -200
		if keystate[pg.K_d]:
			if self.facing == -1:
				self.facing = 1
			force = 200
		if keystate[pg.K_w]:
			self.jump()
			#print(self.status)
		if keystate[pg.K_RETURN]:
			if self.weapon:
				self.fire()
		self.move(force)
		self.animate()
	def animate(self):
		now = pg.time.get_ticks()
		if self.vel.y != 0:
			self.jumping = True
		if self.vel.x != 0 and not self.jumping:
			self.running = True
		else:
			self.running = False

		if self.running:
			if now - self.last_update > 100:
				self.last_update = now
				self.currentFrame = (self.currentFrame + 1) % 8
				self.idle = False
				if self.facing == 1:
					frame = self.run_frames_r[self.currentFrame]
					if self.weapon:
						frame = self.pistol_run_r[self.currentFrame]
					self.image = frame
				else:
					frame = self.run_frames_l[self.currentFrame]
					if self.weapon:
						frame = self.pistol_run_l[self.currentFrame]
					self.image = frame

		if self.jumping:
			self.idle = False
			if self.facing == 1:
				frame = self.jump_frame_r
				if self.weapon:
					frame = self.pistol_jump_r
				self.image = frame
			else:
				frame = self.jump_frame_l
				if self.weapon:
					frame = self.pistol_jump_l
				self.image = frame

		if not self.jumping and not self.running:
			if not self.idle:
				self.last_update = now
				self.currentFrame = (self.currentFrame + 1) % len(self.idle_frames_r)
				if self.facing == 1:
					frame = self.idle_frames_r[self.currentFrame]
					if self.weapon:
						frame = self.pistol_idle_r[self.currentFrame]
					self.image = frame
				else:
					frame = self.idle_frames_l[self.currentFrame]
					if self.weapon:
						frame = self.pistol_idle_l[self.currentFrame]
					self.image = frame
				self.idle = True
			if now - self.last_update > 400:
				self.last_update = now
				self.currentFrame = (self.currentFrame + 1) % len(self.idle_frames_r)
				if self.facing == 1:
					frame = self.idle_frames_r[self.currentFrame]
					if self.weapon:
						frame = self.pistol_idle_r[self.currentFrame]
					self.image = frame
				else:
					frame = self.idle_frames_l[self.currentFrame]
					if self.weapon:
						frame = self.pistol_idle_l[self.currentFrame]
					self.image = frame
		midbottom = self.rect.midbottom
		self.rect = self.image.get_rect()
		self.rect.midbottom = midbottom
	def pickup_weapon(self):
		self.holding_weapon['pistol'] = True
		self.weapon = Pistol(self)
		# self.image = load_image(path.join(self.game.img_dir, 'player_pistol.png'))
	def fire(self):
		now = pg.time.get_ticks()
		if now - self.last_shot > self.weapon.rate:
			self.last_shot = now
			bullet = Bullet(self.pos.x, self.pos.y, self.weapon.damage, self.weapon.bullet_speed, self.facing, self.game)
	def reload(self):
		pass

class Weapon(pg.sprite.Sprite):
	def __init__(self, entity):
		pg.sprite.Sprite.__init__(self)
		self.game = Game()
		self.entity = entity

class Pistol(Weapon):
	def __init__(self, entity):
		super().__init__(entity)
		self.name = 'Pistol'
		self.ammo = 12
		self.damage = 30
		self.bullet_speed = 5
		self.rate = 500
		
class Bullet(pg.sprite.Sprite):
	def __init__(self, posx, posy, damage, speed, facing):
		self.game = Game()
		self.groups = self.game.all_sprites, self.game.bullets
		pg.sprite.Sprite.__init__(self, self.groups)
		self.image = load_image(path.join(self.game.img_dir,'bullet.png'))
		self.rect = self.image.get_rect()
		self.rect.x = posx + facing * 24
		self.rect.y = posy - 54
		self.damage = damage
		self.speed = speed
		self.facing = facing
		self.last_update = pg.time.get_ticks()
	def update(self):
		self.rect.x += self.speed * self.facing
		if self.rect.x > WIDTH:
			self.kill()
		if self.rect.x < 0:
			self.kill()

