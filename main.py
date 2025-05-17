import pygame
import sys
import os
import math
from game.player import Player
from game.level import Level
from game.menu import Menu
from game.boss_level import BossLevel

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
TITLE = "Muscle Baby Mayhem"
FPS = 60

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
LEVEL_COMPLETE = 3
PLAYER_DIED = 4  # New state for player death
BOSS_LEVEL = 5  # New state for boss level


# Helper function to render text with shadow and optional background
def render_text_with_shadow(
    screen,
    text,
    font,
    color,
    position,
    shadow_color=(0, 0, 0),
    shadow_offset=2,
    bg_color=None,
):
    # Create text surface
    text_surface = font.render(text, True, color)
    text_width, text_height = text_surface.get_size()

    # Create background if requested
    if bg_color:
        # Add padding around text
        padding = 10
        bg_rect = pygame.Rect(
            position[0] - padding,
            position[1] - padding,
            text_width + padding * 2,
            text_height + padding * 2,
        )
        if isinstance(bg_color, tuple) and len(bg_color) == 4:
            # Semi-transparent background
            bg_surface = pygame.Surface(
                (bg_rect.width, bg_rect.height), pygame.SRCALPHA
            )
            bg_surface.fill(bg_color)
            screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
        else:
            # Solid background
            pygame.draw.rect(screen, bg_color, bg_rect, border_radius=5)

    # Render shadow
    shadow_surface = font.render(text, True, shadow_color)
    shadow_position = (position[0] + shadow_offset, position[1] + shadow_offset)
    screen.blit(shadow_surface, shadow_position)

    # Render main text
    screen.blit(text_surface, position)

    return text_surface


