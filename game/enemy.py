import pygame
import random
import math
import os


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, level):
        super().__init__()
        self.enemy_type = enemy_type
        self.level = level

        # Set size based on enemy type - increased by 30% total (10% previously + 20% now)
        if enemy_type == "vegetables":
            # Base size was 60, now 78 (30% larger)
            self.width = 90
            self.height = 90
        elif enemy_type == "bananas":
            # Base size was 60, now 78 (30% larger)
            self.width = 90
            self.height = 90
        elif enemy_type == "grandmas":
            # Base size was 60, now 78 (30% larger)
            self.width = 90
            self.height = 90
        else:
            # Default size with 30% increase
            self.width = 90
            self.height = 90

        # Image loading based on enemy type
        self.image = self._load_enemy_image(enemy_type)

        # If image loading failed, create placeholder image
        if self.image is None:
            self.image = self._create_fallback_image(enemy_type)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Store original image for flipping
        self.original_image = self.image.copy()
        self.facing_right = True

        # Movement properties
        self.vel_x = random.choice([-2, 2])
        self.vel_y = 0
        self.gravity = 0.5
        self.max_fall_speed = 10

        # Enemy state
        self.health = 50 + (level * 25)  # More health on higher levels
        self.attack_cooldown = 0
        self.attack_delay = 60  # 1 second at 60 FPS

        # Load sound effects
        try:
            self.hit_sound = pygame.mixer.Sound("assets/sounds/enemy_hit.wav")
        except:
            self.hit_sound = None

    def _load_enemy_image(self, enemy_type):
        """Load the appropriate enemy image based on type"""
        image = None
        try:
            # Select a random image for the enemy type
            if enemy_type == "vegetables":
                # Choose from veg_1.png to veg_5.png
                veg_num = random.randint(1, 5)
                image_path = f"assets/images/veg_{veg_num}.png"
            elif enemy_type == "bananas":
                # Choose from banana_1.png to banana_4.png
                banana_num = random.randint(1, 4)
                image_path = f"assets/images/banana_{banana_num}.png"
            elif enemy_type == "grandmas":
                # Choose from gran_1.png to gran_3.png
                gran_num = random.randint(1, 3)
                image_path = f"assets/images/gran_{gran_num}.png"
            else:
                return None

            # Load and scale the image
            if os.path.exists(image_path):
                image = pygame.image.load(image_path).convert_alpha()
                image = pygame.transform.scale(image, (self.width, self.height))
                print(f"Loaded enemy image: {image_path}")
            else:
                print(f"Enemy image not found: {image_path}")
        except Exception as e:
            print(f"Error loading enemy image: {e}")

        return image

    def _create_fallback_image(self, enemy_type):
        """Create a simple placeholder image if loading fails"""
        image = pygame.Surface((self.width, self.height))

        # Color and appearance based on enemy type
        if enemy_type == "vegetables":
            # Random vegetable color
            colors = [
                (0, 150, 0),  # Green (broccoli)
                (255, 69, 0),  # Orange-red (carrot)
                (128, 0, 0),  # Maroon (beet)
                (139, 69, 19),  # Brown (potato)
            ]
            color = colors[random.randint(0, len(colors) - 1)]
            image.fill(color)
            # Draw vegetable features
            pygame.draw.circle(image, (0, 100, 0), (self.width // 2, 15), 10)

        elif enemy_type == "bananas":
            # Banana yellow
            image.fill((255, 255, 0))
            # Draw curved banana shape
            pygame.draw.arc(
                image,
                (255, 200, 0),
                (10, 10, self.width - 20, self.height - 20),
                math.pi / 4,
                math.pi * 7 / 4,
                5,
            )

        elif enemy_type == "grandmas":
            # Grandma colors
            image.fill((200, 150, 200))
            # Draw grandma hair
            pygame.draw.ellipse(
                image,
                (220, 220, 220),
                (self.width // 4, 0, self.width // 2, self.height // 3),
            )
            # Draw glasses
            pygame.draw.circle(
                image, (0, 0, 0), (self.width // 3, self.height // 3), 5, 2
            )
            pygame.draw.circle(
                image, (0, 0, 0), (self.width * 2 // 3, self.height // 3), 5, 2
            )

        # Set transparent background
        image.set_colorkey((0, 0, 0))
        return image

    def update(self, platforms, player, screen_width, screen_height):
        """Update enemy state"""
        # Simple AI based on enemy type
        if self.enemy_type == "vegetables":
            # Vegetables move back and forth, simple patrol
            self._patrol_movement(platforms, screen_width)

        elif self.enemy_type == "bananas":
            # Bananas hop around and follow player horizontally
            self._follow_player(player, platforms, screen_width)

        elif self.enemy_type == "grandmas":
            # Grandmas move slower but throw objects at the player
            self._ranged_attack(player, platforms, screen_width)

        # Apply gravity
        self._apply_gravity(platforms, screen_height)

        # Update facing direction based on movement
        if self.vel_x > 0 and not self.facing_right:
            self.facing_right = True
            self.image = self.original_image.copy()
        elif self.vel_x < 0 and self.facing_right:
            self.facing_right = False
            self.image = pygame.transform.flip(self.original_image, True, False)

        # Decrease attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def _patrol_movement(self, platforms, screen_width):
        """Simple back and forth movement"""
        # Move horizontally
        self.rect.x += self.vel_x

        # Check for collisions with platforms (horizontal)
        hit_platform = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                hit_platform = True
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                    self.vel_x = -self.vel_x
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right
                    self.vel_x = -self.vel_x

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x = -self.vel_x
        elif self.rect.right > screen_width:
            self.rect.right = screen_width
            self.vel_x = -self.vel_x

        # Randomly change direction sometimes
        if random.random() < 0.01 and not hit_platform:
            self.vel_x = -self.vel_x

    def _follow_player(self, player, platforms, screen_width):
        """Follow the player horizontally and hop occasionally"""
        # Move towards player
        if player.rect.centerx < self.rect.centerx:
            self.vel_x = -2
        else:
            self.vel_x = 2

        # Apply horizontal movement
        self.rect.x += self.vel_x

        # Check for collisions with platforms (horizontal)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > screen_width:
            self.rect.right = screen_width

        # Hop occasionally when on ground
        if self.vel_y == 0 and random.random() < 0.02:
            self.vel_y = -8  # Jump

    def _ranged_attack(self, player, platforms, screen_width):
        """Move slowly and occasionally shoot at player"""
        # Move slower than other enemies
        if player.rect.centerx < self.rect.centerx:
            self.vel_x = -1
        else:
            self.vel_x = 1

        # Apply horizontal movement
        self.rect.x += self.vel_x

        # Check for collisions with platforms (horizontal)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > screen_width:
            self.rect.right = screen_width

        # Attack if cooldown is up and player is within range
        if (
            self.attack_cooldown <= 0
            and abs(player.rect.centerx - self.rect.centerx) < 300
        ):
            # Create a projectile (would need a proper implementation)
            print(f"Grandma at {self.rect.x},{self.rect.y} attacks player!")
            self.attack_cooldown = self.attack_delay

    def _apply_gravity(self, platforms, screen_height):
        """Apply gravity and handle vertical movement"""
        # Apply gravity
        self.vel_y += self.gravity
        if self.vel_y > self.max_fall_speed:
            self.vel_y = self.max_fall_speed

        # Move vertically
        self.rect.y += self.vel_y

        # Check for collisions with platforms (vertical)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                elif self.vel_y < 0:  # Jumping
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        # Screen bottom boundary
        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height
            self.vel_y = 0

    def take_damage(self, amount):
        """Enemy takes damage"""
        self.health -= amount

        # Play hit sound
        if self.hit_sound:
            self.hit_sound.play()

        # Visual feedback - flash red (would need a proper implementation)
        # For now just print
        print(f"{self.enemy_type} enemy takes {amount} damage! Health: {self.health}")

    def draw(self, screen):
        """Draw the enemy"""
        # Draw enemy sprite
        screen.blit(self.image, self.rect)

        # Draw health bar
        health_width = 40
        health_height = 4
        health_x = self.rect.x + (self.width - health_width) // 2
        health_y = self.rect.y - 8

        # Background (red)
        pygame.draw.rect(
            screen, (255, 0, 0), (health_x, health_y, health_width, health_height)
        )

        # Foreground (green) - proportional to health
        max_health = 50 + (self.level * 25)
        health_percent = max(0, self.health / max_health)
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (health_x, health_y, int(health_width * health_percent), health_height),
        )
