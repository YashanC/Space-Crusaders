import pygame
import math
import time
from pygame.locals import *
import random
pygame.init()
pygame.font.init()
pygame.mixer.init()

#Initializing fonts     
label_font = pygame.font.SysFont('couriernew',12)
game_font = pygame.font.SysFont('couriernew',20)
title_font = pygame.font.SysFont("None",75)
#Defining colours and screen size
BLACK = (0,0,0)
WHITE = (255,255,255)
GREEN = (50,200,78)
YELLOW = (252,252,10)
RED = (255,0,0)
size = (600,600)
#Initializing all numerical variables and other variables required for game to run
ROT_SPEED = 250
PLAYERSPEED = 0
ENEMYSPEED = 2.85
MAXPLAYERSPEED = 10.0
ACCELERATION = 5.0
GRAV_CONST = 6.67300*(10**(-11))
PROTOPLANET_MASS = 5.082295*(10**13)
BULLETSPEED = 20
ASTEROIDSPEED = 3
HPBARHEIGHT = 10
HPBARWIDTH = 80
asteroid_type = ['tiny','medium','big','protoplanet']
vec = pygame.math.Vector2
vec2 = pygame.math.Vector2
vec3 = pygame.math.Vector2
shot_delay = 0.2
spawn_delay = 0.5
enemy_time = 0
planet_time = 0
last_spawn = 0.0
last_shot = 0
curr_level = 0
score = 0
scores = []
meteor_counter = 0
hit_coeff = 1.5
avg_score = 0
update_score = True
thruster = [False,False]

class Asteroid(pygame.sprite.Sprite):
    def __init__(self,difficulty,x,y,shipx,shipy):
        pygame.sprite.Sprite.__init__(self)
        self.sizes = difficulty
        #Checks the size of each asteroid and randomly generates an according size
        #Loads a random image from a list of images of asteroids and resizes it to the generated size
        if difficulty=='tiny':
            self.size = random.randint(10,20)
            self.image = pygame.transform.scale(pygame.image.load(tinies[random.randint(0,2)]).convert_alpha(), (self.size,self.size))
        elif difficulty=='medium':
            self.size = random.randint(30,40)
            self.image = pygame.transform.scale(pygame.image.load(meds[random.randint(0,2)]).convert_alpha(), (self.size,self.size))
        elif difficulty == 'big':
            self.size = random.randint(50,60)
            self.image = pygame.transform.scale(pygame.image.load(bigs[random.randint(0,2)]).convert_alpha(), (self.size,self.size))
        else:
            self.size = 200
            self.image = pygame.transform.scale(pygame.image.load("p2.png").convert_alpha(), (self.size,self.size))
        self.rect = self.image.get_rect()
        #Positions the image by changing centre of bounding rectangle
        self.rect.center = (x,y)
        self.initial_pos = self.rect.center
        #Calculates a radius parameter (used for collisions)
        self.radius = int(self.rect.width/2)
        if self.sizes == 'protoplanet':
            self.radius -= 25
        self.dist = 0
        self.angle = 0
        self.homing = random.randint(0,1)
        #Generates a random value to determine if asteroid is homing or not
        if self.homing == 0:
            #If not homing, generates a random angle that maximizes time onscreen
            if self.rect.centerx<=screen.get_width()/2 and self.rect.centery<=screen.get_height()/2:
                self.angle = random.uniform(20,70)
            elif self.rect.centerx<=screen.get_width()/2 and self.rect.centery>=screen.get_height()/2:
                self.angle = random.uniform(290,340)
            elif self.rect.centerx>=screen.get_width()/2 and self.rect.centery>=screen.get_height()/2:
                self.angle = random.uniform(200,250)
            else:
                self.angle = random.uniform(110,160) 
        else:
            #Checks if the ship and asteroid lie on the same horizontal/vertical line
            if self.rect.centerx == shipx:
                if self.rect.centery > shipy:
                    self.angle = 270
                elif self.rect.centery < shipy:
                    self.angle = 90
            elif self.rect.centery == shipy:
                if self.rect.centerx > shipx:
                    self.angle = 180
                elif self.rect.centerx < shipx:
                    self.angle = 0
            else:
            #Calculates an angle based on the arctangent of the slope
                self.angle = math.degrees(math.atan(float(shipy-self.rect.centery)/(shipx-self.rect.centerx)))
                if self.rect.centerx > shipx:
                    self.angle += 180
        #Sine and cosine functions used to find x- and y-components of velocity
        self.dx = float(ASTEROIDSPEED)*math.cos(math.radians(self.angle))
        self.dy = float(ASTEROIDSPEED)*math.sin(math.radians(self.angle))
        
    def update(self):
        #Moving the asteroid by moving the bounding rectangle proportionately to the velocity
        self.rect.centery += self.dy
        self.rect.centerx += self.dx
        #Calculate the Euclidean distance between the asteroid and its initial position
        self.dist = math.sqrt((self.rect.centery-self.initial_pos[0])**(2)+(self.rect.centerx-self.initial_pos[0])**(2))
        #If the asteroid is offscreen AND has travelled 600 or more pixels, delete it to avoid lag
        if (self.rect.top>=screen.get_height() or self.rect.bottom<=0 or self.rect.left>=screen.get_width() or self.rect.right<=0) and self.dist > 600:
            self.kill()
        
