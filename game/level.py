import pygame
import random
import math
from .player import Player
from .platform import Platform
from .enemy import Enemy


class Level:
    def __init__(
        self, screen, level_number, environment, enemy_type, player_health=100
    ):
        self.screen = screen
        self.level_number = level_number
        self.environment = environment
        self.enemy_type = enemy_type
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # Make level much wider than the screen to allow scrolling
        self.level_width = self.screen_width * 5  # 5 screens wide
        self.level_height = self.screen_height

        # Camera position
        self.camera_x = 0

        self.score = 0
        self.completed = False
        self.timer = 0
        self.max_time = 60 * 60  # 60 seconds at 60 FPS

        # Load level background
        self.background_image = None

        # Create a default sky background for level 1 (clouds) if no custom image exists
        if level_number == 1:  # Clouds level
            # Create a sky blue gradient background
            self.background_image = pygame.Surface(
                (self.screen_width, self.screen_height)
            )

            # Draw gradient sky
            for y in range(self.screen_height):
                # Calculate sky color (lighter blue at top, darker at bottom)
                blue_val = max(135, 255 - int(y * 0.5))
                color = (135, 206, blue_val)
                pygame.draw.line(
                    self.background_image, color, (0, y), (self.screen_width, y)
                )

            # Add some static clouds to the background
            for i in range(15):
                cloud_x = random.randint(0, self.screen_width)
                cloud_y = random.randint(0, self.screen_height // 2)
                cloud_size = random.randint(30, 60)
                # Draw several overlapping white circles to create a cloud
                for offset in [
                    (0, 0),
                    (cloud_size // 2, -cloud_size // 3),
                    (-cloud_size // 2, -cloud_size // 4),
                    (0, cloud_size // 3),
                ]:
                    pygame.draw.circle(
                        self.background_image,
                        (255, 255, 255),
                        (cloud_x + offset[0], cloud_y + offset[1]),
                        cloud_size // 2,
                    )

            print("Created cloud level background")

        elif level_number == 2:  # Jungle level
            try:
                self.background_image = pygame.image.load(
                    "assets/images/level_2_background.jpg"
                ).convert()
                self.background_image = pygame.transform.scale(
                    self.background_image, (self.screen_width, self.screen_height)
                )
                print("Loaded jungle background image")
            except Exception as e:
                print(f"Failed to load jungle background: {e}")

        elif level_number == 3:  # Supermarket level
            try:
                self.background_image = pygame.image.load(
                    "assets/images/level_3_background.jpg"
                ).convert()
                self.background_image = pygame.transform.scale(
                    self.background_image, (self.screen_width, self.screen_height)
                )
                print("Loaded supermarket background image")
            except Exception as e:
                print(f"Failed to load supermarket background: {e}")

        # Create player with adjusted size for the image
        player_x = 100
        player_y = self.level_height - 200
        player_width = 130  # Increased from 100
        player_height = 156  # Increased from 120 (keeping proportions)
        self.player = Player(player_x, player_y)
        self.player.width = player_width
        self.player.height = player_height

        # Set player health from parameter (carrying over from previous level)
        self.player.health = player_health
        print(f"Player starting level with health: {self.player.health}")

        # Ensure player health doesn't exceed maximum
        if self.player.health > self.player.max_health:
            self.player.health = self.player.max_health

        # Create level goal - far to the right
        self.goal_x = self.level_width - 200
        self.goal_y = 100  # Will be positioned based on platforms later
        self.goal_width = 70 * 3  # Increased by 3x
        self.goal_height = 70 * 3  # Increased by 3x
        self.goal_rect = pygame.Rect(
            self.goal_x, self.goal_y, self.goal_width, self.goal_height
        )

        # Goal flag animation
        self.goal_animation_timer = 0

        # Load goal image if available
        try:
            self.goal_image = pygame.image.load(
                "assets/images/bottle.png"
            ).convert_alpha()
            self.goal_image = pygame.transform.scale(
                self.goal_image, (self.goal_width, self.goal_height)
            )
            print("Loaded bottle.png image as goal!")
        except:
            self.goal_image = None
            print("Failed to load bottle.png image, using placeholder")

        # Create platforms
        self.platforms = pygame.sprite.Group()
        self._generate_platforms()

        # Update goal position to be on top of a platform
        self._position_goal_on_platform()

        # Create enemies
        self.enemies = pygame.sprite.Group()
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = (
            96  # Reduced by 20% from 120 (was 2s, now 1.6s at 60 FPS)
        )
        # Track player's progression through the level to adjust spawn rate
        self.spawn_rate_adjustment = 1.0
        self.last_spawn_position_x = 0
        # Maximum number of enemies to have on screen at once
        self.max_enemies = 5
        # Flag to track if the main enemy has been spawned for this level
        self.main_enemy_spawned = False
        # Track when to spawn the main enemy (after player progresses a bit into the level)
        self.main_enemy_spawn_progress = random.uniform(
            0.3, 0.7
        )  # Spawn between 30-70% of level progress

        # Background color based on environment (used as fallback)
        self.bg_colors = {
            "clouds": (135, 206, 235),  # Sky blue
            "jungle": (34, 139, 34),  # Forest green
            "supermarket": (220, 220, 220),  # Light gray
        }

        # Level completion requirements - now based on reaching the goal
        self.enemies_to_defeat = 0  # No longer used as completion requirement

        # Sound effects
        try:
            self.level_complete_sound = pygame.mixer.Sound(
                "assets/sounds/level_complete.wav"
            )
        except:
            print("Warning: Level complete sound not found")
            self.level_complete_sound = None

    def _position_goal_on_platform(self):
        """Places the goal bottle on top of the custom platform at the end of the level"""
        # Create a staircase leading up to the bottle at the end of the level
        self._create_goal_staircase()

        # Position the goal on the special bottle platform we created
        if hasattr(self, "flag_platform"):
            # Center the bottle on the platform
            self.goal_x = (
                self.flag_platform.rect.x
                + (self.flag_platform.rect.width // 2)
                - (self.goal_width // 2)
            )
            self.goal_y = (
                self.flag_platform.rect.y - self.goal_height - 10
            )  # Add extra space between bottle and platform

            print(
                f"Goal bottle positioned at ({self.goal_x}, {self.goal_y}) on platform"
            )
        else:
            # Fallback: Find a suitable platform near the end of the level
            right_platforms = []
            for platform in self.platforms:
                # Look for platforms in the rightmost area of the level
                if platform.rect.right > (self.level_width - 300):
                    right_platforms.append(platform)

            if right_platforms:
                # Use the platform closest to the ground
                lowest_platform = max(right_platforms, key=lambda p: p.rect.y)

                # Position the goal on this platform
                self.goal_x = (
                    lowest_platform.rect.x
                    + (lowest_platform.rect.width // 2)
                    - (self.goal_width // 2)
                )
                self.goal_y = lowest_platform.rect.y - self.goal_height - 5
                print(
                    f"Fallback: Goal bottle positioned at ({self.goal_x}, {self.goal_y})"
                )

        # Update the goal rectangle
        self.goal_rect = pygame.Rect(
            self.goal_x, self.goal_y, self.goal_width, self.goal_height
        )

    def _create_goal_staircase(self):
        """Create a staircase of platforms leading to the goal bottle"""
        # Clear any existing platforms near the end of the level to make room for our staircase
        platforms_to_remove = []
        for platform in self.platforms:
            # Remove platforms in the rightmost area where we'll build the staircase
            if platform.rect.x > (self.level_width - 600) and platform.rect.y < (
                self.level_height - 60
            ):
                platforms_to_remove.append(platform)

        for platform in platforms_to_remove:
            self.platforms.remove(platform)

        # Define staircase parameters
        step_width = 120  # Width of each platform step
        step_height = 20  # Height of each platform step
        num_steps = 6  # Number of steps in the staircase - reduced to fit better

        # Starting position for the staircase - moved left to ensure full visibility
        start_x = self.level_width - 550  # More room on the right side
        base_y = self.level_height - 150

        # Calculate step spacing that's easy to navigate
        # Player jump height calculation for reference
        max_jump_height = (self.player.jump_power**2) / (2 * self.player.gravity)
        step_x_spacing = 55  # Horizontal distance between steps (slightly reduced)
        step_y_spacing = 45  # Vertical distance between steps

        # Colors based on environment
        if self.environment == "clouds":
            color = (255, 255, 255)
        elif self.environment == "jungle":
            color = (101, 67, 33)
        elif self.environment == "supermarket":
            color = (210, 180, 140)
        else:
            color = (100, 100, 100)

        # Create the staircase platforms - keep track of the last step position
        last_step_x = 0
        last_step_y = 0
        last_step_platform = None

        for i in range(num_steps):
            # Each step is higher and further to the right
            x = start_x + (i * step_x_spacing)
            y = base_y - (i * step_y_spacing)
            last_step_x = x
            last_step_y = y

            # Create the platform - make the last step slightly wider and with a distinctive color
            if i == num_steps - 1:  # This is the last step
                # Make the last step wider and with a distinctive color
                last_step_width = step_width * 1.5  # 50% wider

                # Choose a distinctive color for the last step based on environment
                if self.environment == "clouds":
                    last_step_color = (255, 200, 100)  # Orange-ish for contrast
                elif self.environment == "jungle":
                    last_step_color = (200, 150, 50)  # Golden brown
                elif self.environment == "supermarket":
                    last_step_color = (240, 200, 80)  # Yellow-ish
                else:
                    last_step_color = (180, 180, 80)  # Yellow-gray

                # Create the final step with distinctive appearance
                platform = Platform(
                    x, y, last_step_width, step_height * 1.5, color=last_step_color
                )
                last_step_platform = platform
            else:
                # Regular step
                platform = Platform(x, y, step_width, step_height, color=color)

            self.platforms.add(platform)

        # Store the last platform for easy reference when positioning the bottle
        self.flag_platform = last_step_platform

        print(f"Last stair step position: ({last_step_x}, {last_step_y})")
        print(
            f"Last step dimensions: {last_step_platform.rect.width}x{last_step_platform.rect.height}"
        )
        print(f"Level width: {self.level_width}, Level height: {self.level_height}")
        print(
            f"Visible range: camera can scroll to {self.level_width - self.screen_width}"
        )

    def _generate_platforms(self):
        """Generate platforms for a long side-scrolling level"""
        # Create a continuous ground platform, but we'll add holes later
        ground = Platform(0, self.level_height - 50, self.level_width, 50)
        self.platforms.add(ground)

        # Create deadly holes in the ground (only for non-boss levels)
        self.deadly_holes = []
        self._create_deadly_holes()

        # Player jump height calculation
        max_jump_height = (self.player.jump_power**2) / (2 * self.player.gravity)
        # Leave some margin for error
        safe_jump_height = max_jump_height * 0.8

        # Maximum safe horizontal jump distance (approximation)
        max_jump_distance = (
            self.player.speed * (2 * self.player.jump_power / self.player.gravity) * 0.8
        )

        # Platform parameters - wider with bigger gaps
        min_width = 120
        max_width = 250
        platform_height = 20

        if self.level_number == 1:  # Cloud level - long path from left to right
            # We'll create platforms all across the level width
            x_pos = 250  # Start a bit after player's initial position

            # Create a variety of platform heights to make an interesting path
            height_pattern = [
                self.level_height - 180,  # Lower
                self.level_height - 250,  # Medium
                self.level_height - 320,  # Higher
                self.level_height - 220,  # Medium-low
                self.level_height - 150,  # Very low
            ]

            # Create platforms across the whole level
            while x_pos < self.level_width - 400:
                # Select a height from our pattern
                pattern_index = int((x_pos / 500) % len(height_pattern))
                base_y = height_pattern[pattern_index]

                # Add some variation
                y_pos = base_y + random.randint(-30, 30)

                # Vary the platform width
                width = random.randint(min_width, max_width)

                # Create the platform
                platform = Platform(
                    x_pos, y_pos, width, platform_height, color=(255, 255, 255)
                )
                self.platforms.add(platform)

                # Create some optional higher platforms
                if random.random() > 0.6:  # 40% chance for a higher platform
                    higher_y = y_pos - random.randint(100, int(safe_jump_height * 0.9))
                    higher_width = random.randint(min_width // 2, min_width)
                    higher_x = x_pos + (width - higher_width) // 2
                    higher_platform = Platform(
                        higher_x,
                        higher_y,
                        higher_width,
                        platform_height,
                        color=(255, 255, 255),
                    )
                    self.platforms.add(higher_platform)

                # Move right with a challenging but possible gap
                jump_distance = random.uniform(
                    max_jump_distance * 0.6, max_jump_distance * 0.9
                )
                x_pos += width + jump_distance

            # Add final platform near right edge for the goal
            final_width = 200
            final_platform = Platform(
                self.level_width - final_width - 100,
                self.level_height - 250,
                final_width,
                platform_height,
                color=(255, 255, 255),
            )
            self.platforms.add(final_platform)

        elif self.level_number == 2:  # Jungle level - long path with branches
            # Generate a path that goes across the entire level
            x_pos = 200

            # Create platforms that zigzag across the level
            base_heights = [
                self.level_height - 180,  # Lower
                self.level_height - 280,  # Medium
                self.level_height - 380,  # Higher
                self.level_height - 320,  # Medium-high
            ]

            # Generate platforms until we reach near the end
            while x_pos < self.level_width - 300:
                # Select height in a pattern
                height_index = int((x_pos / 400) % len(base_heights))
                y_pos = base_heights[height_index] + random.randint(-20, 20)

                # Vary platform width
                width = random.randint(min_width, max_width)

                # Create the platform
                platform = Platform(
                    x_pos, y_pos, width, platform_height, color=(101, 67, 33)
                )
                self.platforms.add(platform)

                # Sometimes add a second platform nearby (branch)
                if random.random() > 0.7:  # 30% chance
                    branch_x = x_pos + random.randint(-50, 50)
                    branch_y = y_pos + random.choice([-80, 80])  # Either above or below
                    branch_width = random.randint(min_width // 2, min_width)
                    branch_platform = Platform(
                        branch_x,
                        branch_y,
                        branch_width,
                        platform_height,
                        color=(101, 67, 33),
                    )
                    self.platforms.add(branch_platform)

                # Move right with a variable gap
                jump_distance = random.uniform(
                    max_jump_distance * 0.6, max_jump_distance * 0.85
                )
                x_pos += width + jump_distance

            # Ensure final platform at the right edge
            final_platform = Platform(
                self.level_width - 300,
                self.level_height - 250,
                200,
                platform_height,
                color=(101, 67, 33),
            )
            self.platforms.add(final_platform)

        elif self.level_number == 3:  # Supermarket level - long aisles with shelves
            # Create a path through "supermarket aisles"
            x_pos = 200

            # Alternate between low and higher platforms
            height_pattern = [
                self.level_height - 180,  # Low shelf
                self.level_height - 180,  # Low shelf
                self.level_height - 320,  # High shelf
                self.level_height - 230,  # Medium shelf
            ]

            # Generate platforms all across the level
            while x_pos < self.level_width - 300:
                # Select height in a pattern
                height_index = int((x_pos / 400) % len(height_pattern))
                y_pos = height_pattern[height_index] + random.randint(-10, 10)

                # Create varying width platforms
                width = random.randint(min_width, max_width)

                # Create the platform
                platform = Platform(
                    x_pos, y_pos, width, platform_height, color=(210, 180, 140)
                )
                self.platforms.add(platform)

                # Sometimes add checkout counters or display stands
                if random.random() > 0.7:
                    counter_width = random.randint(60, 120)
                    counter_x = x_pos + random.randint(0, width - counter_width)
                    counter_y = y_pos - random.randint(60, 120)
                    counter = Platform(
                        counter_x,
                        counter_y,
                        counter_width,
                        platform_height,
                        color=(180, 180, 180),
                    )
                    self.platforms.add(counter)

                # Move to next position
                jump_distance = random.uniform(
                    max_jump_distance * 0.6, max_jump_distance * 0.85
                )
                x_pos += width + jump_distance

            # Final platform for the goal
            final_platform = Platform(
                self.level_width - 300,
                self.level_height - 300,
                200,
                platform_height,
                color=(210, 180, 140),
            )
            self.platforms.add(final_platform)

    def _create_deadly_holes(self):
        """Create two deadly holes in the ground platform"""
        ground_y = self.level_height - 50  # Ground platform Y position
        hole_width = 120  # Width of each deadly hole

        # Store the original ground platform
        original_ground = None
        for platform in self.platforms:
            if platform.rect.y == ground_y and platform.rect.width == self.level_width:
                original_ground = platform
                self.platforms.remove(platform)
                break

        if not original_ground:
            print("Error: Couldn't find ground platform to add holes")
            return

        # Determine hole positions - avoid placing them too close to start, goal, or each other
        level_division = self.level_width / 5  # Divide level into 5 sections

        # First hole in the 2nd section (20-40% of level width)
        hole1_x = random.randint(int(level_division * 1.2), int(level_division * 1.8))

        # Second hole in the 4th section (60-80% of level width)
        hole2_x = random.randint(int(level_division * 3.2), int(level_division * 3.8))

        # Store hole rectangles for collision detection
        self.deadly_holes = [
            pygame.Rect(hole1_x, ground_y, hole_width, 100),  # Make hole deep
            pygame.Rect(hole2_x, ground_y, hole_width, 100),
        ]

        # Create three ground sections instead of one continuous ground
        # 1. Left section (from start to hole1)
        if hole1_x > 0:
            left_ground = Platform(0, ground_y, hole1_x, 50)
            self.platforms.add(left_ground)

        # 2. Middle section (between hole1 and hole2)
        middle_x = hole1_x + hole_width
        middle_width = hole2_x - middle_x
        if middle_width > 0:
            middle_ground = Platform(middle_x, ground_y, middle_width, 50)
            self.platforms.add(middle_ground)

        # 3. Right section (from hole2 to end)
        right_x = hole2_x + hole_width
        right_width = self.level_width - right_x
        if right_width > 0:
            right_ground = Platform(right_x, ground_y, right_width, 50)
            self.platforms.add(right_ground)

        print(f"Created deadly holes at x positions: {hole1_x} and {hole2_x}")

    def _spawn_enemy(self):
        """Spawn an enemy at a random location visible on screen"""
        # Choose a platform to spawn on (not the ground) that's visible on screen
        visible_platforms = [
            p
            for p in self.platforms
            if p.rect.y < self.level_height - 60
            and p.rect.right > self.camera_x
            and p.rect.left < self.camera_x + self.screen_width
        ]

        if not visible_platforms:
            return

        # Sort platforms by width to find the largest one for the main enemy
        sorted_platforms = sorted(
            visible_platforms, key=lambda p: p.rect.width, reverse=True
        )

        # Determine if this should be a main enemy
        # Only spawn a main enemy if we haven't spawned one yet
        # AND player has progressed far enough into the level
        level_progress = min(1.0, max(0.0, self.player.rect.x / self.level_width))

        is_main_enemy = False
        if (
            not self.main_enemy_spawned
            and level_progress >= self.main_enemy_spawn_progress
        ):
            is_main_enemy = True
            # Use the largest platform available
            platform = sorted_platforms[0]
            # Mark that we've spawned the main enemy
            self.main_enemy_spawned = True
            print(f"SPAWNING MAIN ENEMY at {level_progress * 100:.1f}% level progress")
        else:
            # Regular enemy - choose a random platform
            platform = random.choice(visible_platforms)

        # Make sure the platform is large enough for a main enemy
        if is_main_enemy:
            min_platform_width = 180  # 2x normal enemy width
            if platform.rect.width < min_platform_width:
                # Platform too small, wait for a better opportunity
                return

        # Enemy size based on type - increased by 30%
        if self.enemy_type == "vegetables":
            width, height = 91, 91  # Was 70x70 originally
        elif self.enemy_type == "bananas":
            width, height = 78, 104  # Was 60x80 originally
        elif self.enemy_type == "grandmas":
            width, height = 91, 117  # Was 70x90 originally
        else:
            width, height = 78, 78  # Was 60x60 originally

        # Double size for main enemies
        if is_main_enemy:
            width *= 2
            height *= 2

        # Check if platform is wide enough for enemy
        if platform.rect.width <= width:
            # Platform too small, skip spawning
            return

        # Spawn on the platform - ensure valid range for randint
        left_pos = platform.rect.left
        right_pos = platform.rect.right - width

        # Additional safety check to make sure right_pos > left_pos
        if right_pos <= left_pos:
            x = left_pos
        else:
            x = random.randint(left_pos, right_pos)

        y = platform.rect.top - height  # Place on top of platform

        # Remember where we last spawned an enemy
        self.last_spawn_position_x = x

        # Create enemy based on level
        enemy = Enemy(x, y, self.enemy_type, self.level_number, is_main=is_main_enemy)
        # Adjust size
        enemy.width = width
        enemy.height = height
        self.enemies.add(enemy)

        # Log the spawn
        if is_main_enemy:
            print(f"Spawned MAIN {self.enemy_type} enemy at ({x}, {y})")
        else:
            print(f"Spawned regular {self.enemy_type} enemy at ({x}, {y})")

    def update(self):
        """Update level state"""
        # Update timer
        self.timer += 1
        self.goal_animation_timer += 1

        # Calculate player's progression through the level (0.0 to 1.0)
        level_progress = min(1.0, max(0.0, self.player.rect.x / self.level_width))

        # Adjust spawn rate based on player's progression
        # At the start, normal rate (1.0)
        # In the middle, slightly increased rate (0.8)
        # Near the end, significantly increased rate (0.6)
        if level_progress < 0.3:
            self.spawn_rate_adjustment = 1.0
        elif level_progress < 0.7:
            self.spawn_rate_adjustment = 0.8
        else:
            self.spawn_rate_adjustment = 0.6

        # Adjust max enemies based on progression
        if level_progress < 0.3:
            self.max_enemies = 4
        elif level_progress < 0.7:
            self.max_enemies = 5
        else:
            self.max_enemies = 6

        # Apply spawn rate adjustment
        adjusted_spawn_delay = int(self.enemy_spawn_delay * self.spawn_rate_adjustment)

        # Handle enemy spawning
        self.enemy_spawn_timer += 1
        if (
            self.enemy_spawn_timer >= adjusted_spawn_delay
            and len(self.enemies) < self.max_enemies
        ):
            self._spawn_enemy()
            self.enemy_spawn_timer = 0

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

        # Shooting controls
        if keys[pygame.K_a]:  # A key for shooting left
            self.player.set_shoot_direction(False)
        elif keys[pygame.K_d]:  # D key for shooting right
            self.player.set_shoot_direction(True)

        # Shoot when space is pressed
        if keys[pygame.K_SPACE]:
            self.player.shoot()

        # Update player
        player_died = self.player.update(
            self.platforms, self.enemies, self.level_width, self.level_height
        )

        if player_died:
            return False  # Player died - return False

        # Check if player has fallen into a deadly hole
        for hole in self.deadly_holes:
            if self.player.rect.colliderect(hole):
                print("Player fell into a deadly hole!")
                # Kill the player
                self.player.health = 0
                return False  # Player died - return False

        # Update camera position to follow player
        self._update_camera()

        # Update enemies
        for enemy in self.enemies:
            enemy.update(
                self.platforms, self.player, self.level_width, self.level_height
            )

            # Check if enemy is defeated
            if enemy.health <= 0 and enemy.alive():
                enemy.kill()
                self.score += 100

        # Check if player reached the goal
        if self.player.rect.colliderect(self.goal_rect):
            self.completed = True
            if self.level_complete_sound:
                self.level_complete_sound.play()

            return True  # Level completed - return True

        # Update score from player's score
        self.score += self.player.score
        self.player.score = 0

        # If we reach here, the game is still ongoing
        return None  # Game still in progress

    def _update_camera(self):
        """Update the camera position to follow the player"""
        # Center the camera on the player horizontally
        target_x = self.player.rect.centerx - (self.screen_width // 2)

        # Clamp the camera position to the level boundaries
        target_x = max(0, min(target_x, self.level_width - self.screen_width))

        # Smooth camera movement
        self.camera_x += (target_x - self.camera_x) * 0.1

    def _get_screen_position(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        return world_x - self.camera_x, world_y

    def render(self, screen):
        """Render the level with camera offset"""
        # Clear screen
        screen.fill((0, 0, 0))

        # Draw background or use background image
        if self.background_image:
            # Create a parallax effect by moving background slower than camera
            parallax_factor = 0.5

            # Calculate how many background images we need to cover the screen
            # based on camera position
            bg_x = -(self.camera_x * parallax_factor)
            first_bg_x = bg_x % self.screen_width - self.screen_width

            # Draw multiple copies of the background to ensure full coverage
            for i in range(4):  # Draw up to 4 backgrounds to ensure full coverage
                x_position = first_bg_x + (i * self.screen_width)
                if x_position < self.screen_width:  # Only draw if it would be visible
                    screen.blit(self.background_image, (x_position, 0))
        else:
            screen.fill(self.bg_colors.get(self.environment, (0, 0, 0)))

        # Draw environmental details based on level - only if no background image
        if not self.background_image:
            self._draw_environment(screen)

        # Draw platforms that are visible on screen
        for platform in self.platforms:
            # Convert world coordinates to screen coordinates
            screen_x, screen_y = self._get_screen_position(
                platform.rect.x, platform.rect.y
            )

            # Only draw platforms that are visible on screen
            if (
                -platform.rect.width <= screen_x <= self.screen_width
                and -platform.rect.height <= screen_y <= self.screen_height
            ):
                # Create a temporary rect for drawing
                screen_rect = platform.rect.copy()
                screen_rect.x = screen_x
                screen_rect.y = screen_y

                # Draw the platform
                screen.blit(platform.image, screen_rect)

        # Draw holes in the ground (like deep pits)
        for hole in self.deadly_holes:
            hole_screen_x, hole_screen_y = self._get_screen_position(hole.x, hole.y)

            # Only draw if visible on screen
            if (
                -hole.width <= hole_screen_x <= self.screen_width
                and -hole.height <= hole_screen_y <= self.screen_height
            ):
                # Draw a dark pit as the hole
                hole_color = (10, 10, 10)  # Very dark (almost black) color

                # Draw the main hole
                pygame.draw.rect(
                    screen,
                    hole_color,
                    pygame.Rect(hole_screen_x, hole_screen_y, hole.width, hole.height),
                )

                # Add some depth with a gradient
                for i in range(3):
                    depth = 5 + (i * 3)  # Increasing line thickness
                    line_y = hole_screen_y + (i * 10)
                    line_color = (20 + (i * 10), 20 + (i * 5), 20)  # Gradually lighter
                    pygame.draw.line(
                        screen,
                        line_color,
                        (hole_screen_x, line_y),
                        (hole_screen_x + hole.width, line_y),
                        depth,
                    )

        # Draw goal flag if visible on screen
        goal_screen_x, goal_screen_y = self._get_screen_position(
            self.goal_x, self.goal_y
        )
        if (
            -self.goal_width <= goal_screen_x <= self.screen_width
            and -self.goal_height <= goal_screen_y <= self.screen_height
        ):
            self._draw_goal(screen, goal_screen_x, goal_screen_y)

        # Draw enemies that are visible on screen
        for enemy in self.enemies:
            enemy_screen_x, enemy_screen_y = self._get_screen_position(
                enemy.rect.x, enemy.rect.y
            )

            # Only draw enemies that are visible on screen
            if (
                -enemy.rect.width <= enemy_screen_x <= self.screen_width
                and -enemy.rect.height <= enemy_screen_y <= self.screen_height
            ):
                # Create a temporary rect for drawing
                screen_rect = enemy.rect.copy()
                screen_rect.x = enemy_screen_x
                screen_rect.y = enemy_screen_y

                # Draw the enemy with health bar
                screen.blit(enemy.image, screen_rect)

                # Draw health bar
                health_width = 40
                health_height = 4
                health_x = enemy_screen_x + (enemy.width - health_width) // 2
                health_y = enemy_screen_y - 8

                # Background (red)
                pygame.draw.rect(
                    screen,
                    (255, 0, 0),
                    (health_x, health_y, health_width, health_height),
                )

                # Foreground (green) - proportional to health
                max_health = 50 + (enemy.level * 25)
                if hasattr(enemy, "is_main") and enemy.is_main:
                    max_health *= 2
                health_percent = max(0, enemy.health / max_health)
                pygame.draw.rect(
                    screen,
                    (0, 255, 0),
                    (
                        health_x,
                        health_y,
                        int(health_width * health_percent),
                        health_height,
                    ),
                )

                # For main enemies, draw their projectiles if they have any
                if (
                    hasattr(enemy, "is_main")
                    and enemy.is_main
                    and hasattr(enemy, "projectiles")
                ):
                    for projectile in enemy.projectiles:
                        proj_screen_x, proj_screen_y = self._get_screen_position(
                            projectile.rect.x, projectile.rect.y
                        )

                        # Only draw projectiles visible on screen
                        if (
                            -projectile.rect.width <= proj_screen_x <= self.screen_width
                            and -projectile.rect.height
                            <= proj_screen_y
                            <= self.screen_height
                        ):
                            # Create temporary rect for drawing
                            proj_screen_rect = projectile.rect.copy()
                            proj_screen_rect.x = proj_screen_x
                            proj_screen_rect.y = proj_screen_y

                            # Draw the projectile
                            screen.blit(projectile.image, proj_screen_rect)

        # Draw player adjusted for camera
        player_screen_x, player_screen_y = self._get_screen_position(
            self.player.rect.x, self.player.rect.y
        )
        screen_rect = self.player.rect.copy()
        screen_rect.x = player_screen_x
        screen_rect.y = player_screen_y
        screen.blit(self.player.image, screen_rect)

        # Draw player bullets adjusted for camera
        for bullet in self.player.bullets:
            bullet_screen_x, bullet_screen_y = self._get_screen_position(
                bullet.rect.x, bullet.rect.y
            )

            # Only draw bullets that are visible on screen
            if (
                -bullet.rect.width <= bullet_screen_x <= self.screen_width
                and -bullet.rect.height <= bullet_screen_y <= self.screen_height
            ):
                screen_rect = bullet.rect.copy()
                screen_rect.x = bullet_screen_x
                screen_rect.y = bullet_screen_y
                screen.blit(bullet.image, screen_rect)

        # Draw player health bar
        health_width = 50
        health_height = 5
        health_x = player_screen_x + (self.player.width - health_width) // 2
        health_y = player_screen_y - 10

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

        # Draw UI (always positioned relative to screen, not level)
        self._draw_ui(screen)

    def _draw_goal(self, screen, x, y):
        """Draw the goal bottle with animation at the given screen position"""
        if self.goal_image:
            # Simple bobbing animation
            y_offset = math.sin(self.goal_animation_timer / 10) * 5
            screen.blit(self.goal_image, (x, y + y_offset))
        else:
            # Draw placeholder bottle - scaled up to match the larger size
            bottle_color = (100, 200, 255)  # Blue bottle
            cap_color = (50, 100, 200)  # Darker blue cap

            # Bottle base - large rectangle with rounded corners
            bottle_rect = pygame.Rect(x, y + 30, self.goal_width, self.goal_height - 40)
            pygame.draw.rect(screen, bottle_color, bottle_rect, border_radius=20)

            # Bottle neck - narrower at the top
            neck_width = self.goal_width // 3
            neck_start = x + (self.goal_width - neck_width) // 2
            pygame.draw.rect(screen, bottle_color, (neck_start, y + 15, neck_width, 20))

            # Bottle cap
            cap_width = self.goal_width // 2
            cap_start = x + (self.goal_width - cap_width) // 2
            pygame.draw.rect(
                screen, cap_color, (cap_start, y, cap_width, 20), border_radius=5
            )

            # Label text "GOAL"
            font = pygame.font.SysFont("Arial", 30)
            text = font.render("GOAL", True, (255, 255, 255))
            text_rect = text.get_rect(
                center=(x + self.goal_width // 2, y + self.goal_height // 2)
            )
            screen.blit(text, text_rect)

    def _draw_environment(self, screen):
        """Draw environment-specific details with camera offset"""
        if self.environment == "clouds":
            # Draw extra clouds
            for i in range(10):
                # Clouds move at different speeds for a parallax effect
                cloud_x = (i * 200 + self.timer // 5) % (self.level_width + 200) - 100
                cloud_y = 100 + (i % 3) * 100

                # Convert to screen coordinates
                screen_x, screen_y = self._get_screen_position(cloud_x, cloud_y)

                # Only draw clouds that are visible on screen
                if (
                    -200 <= screen_x <= self.screen_width
                    and -100 <= screen_y <= self.screen_height
                ):
                    # Cloud consists of a few overlapping circles
                    for offset in [(0, 0), (20, -10), (-20, -10), (0, 10)]:
                        pygame.draw.circle(
                            screen,
                            (255, 255, 255),
                            (screen_x + offset[0], screen_y + offset[1]),
                            40,
                        )

        elif self.environment == "jungle":
            # Draw tree trunks and vines (visible portion only)
            visible_range = range(
                max(0, int(self.camera_x // 250) - 1),
                min(
                    int((self.camera_x + self.screen_width) // 250) + 2,
                    int(self.level_width // 250) + 1,
                ),
            )

            for i in visible_range:
                x = i * 250
                screen_x, _ = self._get_screen_position(x, 0)

                # Draw visible tree trunk
                pygame.draw.rect(
                    screen, (101, 67, 33), (screen_x, 0, 60, self.level_height)
                )

                # Vines with screen position adjustment
                for j in range(3):
                    vine_x = x + 30 + (j * 10)
                    screen_vine_x, _ = self._get_screen_position(vine_x, 0)

                    # Calculate vine curve with an offset based on time
                    end_x = vine_x + 80 * math.sin(self.timer / 100 + j)
                    screen_end_x, _ = self._get_screen_position(
                        end_x, self.level_height
                    )

                    pygame.draw.line(
                        screen,
                        (50, 205, 50),
                        (screen_vine_x, 0),
                        (screen_end_x, self.level_height),
                        3,
                    )

        elif self.environment == "supermarket":
            # Draw shop shelves and products
            visible_range = range(
                max(0, int(self.camera_x // 300) - 1),
                min(
                    int((self.camera_x + self.screen_width) // 300) + 2,
                    int(self.level_width // 300) + 1,
                ),
            )

            for i in visible_range:
                x = i * 300
                screen_x, _ = self._get_screen_position(x, 0)

                # Shelf structure
                pygame.draw.rect(
                    screen,
                    (169, 169, 169),
                    (screen_x, 50, 250, self.level_height - 100),
                )

                # Draw items on shelves
                for j in range(5):
                    for k in range(3):
                        item_x = x + 20 + (j * 40)
                        item_y = 100 + (k * 150)

                        # Convert to screen coordinates
                        screen_item_x, screen_item_y = self._get_screen_position(
                            item_x, item_y
                        )

                        # Only draw items that are visible on screen
                        if (
                            -30 <= screen_item_x <= self.screen_width
                            and -40 <= screen_item_y <= self.screen_height
                        ):
                            # Random item colors
                            color = [
                                (255, 0, 0),
                                (0, 255, 0),
                                (0, 0, 255),
                                (255, 255, 0),
                                (255, 0, 255),
                            ][random.randint(0, 4)]
                            pygame.draw.rect(
                                screen, color, (screen_item_x, screen_item_y, 30, 40)
                            )

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

        # Draw health bar background with border
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

        # Draw level info with shadow
        level_text = f"Level {self.level_number}: {self.environment.title()}"
        text_width = font.size(level_text)[0]
        # Position the title above the top panel to ensure it's above the flag bar
        text_pos = (self.screen_width // 2 - text_width // 2, 10)
        render_text_with_shadow(
            level_text,
            font,
            (255, 255, 0),
            text_pos,
            shadow_color=(0, 0, 0),
            shadow_offset=2,
            bg_color=(0, 0, 0, 160),  # Add semi-transparent background
        )

        # Draw mini-map to show progress through level
        map_width = 200
        map_height = 10
        map_x = self.screen_width // 2 - map_width // 2
        map_y = 50

        # Black border around mini-map
        pygame.draw.rect(
            screen, (0, 0, 0), (map_x - 2, map_y - 2, map_width + 4, map_height + 4)
        )

        # Background (gray)
        pygame.draw.rect(screen, (100, 100, 100), (map_x, map_y, map_width, map_height))

        # Player position indicator
        player_progress = min(1.0, max(0.0, self.player.rect.x / self.level_width))
        player_map_x = map_x + int(player_progress * map_width) - 3
        pygame.draw.rect(
            screen, (255, 255, 255), (player_map_x, map_y - 2, 6, map_height + 4)
        )

        # Goal position indicator
        goal_progress = min(1.0, max(0.0, self.goal_x / self.level_width))
        goal_map_x = map_x + int(goal_progress * map_width) - 3
        pygame.draw.rect(
            screen, (255, 215, 0), (goal_map_x, map_y - 2, 6, map_height + 4)
        )

        # Don't draw objective text - removed as requested

        # Bottom UI with controls info in a semi-transparent background panel
        small_font = pygame.font.SysFont("comicsans", 20)

        # Create a semi-transparent background panel
        panel_height = 70
        panel_surface = pygame.Surface(
            (self.screen_width, panel_height), pygame.SRCALPHA
        )
        panel_surface.fill((0, 0, 0, 160))  # Black with 60% transparency
        screen.blit(panel_surface, (0, self.screen_height - panel_height))

        # Draw control texts with shadows - spaced more evenly
        control_y_start = self.screen_height - panel_height + 10
        line_height = 25

        # Left side controls
        music_text = "Press M to toggle music"
        render_text_with_shadow(
            music_text, small_font, (200, 200, 255), (20, control_y_start)
        )

        shooting_text = "A/D to aim ← →, SPACE to shoot"
        render_text_with_shadow(
            shooting_text,
            small_font,
            (255, 255, 100),
            (20, control_y_start + line_height),
        )

        # Right side controls
        movement_text = "Arrow keys to move and jump"
        movement_text_width = small_font.size(movement_text)[0]
        render_text_with_shadow(
            movement_text,
            small_font,
            (255, 200, 200),
            (self.screen_width - movement_text_width - 20, control_y_start),
        )