class Game:
    def __init__(self):
        self.state = MENU
        self.current_level = 1
        self.max_levels = 3  # Regular levels, boss level is separate
        self.level = None
        self.boss_level = None  # For the boss level
        self.menu = Menu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.score = 0
        self.player_health = 500  # Store player health at game level

        # Death messages based on level
        self.death_messages = {
            1: [
                "Defeated by vegetables? That's not very muscly of you!",
                "Baby down! Those carrots were tougher than they looked!",
                "Looks like someone needs to eat more vegetables, not fight them!",
                "Whoops! You fell into a hole in the clouds! Gravity wins again!",
                "That's one small step for baby, one giant fall through the clouds!",
            ],
            2: [
                "Slipped on a banana peel? Classic!",
                "That's bananas! You got peeled!",
                "Looks like those bananas split you instead!",
                "You found the quicksand pit in the jungle! Not the treasure you were hoping for!",
                "Tarzan would've swung over that hole! Try again, jungle baby!",
            ],
            3: [
                "Grandma power too strong! Those knitting needles are lethal!",
                "You've been baked into a cookie by grandma!",
                "Beaten by the blue rinse brigade!",
                "Watch out for that broken tile in aisle 5! Store liability incoming!",
                "You fell into the discount bin! Everything must go... including you!",
            ],
        }
        # To store the selected death message
        self.current_death_message = ""

        # Sound for death
        try:
            self.death_sound = pygame.mixer.Sound("assets/sounds/hit.wav")
        except:
            self.death_sound = None

        # Background music
        try:
            pygame.mixer.music.load("assets/sounds/bg_music.mp3")
            pygame.mixer.music.set_volume(0.5)  # 50% volume
            pygame.mixer.music.play(-1)  # Loop indefinitely
            self.music_playing = True
            print("Background music loaded and playing")
        except Exception as e:
            print(f"Error loading background music: {e}")
            self.music_playing = False

    def start_level(self, level_number):
        """Start a new level"""
        global screen
        self.current_level = level_number

        # Check if this is the boss level
        if level_number > self.max_levels:
            # Create boss level with current health
            self.boss_level = BossLevel(screen, player_health=self.player_health)
            self.state = BOSS_LEVEL

            # Stop regular music if it's playing
            if hasattr(self, "music_playing") and self.music_playing:
                pygame.mixer.music.pause()

            print(f"Starting BOSS level! Prepare for the final battle!")
            return

        # Regular levels
        # Level environments and enemies
        environments = {1: "clouds", 2: "jungle", 3: "supermarket"}

        enemies = {1: "vegetables", 2: "bananas", 3: "grandmas"}

        # Level-specific messages
        level_messages = {
            1: "Time to blast those nasty veggies out of the clouds!",
            2: "Those bananas think they're so cool in the jungle. Show them who's boss!",
            3: "Grandmas gone wild! Clean up the supermarket aisle 5!",
        }

        print(f"Starting Level {level_number}: {level_messages[level_number]}")

        # Create level with current health
        self.level = Level(
            screen,
            level_number,
            environments[level_number],
            enemies[level_number],
            player_health=self.player_health,  # Pass current health to the level
        )

        # Set the player's jump height to 30% of the screen height for non-boss levels
        desired_jump_height = SCREEN_HEIGHT * 0.3  # 30% of screen height
        self.level.player.jump_power = math.sqrt(
            2 * self.level.player.gravity * desired_jump_height
        )
        print(
            f"Player jump power set to reach 30% of screen height: {self.level.player.jump_power}"
        )

        self.state = PLAYING

    def complete_level(self):
        """Handle level completion"""
        self.state = LEVEL_COMPLETE
        self.score += self.level.score

        # Save player's current health for the next level
        self.player_health = self.level.player.health
        print(f"Player health at level completion: {self.player_health}")

        # Funny completion messages for each level
        completion_messages = {
            1: "Veggie massacre complete! Those carrots never saw it coming!",
            2: "Bananas? More like banana SPLIT! You've shown those yellow menaces!",
            3: "Grandma rampage contained! Denture-dropping action at its finest!",
        }

        print(
            f"Level {self.current_level} completed! {completion_messages[self.current_level]}"
        )

        # Check if all regular levels are completed
        if self.current_level >= self.max_levels:
            print("All regular levels completed! Time for the BOSS!")
            # Prepare for boss level instead of game over
            self.current_level = 4  # Level 4 is the boss level
        else:
            # Prepare for next level
            self.current_level += 1

    def player_died(self):
        """Handle player death"""
        self.state = PLAYER_DIED

        # Save player's health state (which will be 0)
        self.player_health = 0

        # Play death sound
        if self.death_sound:
            self.death_sound.play()

        # Select a random death message for the current level
        import random

        messages = self.death_messages.get(self.current_level, ["You died!"])
        self.current_death_message = random.choice(messages)
        print(f"Player died: {self.current_death_message}")

    def toggle_music(self):
        """Toggle background music on/off"""
        if self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False
            print("Music paused")
        else:
            pygame.mixer.music.unpause()
            self.music_playing = True
            print("Music resumed")

    def complete_boss(self):
        """Handle boss level completion"""
        # Clean up boss level resources
        if self.boss_level:
            self.boss_level.cleanup()

        # Resume regular background music
        if hasattr(self, "music_playing") and not self.music_playing:
            pygame.mixer.music.unpause()
            self.music_playing = True

        # Add boss level score to total score
        self.score += self.boss_level.score

        # Save player's health
        self.player_health = self.boss_level.player.health
        print(f"Boss defeated! Final health: {self.player_health}")

        print("Congratulations! You've completed the game and defeated the boss!")
        self.state = GAME_OVER

    def run(self):
        """Main game loop"""
        running = True

        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Global key controls
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.toggle_music()

                # Handle menu selection
                if self.state == MENU:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            # Only process ENTER when instructions are not showing
                            if not self.menu.show_instructions:
                                if (
                                    self.menu.options[self.menu.selected_option]
                                    == "Start Game"
                                ):
                                    # Reset player health to 500 when starting a new game
                                    self.player_health = 500
                                    self.start_level(1)
                                # Quit option has been moved to bottom right as a separate button
                            else:
                                # If instructions are showing, close them
                                self.menu.show_instructions = False

                    # Check for menu mouse events
                    selected = self.menu.handle_event(event)
                    if selected == "start_game":
                        # Reset player health to 500 when starting a new game
                        self.player_health = 500
                        self.start_level(1)
                    elif selected == "quit":
                        # Quit the game
                        running = False

                # Level completion
                elif self.state == LEVEL_COMPLETE:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.current_level <= self.max_levels:
                                self.start_level(self.current_level)
                            elif self.current_level == 4:  # Boss level
                                self.start_level(4)  # Start boss level
                            else:
                                self.state = MENU

                # Player died
                elif self.state == PLAYER_DIED:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.state = MENU

                # Game over
                elif self.state == GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.state = MENU
                            self.current_level = 1
                            self.score = 0

            # Update and render based on game state
            if self.state == MENU:
                self.menu.update()
                self.menu.render(screen)

            elif self.state == PLAYING:
                result = self.level.update()
                self.level.render(screen)

                if result is True:  # Level completed (True)
                    self.complete_level()
                elif result is False:  # Player died (False)
                    self.player_died()

            elif self.state == BOSS_LEVEL:
                # Handle boss level state
                result = self.boss_level.update()
                self.boss_level.render(screen)

                if result is True:  # Boss defeated (True)
                    self.complete_boss()
                elif result is False:  # Player died (False)
                    self.player_died()

            elif self.state == LEVEL_COMPLETE:
                # Create a semi-transparent overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))  # Black with 70% transparency
                screen.blit(overlay, (0, 0))

                # Show level complete screen
                font = pygame.font.SysFont("comicsans", 70)
                level_complete_text = f"Level {self.current_level - 1} Complete!"

                # Draw title with background
                title_y = SCREEN_HEIGHT // 3
                render_text_with_shadow(
                    screen,
                    level_complete_text,
                    font,
                    (255, 255, 0),
                    (
                        SCREEN_WIDTH // 2 - font.size(level_complete_text)[0] // 2,
                        title_y,
                    ),
                    shadow_offset=3,
                    bg_color=(50, 50, 100, 180),
                )

                # Show funny completion message
                messages = {
                    1: "Those veggies got SERVED!",
                    2: "Bananas? More like SPLIT!",
                    3: "Grandmas sent back to bingo night!",
                }

                message_text = messages.get(self.current_level - 1, "")
                font = pygame.font.SysFont("comicsans", 40)

                # Draw message with background
                message_y = title_y + 120
                render_text_with_shadow(
                    screen,
                    message_text,
                    font,
                    (255, 255, 255),
                    (SCREEN_WIDTH // 2 - font.size(message_text)[0] // 2, message_y),
                    bg_color=(50, 100, 50, 160),
                )

                # Continue prompt
                prompt_text = "Press ENTER to continue..."
                prompt_y = message_y + 100
                render_text_with_shadow(
                    screen,
                    prompt_text,
                    font,
                    (200, 200, 200),
                    (SCREEN_WIDTH // 2 - font.size(prompt_text)[0] // 2, prompt_y),
                    bg_color=(0, 0, 0, 160),
                )

            elif self.state == PLAYER_DIED:
                # Fill background with dark red
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill((100, 0, 0))
                overlay.set_alpha(220)
                screen.blit(overlay, (0, 0))

                # Show game over message
                font = pygame.font.SysFont("comicsans", 70)
                death_title = "BABY DOWN!"
                title_y = SCREEN_HEIGHT // 3 - 30  # Moved 30px higher

                render_text_with_shadow(
                    screen,
                    death_title,
                    font,
                    (255, 255, 255),
                    (SCREEN_WIDTH // 2 - font.size(death_title)[0] // 2, title_y),
                    shadow_offset=3,
                    bg_color=(100, 0, 0, 200),
                )

                # Show funny death message
                font = pygame.font.SysFont("comicsans", 40)
                message_y = title_y + 180  # Increased from 150 to 180

                # Split long messages across multiple lines if needed
                if len(self.current_death_message) > 40:
                    words = self.current_death_message.split()
                    lines = []
                    current_line = ""

                    for word in words:
                        test_line = current_line + " " + word if current_line else word
                        if font.size(test_line)[0] < SCREEN_WIDTH - 200:
                            current_line = test_line
                        else:
                            lines.append(current_line)
                            current_line = word

                    if current_line:
                        lines.append(current_line)

                    # Draw each line
                    for i, line in enumerate(lines):
                        render_text_with_shadow(
                            screen,
                            line,
                            font,
                            (255, 200, 200),
                            (
                                SCREEN_WIDTH // 2 - font.size(line)[0] // 2,
                                message_y + i * 45,
                            ),
                            bg_color=(80, 0, 0, 180),
                        )
                else:
                    render_text_with_shadow(
                        screen,
                        self.current_death_message,
                        font,
                        (255, 200, 200),
                        (
                            SCREEN_WIDTH // 2
                            - font.size(self.current_death_message)[0] // 2,
                            message_y,
                        ),
                        bg_color=(80, 0, 0, 180),
                    )

                # Show score
                score_text = f"Score: {self.score + self.level.score}"
                score_y = message_y + 130  # Increased from 100 to 130
                render_text_with_shadow(
                    screen,
                    score_text,
                    font,
                    (255, 255, 0),
                    (SCREEN_WIDTH // 2 - font.size(score_text)[0] // 2, score_y),
                    bg_color=(60, 30, 0, 180),
                )

                # Continue prompt
                prompt_text = "Press ENTER to return to menu"
                prompt_y = score_y + 130  # Increased from 100 to 130
                render_text_with_shadow(
                    screen,
                    prompt_text,
                    font,
                    (200, 200, 200),
                    (SCREEN_WIDTH // 2 - font.size(prompt_text)[0] // 2, prompt_y),
                    bg_color=(0, 0, 0, 160),
                )

            elif self.state == GAME_OVER:
                # Create a victory overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 50, 0, 200))  # Dark green with transparency
                screen.blit(overlay, (0, 0))

                # Show game over screen
                font = pygame.font.SysFont("comicsans", 70)
                complete_text = "Game Completed!"
                title_y = SCREEN_HEIGHT // 3

                render_text_with_shadow(
                    screen,
                    complete_text,
                    font,
                    (255, 0, 0),
                    (SCREEN_WIDTH // 2 - font.size(complete_text)[0] // 2, title_y),
                    shadow_offset=3,
                    bg_color=(0, 70, 0, 180),
                )

                # Add John Cena victory message
                cena_text = "Champ life ain't easy!"
                cena_y = title_y + 85
                font_cena = pygame.font.SysFont("comicsans", 40)

                render_text_with_shadow(
                    screen,
                    cena_text,
                    font_cena,
                    (255, 255, 255),
                    (SCREEN_WIDTH // 2 - font_cena.size(cena_text)[0] // 2, cena_y),
                    shadow_offset=2,
                    bg_color=(100, 50, 150, 200),
                )

                # Show final score
                score_text = f"Final Score: {self.score}"
                score_y = cena_y + 80  # Adjusted position to account for new message
                font = pygame.font.SysFont("comicsans", 50)

                render_text_with_shadow(
                    screen,
                    score_text,
                    font,
                    (255, 255, 0),
                    (SCREEN_WIDTH // 2 - font.size(score_text)[0] // 2, score_y),
                    bg_color=(0, 60, 0, 180),
                )

                # Play again prompt
                font = pygame.font.SysFont("comicsans", 40)
                restart_text = "Press ENTER to play again"
                restart_y = score_y + 100

                render_text_with_shadow(
                    screen,
                    restart_text,
                    font,
                    (200, 200, 200),
                    (SCREEN_WIDTH // 2 - font.size(restart_text)[0] // 2, restart_y),
                    bg_color=(0, 0, 0, 160),
                )

            # Update display and maintain frame rate
            pygame.display.update()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()
