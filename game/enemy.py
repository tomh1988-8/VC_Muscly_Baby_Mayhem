import pygame
import random
import math
import os


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, level, is_main=False):
        super().__init__()
        self.enemy_type = enemy_type
        self.level = level
        self.is_main = is_main

        # Set size based on enemy type - increased by 30% total (10% previously + 20% now)
        # Main enemies are twice as large
        if enemy_type == "vegetables":
            # Base size was 60, now 78 (30% larger)
            self.width = 90
            self.height = 90
            # Main vegetable enemy uses veg_3.png (broccoli)
            self.main_image_number = 3
        elif enemy_type == "bananas":
            # Base size was 60, now 78 (30% larger)
            self.width = 90
            self.height = 90
            # Main banana enemy uses banana_2.png
            self.main_image_number = 2
        elif enemy_type == "grandmas":
            # Base size was 60, now 78 (30% larger)
            self.width = 90
            self.height = 90
            # Main grandma enemy uses gran_1.png
            self.main_image_number = 1
        else:
            # Default size with 30% increase
            self.width = 90
            self.height = 90
            self.main_image_number = 1

        # Double the size for main enemies
        if is_main:
            self.width *= 2
            self.height *= 2

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
        self.base_health = 50 + (level * 25)
        if is_main:
            self.health = self.base_health * 2  # Double health for main enemies
        else:
            self.health = self.base_health

        # Attack properties
        self.attack_cooldown = 0
        if is_main:
            # Main enemies shoot more frequently
            self.attack_delay = 45  # 0.75 seconds at 60 FPS (more aggressive)
        else:
            self.attack_delay = 60  # 1 second at 60 FPS

        # Normal contact damage
        self.contact_damage = 1

        # Projectiles for main enemies
        self.can_shoot = is_main
        self.projectiles = pygame.sprite.Group()
        self.projectile_damage = 2  # Double damage from projectiles
        self.shooting_range = (
            500 if is_main else 300
        )  # Increased range for main enemies

        # Load sound effects
        try:
            self.hit_sound = pygame.mixer.Sound("assets/sounds/enemy_hit.wav")
            if self.can_shoot:
                self.shoot_sound = pygame.mixer.Sound("assets/sounds/enemy_shoot.wav")
            else:
                self.shoot_sound = None
        except:
            self.hit_sound = None
            self.shoot_sound = None

    def _load_enemy_image(self, enemy_type):
        """Load the appropriate enemy image based on type"""
        image = None
        try:
            # Select a specific image for main enemies, or random for regular enemies
            if enemy_type == "vegetables":
                if self.is_main:
                    veg_num = (
                        self.main_image_number
                    )  # Main vegetable uses a specific image
                else:
                    veg_num = random.randint(
                        1, 5
                    )  # Regular vegetables use random images
                image_path = f"assets/images/veg_{veg_num}.png"
            elif enemy_type == "bananas":
                if self.is_main:
                    banana_num = (
                        self.main_image_number
                    )  # Main banana uses a specific image
                else:
                    banana_num = random.randint(
                        1, 4
                    )  # Regular bananas use random images
                image_path = f"assets/images/banana_{banana_num}.png"
            elif enemy_type == "grandmas":
                if self.is_main:
                    gran_num = (
                        self.main_image_number
                    )  # Main grandma uses a specific image
                else:
                    gran_num = random.randint(
                        1, 3
                    )  # Regular grandmas use random images
                image_path = f"assets/images/gran_{gran_num}.png"
            else:
                return None

            # Load and scale the image
            if os.path.exists(image_path):
                image = pygame.image.load(image_path).convert_alpha()
                image = pygame.transform.scale(image, (self.width, self.height))
                print(
                    f"Loaded {'main ' if self.is_main else ''}enemy image: {image_path}"
                )
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

        # Handle shooting for main enemies
        if self.can_shoot and self.attack_cooldown <= 0 and player:
            # Calculate distance to player
            distance_to_player = abs(player.rect.centerx - self.rect.centerx)

            # Shoot if player is within range - main enemies have a longer range
            if distance_to_player < self.shooting_range:
                # Make sure enemy can see the player (no platform in the way)
                can_see_player = True

                # Face the player before shooting
                if player.rect.centerx > self.rect.centerx and not self.facing_right:
                    self.facing_right = True
                    self.image = self.original_image.copy()
                elif player.rect.centerx < self.rect.centerx and self.facing_right:
                    self.facing_right = False
                    self.image = pygame.transform.flip(self.original_image, True, False)

                # If we can see the player, shoot!
                if can_see_player:
                    self._shoot_at_player(player)
                    # Main enemies have a faster attack cooldown
                    self.attack_cooldown = self.attack_delay

        # Update projectiles
        self.projectiles.update()

        # Remove projectiles that are off-screen
        for projectile in list(self.projectiles):
            if (
                projectile.rect.right < 0 or projectile.rect.left > 10000
            ):  # Arbitrary large value
                projectile.kill()

        # Check for projectile collisions with player
        if player and self.projectiles:
            hits = pygame.sprite.spritecollide(player, self.projectiles, True)
            for _ in hits:
                player.take_damage(self.projectile_damage)
                print(f"Player hit by projectile! Damage: {self.projectile_damage}")

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
        """Draw the enemy and projectiles"""
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
        if self.is_main:
            max_health *= 2
        health_percent = max(0, self.health / max_health)
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (health_x, health_y, int(health_width * health_percent), health_height),
        )

        # Draw projectiles
        self.projectiles.draw(screen)

    def _shoot_at_player(self, player):
        """Shoot a projectile at the player (for main enemies)"""
        if not self.can_shoot:
            return

        # Determine shooting direction
        shooting_right = player.rect.centerx > self.rect.centerx

        # Determine projectile starting position
        if shooting_right:
            start_x = self.rect.right - 10
        else:
            start_x = self.rect.left + 10

        start_y = self.rect.centery

        # Create projectile
        projectile = EnemyProjectile(start_x, start_y, shooting_right, self.enemy_type)
        self.projectiles.add(projectile)

        # Play sound effect if available
        if self.shoot_sound:
            self.shoot_sound.play()

        print(
            f"Main {self.enemy_type} enemy shooting at player from ({self.rect.centerx}, {self.rect.centery})!"
        )


