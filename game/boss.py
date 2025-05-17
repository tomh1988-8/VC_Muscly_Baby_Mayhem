import pygame
import math
import os
import random


class Boss(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Boss properties
        self.width = 200
        self.height = 200
        self.base_width = self.width  # Store original size for scaling
        self.base_height = self.height
        self.health = 25  # Boss needs exactly 25 hits to defeat
        self.hits_taken = 0

        # Contact damage cooldown
        self.contact_cooldown = 0
        self.contact_cooldown_max = 60  # 1 second at 60 FPS

        # Load boss image
        try:
            self.image = pygame.image.load(
                "assets/images/final_boss.png"
            ).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            print("Loaded final boss image!")
        except Exception as e:
            print(f"Error loading boss image: {e}")
            # Create fallback image
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self.image.fill((200, 0, 0))  # Red background
            pygame.draw.ellipse(
                self.image, (150, 0, 0), (0, 0, self.width, self.height)
            )
            pygame.draw.ellipse(
                self.image,
                (250, 150, 150),
                (self.width // 4, self.height // 4, self.width // 2, self.height // 2),
            )
            text_font = pygame.font.SysFont("Arial", 32)
            text = text_font.render("BOSS", True, (255, 255, 255))
            self.image.blit(
                text,
                (
                    self.width // 2 - text.get_width() // 2,
                    self.height // 2 - text.get_height() // 2,
                ),
            )

        # Store original image for scaling
        self.original_image = self.image.copy()

        # Set up rectangle and position
        self.rect = self.image.get_rect()
        self.rect.centerx = screen_width // 2
        self.rect.bottom = screen_height - 150  # Float above ground

        # Movement properties
        self.base_speed = 4  # Base speed
        self.speed = self.base_speed
        self.vel_x = self.speed
        self.vel_y = 0

        # Jumping properties
        self.gravity = 0.5
        self.jump_power = 15
        self.on_ground = True
        self.jump_cooldown = 0
        self.jump_cooldown_max = 120  # 2 seconds at 60 FPS

        # Attack pattern timer
        self.pattern_timer = 0
        self.pattern_change = 180  # Change pattern every 3 seconds
        self.current_pattern = 0

        # Animation
        self.animation_timer = 0
        self.facing_right = True

        # Sound effects
        try:
            self.hit_sound = pygame.mixer.Sound("assets/sounds/enemy_hit.wav")
            self.jump_sound = pygame.mixer.Sound("assets/sounds/jump.wav")
        except:
            self.hit_sound = None
            self.jump_sound = None

    def update(self, platforms, player):
        """Update boss behavior"""
        # Update timer
        self.animation_timer += 1
        self.pattern_timer += 1

        # Update jump cooldown
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        # Update contact damage cooldown
        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1

        # Check if it's time to change attack pattern
        if self.pattern_timer >= self.pattern_change:
            self.pattern_timer = 0
            self.current_pattern = (self.current_pattern + 1) % 3

        # Execute current attack pattern
        if self.current_pattern == 0:
            self._horizontal_movement()
        elif self.current_pattern == 1:
            self._chase_player(player)
        else:
            self._bouncing_movement()

        # Randomly jump
        if self.on_ground and self.jump_cooldown <= 0 and random.random() < 0.02:
            self._jump()

        # Apply gravity
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        # Check if on ground (bottom of screen - boss height - 50 for the platform)
        floor_y = self.screen_height - 50 - self.height
        if self.rect.y >= floor_y:
            self.rect.y = floor_y
            self.vel_y = 0
            self.on_ground = True

        # Apply horizontal movement
        self.rect.x += self.vel_x

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x = abs(self.vel_x)  # Move right
            self.facing_right = True
        elif self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
            self.vel_x = -abs(self.vel_x)  # Move left
            self.facing_right = False

        # Update facing direction
        if self.vel_x > 0 and not self.facing_right:
            self.facing_right = True
        elif self.vel_x < 0 and self.facing_right:
            self.facing_right = False

        # Animate boss (simple bobbing) - only when not jumping
        if self.on_ground:
            bob_amount = math.sin(self.animation_timer / 15) * 5
            self.rect.y += int(bob_amount)

        # Check for collision with player (50 damage with cooldown)
        if player.rect.colliderect(self.rect) and self.contact_cooldown <= 0:
            player.take_damage(50)  # Apply 50 damage instead of instant death
            self.contact_cooldown = self.contact_cooldown_max  # Start cooldown
            print("Boss touched player - 50 damage applied!")

    def _jump(self):
        """Make the boss jump"""
        if self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False
            self.jump_cooldown = self.jump_cooldown_max

            # Play jump sound
            if self.jump_sound:
                self.jump_sound.play()

            print("Boss jumped!")

    def _horizontal_movement(self):
        """Simple side-to-side movement"""
        # Already handled in update method with screen boundaries
        pass

    def _chase_player(self, player):
        """Move toward player's position"""
        # Adjust velocity to move toward player
        if player.rect.centerx < self.rect.centerx:
            self.vel_x = -self.speed
        else:
            self.vel_x = self.speed

        # Jump more frequently when chasing
        if self.on_ground and self.jump_cooldown <= 0 and random.random() < 0.04:
            self._jump()

    def _bouncing_movement(self):
        """Bounce around more rapidly"""
        # Use slightly faster speed and change direction randomly sometimes
        self.vel_x = 1.5 * self.speed * (-1 if self.vel_x < 0 else 1)

        # Small chance to change direction
        if random.random() < 0.02:
            self.vel_x = -self.vel_x

        # Jump even more frequently in bouncing mode
        if self.on_ground and self.jump_cooldown <= 0 and random.random() < 0.06:
            self._jump()

    def take_damage(self, damage=1):
        """Boss takes damage and grows stronger"""
        self.health -= damage
        self.hits_taken += 1

        # Grow in size by 2%
        growth_factor = 1 + (0.02 * self.hits_taken)
        self.width = int(self.base_width * growth_factor)
        self.height = int(self.base_height * growth_factor)

        # Scale the original image to new size
        self.image = pygame.transform.scale(
            self.original_image, (self.width, self.height)
        )

        # Adjust rect to maintain position
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

        # Increase speed by 2%
        self.speed = self.base_speed * (1 + (0.02 * self.hits_taken))

        # Increase jump power slightly
        self.jump_power = 15 * (1 + (0.01 * self.hits_taken))

        # Play hit sound
        if self.hit_sound:
            self.hit_sound.play()

        print(
            f"Boss hit! Health: {self.health}, Size: {self.width}x{self.height}, Speed: {self.speed:.2f}"
        )

    def draw_health_bar(self, screen):
        """Draw the boss health bar at the top of the screen"""
        bar_width = 500
        bar_height = 20
        bar_x = (self.screen_width - bar_width) // 2
        bar_y = 20

        # Background (red)
        pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Foreground (green) - proportional to health
        health_percent = max(0, self.health / 25)  # Exactly 25 health max
        pygame.draw.rect(
            screen,
            (0, 200, 0),
            (bar_x, bar_y, int(bar_width * health_percent), bar_height),
        )

        # Border
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

        # Text - show X/25 shots
        font = pygame.font.SysFont("Arial", 18)
        text = font.render(f"Boss Health: {self.health}/25", True, (255, 255, 255))
        screen.blit(text, (bar_x + 10, bar_y + (bar_height - text.get_height()) // 2))