class Blaster(pygame.sprite.Sprite):
    def __init__(self,angle): 
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        #Rotate the image by "angle" degrees
        self.image = pygame.transform.rotate(self.image,angle)
        self.rect = self.image.get_rect()
        #Determine x- and y-components of velocity
        self.dx = math.cos(math.radians(-90+angle))*BULLETSPEED
        self.dy = math.sin(math.radians(90-angle))*BULLETSPEED

    def update(self):
        #Update the bullet's position according to its velocity
        self.rect.centerx -= self.dx
        self.rect.centery -= self.dy
        #If the bullet goes offscreen, delete it to avoid lag
        if self.rect.top>=screen.get_height() or self.rect.bottom<=0 or self.rect.left>=screen.get_width() or self.rect.right<=0:
            self.kill()
        
class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.angle = 0
        self.lives = 3        #Each enemy ship takes 3 shots from the player ship to destroy
        self.radius = 25      #Radius parameter for collisions
        
    def tracking(self):
        #Same rationale as the "homing" function for the asteroids
        #The if-else-if ladder below is required to avoid errors in the arctangent function
        #(for example, if the ship and the asteroid have the same x-coordinate, the slope will be undefined,
        #so the arctangent function will malfunction
        if self.rect.centerx == ship.rect.centerx:
            if self.rect.centery > ship.rect.centery:
                self.angle = 270
            elif self.rect.centery < ship.rect.centery:
                self.angle = 90
        elif self.rect.centery == ship.rect.centery:
            if self.rect.centerx > ship.rect.centerx:
                self.angle = 180
            elif self.rect.centerx < ship.rect.centerx:
                self.angle = 0
        else:
            self.angle = math.degrees(math.atan(float(ship.rect.centery-self.rect.centery)/(ship.rect.centerx-self.rect.centerx)))
            if self.rect.centerx > ship.rect.centerx:
                self.angle += 180
        #Rotates the ship according to the angle at which it will move
        self.image = pygame.transform.rotate(enemy_img,-self.angle)
        #Calculate the x- and y-components of the velocity, but also add in the ship's velocity
        #The "homing" function of the asteroids did not take this into account, so they simply travelled towards
        #the ship's position the moment the asteroid spawned (not the current position)
        #Adding in the ship's velocity allows for constant accurate tracking of the ship
        self.dx = float(ENEMYSPEED)*math.cos(math.radians(self.angle)) + ship.vel[0]*dt
        self.dy = float(ENEMYSPEED)*math.sin(math.radians(self.angle)) + ship.vel[1]*dt

    def update(self):
        self.tracking() #Call the tracking function to calculate the new velocity
        #Update the position of the enemy ship
        self.rect.centerx += self.dx
        self.rect.centery += self.dy
        #Display the number of lives each enemy ship has
        life_text = label_font.render(str(self.lives),True,WHITE)
        screen.blit(life_text,(self.rect.centerx,self.rect.centery+50))
        