class EnemyProjectile(pygame.sprite.Sprite):
    """Projectile fired by main enemies"""

    def __init__(self, x, y, direction_right, enemy_type):
        super().__init__()

        # Size based on enemy type
        if enemy_type == "vegetables":
            self.width, self.height = 20, 20
            self.color = (0, 200, 0)  # Green for vegetables
        elif enemy_type == "bananas":
            self.width, self.height = 15, 25
            self.color = (255, 255, 0)  # Yellow for bananas
        elif enemy_type == "grandmas":
            self.width, self.height = 25, 15
            self.color = (200, 150, 200)  # Purple for grandmas
        else:
            self.width, self.height = 20, 10
            self.color = (255, 0, 0)  # Red default

        # Try to load projectile image based on enemy type
        self.image = None
        try:
            if enemy_type == "vegetables":
                image_path = "assets/images/veg_projectile.png"
            elif enemy_type == "bananas":
                image_path = "assets/images/banana_projectile.png"
            elif enemy_type == "grandmas":
                image_path = "assets/images/gran_projectile.png"
            else:
                image_path = None

            if image_path and os.path.exists(image_path):
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(
                    self.image, (self.width, self.height)
                )

                # Flip the image if shooting left
                if not direction_right:
                    self.image = pygame.transform.flip(self.image, True, False)
        except Exception as e:
            print(f"Failed to load projectile image: {e}")

        # Create fallback image if loading failed
        if self.image is None:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(self.color)
            # Add a trail effect
            trail_color = (255, 255, 255)  # White trail
            trail_width = self.width // 3
            if direction_right:
                trail_x = 0
            else:
                trail_x = self.width - trail_width
            pygame.draw.rect(
                self.image,
                trail_color,
                (trail_x, self.height // 3, trail_width, self.height // 3),
            )
            self.image.set_colorkey((0, 0, 0))  # Make black transparent

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Movement properties
        self.speed = 8
        self.direction_right = direction_right

    def update(self):
        """Move the projectile"""
        if self.direction_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        # Remove if off-screen (will be checked by the game loop)
        if (
            self.rect.right < 0 or self.rect.left > 10000
        ):  # Arbitrary large value for level width
            self.kill()
