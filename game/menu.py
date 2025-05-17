import pygame
import random
import math


class Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.selected_option = 0
        self.options = [
            "Start Game",
            "Instructions",
        ]  # Removed "Quit" from main options
        self.title_font = pygame.font.SysFont("comicsans", 80, bold=True)
        self.option_font = pygame.font.SysFont("comicsans", 50)
        self.description_font = pygame.font.SysFont("comicsans", 30)
        self.controls_font = pygame.font.SysFont("comicsans", 22)

        # Variables for quit button highlighting
        self.quit_highlighted = False

        # Title bounce animation
        self.title_y = height // 6
        self.bounce_speed = 1
        self.bounce_height = 10
        self.bounce_direction = 1

        # Animation timer for cloud movement
        self.animation_timer = 0

        # Show instructions popup flag
        self.show_instructions = False

        # Background
        self.bg_color = (100, 170, 255)  # Sky blue for cloud theme

        # Generate cloud positions - ensure they're not near the title
        self.clouds = []
        title_area = (
            width // 4,
            20,
            width // 2,
            height // 3,
        )  # Reserve space for title
        for i in range(10):
            # Generate cloud position
            cloud_x = random.randint(0, width)
            cloud_y = random.randint(0, height)
            cloud_size = random.randint(50, 150)

            # Check if cloud might overlap with title area
            cloud_rect = pygame.Rect(
                cloud_x - cloud_size,
                cloud_y - cloud_size,
                cloud_size * 2,
                cloud_size * 2,
            )
            title_rect = pygame.Rect(title_area)

            # If there's overlap, move cloud away from title area
            if cloud_rect.colliderect(title_rect):
                if cloud_y < height // 2:
                    cloud_y = title_rect.bottom + cloud_size
                else:
                    cloud_y = title_rect.top - cloud_size

            self.clouds.append(
                {
                    "x": cloud_x,
                    "y": cloud_y,
                    "size": cloud_size,
                    "speed": random.uniform(0.2, 0.5),
                }
            )

        # Load a sample sound for menu selection
        try:
            self.select_sound = pygame.mixer.Sound("assets/sounds/select.wav")
        except:
            print("Warning: Menu select sound not found")
            self.select_sound = None

    def update(self):
        """Update menu animations and handle input"""
        # Handle menu navigation
        keys = pygame.key.get_pressed()

        # Handle key press with simple cooldown using current time
        current_time = pygame.time.get_ticks()
        if not hasattr(self, "last_key_time"):
            self.last_key_time = 0

        if current_time - self.last_key_time > 200:  # 200ms cooldown
            # If instructions are showing, ENTER or ESCAPE should close them
            if self.show_instructions and (
                keys[pygame.K_RETURN] or keys[pygame.K_ESCAPE]
            ):
                self.show_instructions = False
                self.last_key_time = current_time
                if self.select_sound:
                    self.select_sound.play()
                return

            # Only process menu navigation when instructions are not showing
            if not self.show_instructions:
                if keys[pygame.K_UP] and self.selected_option > 0:
                    self.selected_option -= 1
                    self.last_key_time = current_time
                    if self.select_sound:
                        self.select_sound.play()
                elif (
                    keys[pygame.K_DOWN] and self.selected_option < len(self.options) - 1
                ):
                    self.selected_option += 1
                    self.last_key_time = current_time
                    if self.select_sound:
                        self.select_sound.play()
                # Add escape key to quit
                elif keys[pygame.K_ESCAPE]:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                    self.last_key_time = current_time

        # Simple title bounce animation
        self.title_y += self.bounce_direction * self.bounce_speed
        if abs(self.title_y - self.height // 6) >= self.bounce_height:
            self.bounce_direction *= -1

        # Update animation timer
        self.animation_timer += 1

        # Update cloud positions
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"]
            if cloud["x"] > self.width + cloud["size"]:
                cloud["x"] = -cloud["size"]

    def handle_event(self, event):
        """Handle menu events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            # Check if instructions are showing
            if self.show_instructions:
                # Calculate popup dimensions to match _render_instructions_popup
                popup_width = int(self.width * 0.8)
                popup_height = int(self.height * 0.7)
                popup_x = (self.width - popup_width) // 2
                popup_y = (self.height - popup_height) // 2

                # Calculate close button position (same as in _render_instructions_popup)
                button_width = 100
                button_height = 40
                button_x = popup_x + (popup_width - button_width) // 2
                button_y = popup_y + popup_height - button_height - 20

                close_button = pygame.Rect(
                    button_x, button_y, button_width, button_height
                )

                if close_button.collidepoint(event.pos):
                    self.show_instructions = False
                return False

            # Check if any menu option was clicked
            panel_height = 270  # Further increased height for better spacing
            panel_y = self.height - panel_height - 20

            # Calculate option heights for positioning - same as in render method
            option_heights = [
                self.option_font.size(option)[1] for option in self.options
            ]

            # Calculate starting position - same as in render method
            total_content_height = sum(option_heights) + 40
            starting_y = panel_y + (panel_height - total_content_height) // 2

            for i, option in enumerate(self.options):
                option_width = self.option_font.size(option)[0]
                option_height = self.option_font.size(option)[1]
                option_x = self.width // 2 - option_width // 2

                # Calculate position - same logic as in render method
                if i == 0:
                    option_y = starting_y
                else:
                    option_y = (
                        starting_y + sum(option_heights[:i]) + (i * 20)
                    )  # 20px gap between options

                option_rect = pygame.Rect(
                    option_x, option_y, option_width, option_height
                )
                if option_rect.collidepoint(event.pos):
                    self.selected_option = i
                    if option == "Instructions":
                        self.show_instructions = True
                        return False
                    elif self.options[self.selected_option] == "Start Game":
                        return "start_game"  # Return "start_game" instead of True

            # Check if Quit button was clicked
            quit_font = pygame.font.SysFont("comicsans", 40)
            quit_text = "Quit"
            quit_width = quit_font.size(quit_text)[0] + 20
            quit_height = quit_font.size(quit_text)[1] + 10
            quit_x = self.width - quit_width - 20
            quit_y = self.height - quit_height - 20

            quit_rect = pygame.Rect(quit_x, quit_y, quit_width, quit_height)
            if quit_rect.collidepoint(event.pos):
                return "quit"  # Return "quit" instead of True

        # Update hover state for quit button
        elif event.type == pygame.MOUSEMOTION:
            # Calculate quit button rect
            quit_font = pygame.font.SysFont("comicsans", 40)
            quit_text = "Quit"
            quit_width = quit_font.size(quit_text)[0] + 20
            quit_height = quit_font.size(quit_text)[1] + 10
            quit_x = self.width - quit_width - 20
            quit_y = self.height - quit_height - 20

            quit_rect = pygame.Rect(quit_x, quit_y, quit_width, quit_height)
            self.quit_highlighted = quit_rect.collidepoint(event.pos)

        return False  # No option was selected

    def render_text_with_shadow(
        self,
        screen,
        text,
        font,
        color,
        position,
        shadow_color=(0, 0, 0),
        shadow_offset=2,
        bg_color=None,
    ):
        """Render text with a shadow for better visibility"""
        # Create text surface
        text_surface = font.render(text, True, color)
        text_width, text_height = text_surface.get_size()

        # Create background if requested
        if bg_color:
            # Add padding around text
            padding = 8
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

        # Draw shadow
        shadow_surface = font.render(text, True, shadow_color)
        shadow_position = (position[0] + shadow_offset, position[1] + shadow_offset)
        screen.blit(shadow_surface, shadow_position)

        # Render main text
        screen.blit(text_surface, position)

        return text_surface

    def render(self, screen):
        """Render the menu"""
        # Fill background with gradient sky
        for y in range(self.height):
            # Calculate sky color (lighter blue at top, darker at bottom)
            blue_val = max(135, 255 - int(y * 0.5))
            color = (135, 206, blue_val)
            pygame.draw.line(screen, color, (0, y), (self.width, y))

        # Draw animated clouds
        for cloud in self.clouds:
            # Draw several overlapping white circles to create a cloud
            for offset in [
                (0, 0),
                (cloud["size"] // 2, -cloud["size"] // 3),
                (-cloud["size"] // 2, -cloud["size"] // 4),
                (cloud["size"] // 3, cloud["size"] // 3),
                (-cloud["size"] // 3, cloud["size"] // 4),
            ]:
                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (int(cloud["x"] + offset[0]), int(cloud["y"] + offset[1])),
                    cloud["size"] // 2,
                )

        # Draw title with shadow - add animated glow effect
        glow_factor = (math.sin(self.animation_timer / 20) + 1) * 0.5
        title_color = (
            int(255),
            int(20 + glow_factor * 80),
            int(147 + glow_factor * 50),
        )

        title_position = (
            self.width // 2 - self.title_font.size("MUSCLE BABY MAYHEM")[0] // 2,
            self.title_y,
        )

        # Draw larger white oval behind title for better visibility
        title_width = self.title_font.size("MUSCLE BABY MAYHEM")[0]
        title_height = self.title_font.size("MUSCLE BABY MAYHEM")[1]
        pygame.draw.ellipse(
            screen,
            (255, 255, 255),
            (
                title_position[0] - 40,
                title_position[1] - 20,
                title_width + 80,
                title_height + 40,
            ),
            0,  # Filled ellipse
        )

        # Add a slight glow/outline to title
        glow_size = 3
        for offset_x in range(-glow_size, glow_size + 1):
            for offset_y in range(-glow_size, glow_size + 1):
                if offset_x != 0 or offset_y != 0:  # Skip the center position
                    glow_pos = (
                        title_position[0] + offset_x,
                        title_position[1] + offset_y,
                    )
                    shadow_surface = self.title_font.render(
                        "MUSCLE BABY MAYHEM", True, (255, 100, 180, 50)
                    )
                    screen.blit(shadow_surface, glow_pos)

        # Render the title with enhanced visibility
        self.render_text_with_shadow(
            screen,
            "MUSCLE BABY MAYHEM",
            self.title_font,
            title_color,
            title_position,
            shadow_offset=3,
        )

        # Draw subtitle with shadow
        subtitle_position = (
            self.width // 2
            - self.description_font.size("The adventures of a very strong infant")[0]
            // 2,
            self.title_y + 100,
        )
        self.render_text_with_shadow(
            screen,
            "The adventures of a very strong infant",
            self.description_font,
            (100, 50, 150),
            subtitle_position,
            bg_color=(255, 255, 255, 180),
        )

        # Create a semi-transparent panel for menu options
        panel_height = 270  # Further increased height for better spacing
        panel_y = self.height - panel_height - 20
        panel = pygame.Surface((self.width // 2, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))  # Semi-transparent black
        panel_x = self.width // 4
        screen.blit(panel, (panel_x, panel_y))

        # Draw menu options with fixed positions
        # Calculate option heights for positioning
        option_heights = [self.option_font.size(option)[1] for option in self.options]

        # Calculate starting position to center options in panel
        total_content_height = sum(option_heights) + 40  # 20px gap between each option
        starting_y = panel_y + (panel_height - total_content_height) // 2

        # Draw each option at its explicit position
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = (255, 0, 0)  # Red for selected
                bg_color = (255, 255, 255, 160)  # Highlighted background
            else:
                color = (0, 0, 0)  # Black for unselected
                bg_color = (200, 200, 200, 120)  # Regular background

            # Calculate position - first option at starting_y, others positioned below with 20px gaps
            if i == 0:
                option_y = starting_y
            else:
                option_y = (
                    starting_y + sum(option_heights[:i]) + (i * 20)
                )  # 20px gap between options

            option_pos = (
                self.width // 2 - self.option_font.size(option)[0] // 2,
                option_y,
            )

            self.render_text_with_shadow(
                screen, option, self.option_font, color, option_pos, bg_color=bg_color
            )

        # Draw controls instructions - moved further down
        instructions = "Press ENTER to select"
        instruction_pos = (
            self.width // 2 - self.description_font.size(instructions)[0] // 2,
            self.height - 70,  # Moved down from -40 to -70
        )
        self.render_text_with_shadow(
            screen,
            instructions,
            self.description_font,
            (0, 0, 0),
            instruction_pos,
            bg_color=(255, 255, 255, 180),
        )

        # Draw Quit button in bottom right
        quit_text = "Quit"
        quit_font = pygame.font.SysFont("comicsans", 40)
        # Determine button size with padding
        quit_width = quit_font.size(quit_text)[0] + 20
        quit_height = quit_font.size(quit_text)[1] + 10
        quit_x = self.width - quit_width - 20  # 20px from right edge
        quit_y = self.height - quit_height - 20  # 20px from bottom edge

        # Draw button background with different color if highlighted
        quit_bg_color = (
            (200, 50, 50, 220) if self.quit_highlighted else (150, 50, 50, 180)
        )

        # Create button background
        quit_bg = pygame.Surface((quit_width, quit_height), pygame.SRCALPHA)
        quit_bg.fill(quit_bg_color)
        screen.blit(quit_bg, (quit_x, quit_y))

        # Draw button border
        pygame.draw.rect(
            screen, (0, 0, 0), (quit_x, quit_y, quit_width, quit_height), 2
        )

        # Draw quit text
        quit_text_pos = (
            quit_x + (quit_width - quit_font.size(quit_text)[0]) // 2,
            quit_y + (quit_height - quit_font.size(quit_text)[1]) // 2,
        )
        self.render_text_with_shadow(
            screen,
            quit_text,
            quit_font,
            (255, 255, 255),
            quit_text_pos,
        )

        # Draw instructions popup if enabled
        if self.show_instructions:
            self._render_instructions_popup(screen)

    def _render_instructions_popup(self, screen):
        """Render the instructions popup"""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark overlay
        screen.blit(overlay, (0, 0))

        # Create popup window
        popup_width = int(self.width * 0.8)
        popup_height = int(self.height * 0.7)
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2

        # Draw popup background
        popup = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup.fill((220, 240, 255, 230))  # Light blue, semi-transparent

        # Draw border
        pygame.draw.rect(popup, (100, 150, 200), (0, 0, popup_width, popup_height), 5)

        # Title
        title = "Game Instructions"
        title_pos = (popup_width // 2 - self.description_font.size(title)[0] // 2, 20)
        self.render_text_with_shadow(
            popup, title, self.description_font, (20, 20, 100), title_pos
        )

        # Content sections
        sections = [
            {
                "title": "Levels:",
                "content": [
                    "Level 1: Battle vegetables in the clouds!",
                    "Level 2: Fight bananas in the jungle!",
                    "Level 3: Take on grandmas in the supermarket!",
                ],
            },
            {
                "title": "Controls:",
                "content": [
                    "Arrow Keys: Move and Jump",
                    "A/D Keys: Aim Left/Right",
                    "Space: Shoot",
                    "M: Toggle Music",
                ],
            },
            {
                "title": "Objective:",
                "content": [
                    "Reach the flag at the end of each level",
                    "Defeat enemies by shooting them",
                    "Avoid enemy attacks",
                    "Complete all three levels to win!",
                ],
            },
        ]

        y_offset = 70
        for section in sections:
            # Section title
            section_title = section["title"]
            section_pos = (30, y_offset)
            self.render_text_with_shadow(
                popup, section_title, self.description_font, (50, 50, 150), section_pos
            )
            y_offset += 40

            # Section content
            for line in section["content"]:
                line_pos = (60, y_offset)
                self.render_text_with_shadow(
                    popup, line, self.controls_font, (50, 50, 50), line_pos
                )
                y_offset += 30

            y_offset += 20  # Extra spacing between sections

        # Close button
        button_width = 100
        button_height = 40
        button_x = (popup_width - button_width) // 2
        button_y = popup_height - button_height - 20

        pygame.draw.rect(
            popup, (100, 100, 100), (button_x, button_y, button_width, button_height)
        )
        pygame.draw.rect(
            popup, (50, 50, 50), (button_x, button_y, button_width, button_height), 2
        )

        close_text = "Close"
        close_pos = (
            button_x + (button_width - self.controls_font.size(close_text)[0]) // 2,
            button_y + (button_height - self.controls_font.size(close_text)[1]) // 2,
        )
        self.render_text_with_shadow(
            popup, close_text, self.controls_font, (255, 255, 255), close_pos
        )

        # Blit popup to screen
        screen.blit(popup, (popup_x, popup_y))
