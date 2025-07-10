import pgzrun
from pygame import Rect
from pgzero.actor import Actor
from pgzero.keyboard import keyboard

WIDTH, HEIGHT, WORLD_WIDTH = 800, 600, 2400
backgrounds, background_width = ["background1", "background2", "background3"], 800
menu_active, game_active, music_on, camera_x, vidas, game_over, victory, current_music = True, False, True, 0, 3, False, False, None
menu_bg, kill_count, star_count, instrucoes_timer = "cacador_de_estrelas", 0, 0, 0
star_x, star_y = 2227, 529

start_button, exit_button, sound_button = Rect(172,255,233,98), Rect(172,377,233,96), Rect(43,493,73,79)
retry_button_game_over, menu_button_game_over = Rect(86,277,631,95), Rect(86,363,631,95)
retry_button_victory, menu_button_victory = Rect(78,333,303,74), Rect(78,441,303,74)
platforms = [Rect((0,467,408,80)), Rect((408,547,392,10)), Rect((800,547,391,10)),
             Rect((1191,467,409,80)), Rect((1600,467,410,80)), Rect((2010,547,390,10))]

class Hero:
    def __init__(self):
        self.x, self.y, self.vx, self.vy, self.speed, self.jump_force, self.gravity = 100, 467, 0, 0, 3, -10, 0.5
        self.on_ground, self.direction, self.state, self.frame, self.frame_delay, self.frame_count = False, "right", "idle", 0, 5, 0
        self.jumping_sound_played, self.shooting, self.shoot_timer, self.shoot_duration = False, False, 0, 10
        self.actor = Actor("hero_idle_0", (self.x, self.y - 30))
    def update(self):
        self.vx = (keyboard.right - keyboard.left) * self.speed
        self.direction = "right" if self.vx > 0 else "left" if self.vx < 0 else self.direction
        self.state = "run" if self.vx else "idle"
        if keyboard.space and self.on_ground:
            self.vy, self.on_ground = self.jump_force, False
            if music_on and not self.jumping_sound_played:
                sounds.jump.play()
                self.jumping_sound_played = True
        elif not keyboard.space: self.jumping_sound_played = False
        self.x += self.vx; self.vy += self.gravity; old_y, self.y = self.y, self.y + self.vy
        self.on_ground = False
        hero_rect = Rect((self.x-20, self.y-60, 40, 60))
        for plat in platforms:
            prev_rect = Rect((self.x-20, old_y-60, 40, 60))
            if hero_rect.colliderect(plat):
                if self.vy > 0 and prev_rect.bottom <= plat.top:
                    self.y, self.vy, self.on_ground = plat.top, 0, True
                else:
                    self.x = plat.left-20 if self.vx>0 else plat.right+20 if self.vx<0 else self.x
                hero_rect = Rect((self.x-20, self.y-60, 40, 60))
        self.frame_count = (self.frame_count+1)%self.frame_delay
        if self.frame_count==0: self.frame = (self.frame+1)%3
        if self.shooting:
            self.shoot_timer -= 1
            if self.shoot_timer <= 0: self.shooting = False
    def draw_at(self, camera_x):
        state = "shoot" if self.shooting else self.state
        img = f"hero_{state}{'_left' if self.direction=='left' else ''}_{self.frame}"
        self.actor.image, self.actor.pos = img, (self.x-camera_x, self.y-30)
        self.actor.draw()

class Enemy:
    def __init__(self, x, y, patrol_width):
        self.shooting, self.shoot_timer, self.x, self.y, self.vx = False, 0, x, y, 2
        self.patrol_start, self.patrol_end = x, x+patrol_width
        self.direction, self.frame, self.frame_count, self.frame_delay = "right", 0, 0, 10
        self.actor = Actor("alien_move_0", (self.x, self.y-30))
    def update(self):
        self.x += self.vx
        if self.x < self.patrol_start or self.x > self.patrol_end:
            self.x = max(self.patrol_start, min(self.x, self.patrol_end))
            self.vx *= -1
            self.direction = "right" if self.vx > 0 else "left"
        self.frame_count = (self.frame_count+1)%self.frame_delay
        if self.frame_count==0: self.frame = (self.frame+1)%3
    def draw_at(self, camera_x):
        img = f"alien_move{'_left' if self.direction=='left' else ''}_{self.frame}"
        self.actor.image, self.actor.pos = img, (self.x-camera_x, self.y)
        self.actor.draw()

class Bullet:
    def __init__(self, x, y, direction):
        self.x, self.y, self.speed, self.direction, self.active = x, y, 10, direction, True
    def update(self):
        self.x += self.speed if self.direction=="right" else -self.speed
        if self.x<0 or self.x>WORLD_WIDTH: self.active = False
    def draw_at(self, camera_x):
        screen.draw.filled_circle((self.x-camera_x, self.y), 5, "yellow")

def make_enemies():
    altura_alien = 64
    meia_altura = altura_alien//2
    return [
        Enemy(550, platforms[1].top-meia_altura-5, 100),
        Enemy(900, platforms[1].top-meia_altura-5, 150),
        Enemy(1300, platforms[3].top-meia_altura-5, 100),
        Enemy(1900, platforms[4].top-meia_altura-5, 120),
    ]

