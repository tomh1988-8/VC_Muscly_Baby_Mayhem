import pygame
import os


def create_flag_image():
    """Create a simple flag image for the game goal"""
    # Initialize pygame
    pygame.init()

    # Flag dimensions
    width, height = 70, 70

    # Create a transparent surface
    flag = pygame.Surface((width, height), pygame.SRCALPHA)

    # Draw flag pole
    pole_color = (150, 75, 0)  # Brown
    pygame.draw.rect(flag, pole_color, (width // 2 - 3, 10, 6, height - 10))

    # Draw flag
    flag_color = (255, 215, 0)  # Gold
    flag_points = [
        (width // 2 + 3, 10),
        (width // 2 + 3 + 30, 20),
        (width // 2 + 3 + 30, 50),
        (width // 2 + 3, 40),
    ]
    pygame.draw.polygon(flag, flag_color, flag_points)

    # Add some detail to the flag - victory symbol
    symbol_color = (255, 0, 0)  # Red
    pygame.draw.polygon(
        flag,
        symbol_color,
        [(width // 2 + 18, 25), (width // 2 + 23, 35), (width // 2 + 13, 30)],
    )

    # Add a base
    base_color = (100, 100, 100)  # Gray
    pygame.draw.rect(flag, base_color, (width // 2 - 10, height - 15, 20, 15))

    # Save the flag image
    os.makedirs("assets/images", exist_ok=True)
    pygame.image.save(flag, "assets/images/goal_flag.png")
    print("Flag image created and saved to assets/images/goal_flag.png")


if __name__ == "__main__":
    create_flag_image()