class Spaceship(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = ship_img
        self.rect = self.image.get_rect()
        #When initialized, the ship starts at the center of the screen
        self.rect.center = (screen.get_width()/2,screen.get_height()/2)
        self.pos = self.rect.center
        self.rot = 0          #Rotation parameter, which is the angle of the ship relative to the screen
        self.radius = 18      #Radius parameter for collisions
        self.shield = 100     #Ship has 100 HP
        #Initializing 3 vectors required to calculate ship's velocity
        self.vel = vec(0,0)
        self.vel_f = vec2(0,0)
        self.vel_g = vec3(0,0)
        
    def get_keys(self,delta_t):
        self.rot_speed = 0                #Rotational speed of ship
        self.pos = self.rect.center
        for i in range(len(thruster)):
            thruster[i] = False           #Sets all thrusters to false (none are activated)
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.rot_speed = ROT_SPEED    #If left key is pressed, ship rotates counterclockwise (positive rotational speed)
            thruster[1] = True            #Right thruster activated (to turn ship counterclockwise)
        elif keys[K_RIGHT]:
            self.rot_speed = -ROT_SPEED   #If right key is pressed, ship rotates clockwise (negative rotational speed)
            thruster[0] = True            #Left thruster activated (to turn ship clockwise)
        elif keys[K_UP]:
            #If up key is pressed, ship must accelerate
            #Velocity due to acceleration is given by ACCELERATION * delta_t
            #where delta_t is the amount of time the up arrow has been pressed
            #This was derived from the kinematics equation by solving for vf in
            #a = (vf-vi)/t
            #Vector is then rotated to the angle that the ship is facing
            self.vel_f = vec2(0,-ACCELERATION*delta_t).rotate(-self.rot)
            #Vector is added to main velocity vector
            self.vel = self.vel + self.vel_f
            #If main velocity vector's magnitude exceeds maximum speed of ship,
            #scale it down to the maximum speed
            if self.vel.length() > MAXPLAYERSPEED:
                self.vel.scale_to_length(MAXPLAYERSPEED)
            for i in range(len(thruster)):
                thruster[i] = True         #Engage both thrusters
        for thing in debris:
            #Looks for protoplanets in the sprite group debris
            if thing.sizes == 'protoplanet':
                #Calculates the Euclidean distance between the protoplanet and the ship
                self.GRAV_R = math.sqrt((thing.rect.centery-self.rect.centery)**(2)+(thing.rect.centerx-self.rect.centerx)**(2))
                #Uses Newton's Law of Universal Acceleration to derive the acceleration due to the planet's gravity
                self.a_g = GRAV_CONST*PROTOPLANET_MASS/((self.GRAV_R)**2)
                #Computes the vector between the ship and the planet
                self.vel_g = vec3(thing.rect.centerx-self.rect.centerx,thing.rect.centery-self.rect.centery)
                #Scales the vector down to the magnitude of velocity due to gravitational acceleration
                self.vel_g.scale_to_length(self.a_g)
                #Adds the the new velocity vector to the main velocity vector
                self.vel = self.vel + self.vel_g
                
    def update(self,delta):
        self.get_keys(delta)
        #Determines the total rotation value by adding the product of the rotational speed
        #and how long the left/right keys have been pressed and taking modulo 360
        #modulo 360 is taken because this is the total amount of rotation since the ship was
        #initialized, which is bound to exceed 360 degrees quite quickly
        #To avoid redundant rotations when the user presses the button for short amounts of time
        #the modulo 360 was included
        self.rot = (self.rot + self.rot_speed * delta)%360
        #If both thrusters are activated, load ship image with both thrusters and rotate it to new rotation value
        if thruster[0] and thruster[1]:
            self.image = pygame.transform.rotate(shipthrust,self.rot)
            self.rect = self.image.get_rect()
        #If left thruster is activated, load according image and rotate it to new rotation value
        elif thruster[0]:
            self.image = pygame.transform.rotate(rightthrust,self.rot)
            self.rect = self.image.get_rect()
        #If right thruster is activated, load according image and rotate it to new rotation value
        elif thruster[1]:
            self.image = pygame.transform.rotate(leftthrust,self.rot)
            self.rect = self.image.get_rect()
        #If no thrusters, load according image and rotate it to new rotation value
        else:
            self.image = pygame.transform.rotate(ship_img,self.rot)
            self.rect = self.image.get_rect()
        #Change position by adding velocity vector
        self.pos += self.vel
        self.rect.center = self.pos
        #If the ship goes offscreen, make it emerge from the opposite edge
        if self.rect.right<=0:
            self.rect.right = screen.get_width() + 30
        elif self.rect.left>=screen.get_width():
            self.rect.left = -30
        elif self.rect.top>=screen.get_height():
            self.rect.top = -30
        elif self.rect.bottom<=0:
            self.rect.bottom = screen.get_height() + 30
            
def update_stats(x,y,power,curr_score):
    score_str = "SCORE:"
    #If the HP is somehow less than 0, change it to 0 to avoid bugs
    if power<0:
        power = 0
    #Change colour of HP bar based on HP value
    if power<=25:
        fill_colour = RED
    elif power<=50:
        fill_colour = YELLOW
    else:
        fill_colour = GREEN
    #Portion of HP bar filled should be equal to percentage of health remaining
    filled = float(power)/100.0*HPBARWIDTH
    #Create a rectangle for the HP bar and another rectangle to outline it
    filler = pygame.Rect(x,y,filled,HPBARHEIGHT)
    outline = pygame.Rect(x,y,HPBARWIDTH,HPBARHEIGHT)
    #Draw both rectangles to the screen
    pygame.draw.rect(screen,fill_colour,filler)
    pygame.draw.rect(screen,WHITE,outline,2)
    bar_text = label_font.render("HP:%d" % power,False,WHITE)
    #Places filler zeroes in front of score to make alignment cleaner (e.g. 000020 instead of 20)
    for i in range(6-len(str(curr_score))):
        score_str += '0'
    score_str += str(curr_score)
    score_text = game_font.render(score_str,True,WHITE)
    #Displays text beside HP bar showing HP and score
    screen.blit(bar_text,(90,5))
    screen.blit(score_text,(screen.get_width()-150,5))

def generate_coords(planet = False):
    x,y = 0,0
    #Choose random side from which the debris/enemy ship will emerge
    #If the object is a planet, it is made to spawn further away from the edge of the screen
    #this prevents half the planet from suddenly materializing
    side = random.randint(0,3)
    if side == 0:    #Emerges from above the screen
        if planet:
            x = random.randint(-100,screen.get_width()+100)
            y = -100
        else:
            x = random.randint(-30,screen.get_width()+30)
            y = -30
    elif side == 1:  #Comes in through the right edge of the screen
        if planet:
            x = screen.get_width()+100
            y = random.randint(-100,screen.get_height()+100)
        else:
            x = screen.get_width()+30
            y = random.randint(-30,screen.get_height()+30)
    elif side == 2:  #Emerges from below the screen
        if planet:
            x = random.randint(-100,screen.get_width()+100)
            y = screen.get_height()+100
        else:
            x = random.randint(-30,screen.get_width()+30)
            y = screen.get_height()+30
    elif side == 3:  #Comes in through the left edge of the screen
        if planet:
            x = -100
            y = random.randint(-100,screen.get_height()+100)
        else:
            x = -30
            y = random.randint(-30,screen.get_height()+30)
    warning_rect.center = (x,y)
    #Find coordinates for the warning image so that it is onscreen
    #and shows where the asteroids will come from
    if x < 0:
        warning_rect.centerx = 30
    elif x > screen.get_width():
        warning_rect.centerx = screen.get_width()-30
    if y < 0:
        warning_rect.centery = 30
    elif y > screen.get_height():
        warning_rect.centery = screen.get_height()-30
    #Displays warning image
    screen.blit(warning_img,warning_rect)
    return (x,y)    #Returns a tuple, which contains an x-coordinate and a y-coordinate
    
def spawn_asteroid(a_type = asteroid_type[random.randint(0,2)]):
    #Generates coordinates for asteroid
    if a_type == "protoplanet":
        (a_x,a_y) = generate_coords(True)
    else:
        (a_x,a_y) = generate_coords()
    #Initializes new asteroid sprite and adds it to debris and avoidance sprite groups
    asteroid = Asteroid(a_type,a_x,a_y,ship.rect.centerx,ship.rect.centery)
    debris.add(asteroid)
    avoidance.add(asteroid)

def spawn_enemy():
    #Generates coordinates for enemy ship
    (e_x,e_y) = generate_coords()
    #Initializes new enemy sprite and adds it to debris and avoidance sprite groups
    enemy = Enemy(e_x,e_y)
    enemies.add(enemy)
    avoidance.add(enemy)
    
#Initializes variables for the screen (screen itself, caption, default background)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Space Crusaders")
background = pygame.Surface(size)
background = background.convert()
background.fill(BLACK)
#Initializes backgrounds for each level and sizes them to cover the entire screen
level1_img = pygame.image.load("darkPurple.png").convert_alpha()
level1_img = pygame.transform.scale(level1_img,(screen.get_width(),screen.get_height()))
level1_rect = level1_img.get_rect()
level2_img = pygame.image.load("blue.png").convert_alpha()
level2_img = pygame.transform.scale(level2_img,(screen.get_width(),screen.get_height()))
level2_rect = level2_img.get_rect()
level3_img = pygame.image.load("purple.png").convert_alpha()
level3_img = pygame.transform.scale(level3_img,(screen.get_width(),screen.get_height()))
level3_rect = level3_img.get_rect()
level4_img = pygame.image.load("black.png").convert_alpha()
level4_img = pygame.transform.scale(level4_img,(screen.get_width(),screen.get_height()))
level4_rect = level4_img.get_rect()
#Retrieves all pictures required to run the game from file
warning_img = pygame.image.load("warning.png").convert_alpha()
warning_img = pygame.transform.scale(warning_img,(50,50))
warning_rect = warning_img.get_rect()
ship_img = pygame.image.load("playerShip1_orange.png").convert_alpha()
ship_img = pygame.transform.scale(ship_img, (30,40))
enemy_img = pygame.image.load("enemyGreen1.png").convert_alpha()
enemy_img = pygame.transform.scale(enemy_img, (50,50))
shipthrust = pygame.image.load("thrusters.png").convert_alpha()
shipthrust = pygame.transform.scale(shipthrust, (30,40))
rightthrust = pygame.image.load("rightthrust.png").convert_alpha()
rightthrust = pygame.transform.scale(rightthrust, (30,40))
leftthrust = pygame.image.load("leftthrust.png").convert_alpha()
leftthrust = pygame.transform.scale(leftthrust, (30,40))
bullet_img = pygame.image.load("laserBlue03.png").convert_alpha()
tinies = ["meteorBrown_tiny1.png","meteorBrown_tiny2.png","meteorBrown_small2.png"]
meds = ["meteorBrown_small1.png","meteorBrown_med1.png","meteorBrown_med3.png"]
bigs = ["meteorBrown_big1.png","meteorBrown_big2.png","meteorBrown_big3.png"]
#Retrieves all sound effects required for the game from file
laser_sfx = pygame.mixer.Sound("sfx_laser1.ogg")
collision_sfx = pygame.mixer.Sound("depth_charge.wav")
win_sfx = pygame.mixer.Sound("sfx_twoTone.ogg")

#Initializes game clock (which is used to control frame rate)
clock = pygame.time.Clock()
#Initializes all sprite groups required to run game
cannon = pygame.sprite.Group()      #Contains all bullets
debris = pygame.sprite.Group()      #Contains all asteroids/planets
enemies = pygame.sprite.Group()     #Contains all enemies
avoidance = pygame.sprite.Group()   #Contains contents of debris and enemies sprite groups
ship = Spaceship()                  #Initializes the player's ship
running = True
#Below is the game loop, in which all functions of the game are executed
while running:
    #Gets a timestamp every time the loop refreshes, keeps the frame rate at 30 FPS
    dt = clock.tick(30) / 1000.0
    #Blits default black background to screen
    screen.blit(background,(0,0))
    #Gets a list of user-prompted events that occurred within this iteration of the loop
    for ev in pygame.event.get():
        #If user has quit the window, close the window
        if ev.type == QUIT:
            running = False
        elif ev.type == KEYDOWN:
            #If user has pressed the space key...
            if ev.key == K_SPACE:
                #...and it has been enough time since the last bullet spawned
                #Compares current timestamp to timestamp of last bullet
                #If the difference is greater than the delay between shots
                #A new bullet is initialized and fired
                if time.time()-last_shot > shot_delay:
                    #Pass the ship's rotation when initializing a bullet
                    #so that the bullet is rotated to the same angle as the ship
                    blast = Blaster(ship.rot)
                    #Move the bullet to the same spot as the ship so it looks like it is being
                    #shot by the ship
                    blast.rect.center = ship.rect.center
                    cannon.add(blast)
                    laser_sfx.play()         #Play laser sound effect
                    last_shot = time.time()  #Refresh timestamp of last bullet shot
    #The initial screen when the game is pressed is considered to be "level 0"
    if curr_level == 0:
        #Display title of the game and instructions
        title_txt = title_font.render("SPACE CRUSADERS",True,WHITE)
        instructions1 = game_font.render("Up to accelerate, left and right to rotate,",True,WHITE)
        instructions2 = game_font.render("space to shoot. Avoid and shoot obstacles and ",True,WHITE)
        instructions3 = game_font.render("remember that the game uses the physics of space.",True,WHITE)
        instructions4 = game_font.render("If you go offscreen, you will emerge",True,WHITE)
        instructions5 = game_font.render("on the other side.",True,WHITE)
        click_txt = game_font.render("Click to continue",True,WHITE)
        screen.blit(title_txt,(40,100))
        screen.blit(instructions1,(35,180))
        screen.blit(instructions2,(20,205))
        screen.blit(instructions3,(5,230))
        screen.blit(instructions4,(70,255))
        screen.blit(instructions5,(180,280))                                 
        screen.blit(click_txt,(200,500))
        #If left mouse button is pressed, proceed to level 1
        if pygame.mouse.get_pressed()[0]:
            curr_level += 1
            #Display level 1 background and display "LEVEL 1"
            screen.blit(level1_img,level1_rect)
            lvl_text = game_font.render("LEVEL 1",True,WHITE)
            screen.blit(lvl_text,(260,100))
            pygame.display.flip()
            pygame.time.wait(1000)
            score = 0           #Reset score
            #Set numerical values to change how easy the level is
            spawn_delay = 0.75
            hit_coeff = 1.5
            meteor_counter = 0
            ship.__init__()
            update_score = True
    elif curr_level == 1:
        screen.blit(level1_img,level1_rect)
        #Spawn either a small or medium asteroid
        next_asteroid = asteroid_type[random.randint(0,1)]
        #Based on the size of the asteroid, generate a random speed
        if next_asteroid == "tiny":
            ASTEROIDSPEED = random.uniform(3,5) #Generates a random real number btwn 3 and 5
        else:
            ASTEROIDSPEED = random.uniform(2,4)
        #If it has been enough time since the last asteroid spawned,
        #initialize a new one
        if time.time()-last_spawn > spawn_delay:
            meteor_counter += 1
            spawn_asteroid(next_asteroid)
            last_spawn = time.time()
        #If the player has survived 60 or more asteroids, they have completed level 1
        if meteor_counter >= 60:
            #Transition to level 2: change background, set numerical values, reset player ship
            curr_level += 1
            meteor_counter = 0
            done_text = game_font.render("You have completed Level 1!",True,WHITE)
            win_sfx.play()
            screen.fill(BLACK)
            screen.blit(level1_img,level1_rect)
            screen.blit(done_text,(140,100))
            pygame.display.flip()
            pygame.time.wait(2000)
            screen.blit(level2_img,level2_rect)
            lvl_text = game_font.render("LEVEL 2",True,WHITE)
            screen.blit(lvl_text,(260,100))
            pygame.display.flip()
            pygame.time.wait(1000)
            debris.empty()
            cannon.empty()
            avoidance.empty()
            ship.__init__()
            spawn_delay = 1.0
            hit_coeff = 1
    elif curr_level == 2:
        screen.blit(level2_img,level2_rect)
        #Generate a small, medium, or large asteroid
        next_asteroid = asteroid_type[random.randint(0,2)]
        #If it has been enough time since the spawn of the
        #last asteroid, generate a new one with a speed
        #assigned based on its size
        if time.time()-last_spawn > spawn_delay:
            meteor_counter += 1
            if next_asteroid == "tiny":
                ASTEROIDSPEED = random.uniform(4,6)
            elif next_asteroid == "medium":
                ASTEROIDSPEED = random.uniform(3,5)
            else:
                ASTEROIDSPEED = random.uniform(2,4)
            spawn_asteroid(next_asteroid)
            last_spawn = time.time()
        #If player survives 60 or more asteroids, they have completed level 2
        if meteor_counter >= 60:
            #Transition to level 3 (involves all the same functions as transition into level 2)
            curr_level += 1
            meteor_counter = 0
            done_text = game_font.render("You have completed Level 2!",True,WHITE)
            win_sfx.play()
            screen.fill(BLACK)
            screen.blit(level2_img,level2_rect)
            screen.blit(done_text,(140,100))
            pygame.display.flip()
            pygame.time.wait(2000)
            screen.blit(level3_img,level3_rect)
            lvl_text = game_font.render("LEVEL 3",True,WHITE)
            screen.blit(lvl_text,(260,100))
            pygame.display.flip()
            pygame.time.wait(1000)
            debris.empty()
            cannon.empty()
            avoidance.empty()
            hit_coeff = 0.6
            spawn_delay = 2.0
            shot_delay = 0.18
            ship.__init__()
    elif curr_level == 3:
        screen.blit(level3_img,level3_rect)
        #Takes the time elapsed between frames and adds it to enemy time
        #This time was computed at the very beginning of the game loop
        enemy_time += dt
        #If there are less than 3 enemies on screen and it has been
        #at least 2 seconds since the last one spawned, spawn a new one
        #and reset enemy_time
        #enemies.sprites() returns a list of all sprites found within
        #the enemies sprite group; thus, the length of the list is the # of enemies
        if len(enemies.sprites()) < 3 and enemy_time >= 2:
            spawn_enemy()
            enemy_time = 0
        #Spawn a small, medium, or large asteroid with an assigned speed
        next_asteroid = asteroid_type[random.randint(0,2)]
        if time.time()-last_spawn > spawn_delay:
            meteor_counter += 1
            if next_asteroid == "tiny":
                ASTEROIDSPEED = random.uniform(4,6)
            elif next_asteroid == "medium":
                ASTEROIDSPEED = random.uniform(3,5)
            else:
                ASTEROIDSPEED = random.uniform(2,4)
            spawn_asteroid(next_asteroid)
            last_spawn = time.time()
        #If user survives 35 or more asteroids, they have completed the level
        if meteor_counter >= 35:
            #Transition into level 4
            curr_level += 1
            meteor_counter = 0
            done_text = game_font.render("You have completed Level 3!",True,WHITE)
            win_sfx.play()
            screen.fill(BLACK)
            screen.blit(level3_img,level3_rect)
            screen.blit(done_text,(140,100))
            pygame.display.flip()
            pygame.time.wait(2000)
            screen.blit(level4_img,level4_rect)
            lvl_text = game_font.render("LEVEL 4",True,WHITE)
            screen.blit(lvl_text,(260,100))
            pygame.display.flip()
            pygame.time.wait(1000)
            #All groups are emptied between levels to avoid "remnants" of past levels
            #appearing onscreen at the beginning of the next level (e.g. asteroids
            #from the very end of the last level)
            debris.empty()
            cannon.empty()
            enemies.empty()
            avoidance.empty()
            spawn_delay = 2.5
            hit_coeff = 0.35
            ship.__init__()
    elif curr_level == 4:
        screen.blit(level4_img,level4_rect)
        next_asteroid = asteroid_type[random.randint(0,2)]
        #Takes the time elapsed between each frame and adds it to planet_time
        #works for the exact same time and is used for the same purpose as
        #the enemy_time += dt
        planet_time += dt
        #Spawn a small, medium, or large asteroid
        if time.time()-last_spawn > spawn_delay:
            meteor_counter += 1
            if next_asteroid == "tiny":
                ASTEROIDSPEED = random.uniform(4,6)
            elif next_asteroid == "medium":
                ASTEROIDSPEED = random.uniform(3,5)
            else:
                ASTEROIDSPEED = random.uniform(2,4)
            spawn_asteroid(next_asteroid)
            last_spawn = time.time()
        #If it has been at least 5 seconds since the last planet spawned,
        #spawn a new one and reset planet_time
        if planet_time >= 5:
            ASTEROIDSPEED = random.uniform(2,3)
            spawn_asteroid("protoplanet")
            planet_time = 0
        #If user survives 24 or more asteroids, they have completed the level
        if meteor_counter >= 24:
            #Since this is the last level, go to the game over screen
            curr_level = -1
            meteor_counter = 0
            done_text = game_font.render("You have completed Level 4!",True,WHITE)
            win_sfx.play()
            screen.fill(BLACK)
            screen.blit(level4_img,level4_rect)
            screen.blit(done_text,(140,100))
            pygame.display.flip()
            pygame.time.wait(2000)
            avoidance.empty()
            debris.empty()
            cannon.empty()
            enemies.empty()
    #The gameover screen is "level -1"
    elif curr_level == -1:
        #Display a black screen
        screen.fill(BLACK)
        #The variable update_score is used to make sure
        #computation of average score only happens once
        #update_score is only made True when the game begins again
        if update_score:
            update_score = False
            #Scores is the list containing all scores from all attempts
            #since the game was last opened (is cleared once the game closes)
            scores.append(score)
            avg_score = float(sum(scores))/len(scores)  #Compute the average score
        over_text = title_font.render("GAME OVER",True,WHITE)
        #Prompts the user on how to (or how not to) play again
        again_text = game_font.render("Play again? Y/N",True,WHITE)
        avg_scorestr = "Average Score: " + str(round(avg_score,2))
        your_scorestr = "Score: " + str(score)
        your_score = game_font.render(your_scorestr,True,WHITE)
        avg_scoretxt = game_font.render(avg_scorestr,True,WHITE)
        #Scores list is sorted
        scores.sort()
        #Thus, the last index must be the highest score
        high_score = scores[len(scores)-1]
        #If the player's score is equal to the high score,
        #they have set a new high score
        if score == high_score:
            #Display a special message if a new high score has been hit
            congrats_txt = game_font.render("NEW HIGH SCORE!",True,WHITE)
            screen.blit(congrats_txt,(200,175))
        high_scorestr = "High Score: " + str(high_score)
        high_scoretxt = game_font.render(high_scorestr,True,WHITE)
        #Display player's score, high score, average score, etc.
        screen.blit(over_text,(140,95))
        screen.blit(your_score,(200,200))
        screen.blit(avg_scoretxt,(200,225))
        screen.blit(high_scoretxt,(200,250))
        screen.blit(again_text,(200,300))
        #Retrieve all the keys that have been pressed by the user
        key = pygame.key.get_pressed()
        #If the 'y' key has been pressed, play again
        if key[pygame.K_y]:
            curr_level = 0
        #If the 'n' key has been pressed, quit
        elif key[pygame.K_n]:
            running = False
        #Clear all groups to avoid any bugs if game restarts
        debris.empty()
        avoidance.empty()
        cannon.empty()
        enemies.empty()
            
    #Updates the ship using 'dt' (time elapsed between frames)
    #This quantity is used to measure how long the arrow keys have been pressed
    ship.update(dt)
    #Update all sprites in each group with the Group.update() function
    cannon.update()
    debris.update()
    enemies.update()
    #Create a list 'vaporized' of every collision between the asteroids and the bullets
    vaporized = pygame.sprite.groupcollide(debris,cannon,True,True)
    for meteor in vaporized:
        #If the asteroid that was hit was medium, split it into 2 small asteroids
        if meteor.sizes=='medium':
            for i in range(2):
                if curr_level == 1:
                    ASTEROIDSPEED = random.uniform(3,5)
                else:
                    ASTEROIDSPEED = random.uniform(4,6)
                asteroid = Asteroid('tiny',meteor.rect.centerx,meteor.rect.centery,ship.rect.centerx,ship.rect.centery)
                avoidance.add(asteroid)
                debris.add(asteroid)
            score += 20
        #If the asteroid that was hit was big, split it into 2 medium asteroids
        elif meteor.sizes=='big':
            for i in range(2):
                if curr_level == 1:
                    ASTEROIDSPEED = random.uniform(2,4)
                else:
                    ASTEROIDSPEED = random.uniform(3,5)
                asteroid = Asteroid('medium',meteor.rect.centerx,meteor.rect.centery,ship.rect.centerx,ship.rect.centery)
                debris.add(asteroid)
                avoidance.add(asteroid)
            score += 10
        #If a planet was hit, split it into 4 large asteroids
        elif meteor.sizes == 'protoplanet':
            for i in range(4):
                ASTEROIDSPEED = random.uniform(2,3)
                asteroid = Asteroid('big',meteor.rect.centerx,meteor.rect.centery,ship.rect.centerx,ship.rect.centery)
                debris.add(asteroid)
                avoidance.add(asteroid)
            score += 200
        else:
            score += 40  #Increments score
    #Initialize list 'shot_down' with all collisions between enemy ships and bullets
    shot_down = pygame.sprite.groupcollide(enemies,cannon,False,True)
    for enemy_hit in shot_down:
        #If the enemy ship has more than 1 life, decrement its lives
        if enemy_hit.lives > 1:
            enemy_hit.lives -= 1
        #If the enemy ship has 0 lives now, delete it
        else:
            enemy_hit.kill()
        score += 100  #Increment score
    #Initialize list 'hits' with all collisions between debris, enemies, and the ship
    hits = pygame.sprite.spritecollide(ship,avoidance,True,pygame.sprite.collide_circle)
    for obstacle in hits:
        #Reduce the ship's HP by an amount proportional to the severity of the collision
        #The severity is measured using the collision radius (larger radius => more severe)
        ship.shield -= obstacle.radius*hit_coeff
        #Play collision sound effect
        collision_sfx.play()
    if curr_level > 0:
        #Only display all sprites if the level is greater than 0
        #We don't want gameplay happening in the gameover screen or the start screen
        #Draw the ship
        screen.blit(ship.image,ship.rect)
        #Draw all the sprites in each group using the Group.draw() function
        cannon.draw(screen)
        debris.draw(screen)
        enemies.draw(screen)
        #Call the update_stats function to update HP bar and score
        update_stats(6,6,ship.shield,score)
        #If the ship has no HP, make the level = -1 so game over screen displays
        #ship.shield < 1 is used instead of ship.shield <= 0 because even if the
        #ship's HP is 0.5, it will be displayed beside the HP bar as 0
        #Thus to avoid confusion, ship.shield < 1 was used
        if ship.shield < 1:
            lose_text = game_font.render("YOU LOSE!",True,WHITE)
            screen.blit(lose_text,(250,190))
            pygame.display.flip()
            pygame.time.delay(1000)
            curr_level = -1
    #Refresh the screen after each iteration of the game loop to reflect changes made
    pygame.display.flip()
#If the program ever escapes the game loop, close the window
pygame.quit()