hero = Hero()
bullets = []
enemies = make_enemies()

def reset_game():
    global kill_count, star_count, victory, camera_x, enemies
    hero.x, hero.y, hero.vx, hero.vy, hero.on_ground, hero.direction = 100, 467, 0, 0, False, "right"
    bullets.clear(); camera_x = 0
    enemies = make_enemies()
    kill_count = star_count = 0; victory = False

def draw():
    screen.clear()
    if game_over: screen.blit("game_over_screen", (0,0))
    elif victory:
        screen.blit("victory_screen", (0,0))
        screen.draw.text(f"Aliens mortos: {kill_count}", (31,552), fontsize=40, color="white")
        screen.draw.text(f"Estrelas coletadas: {star_count}", (381,552), fontsize=40, color="white")
    elif menu_active: screen.blit(menu_bg, (0,0))
    elif game_active: draw_game()

def draw_game():
    for i, bg in enumerate(backgrounds):
        screen.blit(bg, (i*background_width-camera_x, 0))
    screen.blit("star", (star_x-20-camera_x, star_y-40))
    for i in range(3):
        img = "heart_full" if i<vidas else "heart_empty"
        screen.blit(img, (10+i*40, 10))
    hero.draw_at(camera_x)
    for e in enemies: e.draw_at(camera_x)
    for b in bullets: b.draw_at(camera_x)
    if instrucoes_timer>0:
        for i, texto in enumerate(["Use as setas <- -> para andar", "Espace para pular", "Z para atirar"]):
            screen.draw.text(texto, topright=(WIDTH-10, 10+i*25), fontsize=24, color="white")

def on_mouse_down(pos):
    global menu_active, game_active, music_on, game_over, victory, vidas, kill_count, star_count, instrucoes_timer
    if menu_active:
        if start_button.collidepoint(pos):
            instrucoes_timer = 180
            menu_active, game_active, game_over, vidas = False, True, False, 3
        elif sound_button.collidepoint(pos): music_on = not music_on
        elif exit_button.collidepoint(pos): exit()
    elif game_over and retry_button_game_over.collidepoint(pos) or victory and retry_button_victory.collidepoint(pos):
        game_active, game_over, victory, vidas, kill_count, star_count = True, False, False, 3, 0, 0
        reset_game()
    elif game_over and menu_button_game_over.collidepoint(pos) or victory and menu_button_victory.collidepoint(pos):
        menu_active, game_over, victory, game_active, vidas, kill_count, star_count = True, False, False, False, 3, 0, 0
        reset_game()
    elif sound_button.collidepoint(pos):
        music_on = not music_on
        if music_on:
            if menu_active: play_music("menu_music")
            elif game_active: play_music("game_music")
            elif game_over: play_music("game_over_music")
            elif victory: play_music("victory_music")
        else:
            music.stop()
            current_music = None

def on_key_down(key):
    if key == keys.Z and game_active:
        bullets.append(Bullet(hero.x, hero.y-30, hero.direction))
        hero.shooting, hero.shoot_timer = True, 10
        if music_on: sounds.shoot.play()

def play_music(track):
    global current_music
    if music_on and current_music != track:
        music.stop(); music.play(track); music.set_volume(0.5); current_music = track
    elif not music_on:
        music.stop(); current_music = None

def update():
    global game_active, camera_x, vidas, game_over, victory, kill_count, star_count, instrucoes_timer
    if game_active:
        hero.update()
        camera_x = max(0, min(hero.x-WIDTH//2, WORLD_WIDTH-WIDTH))
        for e in enemies: e.update()
        for b in bullets: b.update()
        bullets[:] = [b for b in bullets if b.active]
        to_remove = []
        for b in bullets:
            bullet_rect = Rect(b.x-5, b.y-5, 10, 10)
            for e in enemies:
                enemy_rect = Rect(e.x-20, e.y-32, 40, 60)
                if enemy_rect.colliderect(bullet_rect):
                    b.active = False; to_remove.append(e); break
        for e in to_remove:
            if e in enemies: enemies.remove(e); kill_count += 1
        hero_rect = Rect((hero.x-20, hero.y-60, 40, 60))
        for e in enemies:
            enemy_rect = Rect((e.x-20, e.y-60, 40, 60))
            if hero_rect.colliderect(enemy_rect):
                vidas -= 1; hero.x += -25 if hero.x<e.x else 25; hero.vy = -5
                if vidas<=0: game_active, game_over = False, True
                break
        star_rect = Rect(star_x-20, star_y-20, 40, 40)
        if hero_rect.colliderect(star_rect):
            game_active, victory = False, True; star_count += 1
        if instrucoes_timer>0: instrucoes_timer -= 1
    if menu_active: play_music("menu_music")
    elif game_active: play_music("game_music")
    elif game_over: play_music("game_over_music")
    elif victory: play_music("victory_music")
pgzrun.go()
