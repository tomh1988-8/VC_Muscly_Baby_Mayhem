import pygame
import os
import math


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 100
        self.height = 120

        # Default image is a placeholder rectangle
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((255, 182, 193))  # Light pink for baby

        # Try to load player image
        try:
            player_img = pygame.image.load(
                "assets/images/boss_baby.png"
            ).convert_alpha()
            self.image = pygame.transform.scale(player_img, (self.width, self.height))
            print("Loaded boss_baby.png image!")
        except Exception as e:
            print(f"Error loading player image: {e}")
            # Draw a muscly baby placeholder
            pygame.draw.ellipse(
                self.image, (255, 200, 200), (0, 0, self.width, self.height * 0.6)
            )  # Head
            pygame.draw.rect(
                self.image,
                (255, 200, 200),
                (
                    self.width * 0.2,
                    self.height * 0.5,
                    self.width * 0.6,
                    self.height * 0.5,
                ),
            )  # Body
            pygame.draw.ellipse(
                self.image,
                (200, 100, 100),
                (
                    self.width * 0.1,
                    self.height * 0.4,
                    self.width * 0.3,
                    self.height * 0.3,
                ),
            )  # Left muscle
            pygame.draw.ellipse(
                self.image,
                (200, 100, 100),
                (
                    self.width * 0.6,
                    self.height * 0.4,
                    self.width * 0.3,
                    self.height * 0.3,
                ),
            )  # Right muscle

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Store original image for flipping
        self.original_image = self.image.copy()

        # Movement properties
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 6  # Slightly increased speed for better movement
        self.jump_power = 16  # Slightly increased jump height
        self.gravity = 0.7  # Reduced gravity for more floaty jumps
        self.max_fall_speed = 12

        # Player state
        self.on_ground = False
        self.facing_right = True
        self.shooting_right = (
            True  # Direction player shoots (can differ from facing direction)
        )
        self.health = 500
        self.max_health = 500
        self.score = 0

        # Shooting properties
        self.bullets = pygame.sprite.Group()
        self.shoot_cooldown = 0
        self.shoot_delay = 15  # Frames between shots

        # Load sound effects
        try:
            self.jump_sound = pygame.mixer.Sound("assets/sounds/jump.wav")
            self.shoot_sound = pygame.mixer.Sound("assets/sounds/shoot.wav")
            self.hit_sound = pygame.mixer.Sound("assets/sounds/hit.wav")
        except:
            print("Warning: Player sound effects not found")
            self.jump_sound = None
            self.shoot_sound = None
            self.hit_sound = None

    def update(self, platforms, enemies, screen_width, screen_height):
        """Update player state"""
        # Process movement
        self._process_movement(platforms, screen_width, screen_height)

        # Update player orientation based on facing direction
        if self.vel_x < 0 and self.facing_right:  # Moving left
            self.facing_right = False
            self.image = pygame.transform.flip(self.original_image, True, False)
        elif self.vel_x > 0 and not self.facing_right:  # Moving right
            self.facing_right = True
            self.image = self.original_image.copy()

        # Handle shooting cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Update bullets
        self.bullets.update()

        # Remove bullets that are off-screen
        for bullet in self.bullets:
            if bullet.rect.x < 0 or bullet.rect.x > screen_width:
                bullet.kill()

        # Check for collisions with enemies
        self._check_enemy_collisions(enemies)

        return self.health <= 0

    def _process_movement(self, platforms, screen_width, screen_height):
        """Handle player movement and physics"""
        # Horizontal movement
        self.rect.x += self.vel_x

        # Check for collisions with platforms (horizontal)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right

        # Vertical movement
        self.vel_y += self.gravity
        if self.vel_y > self.max_fall_speed:
            self.vel_y = self.max_fall_speed

        self.rect.y += self.vel_y

        # Reset on_ground flag
        self.on_ground = False

        # Check for collisions with platforms (vertical)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Jumping
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel_y = 0
        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height
            self.vel_y = 0
            self.on_ground = True

    def move_left(self):
        self.vel_x = -self.speed
        self.facing_right = False

    def move_right(self):
        self.vel_x = self.speed
        self.facing_right = True

    def stop(self):
        self.vel_x = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False
            if self.jump_sound:
                self.jump_sound.play()

    def set_shoot_direction(self, shoot_right):
        """Set the shooting direction"""
        self.shooting_right = shoot_right

    def shoot(self):
        """Fire a projectile"""
        if self.shoot_cooldown <= 0:
            # Create bullet at appropriate position based on shooting direction, not facing
            if self.shooting_right:
                bullet_x = self.rect.right - 10
            else:
                bullet_x = self.rect.left + 10

            bullet_y = self.rect.centery

            # Create new bullet and add to group using shooting direction
            bullet = Bullet(bullet_x, bullet_y, self.shooting_right)
            self.bullets.add(bullet)

            # Reset cooldown
            self.shoot_cooldown = self.shoot_delay

            # Play sound
            if self.shoot_sound:
                self.shoot_sound.play()

    def _check_enemy_collisions(self, enemies):
        """Check for collisions between player bullets and enemies"""
        # Check for bullet hits on enemies
        for bullet in self.bullets:
            hits = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hits:
                bullet.kill()
                enemy.take_damage(75)  # Each bullet does 75 damage (was 25)
                self.score += 10

        # Check for direct collisions with enemies
        hits = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hits:
            self.take_damage(1)  # Reduced enemy contact damage from 5 to 1

    def take_damage(self, amount):
        """Reduce player health"""
        self.health -= amount
        if self.health < 0:
            self.health = 0
        if self.hit_sound:
            self.hit_sound.play()

    def heal(self, amount):
        """Increase player health"""
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def draw(self, screen):
        """Draw the player and bullets"""
        # Draw player
        screen.blit(self.image, self.rect)

        # Draw bullets
        self.bullets.draw(screen)

        # Draw health bar
        health_width = 50
        health_height = 5
        health_x = self.rect.x + (self.width - health_width) // 2
        health_y = self.rect.y - 10

        # Background (red)
        pygame.draw.rect(
            screen, (255, 0, 0), (health_x, health_y, health_width, health_height)
        )

        # Foreground (green) - proportional to health
        health_percent = self.health / self.max_health
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (health_x, health_y, int(health_width * health_percent), health_height),
        )

        # Draw shooting direction indicator
        indicator_size = 10
        if self.shooting_right:
            # Arrow pointing right
            pygame.draw.polygon(
                screen,
                (255, 255, 0),
                [
                    (self.rect.right + 5, self.rect.centery),
                    (
                        self.rect.right + 5 + indicator_size,
                        self.rect.centery - indicator_size // 2,
                    ),
                    (
                        self.rect.right + 5 + indicator_size,
                        self.rect.centery + indicator_size // 2,
                    ),
                ],
            )
        else:
            # Arrow pointing left
            pygame.draw.polygon(
                screen,
                (255, 255, 0),
                [
                    (self.rect.left - 5, self.rect.centery),
                    (
                        self.rect.left - 5 - indicator_size,
                        self.rect.centery - indicator_size // 2,
                    ),
                    (
                        self.rect.left - 5 - indicator_size,
                        self.rect.centery + indicator_size // 2,
                    ),
                ],
            )


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction_right):
        super().__init__()

        # Try to load bullet image
        try:
            self.original_image = pygame.image.load(
                "assets/images/bullet.png"
            ).convert_alpha()
            # Scale the image to an appropriate size
            self.original_image = pygame.transform.scale(self.original_image, (20, 10))
            self.image = self.original_image

            # Flip the image if shooting left
            if not direction_right:
                self.image = pygame.transform.flip(self.original_image, True, False)

        except Exception as e:
            # Fallback to a simple shape if loading fails
            print(f"Failed to load bullet image: {e}")
            self.image = pygame.Surface((15, 8))
            self.image.fill((255, 50, 50))  # Bright red bullet
            # Add a bullet "trail"
            pygame.draw.rect(
                self.image, (255, 255, 0), (0 if direction_right else 10, 2, 5, 4)
            )

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 15  # Increased speed
        self.direction_right = direction_right

    def update(self):
        """Move the bullet"""
        if self.direction_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed
