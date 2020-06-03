import pygame as pg
from os import path
from settings import *
from abc import ABC, abstractmethod
from random import choice
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

class UtilsMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls._instance = None
    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__()
        return cls._instance

class Utils(metaclass=UtilsMeta):
	def load_image(self, filename):
		image = pg.image.load(filename).convert_alpha()
		image.set_colorkey((0, 0, 0))
		return image
	def load_animation(self, baseFilename, count):
		animation = []
		for i in range(1, count + 1):
			animation.append(
				self.load_image(f'{baseFilename}{i}.png')
				)
		return animation
	def flip_animation(self, animation):
		for i in range(0, len(animation)):
			animation[i] = pg.transform.flip(animation[i], True, False)
		return animation

class Physics_Object(pg.sprite.Sprite):
	def __init__(self, game, image, x, y):
		pg.sprite.Sprite.__init__(self)
		self.game = game
		self.handler = Utils()
		self.image = self.handler.load_image(path.join(self.game.img_dir, image))
		self.rect = self.image.get_rect()
		self.rect.midbottom = (x * TILESIZE, y * TILESIZE)
		self.pos = vec(x * TILESIZE, y * TILESIZE)

class Block(Physics_Object):
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)

class MusicBlock(Block, pg.mixer.Sound):
	def __init__(self, game, image, x, y, filename):
		Block.__init__(self, game, image, x, y)
		pg.mixer.Sound.__init__(self, filename)
		self.filename = filename
		self.duration = 500
		self.fadeout = 100
	def update(self):
		hits = pg.sprite.spritecollide(self, self.game.player, False)
		if hits:
			self.play(max_time=self.duration, fade_ms=self.fadeout)

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

class Player(ActiveEntity, IUpdate, IFire):
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)
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
	def load_images(self):
		try:
			self.idle_frames_r = self.handler.load_animation(path.join(self.game.img_dir, 'player_idle'), 2)
			self.idle_frames_l = self.handler.flip_animation(self.idle_frames_r.copy())
			self.run_frames_r = self.handler.load_animation(path.join(self.game.img_dir,'player_run'), 8)
			self.run_frames_l = self.handler.flip_animation(self.run_frames_r.copy())
			self.jump_frame_r = self.handler.load_image(path.join(self.game.img_dir,'player_jump.png'))
			self.jump_frame_l = pg.transform.flip(self.jump_frame_r.copy(), True, False)
			self.pistol_run_r = self.handler.load_animation(path.join(self.game.img_dir, 'player_run_pistol'), 8)
			self.pistol_run_l = self.handler.flip_animation(self.pistol_run_r.copy())
			self.pistol_idle_r = self.handler.load_animation(path.join(self.game.img_dir, 'player_idle_pistol'), 2)
			self.pistol_idle_l = self.handler.flip_animation(self.pistol_idle_r.copy())
			self.pistol_jump_r = self.handler.load_image(path.join(self.game.img_dir, 'player_jump_pistol.png'))
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
		self.weapon = Pistol(self.game, self)
	def fire(self):
		now = pg.time.get_ticks()
		if now - self.last_shot > self.weapon.rate:
			self.last_shot = now
			bullet = Bullet(self.pos.x, self.pos.y, self.weapon.damage, self.weapon.bullet_speed, self.facing, self.game)
	def reload(self):
		pass

class Mob(ActiveEntity):
	def __init__(self, game, image, x, y):
		super().__init__(game, image, x, y)
		self.hp = 100
		self.vision_radius = 256
		self.wandering = False
		self.chasing = False
		self.last_update = pg.time.get_ticks()
	def update(self):
		now = pg.time.get_ticks()
		dist, direction = self.getDistToPlayer()
		if self.chasing:
			if dist <= self.vision_radius:
				self.facing = direction
				self.chase()
			else:
				self.chasing = False
				self.last_update = now
		elif dist <= self.vision_radius:
			self.facing = direction
			self.chasing = True
			self.chase()
		elif self.wandering:
			if now - self.last_update < 2000:
				self.wander()
			else:
				self.wandering = False
				self.last_update = now
		elif now - self.last_update > 5000:
			self.last_update = now
			self.wandering = True
			self.facing = choice([1, -1])
			self.wander()
	def getDistToPlayer(self):
		vect = self.pos - self.game.player.pos
		dist = round((vect.x ** 2 + vect.y ** 2) ** 0.5)
		direction = -1
		if vect.x < 0:
			direction = 1
		return dist, direction
	def wander(self):
		self.move(150 * self.facing)
	def chase(self):
		self.move(150 * self.facing)

class Weapon(pg.sprite.Sprite):
	def __init__(self, game, entity):
		pg.sprite.Sprite.__init__(self)
		self.game = game
		self.entity = entity

class Pistol(Weapon):
	def __init__(self, game, entity):
		super().__init__(game, entity)
		self.name = 'Pistol'
		self.ammo = 12
		self.damage = 30
		self.bullet_speed = 10
		self.rate = 500
		
class Bullet(pg.sprite.Sprite):
	def __init__(self, posx, posy, damage, speed, facing, game):
		self.game = game
		self.handler = Utils()
		self.groups = self.game.all_sprites, self.game.bullets
		pg.sprite.Sprite.__init__(self, self.groups)
		self.image = self.handler.load_image(path.join(self.game.img_dir,'bullet.png'))
		self.rect = self.image.get_rect()
		self.rect.x = posx + facing * 24
		self.rect.y = posy - 54
		self.damage = damage
		self.speed = speed
		self.facing = facing
	def update(self):
		self.rect.x += self.speed * self.facing
		if self.rect.x > self.game.map.width or self.rect.x < 0:
			self.kill()
		hits = pg.sprite.spritecollide(self, self.game.mobs, False)
		if hits:
			self.kill()
			enemy = hits[0]
			enemy.hp -= self.damage
			if enemy.hp <= 0:
				enemy.kill()