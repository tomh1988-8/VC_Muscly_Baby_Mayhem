import pygame
import os


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=(100, 100, 100)):
        super().__init__()

        # Try to load platform image
        try:
            platform_img = pygame.image.load(
                "assets/images/platform.png"
            ).convert_alpha()
            self.image = pygame.transform.scale(platform_img, (width, height))
        except Exception as e:
            # Fallback to colored rectangle if image loading fails
            print(f"Error loading platform image: {e}")
            self.image = pygame.Surface((width, height))
            self.image.fill(color)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
