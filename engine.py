import pygame as pg
from os import path
from settings import *
vec = pg.math.Vector2

def load_image(filename):
	image = pg.image.load(filename).convert()
	image.set_colorkey((0, 0, 0))
	return image

class Physics_Object(pg.sprite.Sprite):
	def __init__(self, game, image, x, y):
		pg.sprite.Sprite.__init__(self)
		self.game = game
		self.image = load_image(path.join(self.game.img_dir, image))
		self.rect = self.image.get_rect()
		self.rect.midbottom = (x, y)
		self.pos = vec(x, y)

class Block(Physics_Object):
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)

class Entity(Physics_Object):
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)
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
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)
		self.vel = vec(0, 0)
		self.acc = vec(0, 0)
		self.jumping = False
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
		if abs(self.vel.x) < 0.1:
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

class Player(ActiveEntity):
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)
	def update(self):
		if self.jumping:
			if self.onBlock():
				self.jumping = False
		force = 0
		keystate = pg.key.get_pressed()
		if keystate[pg.K_a]:
			force = -200
		if keystate[pg.K_d]:
			force = 200
		if keystate[pg.K_w]:
			self.jump()
			#print(self.status)
		self.move(force)	

class Camera:
	"""
	Камера, що працює по принципу оффсетів.
	Оффсет задає target в методі updatе. В нашому випадку,
	це Player
	"""
	def __init__(self, width, height):
		self.camera = pg.Rect(0, 0, width, height)
		self.width = width
		self.height = height
	def apply(self, entity):
		return entity.rect.move(self.camera.topleft)
	def update(self, target):
		x = -target.rect.x + int(WIDTH / 2)
		y = -target.rect.y + int(HEIGHT / 2)
		self.camera = pg.Rect(x, y, self.width, self.height)