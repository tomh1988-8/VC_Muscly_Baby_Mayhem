import pygame
import random
import math
from .player import Player
from .platform import Platform
from .boss import Boss


class BossLevel:
    def __init__(self, screen, player_health=500):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # Level dimensions are the same size as the screen (no scrolling)
        self.level_width = self.screen_width
        self.level_height = self.screen_height

        # Score tracking
        self.score = 0
        self.completed = False
        self.timer = 0

        # Create an empty sprite group for enemies
        self.enemies = pygame.sprite.Group()

        # Victory sequence flags
        self.boss_defeated = False
        self.victory_stairs = []
        self.champ_belt = None
        self.champ_belt_rect = None

        # Load boss level background
        try:
            self.background_image = pygame.image.load(
                "assets/images/background_boss_level.jpg"
            ).convert()
            self.background_image = pygame.transform.scale(
                self.background_image, (self.screen_width, self.screen_height)
            )
            print("Loaded boss background image!")
        except Exception as e:
            print(f"Failed to load boss background: {e}")
            # Create fallback background
            self.background_image = pygame.Surface(
                (self.screen_width, self.screen_height)
            )
            self.background_image.fill((50, 0, 0))  # Dark red background

            # Add some details to the background
            for i in range(50):
                x = random.randint(0, self.screen_width)
                y = random.randint(0, self.screen_height)
                size = random.randint(2, 6)
                color = (random.randint(100, 200), 0, 0)  # Reddish colors
                pygame.draw.circle(self.background_image, color, (x, y), size)

        # Create player
        player_x = 100
        player_y = self.level_height - 200
        player_width = 130
        player_height = 156
        self.player = Player(player_x, player_y)
        self.player.width = player_width
        self.player.height = player_height

        # Set player health from parameter (carrying over from previous levels)
        self.player.health = player_health
        print(f"Player starting boss level with health: {self.player.health}")

        # Calculate jump power to reach approximately 40% of the screen height
        # The physics formula is: max_jump_height = (jump_power^2) / (2 * gravity)
        # So: jump_power = sqrt(2 * gravity * desired_max_jump_height)
        desired_max_jump_height = self.screen_height * 0.4
        self.player.jump_power = math.sqrt(
            2 * self.player.gravity * desired_max_jump_height
        )
        print(
            f"Player jump power set to reach ~40% of screen height: {self.player.jump_power}"
        )

        # Ensure player health doesn't exceed maximum
        if self.player.health > self.player.max_health:
            self.player.health = self.player.max_health

        # Create the boss
        self.boss = Boss(self.screen_width, self.screen_height)

        # Create platforms - just a ground platform and some platforms to stand on
        self.platforms = pygame.sprite.Group()
        self._generate_platforms()

        # Load champion belt image
        try:
            self.champ_belt_img = pygame.image.load(
                "assets/images/champ_belt.png"
            ).convert_alpha()
            self.champ_belt_img = pygame.transform.scale(
                self.champ_belt_img, (150, 100)
            )
            print("Loaded champion belt image!")
        except Exception as e:
            print(f"Error loading champion belt image: {e}")
            # Create fallback image
            self.champ_belt_img = pygame.Surface((150, 100), pygame.SRCALPHA)
            self.champ_belt_img.fill((255, 215, 0))  # Gold color
            pygame.draw.rect(
                self.champ_belt_img, (200, 150, 0), (10, 30, 130, 40), border_radius=10
            )
            font = pygame.font.SysFont("Arial", 24)
            text = font.render("CHAMPION", True, (255, 255, 255))
            self.champ_belt_img.blit(text, (25, 35))

        # Boss music
        try:
            self.boss_music = pygame.mixer.Sound("assets/sounds/boss_music.mp3")
            self.boss_music.set_volume(0.7)
            self.boss_music.play(-1)  # Loop indefinitely
            print("Boss music started playing!")
        except Exception as e:
            print(f"Failed to load boss music: {e}")
            self.boss_music = None

        # Sound effects
        try:
            self.victory_sound = pygame.mixer.Sound("assets/sounds/level_complete.wav")
        except:
            print("Warning: Victory sound not found")
            self.victory_sound = None

    def _generate_platforms(self):
        """Generate platforms for the boss level"""
        # Ground platform that spans the entire screen
        ground = Platform(
            0, self.level_height - 50, self.level_width, 50, color=(100, 50, 50)
        )
        self.platforms.add(ground)

        # Add two randomly placed small platforms
        platform_width = 100
        platform_height = 20

        # Generate positions for two platforms that aren't too close to each other
        platforms_added = 0
        attempts = 0
        min_distance = 200  # Minimum distance between platforms

        platform_positions = []

        # Keep trying until we have 2 platforms or too many attempts
        while platforms_added < 2 and attempts < 50:
            attempts += 1

            # Generate random position that's not too close to edges
            x = random.randint(platform_width, self.screen_width - platform_width)
            y = random.randint(self.screen_height // 2, self.screen_height - 150)

            # Check if it's far enough from existing platforms
            too_close = False
            for pos in platform_positions:
                distance = math.sqrt((pos[0] - x) ** 2 + (pos[1] - y) ** 2)
                if distance < min_distance:
                    too_close = True
                    break

            # If valid position, add it
            if not too_close:
                platform_positions.append((x, y))
                platforms_added += 1

        # Create the two platforms
        for pos in platform_positions:
            platform = Platform(
                pos[0]
                - platform_width // 2,  # Center the platform at the generated position
                pos[1],
                platform_width,
                platform_height,
                color=(150, 50, 50),
            )
            self.platforms.add(platform)
            print(f"Added small platform at ({pos[0]}, {pos[1]})")

    def _create_victory_sequence(self):
        """Create victory stairs and place champion belt when boss is defeated"""
        # Remove all existing platforms except the ground
        ground_platform = None
        for platform in self.platforms:
            if platform.rect.y > self.level_height - 100:  # This is likely the ground
                ground_platform = platform
                break

        # Clear platforms
        self.platforms.empty()

        # Add ground back
        if ground_platform:
            self.platforms.add(ground_platform)

        # Create victory stairs (similar to the goal stairs in regular levels)
        stair_width = 100
        stair_height = 20
        stair_x = self.screen_width // 2 - stair_width // 2
        stair_y = self.level_height - 70  # Start just above ground

        # Create 8 stairs going up
        for i in range(8):
            # Make last stair wider for the belt
            if i == 7:
                this_stair_width = stair_width * 1.5
                stair_x = self.screen_width // 2 - this_stair_width // 2
            else:
                this_stair_width = stair_width

            stair = Platform(
                stair_x,
                stair_y - (i * stair_height * 1.5),
                this_stair_width,
                stair_height,
                color=(200, 150, 50),  # Gold stairs
            )
            self.platforms.add(stair)
            self.victory_stairs.append(stair)

        # Place champion belt on top stair
        belt_x = self.screen_width // 2 - self.champ_belt_img.get_width() // 2
        belt_y = (
            stair_y - (7 * stair_height * 1.5) - self.champ_belt_img.get_height() - 10
        )
        self.champ_belt_rect = pygame.Rect(
            belt_x,
            belt_y,
            self.champ_belt_img.get_width(),
            self.champ_belt_img.get_height(),
        )
        print("Victory sequence created: stairs and champion belt ready!")

    def update(self):
        """Update level state"""
        # Update timer
        self.timer += 1

        # Handle input for player
        keys = pygame.key.get_pressed()

        # Movement controls (arrow keys)
        if keys[pygame.K_LEFT]:
            self.player.move_left()
        elif keys[pygame.K_RIGHT]:
            self.player.move_right()
        else:
            self.player.stop()

        # Jumping
        if keys[pygame.K_UP]:
            self.player.jump()

        # Shooting controls - A shoots left, D shoots right
        if keys[pygame.K_a]:  # A key for shooting left
            self.player.set_shoot_direction(False)
            self.player.shoot()
        elif keys[pygame.K_d]:  # D key for shooting right
            self.player.set_shoot_direction(True)
            self.player.shoot()

        # Update player
        player_died = self.player.update(
            self.platforms, self.enemies, self.level_width, self.level_height
        )

        if player_died:
            return False  # Player died

        # Update boss if it's still alive
        if not self.boss_defeated:
            # Update boss state and check if player defeats it
            boss_rect = self.boss.rect  # Save before updating
            self.boss.update(self.platforms, self.player)

            # Check for player bullet hits on boss
            for bullet in self.player.bullets:
                if bullet.rect.colliderect(self.boss.rect):
                    bullet.kill()  # Remove bullet
                    self.boss.take_damage(
                        1
                    )  # Each hit does just 1 damage (takes 25 shots as requested)
                    self.score += 25  # Score for hitting boss

            # Check if boss is defeated
            if self.boss.health <= 0 and not self.boss_defeated:
                self.boss_defeated = True
                print("Boss defeated! Creating victory sequence!")

                # Create stairs and place champion belt
                self._create_victory_sequence()

                # Play victory sound
                if self.victory_sound:
                    self.victory_sound.play()

        # If boss is defeated, check if player reaches the champion belt
        if self.boss_defeated and self.champ_belt_rect:
            if self.player.rect.colliderect(self.champ_belt_rect):
                self.completed = True
                return True  # Level completed

        # Always return None if the game is still in progress
        return None  # Game still in progress

    def render(self, screen):
        """Render the boss level"""
        # Draw background
        screen.blit(self.background_image, (0, 0))

        # Draw platforms
        for platform in self.platforms:
            screen.blit(platform.image, platform.rect)

        # Draw player
        screen.blit(self.player.image, self.player.rect)

        # Draw player bullets
        for bullet in self.player.bullets:
            screen.blit(bullet.image, bullet.rect)

        # Draw boss only if not defeated
        if not self.boss_defeated:
            screen.blit(self.boss.image, self.boss.rect)
            # Draw boss health bar
            self.boss.draw_health_bar(screen)
        # Draw champion belt if boss is defeated
        elif self.champ_belt_rect:
            screen.blit(self.champ_belt_img, self.champ_belt_rect)

        # Draw UI elements
        self._draw_ui(screen)

    def _draw_ui(self, screen):
        """Draw UI elements"""

        # Helper function to render text with shadow/outline for better visibility
        def render_text_with_shadow(
            text,
            font,
            color,
            position,
            shadow_color=(0, 0, 0),
            shadow_offset=2,
            bg_color=None,
        ):
            # Render shadow
            shadow_surface = font.render(text, True, shadow_color)
            shadow_position = (position[0] + shadow_offset, position[1] + shadow_offset)

            # Create text surface
            text_surface = font.render(text, True, color)
            text_width, text_height = text_surface.get_size()

            # Create background if requested
            if bg_color:
                # Add padding around text
                padding = 5
                bg_rect = pygame.Rect(
                    position[0] - padding,
                    position[1] - padding,
                    text_width + padding * 2,
                    text_height + padding * 2,
                )
                pygame.draw.rect(screen, bg_color, bg_rect, border_radius=4)

            # Draw shadow and text
            screen.blit(shadow_surface, shadow_position)
            screen.blit(text_surface, position)

            return text_surface

        # Top panel - semi-transparent background for top UI
        top_panel_height = 80
        top_panel = pygame.Surface(
            (self.screen_width, top_panel_height), pygame.SRCALPHA
        )
        top_panel.fill((0, 0, 0, 160))  # Black with 60% transparency
        screen.blit(top_panel, (0, 0))

        # Draw score with shadow
        font = pygame.font.SysFont("comicsans", 30)
        score_text = f"Score: {self.score}"
        render_text_with_shadow(
            score_text,
            font,
            (255, 255, 0),
            (20, 20),
            shadow_color=(0, 0, 0),
            shadow_offset=2,
        )

        # Draw player health bar
        health_width = 200
        health_height = 20
        health_x = self.screen_width - health_width - 20
        health_y = 20

        # Black border around health bar
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (health_x - 2, health_y - 2, health_width + 4, health_height + 4),
        )

        # Background (red)
        pygame.draw.rect(
            screen, (255, 0, 0), (health_x, health_y, health_width, health_height)
        )

        # Foreground (green) - proportional to health
        health_percent = self.player.health / self.player.max_health
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (health_x, health_y, int(health_width * health_percent), health_height),
        )

        # Health text with shadow
        health_text = f"Health: {self.player.health}"
        render_text_with_shadow(
            health_text,
            font,
            (255, 255, 0),
            (health_x, health_y + health_height + 5),
            shadow_color=(0, 0, 0),
            shadow_offset=2,
        )

    def cleanup(self):
        """Clean up resources when level is done"""
        # Stop music
        if self.boss_music:
            self.boss_music.stop()
